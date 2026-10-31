from app.repositories import workspace_repository as ws


def test_create_and_lookups():
    w = ws.create_workspace("user1", " Acme ")
    assert w["name"] == "Acme"
    assert len(w["widget_key"]) >= 24
    assert ws.get_by_id(w["_id"])["owner_id"] == "user1"
    assert ws.get_by_owner("user1")["_id"] == w["_id"]
    assert ws.get_by_widget_key(w["widget_key"])["_id"] == w["_id"]


def test_widget_keys_unique():
    a = ws.create_workspace("u1", "A")
    b = ws.create_workspace("u2", "B")
    assert a["widget_key"] != b["widget_key"]


def test_missing_returns_none():
    assert ws.get_by_id("nope") is None
    assert ws.get_by_owner("nope") is None
    assert ws.get_by_widget_key("nope") is None