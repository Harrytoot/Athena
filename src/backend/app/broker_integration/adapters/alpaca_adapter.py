from decimal import Decimal

from app.broker_integration.adapters.base_adapter import (
    AdapterConfig,
    BrokerAdapter,
    BrokerMode,
)
from app.execution_live.broker.base import Broker


class AlpacaAdapter(BrokerAdapter):
    """Adapter for Alpaca Markets (US stocks).

    Currently a stub for future live integration.
    Uses PaperBroker internally until live connection is implemented.
    """

    def __init__(
        self,
        api_key: str = "",
        secret_key: str = "",
        config: AdapterConfig | None = None,
        initial_cash: Decimal = Decimal("1000000"),
        seed: int | None = 42,
        price_feed: dict[str, Decimal] | None = None,
    ):
        cfg = config or AdapterConfig(
            mode=BrokerMode.SANDBOX,
            broker_name="alpaca",
        )
        super().__init__(cfg)
        self._api_key = api_key
        self._secret_key = secret_key
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
