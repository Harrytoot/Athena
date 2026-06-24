from app.infrastructure.auth import create_access_token, decode_access_token


class TestJWT:

    def test_create_and_decode_token(self):
        token = create_access_token("user-123", "testuser")
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["username"] == "testuser"
        assert "exp" in payload
        assert "iat" in payload

    def test_invalid_token_returns_none(self):
        assert decode_access_token("invalid.token.here") is None

    def test_expired_token_returns_none(self):
        assert decode_access_token("") is None
