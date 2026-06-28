from dataclasses import dataclass, field

FACTOR_WEIGHT_TREND = 0.30
FACTOR_WEIGHT_LIQUIDITY = 0.25
FACTOR_WEIGHT_BREADTH = 0.20
FACTOR_WEIGHT_VOLATILITY = 0.15
FACTOR_WEIGHT_SENTIMENT = 0.10

MODEL_VERSION = "1.0.0"

SCENARIO_MARKET_SHOCK_NEG5 = "market_shock_neg5"
SCENARIO_MARKET_SHOCK_NEG10 = "market_shock_neg10"
SCENARIO_MARKET_SHOCK_POS5 = "market_shock_pos5"
SCENARIO_VOLATILITY_SPIKE = "volatility_spike_2x"
SCENARIO_VOLATILITY_COLLAPSE = "volatility_collapse_half"
SCENARIO_LIQUIDITY_DRYUP = "liquidity_dryup"
SCENARIO_TREND_REVERSAL = "trend_reversal"
SCENARIO_SENTIMENT_CRASH = "sentiment_crash"


@dataclass
class ScenarioDefinition:
    scenario_id: str
    name: str
    description: str
    price_shift_pct: float = 0.0
    volatility_multiplier: float = 1.0
    liquidity_shift: float = 0.0
    trend_adjustment: float = 0.0
    breadth_adjustment: float = 0.0
    sentiment_adjustment: float = 0.0


@dataclass
class ScenarioResult:
    scenario: ScenarioDefinition
    original_score: float
    simulated_score: float
    score_change: float
    original_state: str
    simulated_state: str
    state_changed: bool
    direction_change: str
    impact_assessment: str
    original_factors: dict[str, float] = field(default_factory=dict)
    simulated_factors: dict[str, float] = field(default_factory=dict)


def _build_default_scenarios() -> list[ScenarioDefinition]:
    return [
        ScenarioDefinition(
            scenario_id=SCENARIO_MARKET_SHOCK_NEG5,
            name="市场冲击 -5%",
            description="单日市场下跌5%，测试信号稳定性",
            price_shift_pct=-0.05,
        ),
        ScenarioDefinition(
            scenario_id=SCENARIO_MARKET_SHOCK_NEG10,
            name="市场冲击 -10%",
            description="单日市场暴跌10%，极端冲击测试",
            price_shift_pct=-0.10,
        ),
        ScenarioDefinition(
            scenario_id=SCENARIO_MARKET_SHOCK_POS5,
            name="市场反弹 +5%",
            description="单日市场上涨5%，测试信号响应",
            price_shift_pct=0.05,
        ),
        ScenarioDefinition(
            scenario_id=SCENARIO_VOLATILITY_SPIKE,
            name="波动率飙升 2x",
            description="波动率翻倍，测试极端波动下的信号韧性",
            volatility_multiplier=2.0,
        ),
        ScenarioDefinition(
            scenario_id=SCENARIO_VOLATILITY_COLLAPSE,
            name="波动率崩塌 0.5x",
            description="波动率减半，测试低波动环境信号表现",
            volatility_multiplier=0.5,
        ),
        ScenarioDefinition(
            scenario_id=SCENARIO_LIQUIDITY_DRYUP,
            name="流动性枯竭",
            description="流动性骤降50%，测试流动性风险",
            liquidity_shift=-50.0,
        ),
        ScenarioDefinition(
            scenario_id=SCENARIO_TREND_REVERSAL,
            name="趋势反转",
            description="趋势方向逆转，测试策略适应性",
            trend_adjustment=-30.0,
        ),
        ScenarioDefinition(
            scenario_id=SCENARIO_SENTIMENT_CRASH,
            name="情绪崩溃",
            description="市场情绪骤降，测试情绪因子影响",
            sentiment_adjustment=-40.0,
        ),
    ]


