from decimal import Decimal

from app.production_layer.alerting.alert_rules import (
    LatencySpikeRule,
    ExecutionDriftRule,
    PnLDegradationRule,
    RiskModelDivergenceRule,
    HealthCheckFailureRule,
    FillRateDropRule,
    ExposureLimitRule,
    DEFAULT_RULES,
)


class TestLatencySpikeRule:
    def test_no_spike(self):
        rule = LatencySpikeRule(name="test", threshold_ms=Decimal("500"))
        triggered, msg = rule.evaluate({"latency_ms": Decimal("200")})
        assert not triggered

    def test_spike_triggered(self):
        rule = LatencySpikeRule(name="test", threshold_ms=Decimal("500"))
        triggered, msg = rule.evaluate({"latency_ms": Decimal("600")})
        assert triggered
        assert "600" in msg

    def test_spike_int_input(self):
        rule = LatencySpikeRule(name="test", threshold_ms=Decimal("500"))
        triggered, msg = rule.evaluate({"latency_ms": 600})
        assert triggered


class TestExecutionDriftRule:
    def test_no_drift(self):
        rule = ExecutionDriftRule(name="test", max_drift_rate=Decimal("0.3"))
        triggered, _ = rule.evaluate({"drift_rate": Decimal("0.1")})
        assert not triggered

    def test_drift_triggered(self):
        rule = ExecutionDriftRule(name="test", max_drift_rate=Decimal("0.3"))
        triggered, msg = rule.evaluate({"drift_rate": Decimal("0.5")})
        assert triggered


class TestPnLDegradationRule:
    def test_no_degradation(self):
        rule = PnLDegradationRule(name="test", drawdown_threshold_pct=Decimal("15"))
        triggered, _ = rule.evaluate({"drawdown_pct": Decimal("5")})
        assert not triggered

    def test_degradation_triggered(self):
        rule = PnLDegradationRule(name="test", drawdown_threshold_pct=Decimal("15"))
        triggered, msg = rule.evaluate({"drawdown_pct": Decimal("20")})
        assert triggered


class TestRiskModelDivergenceRule:
    def test_no_divergence(self):
        rule = RiskModelDivergenceRule(name="test", max_divergence_score=Decimal("0.5"))
        triggered, _ = rule.evaluate({"divergence_score": Decimal("0.2")})
        assert not triggered

    def test_divergence_triggered(self):
        rule = RiskModelDivergenceRule(name="test", max_divergence_score=Decimal("0.5"))
        triggered, msg = rule.evaluate({
            "divergence_score": Decimal("0.7"),
            "divergence_reason": "var drift",
        })
        assert triggered
        assert "var drift" in msg


class TestHealthCheckFailureRule:
    def test_no_failure(self):
        rule = HealthCheckFailureRule(name="test", max_consecutive_failures=3)
        triggered, _ = rule.evaluate({"consecutive_failures": 1, "component": "broker"})
        assert not triggered

    def test_failure_triggered(self):
        rule = HealthCheckFailureRule(name="test", max_consecutive_failures=3)
        triggered, msg = rule.evaluate({"consecutive_failures": 5, "component": "broker"})
        assert triggered
        assert "broker" in msg


class TestFillRateDropRule:
    def test_no_drop(self):
        rule = FillRateDropRule(name="test", min_fill_rate_pct=Decimal("80"))
        triggered, _ = rule.evaluate({"fill_rate_pct": Decimal("90")})
        assert not triggered

    def test_drop_triggered(self):
        rule = FillRateDropRule(name="test", min_fill_rate_pct=Decimal("80"))
        triggered, msg = rule.evaluate({"fill_rate_pct": Decimal("50")})
        assert triggered


class TestExposureLimitRule:
    def test_normal(self):
        rule = ExposureLimitRule(name="test", max_exposure_ratio=Decimal("0.95"))
        triggered, _ = rule.evaluate({"exposure_ratio": Decimal("0.5")})
        assert not triggered

    def test_exceeded(self):
        rule = ExposureLimitRule(name="test", max_exposure_ratio=Decimal("0.95"))
        triggered, msg = rule.evaluate({"exposure_ratio": Decimal("1.2")})
        assert triggered


class TestDefaultRules:
    def test_all_rules_present(self):
        names = {r.name for r in DEFAULT_RULES}
        expected = {
            "latency_spike",
            "execution_drift",
            "pnl_degradation",
            "risk_model_divergence",
            "health_check_failure",
            "fill_rate_drop",
            "exposure_limit",
        }
        assert names == expected
