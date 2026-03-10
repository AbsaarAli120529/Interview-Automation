import uuid
import datetime
from sqlalchemy import Text, Integer, String, ForeignKey, CheckConstraint, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.sql.base import Base

QUESTION_TYPES = ("technical", "coding", "conversational")

class InterviewSessionQuestion(Base):
    __tablename__ = "interview_session_questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    interview_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_session_sections.id", ondelete="CASCADE"), nullable=False, index=True)

    # Question type discriminator — required
    question_type: Mapped[str] = mapped_column(String(20), nullable=False, default="technical")

    # Technical question (FK to questions table)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="SET NULL"), nullable=True)
    custom_text: Mapped[str] = mapped_column(Text, nullable=True)

    # Coding problem (FK to coding_problems table)
    coding_problem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("coding_problems.id", ondelete="SET NULL"), nullable=True)

    # Conversational round index (1-based)
    conversation_round: Mapped[int] = mapped_column(Integer, nullable=True)

    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="session_questions")
    section: Mapped["InterviewSessionSection"] = relationship("InterviewSessionSection", back_populates="questions")
    question: Mapped["Question"] = relationship("Question")
    coding_problem: Mapped["CodingProblem"] = relationship("CodingProblem")

    __table_args__ = (
        CheckConstraint(
            "question_type IN ('technical', 'coding', 'conversational')",
            name="check_session_question_type"
        ),
        CheckConstraint(
            "(question_type = 'technical' AND question_id IS NOT NULL) OR "
            "(question_type = 'coding' AND coding_problem_id IS NOT NULL) OR "
            "(question_type = 'conversational' AND conversation_round IS NOT NULL) OR "
            "(custom_text IS NOT NULL)",
            name="check_question_payload"
        ),
        Index(
            "idx_session_section_order",
            "interview_session_id",
            "section_id",
            "order"
        ),
    )
