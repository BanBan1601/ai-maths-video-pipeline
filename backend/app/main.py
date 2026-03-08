from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings

RENDERS_DIR = Path("/data/renders")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic for production migrations)
    from app.db.session import engine, Base
    import app.models  # noqa: F401 — registers all models with Base metadata
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="AI Maths Video Pipeline", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve rendered video files at /renders/<filename>
RENDERS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/renders", StaticFiles(directory=str(RENDERS_DIR)), name="renders")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
