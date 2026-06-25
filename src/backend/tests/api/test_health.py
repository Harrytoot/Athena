

class TestHealthEndpoint:

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_health_response_content_type(self, client):
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]
