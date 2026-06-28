from datetime import datetime, timedelta, timezone

from app.backtest_engine.dataset_builder import DatasetBuilder
from app.backtest_engine.evaluator import Evaluator, BacktestReport
from app.feature_store.repository import FeatureRepository


class BacktestService:

    def __init__(self, feature_repo: FeatureRepository):
        self._feature_repo = feature_repo
        self._builder = DatasetBuilder(feature_repo)
        self._evaluator = Evaluator()

    async def run_backtest(self, symbol: str = "000001", days: int = 120) -> BacktestReport:
        until = datetime.now(timezone.utc)
        since = until - timedelta(days=days + 30)

        dataset = await self._builder.build(since=since, until=until, prices=None)
        report = self._evaluator.evaluate(dataset)
        return report
