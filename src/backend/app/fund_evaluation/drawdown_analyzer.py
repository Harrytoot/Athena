import math
from dataclasses import dataclass, field

from app.portfolio.portfolio_engine import StrategyInput

TRADING_DAYS = 252.0


@dataclass
class DrawdownCluster:
    drawdown_events: list["DrawdownEvent"] = field(default_factory=list)
    cluster_start_idx: int = 0
    cluster_end_idx: int = 0
    cluster_duration: int = 0
    max_overlap: float = 0.0
    total_drawdown_depth: float = 0.0


@dataclass
class TailRiskMetrics:
    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0
    cvar_99: float = 0.0
    worst_day_return: float = 0.0
    worst_week_return: float = 0.0
    worst_month_return: float = 0.0
    tail_ratio: float = 0.0


@dataclass
class DrawdownEvent:
    start_idx: int
    end_idx: int
    peak_nav: float
    trough_nav: float
    max_drawdown: float
    duration: int
    recovery_time: int


@dataclass
class DrawdownAnalysisResult:
    drawdown_events: list[DrawdownEvent] = field(default_factory=list)
    clusters: list[DrawdownCluster] = field(default_factory=list)
    max_drawdown: float = 0.0
    avg_drawdown: float = 0.0
    avg_drawdown_duration: float = 0.0
    drawdown_frequency: float = 0.0
    clustering_score: float = 0.0
    tail_risk: TailRiskMetrics = field(default_factory=TailRiskMetrics)
    ulcer_index: float = 0.0


WEEK_TRADING_DAYS = 5
MONTH_TRADING_DAYS = 21


