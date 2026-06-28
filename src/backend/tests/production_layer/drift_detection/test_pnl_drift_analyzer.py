from decimal import Decimal
from datetime import datetime, timezone

from app.production_layer.drift_detection.pnl_drift_analyzer import (
    PnLDriftAnalyzer,
    PnLDataPoint,
    PnLDriftResult,
)


class TestPnLDriftAnalyzer:
    def test_record_pnl(self):
        analyzer = PnLDriftAnalyzer(window_size=10)
        point = analyzer.record_pnl("st1", Decimal("100"), Decimal("50"))
        assert point.strategy_id == "st1"
        assert point.total_pnl == Decimal("150")

    def test_insufficient_data(self):
        analyzer = PnLDriftAnalyzer(window_size=50)
        result = analyzer.analyze("st1")
        assert not result.is_degraded
        assert result.degradation_reason == "insufficient_data"

    def test_normal_pnl_no_degradation(self):
        analyzer = PnLDriftAnalyzer(window_size=10)
        for i in range(20):
            analyzer.record_pnl("st1", Decimal(str(100 + i)), Decimal("0"))
        result = analyzer.analyze("st1")
        assert result.rolling_mean_pnl > Decimal("0")

    def test_negative_pnl_detected(self):
        analyzer = PnLDriftAnalyzer(window_size=10, z_score_threshold=Decimal("1"), sharpe_warn_threshold=Decimal("10"))
        for i in range(30):
            analyzer.record_pnl("st1", Decimal(str(50 - i * 2)), Decimal("0"))
        result = analyzer.analyze("st1")
        assert result.latest_pnl < Decimal("0")

    def test_drawdown_detection(self):
        analyzer = PnLDriftAnalyzer(
            window_size=10,
            drawdown_threshold_pct=Decimal("5"),
            z_score_threshold=Decimal("10"),
            sharpe_warn_threshold=Decimal("-100"),
        )
        values = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55]
        for v in values:
            analyzer.record_pnl("st1", Decimal(str(v)), Decimal("0"))
        result = analyzer.analyze("st1")
        assert result.drawdown_pct > Decimal("20")

    def test_z_score_anomaly(self):
        analyzer = PnLDriftAnalyzer(
            window_size=15,
            z_score_threshold=Decimal("1"),
            drawdown_threshold_pct=Decimal("50"),
            sharpe_warn_threshold=Decimal("-100"),
        )
        for i in range(15):
            analyzer.record_pnl("st1", Decimal("100"), Decimal("0"))
        analyzer.record_pnl("st1", Decimal("500"), Decimal("0"))
        result = analyzer.analyze("st1")
        assert abs(result.z_score) > Decimal("1")

    def test_history_limit(self):
        analyzer = PnLDriftAnalyzer(window_size=10)
        for i in range(250):
            analyzer.record_pnl("st1", Decimal(str(i)), Decimal("0"))
        assert len(analyzer.history) <= 200

    def test_clear(self):
        analyzer = PnLDriftAnalyzer()
        analyzer.record_pnl("st1", Decimal("100"), Decimal("0"))
        analyzer.clear()
        assert len(analyzer.history) == 0


class TestPnLDataPoint:
    def test_create(self):
        dp = PnLDataPoint(
            timestamp=datetime.now(timezone.utc),
            strategy_id="strat",
            realized_pnl=Decimal("100"),
            unrealized_pnl=Decimal("-20"),
            total_pnl=Decimal("80"),
        )
        assert dp.strategy_id == "strat"
        assert dp.total_pnl == Decimal("80")
