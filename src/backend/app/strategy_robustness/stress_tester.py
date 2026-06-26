import math
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from app.strategy.portfolio_builder import PortfolioHistory, PortfolioSnapshot, PortfolioBuilder
from app.strategy.position_sizer import StrategyPosition
from app.strategy.pnl_analyzer import PnLAnalyzer, StrategyPerformanceReport
from app.strategy.risk_manager import RiskResult


class StressScenario(str, Enum):
    FLASH_CRASH = "flash_crash"
    BEAR_MARKET = "bear_market"
    VOLATILITY_SPIKE = "volatility_spike"
    RECOVERY_RALLY = "recovery_rally"
    SIDEWAYS_CHOP = "sideways_chop"
    GAP_RISK = "gap_risk"


@dataclass
class ShockScenario:
    name: str
    scenario: StressScenario
    price_shift_pct: float
    affected_days: list[int]
    description: str = ""


@dataclass
class StressTestResult:
    scenario: StressScenario
    description: str
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    calmar_ratio: float
    total_days: int
    return_delta_vs_baseline: float = 0.0
    sharpe_delta_vs_baseline: float = 0.0
    max_drawdown_delta_vs_baseline: float = 0.0
    survived: bool = True


class StressTester:

    def __init__(self, risk_free_rate: float = 0.02):
        self.analyzer = PnLAnalyzer(risk_free_rate=risk_free_rate)
        self.risk_free_rate = risk_free_rate

    def run(
        self,
        history: PortfolioHistory,
        risk_result: RiskResult,
    ) -> list[StressTestResult]:
        if not history.snapshots:
            return []

        baseline = self.analyzer.analyze(history)
        scenarios = self._build_scenarios(history)

        results: list[StressTestResult] = []
        for shock in scenarios:
            stress_history = self._apply_shock(history, shock)
            if not stress_history.snapshots:
                results.append(self._failed_result(shock, baseline))
                continue

            perf = self.analyzer.analyze(stress_history)
            result = StressTestResult(
                scenario=shock.scenario,
                description=shock.description,
                total_return=perf.total_return,
                annualized_return=perf.annualized_return,
                sharpe_ratio=perf.sharpe_ratio,
                max_drawdown=perf.max_drawdown,
                win_rate=perf.win_rate,
                calmar_ratio=perf.calmar_ratio,
                total_days=perf.total_days,
                return_delta_vs_baseline=round(perf.total_return - baseline.total_return, 6),
                sharpe_delta_vs_baseline=round(perf.sharpe_ratio - baseline.sharpe_ratio, 6),
                max_drawdown_delta_vs_baseline=round(
                    perf.max_drawdown - baseline.max_drawdown, 6
                ),
                survived=True,
            )
            results.append(result)

        return results

    def perturbation_stability(
        self,
        history: PortfolioHistory,
        noise_scale: float = 0.001,
        num_trials: int = 10,
    ) -> dict[str, float]:
        if not history.snapshots or num_trials < 1:
            return {"mean_sharpe": 0.0, "sharpe_std": 0.0, "stability": 0.0}

        baseline = self.analyzer.analyze(history)
        sharpes: list[float] = []

        for trial in range(num_trials):
            perturbed_prices: list[float] = []
            for snap in history.snapshots:
                noise = self._deterministic_noise(trial, snap.timestamp, noise_scale)
                perturbed_prices.append(snap.price * (1.0 + noise))

            perturbed_history = self._rebuild_history(history, perturbed_prices)
            if perturbed_history.snapshots:
                perf = self.analyzer.analyze(perturbed_history)
                sharpes.append(perf.sharpe_ratio)

        if len(sharpes) < 2:
            return {
                "mean_sharpe": sharpes[0] if sharpes else 0.0,
                "sharpe_std": 0.0,
                "stability": 0.0,
            }

        mean_sharpe = sum(sharpes) / len(sharpes)
        variance = sum((s - mean_sharpe) ** 2 for s in sharpes) / len(sharpes)
        std_sharpe = math.sqrt(variance)

        stability = 0.0
        if baseline.sharpe_ratio != 0:
            stability = max(0.0, min(1.0, 1.0 - std_sharpe / abs(baseline.sharpe_ratio)))

        return {
            "mean_sharpe": round(mean_sharpe, 6),
            "sharpe_std": round(std_sharpe, 6),
            "stability": round(stability, 4),
        }

    def _build_scenarios(self, history: PortfolioHistory) -> list[ShockScenario]:
        n = len(history.snapshots)
        if n == 0:
            return []

        midpoint = n // 2
        third = n // 3
        end_start = max(0, n - 10)

        return [
            ShockScenario(
                name="闪崩 -5%",
                scenario=StressScenario.FLASH_CRASH,
                price_shift_pct=-0.05,
                affected_days=[midpoint],
                description="单日价格闪崩5%，测试策略抗冲击能力",
            ),
            ShockScenario(
                name="闪崩 -10%",
                scenario=StressScenario.FLASH_CRASH,
                price_shift_pct=-0.10,
                affected_days=[midpoint],
                description="单日价格闪崩10%，极端冲击测试",
            ),
            ShockScenario(
                name="连续下跌5日 -2%/日",
                scenario=StressScenario.BEAR_MARKET,
                price_shift_pct=-0.02,
                affected_days=list(range(midpoint, min(midpoint + 5, n))),
                description="连续5日每日下跌2%，模拟熊市",
            ),
            ShockScenario(
                name="连续下跌10日 -1.5%/日",
                scenario=StressScenario.BEAR_MARKET,
                price_shift_pct=-0.015,
                affected_days=list(range(third, min(third + 10, n))),
                description="连续10日每日下跌1.5%，深度调整",
            ),
            ShockScenario(
                name="波动率飙升 双倍振幅",
                scenario=StressScenario.VOLATILITY_SPIKE,
                price_shift_pct=0.03,
                affected_days=[
                    i for i in range(end_start, n)
                    if i % 2 == 0
                ],
                description="隔日±3%交替波动，波动率翻倍",
            ),
            ShockScenario(
                name="波动率飙升 双倍振幅",
                scenario=StressScenario.VOLATILITY_SPIKE,
                price_shift_pct=-0.03,
                affected_days=[
                    i for i in range(end_start, n)
                    if i % 2 == 1
                ],
                description="隔日±3%交替波动，波动率翻倍",
            ),
            ShockScenario(
                name="快速反弹 +2%/日",
                scenario=StressScenario.RECOVERY_RALLY,
                price_shift_pct=0.02,
                affected_days=list(range(end_start, n)),
                description="连续反弹测试策略适应性",
            ),
            ShockScenario(
                name="横盘震荡 ±1%",
                scenario=StressScenario.SIDEWAYS_CHOP,
                price_shift_pct=0.01,
                affected_days=[
                    i for i in range(third, min(third + 20, n))
                    if (i - third) % 4 < 2
                ],
                description="窄幅震荡，测试信号稳定性",
            ),
            ShockScenario(
                name="横盘震荡 ±1%",
                scenario=StressScenario.SIDEWAYS_CHOP,
                price_shift_pct=-0.01,
                affected_days=[
                    i for i in range(third, min(third + 20, n))
                    if (i - third) % 4 >= 2
                ],
                description="窄幅震荡，测试信号稳定性",
            ),
            ShockScenario(
                name="跳空风险 -3%",
                scenario=StressScenario.GAP_RISK,
                price_shift_pct=-0.03,
                affected_days=[midpoint, midpoint + 10],
                description="跳空低开，测试流动性风险",
            ),
        ]

    def _apply_shock(
        self, history: PortfolioHistory, shock: ShockScenario
    ) -> PortfolioHistory:
        shocked_prices: list[float] = []
        for i, snap in enumerate(history.snapshots):
            price_mult = 1.0
            for idx in shock.affected_days:
                if i >= idx:
                    price_mult *= (1.0 + shock.price_shift_pct)
            shocked_prices.append(snap.price * price_mult)

        return self._rebuild_history(history, shocked_prices)

    def _rebuild_history(
        self, history: PortfolioHistory, prices: list[float]
    ) -> PortfolioHistory:
        if not history.snapshots:
            return PortfolioHistory()

        positions: list[StrategyPosition] = []
        for snap in history.snapshots:
            if snap.position is not None:
                positions.append(snap.position)
            else:
                positions.append(
                    StrategyPosition(
                        timestamp=snap.timestamp,
                        direction=0,
                        signal_weight=0.0,
                        position_pct=0.0,
                        notional=0.0,
                    )
                )

        builder = PortfolioBuilder(initial_nav=history.initial_nav)
        return builder.build(positions, prices)

    def _failed_result(
        self, shock: ShockScenario, baseline: StrategyPerformanceReport
    ) -> StressTestResult:
        return StressTestResult(
            scenario=shock.scenario,
            description=shock.description + " [失败]",
            total_return=0.0,
            annualized_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=-1.0,
            win_rate=0.0,
            calmar_ratio=0.0,
            total_days=0,
            return_delta_vs_baseline=-baseline.total_return,
            sharpe_delta_vs_baseline=-baseline.sharpe_ratio,
            max_drawdown_delta_vs_baseline=-1.0,
            survived=False,
        )

    def _deterministic_noise(
        self, trial: int, timestamp: datetime, scale: float
    ) -> float:
        seed_val = hash(f"{trial}:{timestamp.isoformat()}") % 100000
        t = seed_val / 100000.0
        return scale * (2.0 * t - 1.0)