class DrawdownAnalyzer:

    def __init__(self, cluster_gap_threshold: int = 10):
        self.cluster_gap_threshold = cluster_gap_threshold

    def analyze(
        self,
        strategies: list[StrategyInput],
        weights: list[float],
    ) -> DrawdownAnalysisResult:
        if not strategies or not weights:
            return DrawdownAnalysisResult()

        daily_returns = self._compute_portfolio_returns(strategies, weights)
        if not daily_returns:
            return DrawdownAnalysisResult()

        nav_series = self._compute_nav(daily_returns)
        events = self._compute_drawdowns(nav_series)
        clusters = self._identify_clusters(events)

        max_dd = min(ev.max_drawdown for ev in events) if events else 0.0
        avg_dd = sum(ev.max_drawdown for ev in events) / len(events) if events else 0.0
        avg_dur = sum(ev.duration for ev in events) / len(events) if events else 0.0

        total_days = len(daily_returns)
        dd_freq = len(events) / (total_days / TRADING_DAYS) if total_days > 0 else 0.0

        cluster_score = self._compute_clustering_score(events, clusters)

        tail_risk = self._compute_tail_risk(daily_returns)

        ulcer = self._compute_ulcer_index(nav_series)

        return DrawdownAnalysisResult(
            drawdown_events=events,
            clusters=clusters,
            max_drawdown=round(max_dd, 6),
            avg_drawdown=round(avg_dd, 6),
            avg_drawdown_duration=round(avg_dur, 2),
            drawdown_frequency=round(dd_freq, 4),
            clustering_score=round(cluster_score, 4),
            tail_risk=tail_risk,
            ulcer_index=round(ulcer, 6),
        )

    def _compute_portfolio_returns(
        self,
        strategies: list[StrategyInput],
        weights: list[float],
    ) -> list[float]:
        return_lists: list[list[float]] = []
        for s in strategies:
            if s.history and s.history.snapshots:
                return_lists.append(s.history.daily_returns)
            else:
                return_lists.append([])

        if not return_lists or all(len(rl) == 0 for rl in return_lists):
            return []

        min_len = min(len(rl) for rl in return_lists if len(rl) > 0)
        valid_indices = [i for i, rl in enumerate(return_lists) if len(rl) > 0]

        if not valid_indices or min_len == 0:
            return []

        effective_weights = [weights[i] for i in valid_indices]
        weight_sum = sum(effective_weights)
        if weight_sum == 0:
            return []
        norm_w = [w / weight_sum for w in effective_weights]

        portfolio_returns: list[float] = []
        for t in range(min_len):
            daily_r = sum(
                norm_w[j] * return_lists[valid_indices[j]][t]
                for j in range(len(valid_indices))
            )
            portfolio_returns.append(round(daily_r, 8))

        return portfolio_returns

    def _compute_nav(self, daily_returns: list[float]) -> list[float]:
        nav = [1.0]
        for r in daily_returns:
            nav.append(nav[-1] * (1.0 + r))
        return nav

    def _compute_drawdowns(self, nav_series: list[float]) -> list[DrawdownEvent]:
        events: list[DrawdownEvent] = []
        n = len(nav_series)
        if n < 2:
            return events

        peak = nav_series[0]
        in_drawdown = False
        dd_start = 0
        dd_peak = nav_series[0]

        for i in range(1, n):
            if nav_series[i] > peak:
                peak = nav_series[i]
                if in_drawdown:
                    dd = (dd_peak - nav_series[i - 1]) / dd_peak if dd_peak != 0 else 0.0
                    events.append(
                        DrawdownEvent(
                            start_idx=dd_start,
                            end_idx=i - 1,
                            peak_nav=dd_peak,
                            trough_nav=nav_series[i - 1],
                            max_drawdown=-round(dd, 6),
                            duration=(i - 1) - dd_start,
                            recovery_time=i - (i - 1),
                        )
                    )
                    in_drawdown = False
            else:
                if not in_drawdown:
                    in_drawdown = True
                    dd_start = i - 1
                    dd_peak = peak

        if in_drawdown:
            dd = (dd_peak - nav_series[-1]) / dd_peak if dd_peak != 0 else 0.0
            events.append(
                DrawdownEvent(
                    start_idx=dd_start,
                    end_idx=n - 1,
                    peak_nav=dd_peak,
                    trough_nav=nav_series[-1],
                    max_drawdown=-round(dd, 6),
                    duration=(n - 1) - dd_start,
                    recovery_time=0,
                )
            )

        for i in range(len(events)):
            if events[i].recovery_time == 0 and i < len(events) - 1:
                events[i].recovery_time = events[i + 1].start_idx - events[i].end_idx

        return events

    def _identify_clusters(
        self,
        events: list[DrawdownEvent],
    ) -> list[DrawdownCluster]:
        if not events:
            return []

        clusters: list[DrawdownCluster] = []
        current_cluster_events = [events[0]]

        for i in range(1, len(events)):
            gap = events[i].start_idx - current_cluster_events[-1].end_idx
            if gap <= self.cluster_gap_threshold:
                current_cluster_events.append(events[i])
            else:
                clusters.append(self._build_cluster(current_cluster_events))
                current_cluster_events = [events[i]]

        clusters.append(self._build_cluster(current_cluster_events))
        return clusters

    def _build_cluster(self, events: list[DrawdownEvent]) -> DrawdownCluster:
        start = events[0].start_idx
        end = events[-1].end_idx
        duration = end - start
        depths = [abs(e.max_drawdown) for e in events]
        max_depth = max(depths) if depths else 0.0
        total_depth = sum(depths)
        return DrawdownCluster(
            drawdown_events=events,
            cluster_start_idx=start,
            cluster_end_idx=end,
            cluster_duration=duration,
            max_overlap=max_depth,
            total_drawdown_depth=total_depth,
        )

    def _compute_clustering_score(
        self,
        events: list[DrawdownEvent],
        clusters: list[DrawdownCluster],
    ) -> float:
        if not events or not clusters:
            return 0.0

        total_dd_count = len(events)
        cluster_count = len(clusters)

        if cluster_count == 0:
            return 0.0

        events_per_cluster = total_dd_count / cluster_count

        if events_per_cluster <= 1.0:
            return 0.0

        score = min(1.0, (events_per_cluster - 1.0) / 3.0)
        return score

    def _compute_tail_risk(self, daily_returns: list[float]) -> TailRiskMetrics:
        n = len(daily_returns)
        if n < 2:
            return TailRiskMetrics()

        sorted_r = sorted(daily_returns)

        var_95 = self._percentile(sorted_r, 0.05)
        var_99 = self._percentile(sorted_r, 0.01)
        cvar_95 = self._cvar(sorted_r, var_95)
        cvar_99 = self._cvar(sorted_r, var_99)

        worst_day = min(daily_returns)

        worst_week = 0.0
        for i in range(n - WEEK_TRADING_DAYS + 1):
            cum = 1.0
            for j in range(WEEK_TRADING_DAYS):
                cum *= (1.0 + daily_returns[i + j])
            week_r = cum - 1.0
            if week_r < worst_week:
                worst_week = week_r

        worst_month = 0.0
        for i in range(n - MONTH_TRADING_DAYS + 1):
            cum = 1.0
            for j in range(MONTH_TRADING_DAYS):
                cum *= (1.0 + daily_returns[i + j])
            month_r = cum - 1.0
            if month_r < worst_month:
                worst_month = month_r

        positive_var = sum(r for r in sorted_r if r > 0)
        negative_var = abs(sum(r for r in sorted_r if r < 0))
        tail_ratio = positive_var / negative_var if negative_var > 0 else 0.0

        return TailRiskMetrics(
            var_95=round(var_95, 6),
            var_99=round(var_99, 6),
            cvar_95=round(cvar_95, 6),
            cvar_99=round(cvar_99, 6),
            worst_day_return=round(worst_day, 6),
            worst_week_return=round(worst_week, 6),
            worst_month_return=round(worst_month, 6),
            tail_ratio=round(tail_ratio, 6),
        )

    def _percentile(self, sorted_data: list[float], p: float) -> float:
        n = len(sorted_data)
        if n == 0:
            return 0.0
        idx = int(n * p)
        idx = max(0, min(n - 1, idx))
        return sorted_data[idx]

    def _cvar(self, sorted_data: list[float], var: float) -> float:
        tail = [r for r in sorted_data if r <= var]
        if not tail:
            return var
        return sum(tail) / len(tail)

    def _compute_ulcer_index(self, nav_series: list[float]) -> float:
        n = len(nav_series)
        if n < 2:
            return 0.0

        running_max = nav_series[0]
        squared_dds: list[float] = []

        for nav in nav_series:
            if nav > running_max:
                running_max = nav
            if running_max > 0:
                dd = (running_max - nav) / running_max
                squared_dds.append(dd * dd)
            else:
                squared_dds.append(0.0)

        if not squared_dds:
            return 0.0

        mean_sq = sum(squared_dds) / len(squared_dds)
        return math.sqrt(mean_sq)
