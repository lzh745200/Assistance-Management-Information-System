"""Tests for User model enhancements (revoke_all_tokens)."""


class TestUserRevokeTokens:
    """Tests for User.revoke_all_tokens() method."""

    def test_revoke_all_tokens_increments_version(self):
        """revoke_all_tokens() should increment token_version and set password_changed_at."""
        from app.models.user import User
        from datetime import datetime

        user = User(username="test_user", role="operator")
        original_version = user.token_version_safe
        assert original_version == 0

        user.revoke_all_tokens()

        assert user.token_version == original_version + 1
        assert user.token_version_safe == original_version + 1
        assert user.password_changed_at is not None
        assert isinstance(user.password_changed_at, datetime)

    def test_revoke_all_tokens_handles_none_token_version(self):
        """Should handle token_version being None gracefully."""
        from app.models.user import User

        user = User(username="test_user", role="operator")
        user.token_version = None

        user.revoke_all_tokens()

        assert user.token_version == 1  # None treated as 0, then +1
        assert user.token_version_safe == 1

    def test_multiple_revokes_stack(self):
        """Each call to revoke_all_tokens should increment by 1."""
        from app.models.user import User

        user = User(username="test_user", role="operator")

        for expected in [1, 2, 3, 4, 5]:
            user.revoke_all_tokens()
            assert user.token_version == expected
            assert user.token_version_safe == expected

    def test_revoke_preserves_other_attributes(self):
        """revoke_all_tokens should not change other user attributes."""
        from app.models.user import User

        user = User(
            username="preserved_user",
            role="admin",
            full_name="Test Admin",
            is_active=True,
        )
        original_name = user.full_name
        original_role = user.role
        original_active = user.is_active

        user.revoke_all_tokens()

        assert user.full_name == original_name
        assert user.role == original_role
        assert user.is_active == original_active


class TestTokenVersionSafe:
    """Tests for token_version_safe property (pre-existing)."""

    def test_token_version_safe_defaults_to_zero(self):
        from app.models.user import User

        user = User(username="new_user", role="viewer")
        assert user.token_version_safe == 0

    def test_token_version_safe_handles_none(self):
        from app.models.user import User

        user = User(username="test_user", role="viewer")
        user.token_version = None
        assert user.token_version_safe == 0
