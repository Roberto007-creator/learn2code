from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    submissions: Mapped[list["Submission"]] = relationship(back_populates="user")
    events: Mapped[list["LearningEvent"]] = relationship(back_populates="user")


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    topic: Mapped[str] = mapped_column(String(64), index=True)
    difficulty: Mapped[str] = mapped_column(String(16), index=True)
    statement: Mapped[str] = mapped_column(Text)
    examples: Mapped[str] = mapped_column(Text, default="")

    submissions: Mapped[list["Submission"]] = relationship(back_populates="problem")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[str] = mapped_column(ForeignKey("problems.id"), index=True)

    language: Mapped[str] = mapped_column(String(32), default="python")
    code: Mapped[str] = mapped_column(Text)

    # MVP: статус можно ставить вручную (accepted/rejected) либо позже подключить judge
    status: Mapped[str] = mapped_column(String(16), default="submitted")

    time_spent_sec: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # простая телеметрия (частично агентами)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    had_edge_case_issue: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="submissions")
    problem: Mapped["Problem"] = relationship(back_populates="submissions")
    reviews: Mapped[list["CodeReview"]] = relationship(back_populates="submission")


class CodeReview(Base):
    __tablename__ = "code_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)

    summary: Mapped[str] = mapped_column(String(300), default="")
    details: Mapped[str] = mapped_column(Text, default="")

    score_readability: Mapped[int] = mapped_column(Integer, default=0)  # 0..10
    score_correctness: Mapped[int] = mapped_column(Integer, default=0)
    score_efficiency: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    submission: Mapped["Submission"] = relationship(back_populates="reviews")


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # problem_view / submission_created / mentor_requested / review_requested
    event_type: Mapped[str] = mapped_column(String(64), index=True)

    # JSON как строка: по-студенчески и кросс-СУБД
    payload_json: Mapped[str] = mapped_column(Text, default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="events")
