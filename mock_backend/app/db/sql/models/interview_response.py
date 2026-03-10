import uuid
import datetime
from sqlalchemy import Text, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.sql.base import Base

class InterviewResponse(Base):
    __tablename__ = "interview_responses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_session_questions.id", ondelete="CASCADE"), nullable=False)
    
    answer_text: Mapped[str] = mapped_column(Text, nullable=True)
    answer_audio_url: Mapped[str] = mapped_column(String, nullable=True)
    answer_mode: Mapped[str] = mapped_column(String, nullable=False)  # "text", "audio", "code"
    
    # Evaluation results
    ai_score: Mapped[float] = mapped_column(Float, nullable=True)  # Score out of 10
    ai_feedback: Mapped[str] = mapped_column(Text, nullable=True)
    evaluation_json: Mapped[dict] = mapped_column(JSON, nullable=True)  # Full evaluation details
    
    submitted_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session: Mapped["InterviewSession"] = relationship("InterviewSession")
    question: Mapped["InterviewSessionQuestion"] = relationship("InterviewSessionQuestion")
