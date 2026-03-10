import uuid
import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.sql.base import Base

class InterviewSessionSection(Base):
    __tablename__ = "interview_session_sections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    interview_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    section_type: Mapped[str] = mapped_column(String(50), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="sections", foreign_keys=[interview_session_id])
    questions: Mapped[list["InterviewSessionQuestion"]] = relationship("InterviewSessionQuestion", back_populates="section", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "section_type IN ('technical', 'coding', 'conversational')",
            name="check_section_type"
        ),
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed')",
            name="check_section_status"
        ),
    )
