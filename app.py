import os
from datetime import datetime, timezone
from typing import Iterable, List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db, get_engine
from hf_client import predict_sentiment
from models import AnalysisLog, Base, SentimentLabel
from schemas import PredictRequest, PredictResponse


# Load .env for local/dev. In production, prefer real environment variables.
load_dotenv()


def _parse_allowed_origins(value: str) -> List[str]:
    return [o.strip() for o in (value or "").split(",") if o.strip()]


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v


app = FastAPI(title="Sentiment Analysis Information System", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=get_engine())


# --- CORS (restrictive by default) ---
allowed_origins = _parse_allowed_origins(os.getenv("ALLOWED_ORIGINS", ""))
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )


# --- Security headers middleware ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # HSTS should only be enabled behind HTTPS (e.g. a reverse proxy / load balancer).
    # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/predict", response_model=PredictResponse)
async def predict(payload: PredictRequest, db: Session = Depends(get_db)):
    # Extra safety: ensure secrets exist server-side.
    try:
        _require_env("HF_TOKEN")
        _require_env("DATABASE_URL")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        label_str, score = await predict_sentiment(payload.text)
        label = SentimentLabel(label_str)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    log = AnalysisLog(input_text=payload.text, sentiment_label=label, score=score)
    db.add(log)
    db.commit()
    db.refresh(log)

    ts = log.timestamp
    if isinstance(ts, datetime) and ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    return PredictResponse(sentiment_label=label.value, score=log.score, timestamp=ts)

