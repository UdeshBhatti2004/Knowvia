from app.repositories.settings_store import load_settings, save_settings


def test_missing_settings_return_empty_dict():
    assert load_settings("widget") == {}


def test_save_then_load_round_trip():
    save_settings("widget", {"key": "wk_1", "allowed_domains": ["a.com"]})
    assert load_settings("widget") == {"key": "wk_1", "allowed_domains": ["a.com"]}


def test_save_overwrites_previous_value():
    save_settings("assistant", {"name": "A"})
    save_settings("assistant", {"name": "B"})
    assert load_settings("assistant") == {"name": "B"}


def test_kinds_and_workspaces_are_isolated():
    save_settings("widget", {"x": 1})
    save_settings("assistant", {"x": 2})
    save_settings("widget", {"x": 3}, workspace_id="other")

    assert load_settings("widget") == {"x": 1}
    assert load_settings("assistant") == {"x": 2}
    assert load_settings("widget", workspace_id="other") == {"x": 3}


def test_keys_with_dots_are_safe():
    save_settings("sources", {"fees.pdf": {"status": "Processed"}})
    assert load_settings("sources") == {"fees.pdf": {"status": "Processed"}}