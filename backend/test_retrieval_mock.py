from unittest.mock import patch

import retrieval

def test_retrieve_refund_policy_without_gemini():

    fake_document = {
        "text": "Refund requests are allowed within 7 days of Payment",
        "source" : "business_info.pdf",
        "page" : 1
    }

    with(

         patch.object(
             retrieval,
             "decompose_query",
             return_value = [" Can I get a refund within 5 days"],
         ),

         patch.object(
              retrieval,
              "get_embedding",
              return_value =  [ 1.0 , 0.0]
         ),
         patch.object(
             retrieval,
             "knowledge_base",
             [fake_document],
         ),
         patch.object(
             retrieval,
             "document_embeddings",
             [[1.0, 0.0]],
         ),
    ):
        results, highest_score = retrieval.retrieve_document(
            "Can I get a refund within 5 days"
        )

    assert results is not None
    assert results[0][0]["source"] == "business_info.pdf"
    assert highest_score >= 0.60


def test_rejects_documents_below_threshold():

    fake_document = {
        "text": "Refund requests are allowed within 7 days",
        "source" : "business_info.pdf",
        "page": 1,
    }


    with(

        patch.object(
             retrieval,
             "decompose_query",
             return_value = ["What is the refund policy?"],
        ),
        patch.object(
             retrieval,
             "get_embedding",
             return_value = [1.0,0.0]
        ),
        patch.object(
            retrieval,
            "knowledge_base",
            [fake_document],
        ),
        patch.object(
            retrieval,
            "document_embeddings",
            [[0.0,1.0]],
        ),
    ):

      results, highest_score = retrieval.retrieve_document(
            "What is the refund policy?"
        )

      assert results is None
      assert highest_score == 0.0

def test_duplicate_documents_are_removed():

     fake_document = {
        "text": "Refund requests are allowed within 7 days.",
        "source": "business_info.pdf",
        "page": 1,
    }

     with(

          patch.object(
              retrieval,
              "decompose_query",
               return_value=[
                "What is the refund deadline?",
                "Can I request a refund?",
            ],
          ),
            patch.object(
            retrieval,
            "get_embedding",
            return_value=[1.0, 0.0],
        ),
        patch.object(
            retrieval,
            "knowledge_base",
            [fake_document],
        ),
        patch.object(
            retrieval,
            "document_embeddings",
            [[1.0, 0.0]],
        ),
     ):

         results , highest_score = retrieval.retrieve_document(
              "What is the refund deadline and can I request a refund?"
         )

         assert results is not None
         assert len(results) == 1
         assert results[0][0]["source"] == "business_info.pdf"