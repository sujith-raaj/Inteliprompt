from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import create_tables
from backend.routers import history, prompt


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    create_tables()
    yield


app = FastAPI(
    title="IntelliPrompt API",
    description=(
        "Adaptive Multi-stage Prompt Optimization (AMPOA) + "
        "Model-Adaptive Prompt Translation (MAPT) backend."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS – allow all origins in development
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(prompt.router)
app.include_router(history.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def health_check():
    """Simple health/liveness probe."""
    return {"status": "ok", "service": "IntelliPrompt API"}
