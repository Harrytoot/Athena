import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.decision_semantics.schema import DecisionSemantic


@dataclass
class SymbolNode:
    symbol: str
    active_semantic: DecisionSemantic | None = None
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    sequence_number: int = 0
    last_updated: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class CorrelationEdge:
    from_symbol: str
    to_symbol: str
    coefficient: float
    edge_id: str = ""
    inserted_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self):
        if not self.edge_id:
            self.edge_id = self._compute_id()
        self.coefficient = float(self.coefficient)

    def _compute_id(self) -> str:
        raw = json.dumps({
            "from_symbol": self.from_symbol,
            "to_symbol": self.to_symbol,
            "coefficient": self.coefficient,
        }, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @property
    def is_significant(self) -> bool:
        return abs(self.coefficient) > 0.1

    @property
    def direction(self) -> str:
        if self.coefficient > 0:
            return "positive"
        if self.coefficient < 0:
            return "negative"
        return "neutral"


@dataclass
class PortfolioUpdateResult:
    symbol: str
    applied: bool
    propagated_to: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    consistency_violations: list[str] = field(default_factory=list)


class PortfolioRuntimeGraph:

    def __init__(self, correlation_threshold: float = 0.3):
        self._nodes: dict[str, SymbolNode] = {}
        self._edges: dict[str, CorrelationEdge] = {}
        self._threshold = correlation_threshold

    def register_symbol(
        self, symbol: str, semantic: DecisionSemantic | None = None
    ) -> SymbolNode:
        node = self._nodes.get(symbol)
        if node is None:
            node = SymbolNode(symbol=symbol, active_semantic=semantic)
            self._nodes[symbol] = node
        else:
            if semantic is not None:
                node.active_semantic = semantic
        return node

    def update_symbol(self, symbol: str, semantic: DecisionSemantic) -> PortfolioUpdateResult:
        node = self._nodes.get(symbol)
        if node is None:
            node = self.register_symbol(symbol, semantic)
        else:
            node.active_semantic = semantic

        node.sequence_number += 1
        node.last_updated = datetime.now(timezone.utc).isoformat()

        propagated_to: list[str] = []
        conflicts: list[str] = []
        violations: list[str] = []

        for dep in node.dependents:
            edge_key = self._edge_key(symbol, dep)
            edge = self._edges.get(edge_key)
            if edge is None:
                edge_key = self._edge_key(dep, symbol)
                edge = self._edges.get(edge_key)

            if edge is None or not edge.is_significant:
                continue

            propagated_to.append(dep)

            dep_node = self._nodes.get(dep)
            if dep_node and dep_node.active_semantic:
                if semantic.action != "HOLD" and dep_node.active_semantic.action != "HOLD":
                    if edge.coefficient > self._threshold:
                        if semantic.action != dep_node.active_semantic.action:
                            conflicts.append(
                                f"{symbol}({semantic.action}) vs {dep}({dep_node.active_semantic.action}) "
                                f"with correlation {edge.coefficient:.2f}"
                            )

        if node.dependencies:
            for dep_sym in node.dependencies:
                dep_node = self._nodes.get(dep_sym)
                if dep_node and dep_node.active_semantic:
                    if dep_node.active_semantic.action != "HOLD" and semantic.action == "HOLD":
                        violations.append(
                            f"{symbol} HOLD conflicts with dependent {dep_sym}({dep_node.active_semantic.action})"
                        )

        return PortfolioUpdateResult(
            symbol=symbol,
            applied=True,
            propagated_to=propagated_to,
            conflicts=conflicts,
            consistency_violations=violations,
        )

    def set_correlation(
        self, symbol_a: str, symbol_b: str, coefficient: float
    ) -> CorrelationEdge:
        self.register_symbol(symbol_a)
        self.register_symbol(symbol_b)

        edge_key = self._edge_key(symbol_a, symbol_b)
        edge = CorrelationEdge(
            from_symbol=symbol_a,
            to_symbol=symbol_b,
            coefficient=coefficient,
        )
        self._edges[edge_key] = edge

        node_a = self._nodes[symbol_a]
        if symbol_b not in node_a.dependents:
            node_a.dependents.append(symbol_b)

        node_b = self._nodes[symbol_b]
        if symbol_a not in node_b.dependencies:
            node_b.dependencies.append(symbol_a)

        return edge

    def set_correlations(
        self, correlations: list[tuple[str, str, float]]
    ) -> list[CorrelationEdge]:
        edges: list[CorrelationEdge] = []
        for sym_a, sym_b, coef in correlations:
            edges.append(self.set_correlation(sym_a, sym_b, coef))
        return edges

    def remove_correlation(self, symbol_a: str, symbol_b: str) -> None:
        edge_key = self._edge_key(symbol_a, symbol_b)
        self._edges.pop(edge_key, None)

        node_a = self._nodes.get(symbol_a)
        if node_a and symbol_b in node_a.dependents:
            node_a.dependents.remove(symbol_b)

        node_b = self._nodes.get(symbol_b)
        if node_b and symbol_a in node_b.dependencies:
            node_b.dependencies.remove(symbol_a)

    def get_correlation(self, symbol_a: str, symbol_b: str) -> float:
        edge = self._edges.get(self._edge_key(symbol_a, symbol_b))
        if edge is None:
            edge = self._edges.get(self._edge_key(symbol_b, symbol_a))
        if edge is None:
            return 0.0
        return edge.coefficient if edge.from_symbol == symbol_a else edge.coefficient

    def get_correlations_for(self, symbol: str) -> dict[str, float]:
        result: dict[str, float] = {}
        for edge_key, edge in self._edges.items():
            sym_a, sym_b = self._parse_edge_key(edge_key)
            if sym_a == symbol:
                result[sym_b] = edge.coefficient
            elif sym_b == symbol:
                result[sym_a] = edge.coefficient
        return result

    def get_node(self, symbol: str) -> SymbolNode | None:
        return self._nodes.get(symbol)

    def get_active_semantics(self) -> dict[str, DecisionSemantic]:
        result: dict[str, DecisionSemantic] = {}
        for sym, node in self._nodes.items():
            if node.active_semantic is not None:
                result[sym] = node.active_semantic
        return result

    def check_portfolio_consistency(self) -> list[str]:
        issues: list[str] = []

        for edge_key, edge in self._edges.items():
            if not edge.is_significant:
                continue

            sym_a, sym_b = self._parse_edge_key(edge_key)
            node_a = self._nodes.get(sym_a)
            node_b = self._nodes.get(sym_b)

            if node_a is None or node_b is None:
                continue
            if node_a.active_semantic is None or node_b.active_semantic is None:
                continue

            sem_a = node_a.active_semantic
            sem_b = node_b.active_semantic

            if sem_a.action == "HOLD" or sem_b.action == "HOLD":
                continue

            if edge.coefficient > self._threshold:
                if sem_a.action != sem_b.action:
                    issues.append(
                        f"Divergent actions on correlated pair {sym_a}({sem_a.action}) / "
                        f"{sym_b}({sem_b.action}) with correlation {edge.coefficient:.2f}"
                    )

            elif edge.coefficient < -self._threshold:
                if sem_a.action == sem_b.action:
                    issues.append(
                        f"Identical actions on negatively correlated pair {sym_a}({sem_a.action}) / "
                        f"{sym_b}({sem_b.action}) with correlation {edge.coefficient:.2f}"
                    )

        return issues

    def query_impact(
        self, symbol: str, field_change: dict[str, float]
    ) -> dict[str, float]:
        correlations = self.get_correlations_for(symbol)
        impact: dict[str, float] = {}
        for target_sym, coef in correlations.items():
            if abs(coef) > self._threshold:
                total_impact = sum(
                    abs(v) * abs(coef) for v in field_change.values()
                )
            impact[target_sym] = round(total_impact, 6)
        return impact

    def get_all_symbols(self) -> list[str]:
        return list(self._nodes.keys())

    def get_all_edges(self) -> list[CorrelationEdge]:
        return list(self._edges.values())

    def reset(self) -> None:
        self._nodes.clear()
        self._edges.clear()

    @staticmethod
    def _edge_key(symbol_a: str, symbol_b: str) -> str:
        sorted_pair = sorted([symbol_a, symbol_b])
        return f"{sorted_pair[0]}::{sorted_pair[1]}"

    def _parse_edge_key(self, edge_key: str) -> tuple[str, str]:
        parts = edge_key.split("::")
        return parts[0], parts[1]
