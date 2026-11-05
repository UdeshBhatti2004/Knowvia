import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import require_user
from app.api.routes.conversations import router as conversations_router
from app.api.routes.ask import router as ask_router
from app.api.routes.assistant import router as assistant_router
from app.api.routes.auth import router as auth_router
from app.api.routes.billing import router as billing_router
from app.api.routes.public import router as public_router
from app.api.routes.sources import router as sources_router
from app.api.routes.usage import router as usage_router
from app.api.routes.widget import router as widget_router
from app.core.config import CORS_ORIGINS
from app.services.source_service import recover_interrupted_uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts. Knowledge bases are built lazily per
    # workspace on first use, so startup only fixes uploads that a restart
    # left in "Processing". Uploads made after started_at belong to live
    # background jobs, so recovery never touches them.
    started_at = datetime.now(timezone.utc)

    try:
        changed = await asyncio.to_thread(recover_interrupted_uploads, started_at)
        if changed:
            print(f"Recovered {changed} interrupted upload(s).")
    except Exception as exc:
        print(f"Upload recovery failed: {exc}")

    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Knowvia API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def home():
        return {"message": "Knowvia API is running"}

    @app.api_route("/health", methods=["GET", "HEAD"])
    def health():
        return {"status": "ok"}

    authed = [Depends(require_user)]

    # Dashboard API: account token required.
    app.include_router(ask_router, dependencies=authed)
    app.include_router(sources_router, dependencies=authed)
    app.include_router(assistant_router, dependencies=authed)
    app.include_router(conversations_router, dependencies=authed)
    app.include_router(usage_router, dependencies=authed)

    # Open or self-protected: login, public widget (widget key), widget routes
    # (per-route protection inside widget.py).
    app.include_router(auth_router)
    app.include_router(public_router)
    app.include_router(widget_router)
    app.include_router(billing_router)

    return app


app = create_app()