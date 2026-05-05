import enum

from sqlalchemy import DateTime, Enum, Float, Integer, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SentimentLabel(str, enum.Enum):
    NEUTRAL = "NEUTRAL"
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment_label: Mapped[SentimentLabel] = mapped_column(
        Enum(SentimentLabel, name="sentiment_label_enum"),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

