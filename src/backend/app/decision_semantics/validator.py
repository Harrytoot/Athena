from app.decision_semantics.schema import (
    ConsistencyReport,
    ContradictionEntry,
    FactorSemantic,
    SignalSemantic,
    RiskSemantic,
    ScenarioSemantic,
)

CONTRADICTION_SIGNAL_RISK = "signal_vs_risk"
CONTRADICTION_SCENARIO_SIGNAL = "scenario_vs_signal"
CONTRADICTION_FACTOR_CONFLICT = "factor_conflict"
CONTRADICTION_SCENARIO_MISMATCH = "scenario_mismatch"

SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

DIRECTION_LONG = "LONG"
DIRECTION_SHORT = "SHORT"
DIRECTION_NEUTRAL = "NEUTRAL"


class SemanticValidator:

    def validate(
        self,
        signal: SignalSemantic,
        factors: list[FactorSemantic] | None = None,
        risk: RiskSemantic | None = None,
        scenario: ScenarioSemantic | None = None,
    ) -> ConsistencyReport:
        contradictions: list[ContradictionEntry] = []

        if risk is not None:
            contradictions.extend(self._check_signal_vs_risk(signal, risk))
        if scenario is not None:
            contradictions.extend(self._check_scenario_vs_signal(signal, scenario))
        if factors:
            contradictions.extend(self._check_factor_conflicts(factors))
            contradictions.extend(self._check_factor_vs_signal(factors, signal))

        if not contradictions:
            return ConsistencyReport(
                is_consistent=True,
                contradictions=[],
                consistency_score=1.0,
            )

        high_count = sum(1 for c in contradictions if c.severity == SEVERITY_HIGH)
        medium_count = sum(1 for c in contradictions if c.severity == SEVERITY_MEDIUM)
        low_count = sum(1 for c in contradictions if c.severity == SEVERITY_LOW)

        penalty = high_count * 0.30 + medium_count * 0.15 + low_count * 0.05
        consistency_score = round(max(0.0, 1.0 - penalty), 4)

        return ConsistencyReport(
            is_consistent=False,
            contradictions=contradictions,
            consistency_score=consistency_score,
        )

    def _check_signal_vs_risk(
        self,
        signal: SignalSemantic,
        risk: RiskSemantic,
    ) -> list[ContradictionEntry]:
        results: list[ContradictionEntry] = []

        if signal.direction == DIRECTION_LONG and risk.overall_level == "HIGH":
            results.append(ContradictionEntry(
                contradiction_type=CONTRADICTION_SIGNAL_RISK,
                severity=SEVERITY_HIGH,
                description=f"做多信号与高风险({risk.overall_level})冲突",
            ))
        elif signal.direction == DIRECTION_LONG and risk.overall_level == "MODERATE":
            results.append(ContradictionEntry(
                contradiction_type=CONTRADICTION_SIGNAL_RISK,
                severity=SEVERITY_MEDIUM,
                description=f"做多信号在中等风险({risk.overall_level})下需谨慎",
            ))
        elif signal.direction == DIRECTION_SHORT and risk.overall_level == "HIGH":
            results.append(ContradictionEntry(
                contradiction_type=CONTRADICTION_SIGNAL_RISK,
                severity=SEVERITY_HIGH,
                description=f"做空信号与高风险({risk.overall_level})叠加",
            ))

        if signal.strength >= 0.8 and risk.overall_level == "HIGH":
            if not any(
                c.description == f"做多信号与高风险({risk.overall_level})冲突"
                for c in results
            ):
                results.append(ContradictionEntry(
                    contradiction_type=CONTRADICTION_SIGNAL_RISK,
                    severity=SEVERITY_HIGH,
                    description=f"强信号({signal.strength:.1%})与高风险不匹配",
                ))

        return results

    def _check_scenario_vs_signal(
        self,
        signal: SignalSemantic,
        scenario: ScenarioSemantic,
    ) -> list[ContradictionEntry]:
        results: list[ContradictionEntry] = []

        if scenario.state_change_count >= len(scenario.entries) * 0.5 and len(scenario.entries) > 0:
            results.append(ContradictionEntry(
                contradiction_type=CONTRADICTION_SCENARIO_SIGNAL,
                severity=SEVERITY_HIGH,
                description=f"多数情景({scenario.state_change_count}/{len(scenario.entries)})下方向改变",
            ))

        if scenario.stability_score < 0.3:
            results.append(ContradictionEntry(
                contradiction_type=CONTRADICTION_SCENARIO_SIGNAL,
                severity=SEVERITY_HIGH,
                description=f"情景稳定性极低 ({scenario.stability_score:.2f})",
            ))
        elif scenario.stability_score < 0.6:
            results.append(ContradictionEntry(
                contradiction_type=CONTRADICTION_SCENARIO_SIGNAL,
                severity=SEVERITY_MEDIUM,
                description=f"情景稳定性偏低 ({scenario.stability_score:.2f})",
            ))

        if signal.direction != DIRECTION_NEUTRAL and abs(scenario.worst_case_score_change) >= 30:
            results.append(ContradictionEntry(
                contradiction_type=CONTRADICTION_SCENARIO_MISMATCH,
                severity=SEVERITY_HIGH,
                description=f"极端情景下评分剧烈变化 ({scenario.worst_case_score_change:+.1f})",
            ))

        return results

    def _check_factor_conflicts(
        self,
        factors: list[FactorSemantic],
    ) -> list[ContradictionEntry]:
        results: list[ContradictionEntry] = []

        bullish_factors = [f for f in factors if f.is_bullish]
        bearish_factors = [f for f in factors if not f.is_bullish]

        if bullish_factors and bearish_factors:
            if len(bearish_factors) >= 2:
                results.append(ContradictionEntry(
                    contradiction_type=CONTRADICTION_FACTOR_CONFLICT,
                    severity=SEVERITY_MEDIUM,
                    description=f"因子分歧: {len(bullish_factors)}个偏多 vs {len(bearish_factors)}个偏空",
                ))

            for bull_f in bullish_factors:
                for bear_f in bearish_factors:
                    if abs(bull_f.value - bear_f.value) >= 60:
                        results.append(ContradictionEntry(
                            contradiction_type=CONTRADICTION_FACTOR_CONFLICT,
                            severity=SEVERITY_HIGH,
                            description=f"因子极端冲突: {bull_f.label}({bull_f.value:.0f}) vs {bear_f.label}({bear_f.value:.0f})",
                        ))
                        break

        strong_factors = [f for f in factors if f.value >= 80]
        weak_factors = [f for f in factors if f.value <= 20]
        if strong_factors and weak_factors:
            for sf in strong_factors:
                for wf in weak_factors:
                    results.append(ContradictionEntry(
                        contradiction_type=CONTRADICTION_FACTOR_CONFLICT,
                        severity=SEVERITY_HIGH,
                        description=f"因子两极化: {sf.label}({sf.value:.0f}) vs {wf.label}({wf.value:.0f})",
                    ))
                    break

        return results[:5]

    def _check_factor_vs_signal(
        self,
        factors: list[FactorSemantic],
        signal: SignalSemantic,
    ) -> list[ContradictionEntry]:
        results: list[ContradictionEntry] = []

        if signal.direction == DIRECTION_NEUTRAL:
            return results

        expected_bullish = signal.direction == DIRECTION_LONG
        disagreeing = [f for f in factors if f.is_bullish != expected_bullish]

        heavy_disagreers = [f for f in disagreeing if f.weight >= 0.25]
        for f in heavy_disagreers:
            results.append(ContradictionEntry(
                contradiction_type=CONTRADICTION_FACTOR_CONFLICT,
                severity=SEVERITY_MEDIUM,
                description=f"重要因子[{f.label}]与信号方向({signal.direction_label})相悖 (值={f.value:.0f})",
            ))

        if len(disagreeing) >= 3:
            results.append(ContradictionEntry(
                contradiction_type=CONTRADICTION_FACTOR_CONFLICT,
                severity=SEVERITY_HIGH,
                description=f"多数因子({len(disagreeing)}/{len(factors)})与信号方向({signal.direction_label})不一致",
            ))

        return results
