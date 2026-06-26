from datetime import datetime, timezone, timedelta

import pytest

from app.feature_store.repository import FeatureItem, InMemoryFeatureRepository


class TestFeatureItem:

    def test_feature_item_creation(self):
        now = datetime.now(timezone.utc)
        item = FeatureItem(
            name="trend_strength",
            value=80.0,
            category="trend",
            timestamp=now,
            version="1.0.0",
            source="mock_v1",
            confidence=1.0,
        )
        assert item.name == "trend_strength"
        assert item.value == 80.0
        assert item.category == "trend"
        assert item.timestamp == now
        assert item.version == "1.0.0"
        assert item.source == "mock_v1"
        assert item.confidence == 1.0


class TestInMemoryFeatureRepository:

    @pytest.fixture
    def repo(self):
        return InMemoryFeatureRepository()

    @pytest.fixture
    def sample_feature(self):
        return FeatureItem(
            name="trend_strength",
            value=80.0,
            category="trend",
            timestamp=datetime.now(timezone.utc),
            version="1.0.0",
            source="mock_v1",
            confidence=1.0,
        )

    @pytest.mark.asyncio
    async def test_save_and_get_latest(self, repo, sample_feature):
        await repo.save(sample_feature)
        latest = await repo.get_latest("trend_strength")
        assert latest is not None
        assert latest.value == 80.0

    @pytest.mark.asyncio
    async def test_get_latest_returns_none_for_missing(self, repo):
        latest = await repo.get_latest("nonexistent")
        assert latest is None

    @pytest.mark.asyncio
    async def test_get_latest_returns_most_recent(self, repo):
        earlier = FeatureItem(
            name="trend_strength", value=70.0, category="trend",
            timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
            version="1.0.0", source="mock_v1", confidence=1.0,
        )
        later = FeatureItem(
            name="trend_strength", value=80.0, category="trend",
            timestamp=datetime.now(timezone.utc),
            version="1.0.0", source="mock_v1", confidence=1.0,
        )
        await repo.save(earlier)
        await repo.save(later)
        latest = await repo.get_latest("trend_strength")
        assert latest.value == 80.0

    @pytest.mark.asyncio
    async def test_save_batch(self, repo):
        now = datetime.now(timezone.utc)
        features = [
            FeatureItem(name="trend_strength", value=80.0, category="trend", timestamp=now, version="1.0.0", source="mock_v1", confidence=1.0),
            FeatureItem(name="market_turnover", value=75.0, category="liquidity", timestamp=now, version="1.0.0", source="mock_v1", confidence=1.0),
        ]
        await repo.save_batch(features)
        assert len(repo._store) == 2

    @pytest.mark.asyncio
    async def test_get_history(self, repo):
        now = datetime.now(timezone.utc)
        t1 = now - timedelta(hours=2)
        t2 = now - timedelta(hours=1)
        t3 = now

        f1 = FeatureItem(name="trend_strength", value=70.0, category="trend", timestamp=t1, version="1.0.0", source="mock_v1", confidence=1.0)
        f2 = FeatureItem(name="trend_strength", value=75.0, category="trend", timestamp=t2, version="1.0.0", source="mock_v1", confidence=1.0)
        f3 = FeatureItem(name="trend_strength", value=80.0, category="trend", timestamp=t3, version="1.0.0", source="mock_v1", confidence=1.0)
        f4 = FeatureItem(name="market_turnover", value=70.0, category="liquidity", timestamp=t1, version="1.0.0", source="mock_v1", confidence=1.0)

        await repo.save_batch([f1, f2, f3, f4])

        since = t1 - timedelta(minutes=1)
        until = t2 + timedelta(minutes=1)
        history = await repo.get_history("trend_strength", since, until)
        assert len(history) == 2
        assert history[0].value == 70.0
        assert history[1].value == 75.0

    @pytest.mark.asyncio
    async def test_get_history_empty_when_no_match(self, repo):
        now = datetime.now(timezone.utc)
        history = await repo.get_history("nonexistent", now, now)
        assert history == []
