from decimal import Decimal

from app.broker_integration.adapters.base_adapter import (
    AdapterConfig,
    BrokerAdapter,
    BrokerMode,
)
from app.execution_live.broker.base import Broker


class IBKRAdapter(BrokerAdapter):
    """Adapter for Interactive Brokers.

    Currently a stub for future live integration.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
        config: AdapterConfig | None = None,
        initial_cash: Decimal = Decimal("1000000"),
        seed: int | None = 42,
        price_feed: dict[str, Decimal] | None = None,
    ):
        cfg = config or AdapterConfig(
            mode=BrokerMode.SANDBOX,
            broker_name="ibkr",
        )
        super().__init__(cfg)
        self._host = host
        self._port = port
        self._client_id = client_id
        self._initial_cash = initial_cash
        self._seed = seed
        self._price_feed = price_feed

    def _create_broker(self) -> Broker:
        from app.execution_live.broker.paper_broker import PaperBroker, PaperBrokerConfig

        config = PaperBrokerConfig(
            initial_cash=self._initial_cash,
            seed=self._seed,
        )
        return PaperBroker(config=config, price_feed=self._price_feed)
