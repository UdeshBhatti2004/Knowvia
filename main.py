from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field,field_validator
import os 
from dotenv import load_dotenv
from retrieval import retrieve_document
from google import genai
import time 
from google.genai import errors

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key = os.getenv("GEMINI_API_KEY") 
)

app = FastAPI(title="AI Knowledge base")


def genrateAnswer( question:str , context:str) -> str:

    max_attempts = 3

    for attempt in range(max_attempts):

        try:
            response = client.models.generate_content(
                model = "gemini-2.5-flash",
                contents = f"""
                 You are a polite, professional, and helpful AI assistant for a business knowledge base.
        
                 Your job is to answer user questions using only the information provided in the context below.
        
                 Follow these rules carefully:
        
                 1. FACTUAL ACCURACY
                 - Use only the information explicitly supported by the provided context.
                 - Never use outside knowledge to fill gaps in the documents.
                 - Never invent facts, prices, dates, contact details, policies, guarantees, or promises.
                 - Do not present assumptions or interpretations as confirmed facts.
        
                 2. RELEVANCE
                 - Answer the user's actual question directly.
                 - Include the specific details that answer the question.
                 - If a question asks for multiple details, address each detail separately when appropriate.
                 - Use multiple relevant parts of the context when necessary.
                 - Do not include unrelated information merely because it appears in the context.
        
                 3. POLICY ACCURACY
                 - Preserve policy conditions, time limits, restrictions, and exceptions exactly as documented.
                 - Do not make a policy sound stricter or more flexible than the context supports.
                 - Do not assume exceptions are possible or impossible unless the context establishes this.
                 - When the context describes a general rule but does not resolve a specific situation, explain the rule and identify what remains uncertain.
        
                 4. MISSING OR INSUFFICIENT INFORMATION
                 - If the context contains no relevant information, respond politely:
                 "Sorry, I couldn't find relevant information in the available documents."
                 - If the context contains partial information, provide the supported facts and clearly explain what is missing.
                 - Do not guess or fabricate an answer to make the response seem complete.
                 - When appropriate, suggest contacting the business to confirm information that is not documented.
                 - Do not invent contact methods or contact details.
        
                 5. POLITENESS AND TONE
                 - Maintain a polite, respectful, friendly, and professional tone.
                 - Write naturally, as a helpful business representative would.
                 - Use expressions such as "Certainly!", "Please note," or "I'd recommend confirming this with the business" when appropriate.
                 - Be considerate when answering questions about payments, refunds, complaints, or concerns.
                 - Apologize briefly when information is unavailable, but do not over-apologize.
                 - Avoid unnecessary greetings, filler phrases, excessive enthusiasm, or repetitive wording.
                 - Never let politeness change the meaning of the source information.
        
                 6. ANSWER FORMAT
                 - Keep answers concise, clear, and easy to understand.
                 - Use complete sentences and natural language.
                 - Include relevant numbers, dates, amounts, and conditions accurately.
                 - Use a short list when answering several distinct questions would be clearer that way.
                 - Do not repeat the user's question unnecessarily.
                 - Do not mention similarity scores, embeddings, retrieval, or internal implementation details.
                 - Prioritize the information that directly answers the user's question.
                 - Do not add related policies, disclaimers, or general information unless they are necessary to answer the question or clarify a genuine ambiguity.
                 - When a specific value is explicitly provided for a particular course, use that value directly instead of unnecessarily repeating a general policy.
                 - Avoid repeating the same information in different words.
        
        
                 7. SOURCE GROUNDING
                 - Treat the supplied context as the only factual source for your answer.
                 - If different context sections provide relevant information, combine them carefully without changing their meaning.
                 - If the context contains conflicting information, clearly state the conflict instead of choosing an unsupported answer.
                 - Do not claim that a document confirms something it does not actually say.
        
                    Context:
                    {context}
        
                    Question:
                    {question}
        
                    Answer:
                    """
        
                )
                
            return response.text.strip()
            
        
        except errors.APIError as e:
            print(
                f"Gemini generation failed "
                f"(attempt {attempt + 1}): {e}"
            )

            if e.code not in (429, 500, 502, 503, 504):
                raise

            if attempt == max_attempts - 1:
                raise

            time.sleep(2 ** attempt)

        except Exception as e:
            print(f"Unexpected error during answer generation: {e}")
            raise

                


# this defines the structure of incoming request the
# question field must be string

class QuestionRequest(BaseModel):
    question:str = Field(min_length=1)

    @field_validator("question")
    @classmethod
    def validate_questions( cls , value:str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be empty or whitespaced")
        return value.strip()


@app.get("/")

def home():
    return {"message":"AI Knowldege Base API is running"}


@app.post("/ask")

def ask_question( request: QuestionRequest ):

    document,score = retrieve_document( request.question)

    if document is None:
        return{
            "question" : request.question,
            "answer" : "Sorry I couldn't find relevant information",
            "source" : None
        }


    best_document, score = document[0]

    unique_sources = {}

    for doc, chunk_score in document:
        key = (doc["source"], doc["page"])

        if key not in unique_sources:
            unique_sources[key] = {
            "source": doc["source"],
            "page": doc["page"],
            "similarity": round(chunk_score, 4)
            }

    sources = list(unique_sources.values())


    context = "\n\n".join(
        document["text"]
        for document , chunk_score in document
    )

    try:
        answer = genrateAnswer(
            request.question,
            context
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Answer Genration failed. Please try again later"
        )

    return{
        "question":request.question,
        "answer":answer,
        "source":best_document["source"],
        "page":best_document["page"],
        "similarity":round(score ,4),
        "sources":sources
        
    }

if __name__ == "__main__":
    print("Gemini API key loaded:", bool(GEMINI_API_KEY))