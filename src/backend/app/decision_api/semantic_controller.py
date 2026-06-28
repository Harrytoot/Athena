from app.application.services.market_score_service import MarketScoreService
from app.application.services.stock_service import StockService
from app.decision_api.semantic_cache import SemanticCache
from app.decision_api.semantic_serializer import (
    DecisionSemanticResponse,
    ExplainResponse,
    SemanticSerializer,
)
from app.decision_semantics.confidence_model import ConfidenceModel
from app.decision_semantics.mapper import SemanticMapper
from app.decision_semantics.registry import DEFAULT_SEMANTIC_VERSION, SemanticRegistry
from app.decision_semantics.schema import DecisionSemantic
from app.decision_semantics.validator import SemanticValidator
from app.decision_transparency.factor_attribution import FactorAttributionEngine
from app.decision_transparency.scenario_simulator import ScenarioSimulator
from app.decision_transparency.signal_explainer import SignalExplainer
from app.domain.market.market_score import MarketScore


class SemanticController:

    def __init__(
        self,
        market_score_service: MarketScoreService,
        stock_service: StockService,
        cache: SemanticCache | None = None,
    ):
        self._market_score_service = market_score_service
        self._stock_service = stock_service
        self._cache = cache or SemanticCache()
        self._signal_explainer = SignalExplainer()
        self._factor_engine = FactorAttributionEngine()
        self._scenario_simulator = ScenarioSimulator()
        self._mapper = SemanticMapper()
        self._confidence_model = ConfidenceModel()
        self._validator = SemanticValidator()
        self._registry = SemanticRegistry()
        self._serializer = SemanticSerializer()

    async def decide(self, symbol: str) -> DecisionSemantic | None:
        stock = await self._stock_service.get_stock_detail(symbol)
        if stock is None:
            return None

        score_data = await self._market_score_service.get_score()
        score_values = {
            "trend": score_data["trend"],
            "liquidity": score_data["liquidity"],
            "breadth": score_data["breadth"],
            "volatility": score_data["volatility"],
            "sentiment": score_data["sentiment"],
        }

        cached = self._cache.get(symbol, score_values, DEFAULT_SEMANTIC_VERSION)
        if cached is not None:
            return cached

        semantic = self._build_semantic(stock.symbol, stock.name, score_values)
        self._cache.set(symbol, score_values, semantic, DEFAULT_SEMANTIC_VERSION)
        return semantic

    async def decide_response(self, symbol: str) -> DecisionSemanticResponse | None:
        semantic = await self.decide(symbol)
        if semantic is None:
            return None
        return self._serializer.serialize(semantic)

    async def decide_batch(self, symbols: list[str]) -> list[DecisionSemanticResponse]:
        results: list[DecisionSemanticResponse] = []
        for symbol in symbols:
            response = await self.decide_response(symbol)
            if response is not None:
                results.append(response)
        return results

    async def explain(self, symbol: str) -> ExplainResponse | None:
        semantic = await self.decide(symbol)
        if semantic is None:
            return None
        return self._serializer.serialize_explain(semantic)

    def _build_semantic(self, symbol: str, name: str, score_values: dict) -> DecisionSemantic:
        score = MarketScore(
            trend=score_values["trend"],
            liquidity=score_values["liquidity"],
            breadth=score_values["breadth"],
            volatility=score_values["volatility"],
            sentiment=score_values["sentiment"],
        )

        explanation = self._signal_explainer.explain(score)
        attribution = self._factor_engine.attribute(score)
        scenario_results = self._scenario_simulator.simulate(
            trend=score.trend,
            liquidity=score.liquidity,
            breadth=score.breadth,
            volatility=score.volatility,
            sentiment=score.sentiment,
        )

        signal_semantic = self._mapper.map_signal(explanation)
        factors = self._mapper.map_factors(score, attribution)
        risk_semantic = self._mapper.map_risk_from_signals(attribution.items, scenario_results)
        scenario_semantic = self._mapper.map_scenario(scenario_results, signal_semantic.direction)

        confidence = self._confidence_model.compute(
            signal=signal_semantic,
            factors=factors,
            scenario=scenario_semantic,
            risk=risk_semantic,
        )

        consistency = self._validator.validate(
            signal=signal_semantic,
            factors=factors,
            risk=risk_semantic,
            scenario=scenario_semantic,
        )

        action = self._resolve_action(signal_semantic.direction)
        action_label = self._resolve_action_label(action)
        summary = explanation.summary

        return DecisionSemantic(
            symbol=symbol,
            name=name,
            signal=signal_semantic,
            factors=factors,
            risk=risk_semantic,
            scenario=scenario_semantic,
            confidence_score=confidence,
            consistency=consistency,
            action=action,
            action_label=action_label,
            summary=summary,
            semantic_version=DEFAULT_SEMANTIC_VERSION,
        )

    def _resolve_action(self, direction: str) -> str:
        if direction == "LONG":
            return "APPROVE"
        if direction == "SHORT":
            return "REJECT"
        return "HOLD"

    def _resolve_action_label(self, action: str) -> str:
        labels = {
            "APPROVE": "执行买入",
            "HOLD": "等待确认信号",
            "REJECT": "清仓离场",
        }
        return labels.get(action, "等待确认信号")
