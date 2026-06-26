import math
from statistics import NormalDist


def pearson_correlation(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n < 3 or len(y) != n:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
    if std_x == 0 or std_y == 0:
        return 0.0
    return round(cov / (std_x * std_y), 6)


def spearman_rank_correlation(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n < 3 or len(y) != n:
        return 0.0

    def rank(values: list[float]) -> list[float]:
        indexed = sorted((v, i) for i, v in enumerate(values))
        ranks = [0.0] * n
        for pos, (_, idx) in enumerate(indexed):
            ranks[idx] = float(pos + 1)
        return ranks

    return pearson_correlation(rank(x), rank(y))


def information_coefficient(scores: list[float], forward_returns: list[float]) -> float:
    return pearson_correlation(scores, forward_returns)


def rank_information_coefficient(scores: list[float], forward_returns: list[float]) -> float:
    return spearman_rank_correlation(scores, forward_returns)


def sharpe_ratio(returns: list[float], annual_factor: float = 252.0) -> float:
    if len(returns) < 2:
        return 0.0
    mean_r = sum(returns) / len(returns)
    if mean_r == 0:
        return 0.0
    variance = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    std_r = math.sqrt(variance)
    if std_r == 0:
        return 0.0
    daily_sharpe = mean_r / std_r
    return round(daily_sharpe * math.sqrt(annual_factor), 6)


def win_rate(signals: list[int], forward_returns: list[float]) -> float:
    if len(signals) != len(forward_returns):
        return 0.0
    traded = [(s, r) for s, r in zip(signals, forward_returns) if s != 0]
    if not traded:
        return 0.0
    wins = sum(1 for s, r in traded if (s > 0 and r > 0) or (s < 0 and r < 0))
    return round(wins / len(traded), 6)
