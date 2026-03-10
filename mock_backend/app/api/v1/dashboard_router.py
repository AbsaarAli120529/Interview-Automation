import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from typing import Dict, Optional
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

from app.db.sql.session import get_db_session
from app.db.sql.unit_of_work import UnitOfWork
from app.db.sql.models.interview import Interview
from app.db.sql.models.user import User
from app.db.sql.enums import InterviewStatus, UserRole
from app.core.config import settings
from app.services.report_generation_service import report_generation_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_admin_from_token(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db_session)):
    """Get current admin user from token - extracted to avoid circular import."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    async with UnitOfWork(session) as uow:
        import uuid
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise credentials_exception
        user = await uow.users.get_by_id(user_id)
        if user is None:
            raise credentials_exception
        if user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return user

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    current_admin: User = Depends(get_current_admin_from_token),
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, int]:
    """
    Get dashboard statistics using real database aggregates.
    """
    result_total = await session.execute(select(func.count(Interview.id)))
    total_interviews = result_total.scalar() or 0

    result_completed = await session.execute(select(func.count(Interview.id)).where(Interview.status == InterviewStatus.COMPLETED))
    completed = result_completed.scalar() or 0

    result_pending = await session.execute(select(func.count(Interview.id)).where(Interview.status == InterviewStatus.SCHEDULED))
    pending_review = result_pending.scalar() or 0

    result_candidates = await session.execute(select(func.count(distinct(Interview.candidate_id))))
    total_candidates = result_candidates.scalar() or 0

    # Count in_progress as pending
    result_in_progress = await session.execute(select(func.count(Interview.id)).where(Interview.status == InterviewStatus.IN_PROGRESS))
    in_progress = result_in_progress.scalar() or 0
    
    # Total pending = scheduled + in_progress
    pending = pending_review + in_progress
    
    # Flagged interviews (not implemented yet, return 0)
    flagged = 0
    
    return {
        "total_interviews": total_interviews,
        "completed": completed,
        "pending": pending,
        "flagged": flagged
    }


@router.get("/interviews/{interview_id}/report")
async def get_interview_report(
    interview_id: str,
    session_id: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_from_token),
    session: AsyncSession = Depends(get_db_session)
) -> Dict:
    """
    Get comprehensive interview report with scores, feedback, and recommendations.
    
    Args:
        interview_id: Interview UUID string
        session_id: Optional session UUID string (uses latest if not provided)
        
    Returns:
        Full interview report dictionary
    """
    try:
        import uuid
        interview_uuid = uuid.UUID(interview_id)
        
        # 1️⃣ Fetch Interview
        stmt = select(Interview).where(Interview.id == interview_uuid)
        result = await session.execute(stmt)
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
        
        # 2️⃣ If report_json is missing
        if not interview.report_json:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Report has not been generated yet. Please complete the interview first."
            )
        
        # 3️⃣ Otherwise return stored report
        return interview.report_json
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid interview ID format")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate report")
