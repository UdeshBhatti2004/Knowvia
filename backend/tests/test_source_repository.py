from app.repositories.source_repository import (
    load_sources_metadata,
    save_sources_metadata,
)

REC = {"filename": "fees.pdf", "size": 10, "status": "Processing"}


def test_empty_by_default():
    assert load_sources_metadata() == {}


def test_round_trip_with_dotted_names():
    save_sources_metadata({"fees.pdf": REC})
    assert load_sources_metadata() == {"fees.pdf": REC}


def test_save_removes_dropped_records():
    save_sources_metadata({"a.pdf": REC, "b.pdf": REC})
    save_sources_metadata({"a.pdf": REC})
    assert list(load_sources_metadata()) == ["a.pdf"]


def test_workspaces_are_isolated():
    save_sources_metadata({"a.pdf": REC}, workspace_id="other")
    assert load_sources_metadata() == {}
    assert list(load_sources_metadata(workspace_id="other")) == ["a.pdf"]