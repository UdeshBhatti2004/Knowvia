import os 
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key = api_key)


text = "Refund requests are allowed within 7 days"

result = client.models.embed_content(
    model="gemini-embedding-2",
    contents=text
)

embedding = result.embeddings[0].values

print("Embedding genreated successfully")
print("Number of dimensions:", len(embedding))
print("First 5 numbers:", embedding[:5])