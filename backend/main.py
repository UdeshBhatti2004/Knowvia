
from pathlib import Path
import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from google import genai
from google.genai import errors
from retrieval import retrieve_document, refresh_knowledge_base
import json
from datetime import datetime, timezone

from retrieval import retrieve_document

BACKEND_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BACKEND_DIR / "documents"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


load_dotenv(BACKEND_DIR.parent / ".env")


SOURCES_METADATA_FILE = DOCUMENTS_DIR / "sources_metadata.json"


def load_sources_metadata():
    if not SOURCES_METADATA_FILE.exists():
        return {}

    try:
        with SOURCES_METADATA_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        raise HTTPException(
            status_code=500,
            detail="Unable to read uploaded-file metadata.",
        )


def save_sources_metadata(metadata):
    temporary_file = SOURCES_METADATA_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    temporary_file.replace(SOURCES_METADATA_FILE)



GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY was not found. Check the .env file in the project root."
    )

client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(title="AI Knowledge Base")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def genrateAnswer(question: str, context: str) -> str:
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"""
                You are a polite, professional, and helpful AI assistant for a business knowledge base.

                Answer user questions using only the information provided in the context.

                Rules:
                1. Use only facts explicitly supported by the context.
                2. Never invent facts, prices, dates, policies, or contact details.
                3. Answer the user's actual question directly and concisely.
                4. Preserve policy conditions, restrictions, and time limits accurately.
                5. If information is missing, say:
                "Sorry, I couldn't find relevant information in the available documents."
                6. If the context contains conflicting information, explain the conflict.
                7. Do not mention similarity scores, embeddings, or internal implementation details.

                Context:
                {context}

                Question:
                {question}

                Answer:
                """,
            )

            if not response.text:
                raise RuntimeError("Gemini returned an empty answer.")

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



class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be empty or whitespace.")
        return value.strip()


@app.get("/")
def home():
    return {"message": "AI Knowledge Base API is running"}


@app.post("/sources/upload")
async def upload_source(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    content = await file.read()

    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF.",
        )

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="PDF files must be 10 MB or smaller.",
        )

    destination = DOCUMENTS_DIR / Path(file.filename).name

    if destination.exists():
        raise HTTPException(
            status_code=409,
            detail="A file with this name already exists.",
        )

    destination.write_bytes(content)

    try:
        refresh_knowledge_base()
    except Exception as e:
        destination.unlink(missing_ok=True)
        print(f"Failed to refresh knowledge base: {e}")
        raise HTTPException(
            status_code=500,
            detail="PDF was not added to the knowledge base. Please try again.",
        )

    record = {
    "filename": destination.name,
    "size": len(content),
    "uploaded_at": datetime.now(timezone.utc).isoformat(),
    "timestamp_is_estimated": False,
    "status": "Processed",
}

    try:
        metadata = load_sources_metadata()
        metadata[destination.name] = record
        save_sources_metadata(metadata)
    except Exception as e:
        destination.unlink(missing_ok=True)
        print(f"Failed to save source metadata: {e}")

        raise HTTPException(
            status_code=500,
            detail="Unable to save file metadata. Please try again.",
        )

    return {
        "message": "PDF uploaded successfully.",
        **record,
    }

@app.post("/ask")
def ask_question(request: QuestionRequest):
    try:
        documents, _ = retrieve_document(request.question)
    except Exception as e:
        print(f"Document retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Document retrieval failed. Check the backend logs.",
        )

    if not documents:
        return {
            "question": request.question,
            "answer": (
                "Sorry, I couldn't find relevant information "
                "in the available documents."
            ),
            "source": None,
            "page": None,
            "similarity": None,
            "sources": [],
        }

    best_document, best_score = documents[0]

    unique_sources = {}

    for doc, chunk_score in documents:
        key = (doc["source"], doc["page"])

        if key not in unique_sources:
            unique_sources[key] = {
                "source": doc["source"],
                "page": doc["page"],
                "similarity": round(chunk_score, 4),
            }

    sources = list(unique_sources.values())

    context = "\n\n".join(
        doc["text"] for doc, _ in documents
    )

    try:
        answer = genrateAnswer(request.question, context)
    except Exception as e:
        print(f"Answer generation failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="Answer generation failed. Please try again later.",
        )

    return {
        "question": request.question,
        "answer": answer,
        "source": best_document["source"],
        "page": best_document["page"],
        "similarity": round(best_score, 4),
        "sources": sources,
    }

@app.get("/sources")

def get_sources():

    metadata = load_sources_metadata()
    sources = []

    for path in DOCUMENTS_DIR.iterdir():
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue

        record = metadata.get(path.name)

        if record:
            sources.append(record)
        else:
            sources.append({
                "filename":path.name,
                "size":path.stat().st_size,
                "upload_at": datetime.fromtimestamp(
                    path.stat().st_mtime,
                    tz=timezone.utc
                ).isoformat(),
                "timestamp_is_estimated":True,
                "status":"Processed"
            })

        sources.sort(
        key=lambda source: source.get("uploaded_at", ""),
        reverse=True,
        )

        return {"sources": sources}


if __name__ == "__main__":
    print("Gemini API key loaded:", bool(GEMINI_API_KEY))

