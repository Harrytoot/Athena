import json

import pytest


def _collect_response_fields(response_data: dict, prefix: str = "") -> set:
    fields = set()
    for key, value in response_data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        fields.add(full_key)
        if isinstance(value, dict):
            fields |= _collect_response_fields(value, full_key)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    fields |= _collect_response_fields(item, f"{full_key}[]")
    return fields


class TestNoLegacyModelLeakage:

    LEGACY_TERMS = {
        "MarketScore", "MarketScoreService",
        "RiskReport", "ScenarioReport", "ExecutionReport",
        "DecisionReport", "FactorAttribution",
        "ConsensusItemDTO", "consensusItems",
        "RiskItemDTO", "riskItems",
        "ScenarioEntryDTO", "scenarios",
        "SignalEnum", "STRONG_BUY", "STRONG_SELL",
        "ConsensusTypeEnum", "SeverityEnum",
        "ActionEnum",
        "FeatureRepository", "SQLAlchemyFeatureRepository",
    }

    INTERNAL_MODULE_PATHS = [
        "app.domain.market.market_score",
        "app.execution.execution_report",
        "app.decision_transparency.decision_report_builder",
        "app.decision_transparency.decision_trace",
        "app.decision_transparency.factor_attribution",
        "app.decision_transparency.risk_explainer",
        "app.feature_store",
    ]

    def test_serializer_does_not_import_legacy_modules(self):
        import app.decision_api.semantic_serializer as mod
        source = mod.__file__
        assert source is not None

        with open(source, encoding="utf-8") as f:
            content = f.read()

        for path in self.INTERNAL_MODULE_PATHS:
            assert path not in content, f"Semantic serializer imports legacy module: {path}"

    def test_gateway_does_not_import_legacy_modules(self):
        import app.decision_api.semantic_gateway as mod
        source = mod.__file__
        assert source is not None

        with open(source, encoding="utf-8") as f:
            content = f.read()

        for path in self.INTERNAL_MODULE_PATHS:
            assert path not in content, f"Gateway imports legacy module: {path}"

    def test_controller_does_not_expose_internal_models(self):
        from app.decision_api.semantic_controller import SemanticController

        public_methods = [
            m for m in dir(SemanticController)
            if not m.startswith("_") and callable(getattr(SemanticController, m, None))
        ]

        for method_name in public_methods:
            method = getattr(SemanticController, method_name)
            import inspect
            try:
                hints = inspect.signature(method)
                return_annotation = hints.return_annotation
                if return_annotation is not inspect.Parameter.empty:
                    annotation_str = str(return_annotation)
                    for term in self.LEGACY_TERMS:
                        assert term not in annotation_str, (
                            f"Method '{method_name}' return type references legacy model: {term}"
                        )
            except (ValueError, TypeError):
                pass

    def test_response_dto_has_no_legacy_field_names(self):
        from app.decision_api.semantic_serializer import DecisionSemanticResponse

        legacy_aliases = {
            "consensusItems", "riskItems", "scenarios",
            "signalEnum", "signalLabel", "explanation",
            "consensus_items", "risk_items",
        }

        fields = DecisionSemanticResponse.model_fields
        for field_name in fields:
            assert field_name not in legacy_aliases, f"Legacy field '{field_name}' in response DTO"

        model_dump = DecisionSemanticResponse.model_json_schema()
        props = model_dump.get("properties", {})
        for prop_name in props:
            assert prop_name not in legacy_aliases, f"Legacy field '{prop_name}' in JSON schema"

    def test_explain_response_has_no_legacy_field_names(self):
        from app.decision_api.semantic_serializer import ExplainResponse

        legacy_aliases = {
            "consensusItems", "riskItems", "scenarios",
            "signalEnum", "signalLabel", "explanation",
            "consensus_items", "risk_items",
        }

        fields = ExplainResponse.model_fields
        for field_name in fields:
            assert field_name not in legacy_aliases, f"Legacy field '{field_name}' in explain DTO"

    def test_internal_models_not_in_api_init(self):
        import app.decision_api as api_module
        source = api_module.__file__
        assert source is not None

        with open(source, encoding="utf-8") as f:
            content = f.read()

        internal_imports = [
            "MarketScore", "ExecutionReport", "DecisionReport",
            "FactorAttribution", "RiskReport",
        ]
        for name in internal_imports:
            assert name not in content, f"Internal model '{name}' leaked into decision_api __init__"
