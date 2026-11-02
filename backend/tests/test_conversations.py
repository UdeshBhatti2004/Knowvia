import time
from app.api.routes.ask import OFF_TOPIC_MESSAGE
from app.api.routes.public import _outcome
from app.repositories import conversation_repository as repo


def test_outcome_classification():
    assert _outcome(OFF_TOPIC_MESSAGE, []) == "off_topic"
    assert _outcome("Sorry, nothing.", []) == "not_found"
    assert _outcome("Fees are 500.", [{"source": "fees.pdf"}]) == "answered"


def test_log_and_list_newest_first():
    repo.log_conversation("w1", "first?", "a1", "answered", ["fees.pdf"])
    time.sleep(0.05)
    repo.log_conversation("w1", "second?", "a2", "not_found", [])

    items = repo.list_recent("w1")

    assert [i["question"] for i in items] == ["second?", "first?"]
    assert items[1]["sources"] == ["fees.pdf"]

def test_list_is_scoped_to_workspace():
    repo.log_conversation("w1", "mine", "a", "answered", [])
    repo.log_conversation("w2", "theirs", "a", "answered", [])

    assert [i["question"] for i in repo.list_recent("w1")] == ["mine"]


def test_list_filters_by_outcome():
    repo.log_conversation("w1", "q1", "a", "answered", [])
    repo.log_conversation("w1", "q2", "a", "not_found", [])

    items = repo.list_recent("w1", outcome="not_found")

    assert [i["question"] for i in items] == ["q2"]