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


def test_grouped_merges_repeats_ignoring_case_spacing_and_punctuation():
    repo.log_conversation("w1", "What is the redubf policy", "a1", "not_found", [])
    time.sleep(0.05)
    repo.log_conversation("w1", "what is  the REDUBF policy?", "a2", "not_found", [])
    time.sleep(0.05)
    repo.log_conversation("w1", "what is the redubf policy?!", "a3", "not_found", [])

    items = repo.list_grouped("w1")

    assert len(items) == 1
    assert items[0]["count"] == 3
    assert items[0]["question"] == "what is the redubf policy?!"
    assert items[0]["answer"] == "a3"


def test_grouped_keeps_different_outcomes_separate():
    repo.log_conversation("w1", "refund policy", "no info", "not_found", [])
    time.sleep(0.05)
    repo.log_conversation("w1", "refund policy", "30 days", "answered", ["r.pdf"])

    items = repo.list_grouped("w1")

    assert len(items) == 2
    assert {i["outcome"] for i in items} == {"not_found", "answered"}
    assert all(i["count"] == 1 for i in items)


def test_grouped_sorted_by_count_then_recency():
    repo.log_conversation("w1", "common", "a", "not_found", [])
    time.sleep(0.05)
    repo.log_conversation("w1", "common", "a", "not_found", [])
    time.sleep(0.05)
    repo.log_conversation("w1", "rare", "a", "not_found", [])

    items = repo.list_grouped("w1")

    assert [i["question"] for i in items] == ["common", "rare"]
    assert [i["count"] for i in items] == [2, 1]


def test_grouped_scoped_filtered_and_limited():
    repo.log_conversation("w1", "q1", "a", "answered", [])
    repo.log_conversation("w1", "q2", "a", "not_found", [])
    repo.log_conversation("w1", "q3", "a", "not_found", [])
    repo.log_conversation("w2", "theirs", "a", "not_found", [])

    only_missing = repo.list_grouped("w1", outcome="not_found")
    limited = repo.list_grouped("w1", limit=1)

    assert {i["question"] for i in only_missing} == {"q2", "q3"}
    assert len(limited) == 1
    assert all(i["question"] != "theirs" for i in repo.list_grouped("w1"))