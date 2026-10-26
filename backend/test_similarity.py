import os
import numpy as np
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def get_embedding(text):
    result = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text
    )
    return result.embeddings[0].values


def cosine_similarity(vector_a , vector_b):
    a = np.array(vector_a)
    b = np.array(vector_b)

    return np.dot(a,b) /(
        np.linalg.norm(a) * np.linalg.norm(b)
    )

document = "Refund requests are allowed within 7 days."
question = "Can I get my money back after five days?"


document_embedding = get_embedding(document)
question_embedding = get_embedding(question)

score = cosine_similarity(
    document_embedding,
    question_embedding
)

print("Cosine Simlarity :" ,score)