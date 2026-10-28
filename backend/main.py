
"""Entry point for the Knowvia backend."""

import uvicorn

from app.main import app


from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ask import router as ask_router
from app.api.routes.sources import router as sources_router
from app.knowledge.retrieval import refresh_knowledge_base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts, not when the module is imported.
    refresh_knowledge_base()
    yield


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

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["app"],
    )