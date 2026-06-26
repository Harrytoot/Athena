from dataclasses import dataclass


@dataclass
class MarketScore:
    trend: float
    liquidity: float
    breadth: float
    volatility: float
    sentiment: float

    @property
    def total(self) -> float:
        return round(
            self.trend * 0.30
            + self.liquidity * 0.25
            + self.breadth * 0.20
            + self.volatility * 0.15
            + self.sentiment * 0.10,
            2,
        )

    @property
    def state(self) -> str:
        s = self.total
        if s >= 80:
            return "Strong Bull"
        if s >= 60:
            return "Bull"
        if s >= 40:
            return "Neutral"
        if s >= 20:
            return "Bear"
        return "Extreme Bear"
