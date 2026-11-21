from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))

class Concept(Base):
    __tablename__ = "concepts"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    prereqs: Mapped[list] = mapped_column(JSON, default=list)

class Misconception(Base):
    __tablename__ = "misconceptions"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"))
    description: Mapped[str] = mapped_column(String(300))

class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    prompt: Mapped[str] = mapped_column(String(1000))
    # [{"key": "A", "text": "...", "misconception_id": null | "id"}]
    options: Mapped[list] = mapped_column(JSON)
    answer_key: Mapped[str] = mapped_column(String(2))

class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    choice: Mapped[str] = mapped_column(String(2))
    correct: Mapped[bool] = mapped_column(Boolean)
    misconception_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class Mastery(Base):
    __tablename__ = "mastery"
    __table_args__ = (UniqueConstraint("user_id", "concept_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"))
    score: Mapped[float] = mapped_column(Float, default=0.5)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(10), default="unseen")
