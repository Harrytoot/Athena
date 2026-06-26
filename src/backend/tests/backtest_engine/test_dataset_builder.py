from datetime import datetime, timezone, timedelta

import pytest

from app.backtest_engine.dataset_builder import DatasetBuilder, BacktestDataset
from app.feature_store.repository import FeatureItem, InMemoryFeatureRepository


def _make_item(name: str, value: float, category: str, ts: datetime) -> FeatureItem:
    return FeatureItem(
        name=name,
        value=value,
        category=category,
        timestamp=ts,
        version="1.0.0",
        source="mock_v1",
        confidence=1.0,
    )


class TestDatasetBuilder:

    @pytest.fixture
    def repo_with_data(self):
        repo = InMemoryFeatureRepository()
        base = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        for i in range(50):
            ts = base - timedelta(days=49 - i)
            repo._store.extend([
                _make_item("trend_strength", 50.0 + i * 2, "trend", ts),
                _make_item("market_turnover", 55.0 + i * 1.5, "liquidity", ts),
                _make_item("advancers_ratio", 45.0 + i * 1.0, "breadth", ts),
                _make_item("volatility_index", 40.0 + i * 0.5, "volatility", ts),
                _make_item("northbound_flow", 50.0 + i * 1.2, "sentiment", ts),
            ])
        return repo

    @pytest.mark.asyncio
    async def test_build_dataset_loads_timestamps_and_trims_trailing(self, repo_with_data):
        since = datetime.now(timezone.utc) - timedelta(days=50)
        until = datetime.now(timezone.utc)
        builder = DatasetBuilder(repo_with_data)
        dataset = await builder.build(since, until)
        assert len(dataset.rows) == 30

    @pytest.mark.asyncio
    async def test_build_dataset_scores_are_computed(self, repo_with_data):
        since = datetime.now(timezone.utc) - timedelta(days=50)
        until = datetime.now(timezone.utc)
        builder = DatasetBuilder(repo_with_data)
        dataset = await builder.build(since, until)
        assert all(r.score > 0 for r in dataset.rows)
        assert all(r.state in ("Strong Bull", "Bull", "Neutral", "Bear", "Extreme Bear") for r in dataset.rows)

    @pytest.mark.asyncio
    async def test_build_dataset_has_prices(self, repo_with_data):
        since = datetime.now(timezone.utc) - timedelta(days=50)
        until = datetime.now(timezone.utc)
        builder = DatasetBuilder(repo_with_data)
        dataset = await builder.build(since, until)
        for row in dataset.rows:
            assert row.price > 0

    @pytest.mark.asyncio
    async def test_forward_returns_no_lookahead(self, repo_with_data):
        since = datetime.now(timezone.utc) - timedelta(days=50)
        until = datetime.now(timezone.utc)
        builder = DatasetBuilder(repo_with_data)
        dataset = await builder.build(since, until)

        for i, row in enumerate(dataset.rows):
            if i + 5 < len(dataset.rows):
                expected_5d = (dataset.rows[i + 5].price - row.price) / row.price
                assert row.forward_return_5d == pytest.approx(expected_5d, abs=1e-6)
            assert row.forward_return_20d != 0.0

    @pytest.mark.asyncio
    async def test_prices_independent_of_scores(self, repo_with_data):
        since = datetime.now(timezone.utc) - timedelta(days=50)
        until = datetime.now(timezone.utc)
        builder = DatasetBuilder(repo_with_data)
        dataset = await builder.build(since, until)

        score_returns = list(zip(dataset.scores, dataset.forward_returns_5d))
        score_values = [s for s, _ in score_returns]
        return_values = [r for _, r in score_returns]
        if len(score_values) >= 5:
            from app.backtest_engine.metrics import pearson_correlation
            ic = pearson_correlation(score_values, return_values)
            assert abs(ic) < 0.5

    @pytest.mark.asyncio
    async def test_empty_dataset_when_no_features(self):
        repo = InMemoryFeatureRepository()
        since = datetime.now(timezone.utc) - timedelta(days=10)
        until = datetime.now(timezone.utc)
        builder = DatasetBuilder(repo)
        dataset = await builder.build(since, until)
        assert len(dataset.rows) == 0
        assert isinstance(dataset, BacktestDataset)

    @pytest.mark.asyncio
    async def test_dataset_properties(self, repo_with_data):
        since = datetime.now(timezone.utc) - timedelta(days=50)
        until = datetime.now(timezone.utc)
        builder = DatasetBuilder(repo_with_data)
        dataset = await builder.build(since, until)
        assert len(dataset.timestamps) == 30
        assert len(dataset.scores) == 30
        assert len(dataset.signals) == 30
        assert len(dataset.forward_returns_5d) == 30
        assert len(dataset.forward_returns_10d) == 30
        assert len(dataset.forward_returns_20d) == 30

    @pytest.mark.asyncio
    async def test_custom_prices_are_used(self, repo_with_data):
        since = datetime.now(timezone.utc) - timedelta(days=50)
        until = datetime.now(timezone.utc)
        custom_prices = [float(i) for i in range(100, 150)]
        builder = DatasetBuilder(repo_with_data)
        dataset = await builder.build(since, until, prices=custom_prices)
        for row in dataset.rows:
            assert row.price >= 100.0
