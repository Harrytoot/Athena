from decimal import Decimal

from app.domain.entities.market import (
    AiMarketSummary,
    HotSector,
    MarketOverview,
    MarketRegime,
    MarketSnapshot,
)


class TestMarket:
    def test_market_snapshot_creation(self):
        snap = MarketSnapshot(
            index_code="000001",
            index_name="上证指数",
            current_point=Decimal("3200.50"),
            change_pct=Decimal("0.85"),
            change_amount=Decimal("27.00"),
            volume=Decimal("3500000000"),
            amount=Decimal("450000000000"),
        )
        assert snap.index_code == "000001"
        assert snap.change_pct == Decimal("0.85")

    def test_market_regime_enum(self):
        assert MarketRegime.BULL.value == "bull"
        assert MarketRegime.BEAR.value == "bear"
        assert MarketRegime.RANGE.value == "range"
        assert MarketRegime.VOLATILE.value == "volatile"

    def test_hot_sector_creation(self):
        sector = HotSector(
            sector_name="半导体",
            change_pct=Decimal("3.25"),
            leader_stock="688981",
        )
        assert sector.sector_name == "半导体"
        assert sector.leader_stock == "688981"

    def test_ai_market_summary(self):
        summary = AiMarketSummary(
            regime=MarketRegime.BULL,
            confidence=0.85,
            summary="市场整体强势",
            risk_warning="注意高位回调风险",
        )
        assert summary.regime == MarketRegime.BULL
        assert summary.confidence == 0.85

    def test_market_overview_creation(self):
        overview = MarketOverview(
            regime=MarketRegime.BULL,
            summary="市场整体向好",
            rise_count=2800,
            fall_count=1200,
        )
        assert overview.regime == MarketRegime.BULL
        assert overview.rise_count == 2800
        assert overview.fall_count == 1200
        assert len(overview.indices) == 0

    def test_market_overview_with_ai_summary(self):
        ai = AiMarketSummary(
            regime=MarketRegime.BULL, confidence=0.78, summary="短期震荡向上"
        )
        overview = MarketOverview(
            regime=MarketRegime.BULL,
            summary="震荡行情",
            ai_summary=ai,
        )
        assert overview.ai_summary is not None
        assert overview.ai_summary.confidence == 0.78