class ScenarioSimulator:

    def __init__(self, scenarios: list[ScenarioDefinition] | None = None):
        self._scenarios = scenarios or _build_default_scenarios()

    @property
    def scenarios(self) -> list[ScenarioDefinition]:
        return list(self._scenarios)

    def simulate(
        self,
        trend: float,
        liquidity: float,
        breadth: float,
        volatility: float,
        sentiment: float,
    ) -> list[ScenarioResult]:
        factors = {
            "trend": trend,
            "liquidity": liquidity,
            "breadth": breadth,
            "volatility": volatility,
            "sentiment": sentiment,
        }
        original_score = self._compute_score(
            trend, liquidity, breadth, volatility, sentiment
        )
        original_state = self._classify_state(original_score)

        results: list[ScenarioResult] = []
        for scenario in self._scenarios:
            sim_factors = self._apply_scenario(factors, scenario)
            sim_score = self._compute_score(
                sim_factors["trend"],
                sim_factors["liquidity"],
                sim_factors["breadth"],
                sim_factors["volatility"],
                sim_factors["sentiment"],
            )
            sim_state = self._classify_state(sim_score)

            score_change = round(sim_score - original_score, 2)
            state_changed = sim_state != original_state

            direction_change = self._direction_change(original_state, sim_state)

            impact = self._assess_impact(
                scenario, original_score, sim_score, score_change, state_changed
            )

            results.append(ScenarioResult(
                scenario=scenario,
                original_score=original_score,
                simulated_score=round(sim_score, 2),
                score_change=score_change,
                original_state=original_state,
                simulated_state=sim_state,
                state_changed=state_changed,
                direction_change=direction_change,
                impact_assessment=impact,
                original_factors=dict(factors),
                simulated_factors=sim_factors,
            ))

        return results

    def run_custom(
        self,
        trend: float,
        liquidity: float,
        breadth: float,
        volatility: float,
        sentiment: float,
        scenario: ScenarioDefinition,
    ) -> ScenarioResult:
        factors = {
            "trend": trend,
            "liquidity": liquidity,
            "breadth": breadth,
            "volatility": volatility,
            "sentiment": sentiment,
        }
        original_score = self._compute_score(**factors)
        original_state = self._classify_state(original_score)

        sim_factors = self._apply_scenario(factors, scenario)
        sim_score = self._compute_score(**sim_factors)
        sim_state = self._classify_state(sim_score)

        return ScenarioResult(
            scenario=scenario,
            original_score=original_score,
            simulated_score=round(sim_score, 2),
            score_change=round(sim_score - original_score, 2),
            original_state=original_state,
            simulated_state=sim_state,
            state_changed=sim_state != original_state,
            direction_change=self._direction_change(original_state, sim_state),
            impact_assessment=self._assess_impact(
                scenario, original_score, sim_score,
                round(sim_score - original_score, 2), sim_state != original_state
            ),
            original_factors=dict(factors),
            simulated_factors=sim_factors,
        )

    def _compute_score(
        self,
        trend: float,
        liquidity: float,
        breadth: float,
        volatility: float,
        sentiment: float,
    ) -> float:
        return round(
            trend * FACTOR_WEIGHT_TREND
            + liquidity * FACTOR_WEIGHT_LIQUIDITY
            + breadth * FACTOR_WEIGHT_BREADTH
            + volatility * FACTOR_WEIGHT_VOLATILITY
            + sentiment * FACTOR_WEIGHT_SENTIMENT,
            2,
        )

    def _classify_state(self, score: float) -> str:
        if score >= 80:
            return "Strong Bull"
        if score >= 60:
            return "Bull"
        if score >= 40:
            return "Neutral"
        if score >= 20:
            return "Bear"
        return "Extreme Bear"

    def _apply_scenario(
        self,
        factors: dict[str, float],
        scenario: ScenarioDefinition,
    ) -> dict[str, float]:
        result = dict(factors)

        if scenario.volatility_multiplier != 1.0:
            current = result["volatility"]
            new_val = current * scenario.volatility_multiplier
            result["volatility"] = max(0.0, min(100.0, new_val))

        if scenario.liquidity_shift != 0.0:
            current = result["liquidity"]
            result["liquidity"] = max(0.0, min(100.0, current + scenario.liquidity_shift))

        if scenario.trend_adjustment != 0.0:
            current = result["trend"]
            result["trend"] = max(0.0, min(100.0, current + scenario.trend_adjustment))

        if scenario.breadth_adjustment != 0.0:
            current = result["breadth"]
            result["breadth"] = max(0.0, min(100.0, current + scenario.breadth_adjustment))

        if scenario.sentiment_adjustment != 0.0:
            current = result["sentiment"]
            result["sentiment"] = max(0.0, min(100.0, current + scenario.sentiment_adjustment))

        if scenario.price_shift_pct != 0.0:
            pct = scenario.price_shift_pct
            result["trend"] = max(0.0, min(100.0, result["trend"] + pct * 50.0))
            result["sentiment"] = max(0.0, min(100.0, result["sentiment"] + pct * 40.0))
            result["breadth"] = max(0.0, min(100.0, result["breadth"] + pct * 30.0))

        return result

    def _direction_change(self, original_state: str, sim_state: str) -> str:
        if original_state == sim_state:
            return "不变"
        bullish_states = {"Strong Bull", "Bull"}
        orig_bullish = original_state in bullish_states
        sim_bullish = sim_state in bullish_states
        if orig_bullish and not sim_bullish:
            return "多头→中性/空头"
        if not orig_bullish and sim_bullish:
            return "中性/空头→多头"
        return f"{original_state}→{sim_state}"

    def _assess_impact(
        self,
        scenario: ScenarioDefinition,
        original_score: float,
        sim_score: float,
        score_change: float,
        state_changed: bool,
    ) -> str:
        abs_change = abs(score_change)
        severity = (
            "严重" if abs_change >= 20 else
            "显著" if abs_change >= 10 else
            "轻微" if abs_change >= 5 else
            "极小"
        )

        parts = [f"{scenario.name}造成{severity}影响"]
        parts.append(f"评分变化: {score_change:+.1f}")

        if state_changed:
            parts.append(f"状态改变: {self._classify_state(original_score)}→{self._classify_state(sim_score)}")

        if abs_change >= 20:
            parts.append("提示: 该情景下策略信号可能不可靠，建议人工复核")
        elif abs_change >= 10:
            parts.append("提示: 该情景下策略稳定性需要关注")

        return "；".join(parts)
