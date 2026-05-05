from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SentimentLabel = Literal["NEUTRAL", "POSITIVE", "NEGATIVE"]


class PredictRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Russian text to analyze",
        examples=["Сегодня был отличный день!"],
    )


class PredictResponse(BaseModel):
    sentiment_label: SentimentLabel
    score: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime

