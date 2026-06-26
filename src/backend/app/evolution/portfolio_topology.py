import math
from dataclasses import dataclass, field
from statistics import mean as stat_mean

from app.portfolio.portfolio_engine import StrategyInput


@dataclass
class StrategyCluster:
    cluster_label: str
    strategy_ids: list[str]
    avg_intra_cluster_corr: float
    size: int

    @property
    def is_singleton(self) -> bool:
        return self.size == 1


@dataclass
class TopologyMetrics:
    effective_n: float
    herfindahl_index: float
    correlation_complexity: float
    risk_balance_ratio: float
    structural_efficiency: float
    redundancy_score: float
    fragility_score: float
    entropy: float

    @property
    def is_well_diversified(self) -> bool:
        return self.effective_n >= 3.0 and self.structural_efficiency >= 0.6

    @property
    def is_concentrated(self) -> bool:
        return self.herfindahl_index >= 0.3 or self.effective_n < 2.0


@dataclass
class PortfolioTopologyReport:
    metrics: TopologyMetrics = field(default_factory=lambda: TopologyMetrics(
        effective_n=0.0,
        herfindahl_index=0.0,
        correlation_complexity=0.0,
        risk_balance_ratio=0.0,
        structural_efficiency=0.0,
        redundancy_score=0.0,
        fragility_score=0.0,
        entropy=0.0,
    ))
    clusters: list[StrategyCluster] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)
    assessment: str = ""


