from retrieval import retrieve_document

def test_retrieve_refund_policy():

    result = retrieve_document("Can I get a refund within 5 days")
    assert result is not None


    documents , highest_score = result

    assert len(documents) > 0 

    # Checking that the refund policy was reterived
    sources = [ document["source"] for document , score in documents]
    assert "business_info.pdf" in sources

    assert highest_score >= 0.60

def test_unrelated_question():
    result = retrieve_document("What is the capital of France")\

    documents , highest_score = result

    assert documents is None


def test_multi_part_question():

    result = retrieve_document(
        "What is the Python course duration and refund policy?"
    )

    assert result is not None

    documents , highest_score  = result

    assert len(documents) > 0 

    combined_text = " ".join(
        document["text"] for document , score in documents
    ).lower()

    assert "3 months" in combined_text
    assert "7 days" in combined_text

