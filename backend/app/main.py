from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ask import router as ask_router
from app.api.routes.sources import router as sources_router
from app.knowledge.retrieval import refresh_knowledge_base
from app.knowledge.startup import stop_retrying, warm_up
from app.services.source_service import recover_interrupted_uploads
from app.api.routes.assistant import router as assistant_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts, not when the module is imported.
    # A failed build (for example a rate limit) no longer stops the server.
    # Uploads made after this moment belong to live background jobs, so
    # recovery must never touch them.
    started_at = datetime.now(timezone.utc)

    def recover():
        changed = recover_interrupted_uploads(started_at)
        if changed:
            print(f"Recovered {changed} interrupted upload(s).")

    # recover() runs only after a successful refresh (now or in a retry).
    retry_task = await warm_up(refresh_knowledge_base, on_ready=recover)
    yield
    await stop_retrying(retry_task)


def create_app() -> FastAPI:
    app = FastAPI(title="Knowvia API", lifespan=lifespan)

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

    @app.get("/")
    def home():
        return {"message": "Knowvia API is running"}

    app.include_router(ask_router)
    app.include_router(sources_router)
    app.include_router(assistant_router)   

    return app

app = create_app()