class PortfolioTopologyAnalyzer:

    def __init__(
        self,
        correlation_threshold_high: float = 0.7,
        correlation_threshold_low: float = 0.3,
        max_risk_concentration: float = 0.4,
    ):
        self.correlation_threshold_high = correlation_threshold_high
        self.correlation_threshold_low = correlation_threshold_low
        self.max_risk_concentration = max_risk_concentration

    def analyze(
        self,
        strategies: list[StrategyInput],
        weights: list[float] | None = None,
        correlation_matrix: dict[str, dict[str, float]] | None = None,
    ) -> PortfolioTopologyReport:
        if not strategies:
            return PortfolioTopologyReport(assessment="无策略数据")

        n = len(strategies)
        ids = [s.strategy_id for s in strategies]

        if weights is None:
            weights = [1.0 / n] * n
        else:
            total = sum(weights)
            if total > 0:
                weights = [w / total for w in weights]
            else:
                weights = [1.0 / n] * n

        if correlation_matrix is None:
            correlation_matrix = self._infer_correlation_matrix(strategies)

        corr_flat = self._flatten_correlation(correlation_matrix, ids)

        vol_map = {
            s.strategy_id: s.performance.daily_volatility * math.sqrt(252.0)
            for s in strategies
        }

        effective_n = self._compute_effective_n(corr_flat, n)

        herfindahl = self._compute_herfindahl(weights)

        risk_balance = self._compute_risk_balance(weights, vol_map, ids)

        corr_complexity = self._compute_correlation_complexity(corr_flat)

        redundancy = self._compute_redundancy(corr_flat, n)

        fragility = self._compute_fragility(weights, corr_flat, ids, correlation_matrix)

        structural_efficiency = self._compute_structural_efficiency(
            effective_n, herfindahl, corr_complexity, risk_balance, redundancy
        )

        entropy = self._compute_entropy(weights)

        metrics = TopologyMetrics(
            effective_n=round(effective_n, 4),
            herfindahl_index=round(herfindahl, 4),
            correlation_complexity=round(corr_complexity, 4),
            risk_balance_ratio=round(risk_balance, 4),
            structural_efficiency=round(structural_efficiency, 4),
            redundancy_score=round(redundancy, 4),
            fragility_score=round(fragility, 4),
            entropy=round(entropy, 4),
        )

        clusters = self._identify_clusters(ids, correlation_matrix)

        suggestions = self._generate_suggestions(metrics, clusters, n)

        assessment = self._assess_topology(metrics, clusters, suggestions)

        return PortfolioTopologyReport(
            metrics=metrics,
            clusters=clusters,
            improvement_suggestions=suggestions,
            assessment=assessment,
        )

    def _infer_correlation_matrix(
        self, strategies: list[StrategyInput]
    ) -> dict[str, dict[str, float]]:
        ids = [s.strategy_id for s in strategies]
        n = len(ids)
        matrix: dict[str, dict[str, float]] = {}
        for i, id_i in enumerate(ids):
            matrix[id_i] = {}
            for j, id_j in enumerate(ids):
                if i == j:
                    matrix[id_i][id_j] = 1.0
                else:
                    matrix[id_i][id_j] = 0.3
        return matrix

    def _flatten_correlation(
        self,
        matrix: dict[str, dict[str, float]],
        ids: list[str],
    ) -> list[float]:
        flat: list[float] = []
        for i, id_i in enumerate(ids):
            for j, id_j in enumerate(ids):
                if i < j:
                    flat.append(matrix.get(id_i, {}).get(id_j, 0.3))
        return flat

    def _compute_effective_n(
        self, correlations: list[float], n: int
    ) -> float:
        if n <= 1:
            return float(n)
        avg_corr = sum(correlations) / len(correlations) if correlations else 0.0
        if abs(avg_corr) > 1.0 - 1e-10:
            return 1.0
        if avg_corr < 0:
            denom = 1.0 + (n - 1) * avg_corr
            return float(n) / denom if denom > 0 else float(n)
        denom = 1.0 + (n - 1) * avg_corr
        return float(n) / denom if denom > 0 else 1.0

    def _compute_herfindahl(self, weights: list[float]) -> float:
        return sum(w ** 2 for w in weights)

    def _compute_risk_balance(
        self,
        weights: list[float],
        vol_map: dict[str, float],
        ids: list[str],
    ) -> float:
        risk_contributions = []
        for i, id_i in enumerate(ids):
            vol = vol_map.get(id_i, 0.1)
            rc = weights[i] * vol
            risk_contributions.append(rc)

        total_rc = sum(risk_contributions)
        if total_rc <= 0:
            return 0.0

        normalized = [rc / total_rc for rc in risk_contributions]
        n = len(normalized)
        equal_share = 1.0 / n

        deviations = sum(abs(nc - equal_share) for nc in normalized)
        max_deviation = 2.0 * (1.0 - equal_share)
        balance = 1.0 - (deviations / max_deviation) if max_deviation > 0 else 1.0
        return max(0.0, min(1.0, balance))

    def _compute_correlation_complexity(self, correlations: list[float]) -> float:
        if not correlations:
            return 0.0
        unique_abs_values = set(round(abs(c), 4) for c in correlations)
        n_unique = len(unique_abs_values)
        max_unique = len(correlations)
        if max_unique <= 1:
            return 0.0
        return n_unique / max_unique

    def _compute_redundancy(
        self, correlations: list[float], n: int
    ) -> float:
        if not correlations or n <= 1:
            return 0.0
        high_corr = sum(1 for c in correlations if c > self.correlation_threshold_high)
        return high_corr / len(correlations)

    def _compute_fragility(
        self,
        weights: list[float],
        correlations: list[float],
        ids: list[str],
        matrix: dict[str, dict[str, float]],
    ) -> float:
        n = len(ids)
        if n <= 1:
            return 0.0

        max_weight = max(weights) if weights else 0.0

        max_pair_corr = max(correlations) if correlations else 0.0

        fragility = max_weight * 0.4 + max(max_pair_corr, 0.0) * 0.6
        return min(1.0, fragility)

    def _compute_entropy(self, weights: list[float]) -> float:
        total = sum(weights)
        if total <= 0:
            return 0.0
        norm = [w / total for w in weights]
        entropy = 0.0
        for w in norm:
            if w > 0:
                entropy -= w * math.log(w)
        max_entropy = math.log(len(weights)) if len(weights) > 0 else 1.0
        if max_entropy <= 0:
            return 0.0
        return entropy / max_entropy

    def _compute_structural_efficiency(
        self,
        effective_n: float,
        herfindahl: float,
        corr_complexity: float,
        risk_balance: float,
        redundancy: float,
    ) -> float:
        total_strategies = max(effective_n, 1.0)

        en_component = min(1.0, effective_n / max(total_strategies, 1.0)) * 0.25

        concentration = 1.0 - herfindahl
        if total_strategies > 1:
            ideal_hhi = 1.0 / total_strategies
            concentration = 1.0 - max(0.0, (herfindahl - ideal_hhi) / (1.0 - ideal_hhi)) if ideal_hhi < 1.0 else 1.0
        hhi_component = concentration * 0.25

        cc_component = corr_complexity * 0.15

        rb_component = risk_balance * 0.20

        red_component = (1.0 - redundancy) * 0.15

        score = en_component + hhi_component + cc_component + rb_component + red_component
        return min(1.0, max(0.0, score))

    def _identify_clusters(
        self,
        ids: list[str],
        matrix: dict[str, dict[str, float]],
    ) -> list[StrategyCluster]:
        n = len(ids)
        if n == 0:
            return []
        if n == 1:
            return [
                StrategyCluster(
                    cluster_label="cluster_1",
                    strategy_ids=list(ids),
                    avg_intra_cluster_corr=1.0,
                    size=1,
                )
            ]

        visited: set[str] = set()
        clusters: list[StrategyCluster] = []
        cluster_idx = 1

        for id_i in ids:
            if id_i in visited:
                continue
            cluster: list[str] = [id_i]
            visited.add(id_i)
            for id_j in ids:
                if id_j in visited:
                    continue
                corr = matrix.get(id_i, {}).get(id_j, 0.3)
                if corr > self.correlation_threshold_high:
                    if self._all_connected(id_j, cluster, matrix):
                        cluster.append(id_j)
                        visited.add(id_j)

            intra_corr = self._avg_intra_cluster_corr(cluster, matrix)
            clusters.append(
                StrategyCluster(
                    cluster_label=f"cluster_{cluster_idx}",
                    strategy_ids=cluster,
                    avg_intra_cluster_corr=round(intra_corr, 4),
                    size=len(cluster),
                )
            )
            cluster_idx += 1

        for id_i in ids:
            if id_i not in visited:
                clusters.append(
                    StrategyCluster(
                        cluster_label=f"cluster_{cluster_idx}",
                        strategy_ids=[id_i],
                        avg_intra_cluster_corr=1.0,
                        size=1,
                    )
                )
                visited.add(id_i)
                cluster_idx += 1

        clusters.sort(key=lambda c: c.size, reverse=True)
        return clusters

    def _all_connected(
        self,
        candidate: str,
        cluster: list[str],
        matrix: dict[str, dict[str, float]],
    ) -> bool:
        for member in cluster:
            corr = matrix.get(candidate, {}).get(member, 0.3)
            if corr <= self.correlation_threshold_high:
                return False
        return True

    def _avg_intra_cluster_corr(
        self,
        cluster: list[str],
        matrix: dict[str, dict[str, float]],
    ) -> float:
        if len(cluster) <= 1:
            return 1.0
        total = 0.0
        count = 0
        for i, id_i in enumerate(cluster):
            for j, id_j in enumerate(cluster):
                if i < j:
                    total += matrix.get(id_i, {}).get(id_j, 0.3)
                    count += 1
        return total / count if count > 0 else 1.0

    def _generate_suggestions(
        self,
        metrics: TopologyMetrics,
        clusters: list[StrategyCluster],
        n: int,
    ) -> list[str]:
        suggestions: list[str] = []

        if metrics.structural_efficiency < 0.4:
            suggestions.append("组合结构效率低: 建议增加低相关策略以提升分散化")
        elif metrics.structural_efficiency < 0.6:
            suggestions.append("组合结构效率中等: 考虑调整权重或替换高相关策略")

        if metrics.redundancy_score > 0.5:
            suggestions.append("策略冗余度高: 存在多个高度相关策略，建议合并或替换")

        if metrics.fragility_score > 0.6:
            suggestions.append("组合脆弱性高: 建议降低最大策略权重并引入对冲策略")

        if metrics.risk_balance_ratio < 0.4:
            suggestions.append("风险贡献失衡: 建议重新平衡各策略的风险预算")

        if metrics.effective_n < 2.0 and n >= 3:
            suggestions.append("有效策略数过低: 当前策略高度相关，分散化效果有限")

        if metrics.herfindahl_index > 0.3:
            suggestions.append("权重集中度过高: 建议设置权重上限并分散配置")

        if metrics.entropy < 0.5:
            suggestions.append("权重分布不均衡: 建议采用更均匀的权重分配")

        large_clusters = [c for c in clusters if c.size >= 3]
        if large_clusters:
            c = large_clusters[0]
            suggestions.append(
                f"策略聚类过大: {c.cluster_label}包含{c.size}个高相关策略，建议精简"
            )

        return suggestions

    def _assess_topology(
        self,
        metrics: TopologyMetrics,
        clusters: list[StrategyCluster],
        suggestions: list[str],
    ) -> str:
        parts: list[str] = []

        if metrics.structural_efficiency >= 0.7:
            parts.append("组合结构: 优秀")
        elif metrics.structural_efficiency >= 0.5:
            parts.append("组合结构: 良好")
        elif metrics.structural_efficiency >= 0.3:
            parts.append("组合结构: 一般")
        else:
            parts.append("组合结构: 较差")

        parts.append(f"结构效率: {metrics.structural_efficiency:.2f}")
        parts.append(f"有效策略数: {metrics.effective_n:.1f}")
        parts.append(f"冗余度: {metrics.redundancy_score:.2f}")
        parts.append(f"脆弱性: {metrics.fragility_score:.2f}")

        if len(clusters) > 1:
            parts.append(f"策略聚类: {len(clusters)}组")
        else:
            parts.append("策略聚类: 单一簇")

        if suggestions:
            parts.append(f"改进建议: {len(suggestions)}条")

        return " | ".join(parts)
