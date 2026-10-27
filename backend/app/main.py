
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ask import router as ask_router
from app.api.routes.sources import router as sources_router


def create_app() -> FastAPI:
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

    @app.get("/")
    def home():
        return {"message": "AI Knowledge Base API is running"}

    app.include_router(ask_router)
    app.include_router(sources_router)

    return app


app = create_app()
