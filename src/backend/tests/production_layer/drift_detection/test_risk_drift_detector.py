from decimal import Decimal
from datetime import datetime, timezone

from app.production_layer.drift_detection.risk_drift_detector import (
    RiskDriftDetector,
    RiskModelSnapshot,
    RiskDriftResult,
)


class TestRiskDriftDetector:
    def test_set_baseline(self):
        detector = RiskDriftDetector()
        snapshot = _make_snapshot()
        detector.set_baseline(snapshot)
        assert detector.baseline is snapshot

    def test_record_snapshot(self):
        detector = RiskDriftDetector()
        snap = detector.record_snapshot(
            var_95=Decimal("1000"),
            var_99=Decimal("1500"),
            cvar_95=Decimal("1200"),
            max_drawdown_pct=Decimal("10"),
            beta_exposure=Decimal("1.0"),
            leverage=Decimal("2.0"),
            concentration_hhi=Decimal("500"),
        )
        assert len(detector.snapshots) == 1
        assert snap.var_95 == Decimal("1000")

    def test_detect_no_divergence(self):
        detector = RiskDriftDetector()
        baseline = _make_snapshot()
        detector.set_baseline(baseline)
        current = _make_snapshot()
        result = detector.detect(current)
        assert not result.is_diverged
        assert result.overall_drift_score == Decimal("0")

    def test_detect_var_divergence(self):
        detector = RiskDriftDetector(var_drift_threshold_pct=Decimal("10"))
        baseline = _make_snapshot(var_95=Decimal("1000"), var_99=Decimal("1500"))
        detector.set_baseline(baseline)
        current = _make_snapshot(var_95=Decimal("1500"), var_99=Decimal("2200"))
        result = detector.detect(current)
        assert result.is_diverged
        assert abs(result.var_95_drift_pct) > Decimal("30")

    def test_detect_beta_divergence(self):
        detector = RiskDriftDetector(drift_threshold_pct=Decimal("10"))
        baseline = _make_snapshot(beta_exposure=Decimal("1.0"))
        detector.set_baseline(baseline)
        current = _make_snapshot(beta_exposure=Decimal("1.5"))
        result = detector.detect(current)
        assert result.is_diverged
        assert abs(result.beta_drift_pct) > Decimal("10")

    def test_detect_leverage_divergence(self):
        detector = RiskDriftDetector(drift_threshold_pct=Decimal("10"))
        baseline = _make_snapshot(leverage=Decimal("2.0"))
        detector.set_baseline(baseline)
        current = _make_snapshot(leverage=Decimal("3.0"))
        result = detector.detect(current)
        assert result.is_diverged

    def test_no_baseline_fallback(self):
        detector = RiskDriftDetector()
        detector.record_snapshot(
            var_95=Decimal("1000"), var_99=Decimal("1500"),
            cvar_95=Decimal("1200"), max_drawdown_pct=Decimal("10"),
            beta_exposure=Decimal("1.0"), leverage=Decimal("2.0"),
            concentration_hhi=Decimal("500"),
        )
        snap2 = detector.record_snapshot(
            var_95=Decimal("2000"), var_99=Decimal("2500"),
            cvar_95=Decimal("2200"), max_drawdown_pct=Decimal("10"),
            beta_exposure=Decimal("1.0"), leverage=Decimal("2.0"),
            concentration_hhi=Decimal("500"),
        )
        result = detector.detect(snap2)
        assert isinstance(result, RiskDriftResult)

    def test_max_snapshots(self):
        detector = RiskDriftDetector(max_snapshots=10)
        for i in range(20):
            detector.record_snapshot(
                var_95=Decimal(str(1000 + i)),
                var_99=Decimal("1500"),
                cvar_95=Decimal("1200"),
                max_drawdown_pct=Decimal("10"),
                beta_exposure=Decimal("1.0"),
                leverage=Decimal("2.0"),
                concentration_hhi=Decimal("500"),
            )
        assert len(detector.snapshots) <= 10

    def test_clear(self):
        detector = RiskDriftDetector()
        detector.record_snapshot(
            var_95=Decimal("1000"), var_99=Decimal("1500"),
            cvar_95=Decimal("1200"), max_drawdown_pct=Decimal("10"),
            beta_exposure=Decimal("1.0"), leverage=Decimal("2.0"),
            concentration_hhi=Decimal("500"),
        )
        detector.clear()
        assert len(detector.snapshots) == 0
        assert detector.baseline is None


def _make_snapshot(**overrides):
    defaults = {
        "timestamp": datetime.now(timezone.utc),
        "var_95": Decimal("1000"),
        "var_99": Decimal("1500"),
        "cvar_95": Decimal("1200"),
        "max_drawdown_pct": Decimal("10"),
        "beta_exposure": Decimal("1.0"),
        "leverage": Decimal("2.0"),
        "concentration_hhi": Decimal("500"),
    }
    defaults.update(overrides)
    return RiskModelSnapshot(**defaults)
