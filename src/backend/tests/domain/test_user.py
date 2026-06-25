from app.domain.entities.user import User


class TestUser:
    def test_create_user(self):
        user = User(username="alice", email="alice@test.com", display_name="Alice")
        assert user.username == "alice"
        assert user.email == "alice@test.com"
        assert user.is_active is True

    def test_deactivate_user(self):
        user = User(username="alice", email="alice@test.com")
        user.deactivate()
        assert user.is_active is False

    def test_activate_user(self):
        user = User(username="alice", email="alice@test.com")
        user.deactivate()
        user.activate()
        assert user.is_active is True
