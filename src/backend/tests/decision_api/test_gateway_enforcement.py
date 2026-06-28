import pytest
from fastapi import APIRouter

from app.decision_api.semantic_gateway import router as gateway_router


class TestGatewayEnforcement:

    def test_gateway_is_the_only_router(self):
        import app.api.v1.decision as decision_module
        assert hasattr(decision_module, "router")
        assert decision_module.router is gateway_router, \
            "app.api.v1.decision.router must be exactly the gateway router"

    def test_gateway_has_required_endpoints(self):
        full_paths = set()
        for route in gateway_router.routes:
            if hasattr(route, "path"):
                full_paths.add(route.path)

        assert "/decision/{symbol}" in full_paths, f"Missing GET /decision/{{symbol}}, got: {full_paths}"
        assert "/decision/batch" in full_paths, f"Missing POST /decision/batch, got: {full_paths}"
        assert "/decision/explain/{symbol}" in full_paths, f"Missing GET /decision/explain/{{symbol}}, got: {full_paths}"

    def test_get_endpoint_uses_semantic_response(self):
        for route in gateway_router.routes:
            if hasattr(route, "path") and route.path == "/decision/{symbol}":
                if hasattr(route, "methods") and "GET" in route.methods:
                    assert route.response_model is not None, \
                        "GET /decision/{symbol} must have response_model"
                    model_name = route.response_model.__name__
                    assert "Semantic" in model_name, \
                        f"GET response model must be semantic: got {model_name}"
                    assert "Decision" not in model_name.split("Semantic")[-1] or "SemanticResponse" in model_name, \
                        f"Response model should be DecisionSemanticResponse: got {model_name}"

    def test_batch_endpoint_exists_and_uses_semantic_response(self):
        for route in gateway_router.routes:
            if hasattr(route, "path") and route.path == "/decision/batch":
                assert "POST" in route.methods if hasattr(route, "methods") else False
                assert route.response_model is not None

    def test_explain_endpoint_exists_and_uses_explain_response(self):
        for route in gateway_router.routes:
            if hasattr(route, "path") and route.path == "/decision/explain/{symbol}":
                assert "GET" in route.methods if hasattr(route, "methods") else False
                assert route.response_model is not None

    def test_no_direct_decision_service_bypass(self):
        import app.api.v1.decision as decision_module
        import inspect

        source = inspect.getsource(decision_module)
        assert "DecisionService" not in source, \
            "decision.py must not directly reference DecisionService"
        assert "get_decision_service" not in source, \
            "decision.py must not directly use get_decision_service"

    def test_gateway_prefix_is_decision(self):
        assert gateway_router.prefix == "/decision", \
            f"Gateway prefix must be /decision, got: {gateway_router.prefix}"
