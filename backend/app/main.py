"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .database import init_db
from .routes import auth, boards, cards, columns


def create_app() -> FastAPI:
    app = FastAPI(
        title="TaskFlow",
        version=__version__,
        description="Self-hosted Kanban — REST API + dashboard.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    @app.get("/api/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    app.include_router(auth.router)
    app.include_router(boards.router)
    app.include_router(columns.router)
    app.include_router(cards.router)

    # Locate the frontend directory in dev (../../frontend) and Docker (/app/frontend).
    here = Path(__file__).resolve().parent
    candidates = [here.parent.parent / "frontend", here.parent / "frontend"]
    for frontend_dir in candidates:
        if frontend_dir.exists():
            app.mount(
                "/", StaticFiles(directory=str(frontend_dir), html=True), name="static"
            )
            break

    return app


app = create_app()
