from decimal import Decimal
from datetime import datetime, timezone

from app.production_layer.drift_detection.execution_drift_detector import (
    ExecutionDriftDetector,
    ExecutionExpectation,
    ExecutionActual,
    ExecutionDriftResult,
)


class TestExecutionDriftDetector:
    def test_no_drift(self):
        detector = ExecutionDriftDetector()
        expected = ExecutionExpectation(
            symbol="AAPL",
            expected_price=Decimal("150.00"),
            expected_quantity=Decimal("100"),
            expected_slippage_bps=Decimal("5"),
            expected_fill_percentage=Decimal("100"),
        )
        actual = ExecutionActual(
            symbol="AAPL",
            actual_price=Decimal("150.00"),
            actual_quantity=Decimal("100"),
            actual_slippage_bps=Decimal("5"),
            actual_fill_percentage=Decimal("100"),
            timestamp=datetime.now(timezone.utc),
        )
        result = detector.detect(expected, actual)
        assert not result.is_drifted
        assert result.drift_score == Decimal("0")

    def test_price_drift(self):
        detector = ExecutionDriftDetector(price_drift_threshold_bps=Decimal("50"))
        expected = ExecutionExpectation(
            symbol="AAPL",
            expected_price=Decimal("100.00"),
            expected_quantity=Decimal("100"),
            expected_slippage_bps=Decimal("0"),
            expected_fill_percentage=Decimal("100"),
        )
        actual = ExecutionActual(
            symbol="AAPL",
            actual_price=Decimal("101.00"),
            actual_quantity=Decimal("100"),
            actual_slippage_bps=Decimal("0"),
            actual_fill_percentage=Decimal("100"),
            timestamp=datetime.now(timezone.utc),
        )
        result = detector.detect(expected, actual)
        assert result.price_drift_bps == Decimal("100")

    def test_quantity_drift(self):
        detector = ExecutionDriftDetector(quantity_drift_threshold_pct=Decimal("5"))
        expected = ExecutionExpectation(
            symbol="AAPL",
            expected_price=Decimal("100"),
            expected_quantity=Decimal("100"),
            expected_slippage_bps=Decimal("0"),
            expected_fill_percentage=Decimal("100"),
        )
        actual = ExecutionActual(
            symbol="AAPL",
            actual_price=Decimal("100"),
            actual_quantity=Decimal("50"),
            actual_slippage_bps=Decimal("0"),
            actual_fill_percentage=Decimal("100"),
            timestamp=datetime.now(timezone.utc),
        )
        result = detector.detect(expected, actual)
        assert result.quantity_drift_pct == Decimal("-50")

    def test_multi_factor_drift_triggers(self):
        detector = ExecutionDriftDetector(
            price_drift_threshold_bps=Decimal("10"),
            quantity_drift_threshold_pct=Decimal("5"),
        )
        expected = ExecutionExpectation(
            symbol="TECH",
            expected_price=Decimal("200"),
            expected_quantity=Decimal("100"),
            expected_slippage_bps=Decimal("0"),
            expected_fill_percentage=Decimal("100"),
        )
        actual = ExecutionActual(
            symbol="TECH",
            actual_price=Decimal("205"),
            actual_quantity=Decimal("80"),
            actual_slippage_bps=Decimal("5"),
            actual_fill_percentage=Decimal("95"),
            timestamp=datetime.now(timezone.utc),
        )
        result = detector.detect(expected, actual)
        assert result.is_drifted
        assert result.drift_score >= Decimal("2")

    def test_symbol_mismatch_raises(self):
        detector = ExecutionDriftDetector()
        expected = ExecutionExpectation(
            symbol="A", expected_price=Decimal("1"), expected_quantity=Decimal("1"),
            expected_slippage_bps=Decimal("0"), expected_fill_percentage=Decimal("100"),
        )
        actual = ExecutionActual(
            symbol="B", actual_price=Decimal("1"), actual_quantity=Decimal("1"),
            actual_slippage_bps=Decimal("0"), actual_fill_percentage=Decimal("100"),
            timestamp=datetime.now(timezone.utc),
        )
        try:
            detector.detect(expected, actual)
            assert False
        except ValueError:
            pass

    def test_history_accumulation(self):
        detector = ExecutionDriftDetector(window_size=10)
        for i in range(15):
            expected = ExecutionExpectation(
                symbol="X", expected_price=Decimal("100"),
                expected_quantity=Decimal("100"), expected_slippage_bps=Decimal("0"),
                expected_fill_percentage=Decimal("100"),
            )
            actual = ExecutionActual(
                symbol="X",
                actual_price=Decimal(str(100 + i * 2)),
                actual_quantity=Decimal("100"),
                actual_slippage_bps=Decimal("0"),
                actual_fill_percentage=Decimal("100"),
                timestamp=datetime.now(timezone.utc),
            )
            detector.detect(expected, actual)
        assert len(detector.history) <= 10

    def test_recent_drift_rate(self):
        detector = ExecutionDriftDetector(
            price_drift_threshold_bps=Decimal("10"),
            quantity_drift_threshold_pct=Decimal("5"),
        )
        for i in range(20):
            expected = ExecutionExpectation(
                symbol="X", expected_price=Decimal("100"),
                expected_quantity=Decimal("100"), expected_slippage_bps=Decimal("0"),
                expected_fill_percentage=Decimal("100"),
            )
            actual = ExecutionActual(
                symbol="X",
                actual_price=Decimal(str(100 + i * 5)),
                actual_quantity=Decimal(str(50 if i < 15 else 100)),
                actual_slippage_bps=Decimal("0"),
                actual_fill_percentage=Decimal("100"),
                timestamp=datetime.now(timezone.utc),
            )
            detector.detect(expected, actual)
        rate = detector.recent_drift_rate(10)
        assert Decimal("0") <= rate <= Decimal("1")

    def test_is_degrading(self):
        detector = ExecutionDriftDetector(
            price_drift_threshold_bps=Decimal("1"),
            quantity_drift_threshold_pct=Decimal("1"),
        )
        for i in range(15):
            expected = ExecutionExpectation(
                symbol="X", expected_price=Decimal("100"),
                expected_quantity=Decimal("100"), expected_slippage_bps=Decimal("0"),
                expected_fill_percentage=Decimal("100"),
            )
            actual = ExecutionActual(
                symbol="X",
                actual_price=Decimal(str(100 + i * 5)),
                actual_quantity=Decimal(str(100 + i)),
                actual_slippage_bps=Decimal("0"),
                actual_fill_percentage=Decimal("100"),
                timestamp=datetime.now(timezone.utc),
            )
            detector.detect(expected, actual)
        assert detector.is_degrading(10, Decimal("0.2"))

    def test_clear_history(self):
        detector = ExecutionDriftDetector()
        expected = ExecutionExpectation(
            symbol="X", expected_price=Decimal("100"), expected_quantity=Decimal("100"),
            expected_slippage_bps=Decimal("0"), expected_fill_percentage=Decimal("100"),
        )
        actual = ExecutionActual(
            symbol="X", actual_price=Decimal("100"), actual_quantity=Decimal("100"),
            actual_slippage_bps=Decimal("0"), actual_fill_percentage=Decimal("100"),
            timestamp=datetime.now(timezone.utc),
        )
        detector.detect(expected, actual)
        detector.clear_history()
        assert len(detector.history) == 0


class TestExecutionDriftResult:
    def test_summary(self):
        result = ExecutionDriftResult(
            symbol="AAPL",
            price_drift_bps=Decimal("50"),
            quantity_drift_pct=Decimal("0"),
            slippage_drift_bps=Decimal("0"),
            fill_rate_drift_pct=Decimal("0"),
            is_drifted=True,
            drift_score=Decimal("1"),
            timestamp=datetime.now(timezone.utc),
        )
        summary = result.summary()
        assert "AAPL" in summary
        assert "price" in summary

    def test_summary_no_drift(self):
        result = ExecutionDriftResult(
            symbol="AAPL",
            price_drift_bps=Decimal("0"),
            quantity_drift_pct=Decimal("0"),
            slippage_drift_bps=Decimal("0"),
            fill_rate_drift_pct=Decimal("0"),
            is_drifted=False,
            drift_score=Decimal("0"),
            timestamp=datetime.now(timezone.utc),
        )
        summary = result.summary()
        assert "no drift" in summary
