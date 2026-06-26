from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.feature_store.repository import FeatureItem
from app.ingestion.feature_writer import FeatureWriter
from app.ingestion.ingestion_service import IngestionService
from app.ingestion.market_fetcher import MarketDataFetcher
from app.ingestion.transformer import DataTransformer
from app.providers.market.base import MarketProvider


def _make_item(name: str, value: float, category: str) -> FeatureItem:
    return FeatureItem(
        name=name,
        value=value,
        category=category,
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
        source="akshare_v1",
        confidence=0.95,
    )


SAMPLE_RAW = {
    "trend_strength": 65.5,
    "market_turnover": 72.3,
    "advancers_ratio": 55.0,
    "volatility_index": 40.0,
    "northbound_flow": 60.5,
}

SAMPLE_ITEMS = [
    _make_item("trend_strength", 65.5, "trend"),
    _make_item("market_turnover", 72.3, "liquidity"),
    _make_item("advancers_ratio", 55.0, "breadth"),
    _make_item("volatility_index", 40.0, "volatility"),
    _make_item("northbound_flow", 60.5, "sentiment"),
]


@pytest.fixture
def mock_fetcher():
    fetcher = AsyncMock(spec=MarketDataFetcher)
    fetcher.fetch_raw = AsyncMock(return_value=SAMPLE_RAW)
    return fetcher


@pytest.fixture
def mock_transformer():
    transformer = MagicMock(spec=DataTransformer)
    transformer.transform = MagicMock(return_value=SAMPLE_ITEMS)
    return transformer


@pytest.fixture
def mock_writer():
    writer = AsyncMock(spec=FeatureWriter)
    writer.write_features = AsyncMock()
    return writer


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_session_factory(mock_session):
    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    factory.return_value.__aexit__ = AsyncMock(return_value=None)
    return factory


@pytest.fixture
def service(mock_fetcher, mock_transformer, mock_writer, mock_session_factory):
    return IngestionService(
        session_factory=mock_session_factory,
        fetcher=mock_fetcher,
        transformer=mock_transformer,
        writer=mock_writer,
    )


class TestIngestionService:
    @pytest.mark.asyncio
    async def test_run_pipeline_returns_result_dict(self, service):
        result = await service.run_pipeline()
        assert result["status"] == "ok"
        assert result["features_written"] == 5
        assert "elapsed_seconds" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_run_pipeline_calls_fetcher(self, service, mock_fetcher):
        await service.run_pipeline()
        mock_fetcher.fetch_raw.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_pipeline_calls_transformer(self, service, mock_transformer):
        await service.run_pipeline()
        mock_transformer.transform.assert_called_once_with(SAMPLE_RAW)

    @pytest.mark.asyncio
    async def test_run_pipeline_calls_writer(self, service, mock_writer):
        await service.run_pipeline()
        mock_writer.write_features.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_pipeline_writes_correct_items(self, service, mock_writer):
        await service.run_pipeline()
        call_args = mock_writer.write_features.call_args
        features_written = call_args[0][0]
        assert len(features_written) == 5
        for item in features_written:
            assert isinstance(item, FeatureItem)

    @pytest.mark.asyncio
    async def test_run_manual_adds_mode_key(self, service):
        result = await service.run_manual()
        assert result["mode"] == "manual"
        assert result["status"] == "ok"
        assert result["features_written"] == 5

    @pytest.mark.asyncio
    async def test_run_manual_returns_same_structure_as_pipeline(self, service):
        result = await service.run_manual()
        assert "status" in result
        assert "features_written" in result
        assert "source" in result
        assert "version" in result
        assert "elapsed_seconds" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_run_pipeline_with_custom_provider(self, mock_session_factory, mock_transformer, mock_writer):
        custom_provider = AsyncMock(spec=MarketProvider)
        fetcher = MarketDataFetcher(provider=custom_provider)
        service = IngestionService(
            session_factory=mock_session_factory,
            fetcher=fetcher,
            transformer=mock_transformer,
            writer=mock_writer,
        )
        result = await service.run_pipeline()
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_run_pipeline_execution_order(self, service, mock_fetcher, mock_transformer, mock_writer):
        await service.run_pipeline()

        mock_fetcher.fetch_raw.assert_awaited()
        mock_transformer.transform.assert_called()
        mock_writer.write_features.assert_awaited()

        fetcher_call_order = mock_fetcher.fetch_raw.call_count
        transformer_call_order = mock_transformer.transform.call_count
        writer_call_order = mock_writer.write_features.call_count
        assert fetcher_call_order == 1
        assert transformer_call_order == 1
        assert writer_call_order == 1
