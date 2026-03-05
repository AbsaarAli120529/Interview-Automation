import uuid
import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.sql.base import Base

class InterviewTemplate(Base):
    __tablename__ = "interview_templates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False, default="Untitled Template")
    role_name: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default_for_role: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Deprecated: retained for backward-compatible reads only; not written by new code
    settings: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Primary configuration fields
    technical_config: Mapped[dict] = mapped_column(JSON, nullable=True)
    coding_config: Mapped[dict] = mapped_column(JSON, nullable=True)
    conversational_config: Mapped[dict] = mapped_column(JSON, nullable=True)

    interviews: Mapped[list["Interview"]] = relationship("Interview", back_populates="template")
