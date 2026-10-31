import pytest

from app.repositories import user_repository as users


def test_create_and_get():
    u = users.create_user("A@Example.com ", "hash1")
    assert u["email"] == "a@example.com"
    assert users.get_by_email("a@example.com")["_id"] == u["_id"]
    assert users.get_by_email("A@EXAMPLE.COM")["_id"] == u["_id"]
    assert users.get_by_id(u["_id"])["email"] == "a@example.com"


def test_duplicate_email_rejected():
    users.create_user("a@example.com", "h")
    with pytest.raises(users.UserExistsError):
        users.create_user("A@example.com", "h2")


def test_missing_returns_none():
    assert users.get_by_email("nobody@example.com") is None
    assert users.get_by_id("nope") is None