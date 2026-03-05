import uuid
import random
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.sql.unit_of_work import UnitOfWork
from app.db.sql.enums import InterviewStatus
from app.db.sql.models.interview_session import InterviewSession
from app.db.sql.models.interview import Interview
from app.db.sql.models.interview_session_question import InterviewSessionQuestion
from app.db.sql.models.interview_response import InterviewResponse
from app.db.sql.models.user import CandidateProfile
from app.db.sql.models.coding_problem import CodingProblem, TestCase
from app.db.sql.models.question import QuestionType
from app.services.answer_evaluation_service import answer_evaluation_service

# ── Mock score generation ──────────────────────────────────────────────────────
_STRENGTH_POOL = [
    "Clear communication and structured thinking",
    "Strong grasp of SQL and data manipulation",
    "Good understanding of ML model evaluation",
    "Solid problem-solving approach",
    "Confident and concise answers",
]
_GAP_POOL = [
    "Could improve depth on neural network architecture",
    "Limited exposure to distributed computing",
    "Overfitting discussion lacked concrete techniques",
    "Could elaborate more on production deployment",
]
_RECOMMENDATIONS = [
    ("PROCEED",  "Strong candidate — recommend moving forward."),
    ("REVIEW",   "Good potential — recommend technical panel review."),
    ("PROCEED",  "Meets bar — proceed to next round."),
]


def _generate_mock_result(interview_id: uuid.UUID) -> Dict[str, Any]:
    """
    Seeded deterministic mock scoring — same interview always gets same result.
    Score range: 70–95.
    """
    rng = random.Random(interview_id.int)
    score = round(rng.uniform(70.0, 95.0), 1)
    recommendation, note = rng.choice(_RECOMMENDATIONS)
    strengths = rng.sample(_STRENGTH_POOL, k=2)
    gaps = rng.sample(_GAP_POOL, k=1)
    fraud_risk = rng.choice(["LOW", "LOW", "LOW", "MEDIUM"])
    return {
        "final_score": score,
        "recommendation": recommendation,
        "fraud_risk": fraud_risk,
        "strengths": strengths,
        "gaps": gaps,
        "notes": note,
    }


class InterviewSessionSQLService:

    @staticmethod
    async def _get_session_and_interview(
        uow: UnitOfWork,
        session_id: uuid.UUID,
        candidate_id: Optional[uuid.UUID] = None,
        with_for_update: bool = False,
    ):
        stmt = select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.status == "active",
        )
        if with_for_update:
            stmt = stmt.with_for_update()

        result = await uow.session.execute(stmt)
        session_obj = result.scalar_one_or_none()

        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or not active",
            )

        if candidate_id and session_obj.candidate_id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to you",
            )

        interview = await uow.interviews.get_by_id(
            session_obj.interview_id, with_for_update=with_for_update
        )
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
            )

        return session_obj, interview

    @staticmethod
    async def validate_session(
        session: AsyncSession,
        session_id: uuid.UUID,
        candidate_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        async with UnitOfWork(session) as uow:
            session_obj, interview = await InterviewSessionSQLService._get_session_and_interview(
                uow, session_id, candidate_id
            )
            return {
                "session_id": str(session_obj.id),
                "interview_id": str(interview.id),
                "candidate_id": str(session_obj.candidate_id),
                "status": session_obj.status,
            }

    @staticmethod
    async def get_sections(
        session: AsyncSession,
        session_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> list:
        async with UnitOfWork(session) as uow:
            from app.db.sql.models.interview_session_section import InterviewSessionSection
            from app.db.sql.models.interview_session_question import InterviewSessionQuestion
            from app.db.sql.models.interview_response import InterviewResponse
            
            session_obj, _ = await InterviewSessionSQLService._get_session_and_interview(
                uow, session_id, candidate_id
            )
            
            stmt = select(InterviewSessionSection).where(
                InterviewSessionSection.interview_session_id == session_obj.id
            ).order_by(InterviewSessionSection.order_index)
            
            result = await session.execute(stmt)
            sections = result.scalars().all()
            
            res = []
            for s in sections:
                q_stmt = select(InterviewSessionQuestion.id).where(
                    InterviewSessionQuestion.interview_session_id == session_obj.id,
                    InterviewSessionQuestion.section_id == s.id
                )
                q_res = await session.execute(q_stmt)
                q_ids = list(q_res.scalars().all())
                
                completed_q = 0
                if q_ids:
                    resp_stmt = select(func.count(InterviewResponse.id)).where(
                        InterviewResponse.session_id == session_obj.id,
                        InterviewResponse.question_id.in_(q_ids)
                    )
                    resp_res = await session.execute(resp_stmt)
                    completed_q = resp_res.scalar() or 0
                
                res.append({
                    "id": str(s.id),
                    "section_type": s.section_type,
                    "order_index": s.order_index,
                    "duration_minutes": s.duration_minutes,
                    "status": s.status,
                    "total_questions": len(q_ids),
                    "completed_questions": completed_q,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                    "is_current": s.id == session_obj.current_section_id
                })
            return res

    @staticmethod
    async def start_section(
        session: AsyncSession,
        session_id: uuid.UUID,
        section_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> Dict[str, Any]:
        async with UnitOfWork(session) as uow:
            from app.db.sql.models.interview_session_section import InterviewSessionSection
            
            session_obj, interview = await InterviewSessionSQLService._get_session_and_interview(
                uow, session_id, candidate_id, with_for_update=True
            )
            
            target_section = await uow.session.get(InterviewSessionSection, section_id)
            if not target_section or target_section.interview_session_id != session_obj.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Section not found in this session"
                )
            
            if target_section.status == "completed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot start a completed section"
                )
                
            now = datetime.now(timezone.utc)
            
            # If there's an active section, mark it as completed or leave it?
            # Normally we should enforce one active section at a time.
            if session_obj.current_section_id and session_obj.current_section_id != section_id:
                current_section = await uow.session.get(InterviewSessionSection, session_obj.current_section_id)
                if current_section and current_section.status == "in_progress":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Another section is already in progress. Please complete it first."
                    )
            
            session_obj.current_section_id = section_id
            target_section.status = "in_progress"
            if not target_section.started_at:
                target_section.started_at = now
            
            await uow.flush()
            
            return {
                "state": "IN_PROGRESS",
                "section_id": str(target_section.id),
                "section_type": target_section.section_type,
                "status": target_section.status
            }

    @staticmethod
    async def get_session_state(
        session: AsyncSession,
        session_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> Dict[str, Any]:
        async with UnitOfWork(session) as uow:
            session_obj, interview = await InterviewSessionSQLService._get_session_and_interview(
                uow, session_id, candidate_id
            )

            if not session_obj.current_section_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active section. Please start a section first."
                )

            stmt = (
                select(InterviewSessionQuestion)
                .options(
                    selectinload(InterviewSessionQuestion.question),
                    selectinload(InterviewSessionQuestion.coding_problem),
                )
                .where(
                    InterviewSessionQuestion.interview_session_id == session_obj.id,
                    InterviewSessionQuestion.section_id == session_obj.current_section_id
                )
                .order_by(InterviewSessionQuestion.order)
            )
            result = await session.execute(stmt)
            questions = result.scalars().all()

            # Find the first unanswered question
            # We determine if a question is answered by checking InterviewResponse
            responses_stmt = select(InterviewResponse.question_id).where(
                InterviewResponse.session_id == session_obj.id
            )
            responses_result = await session.execute(responses_stmt)
            answered_q_ids = set(responses_result.scalars().all())

            unanswered_questions = [q for q in questions if q.id not in answered_q_ids]

            if not unanswered_questions:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="No more questions in current section"
                )

            q = unanswered_questions[0]
            answered_count_in_section = len(questions) - len(unanswered_questions)
            
            q_type = getattr(q, "question_type", None) or "technical"

            # ── CODING branch ─────────────────────────────────────────────────
            if q_type == "coding":
                # Prefer coding_problem loaded via direct FK (new path)
                coding_problem = q.coding_problem

                # Legacy fallback: coding loaded via Question.question_type
                if coding_problem is None and q.question and q.question.question_type == QuestionType.CODING:
                    cp_result = await session.execute(
                        select(CodingProblem).where(CodingProblem.question_id == q.question.id)
                    )
                    coding_problem = cp_result.scalars().first()

                if not coding_problem:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Coding problem configuration missing for this question.",
                    )

                tc_result = await session.execute(
                    select(TestCase)
                    .where(
                        TestCase.problem_id == coding_problem.id,
                        TestCase.is_hidden == False,  # noqa: E712
                    )
                    .order_by(TestCase.order)
                )
                visible_tcs = tc_result.scalars().all()

                return {
                    "type": "coding",
                    "question_id": str(q.question.id) if q.question else None,
                    "session_question_id": str(q.id),
                    "problem_id": str(coding_problem.id),
                    "title": coding_problem.title,
                    "difficulty": coding_problem.difficulty,
                    "description": coding_problem.description,
                    "starter_code": coding_problem.starter_code or {},
                    "examples": [
                        {"input": tc.input, "expected_output": tc.expected_output}
                        for tc in visible_tcs
                    ],
                    "time_limit_sec": coding_problem.time_limit_sec,
                    "question_number": answered_count_in_section + 1,
                    "total_questions": len(questions),
                }

            # ── CONVERSATIONAL branch ─────────────────────────────────────────
            if q_type == "conversational":
                return {
                    "type": "conversational",
                    "conversation_round": q.conversation_round,
                    "round_number": q.conversation_round,
                    "answer_mode": "AUDIO",
                    "time_limit_sec": 300,
                    "question_text": q.custom_text or (q.question.text if q.question else ""),
                    "question_number": answered_count_in_section + 1,
                    "total_questions": len(questions),
                }

            # ── TECHNICAL branch ──────────────────────────────────────────────
            answer_mode = "TEXT"
            time_limit_sec = 240

            if interview.curated_questions and "questions" in interview.curated_questions:
                questions_list = interview.curated_questions["questions"]
                # Match by order or question_id in curated_questions
                q_data = None
                for curated_q in questions_list:
                    if curated_q.get("question_id") == str(q.question_id):
                        q_data = curated_q
                        break
                
                if not q_data and len(questions_list) > answered_count_in_section:
                    q_data = questions_list[answered_count_in_section]
                
                if q_data:
                    answer_mode = q_data.get("answer_mode", "text").upper() or "TEXT"
                    time_limit_sec = q_data.get("time_limit_sec", 240)

            if answer_mode == "TEXT":
                if q.question:
                    category_name = q.question.category.name if hasattr(q.question.category, "name") else str(q.question.category)
                    answer_mode = "CODE" if category_name in ["SQL", "DATA_STRUCTURES"] else "AUDIO"
                elif q.custom_text:
                    answer_mode = "AUDIO"

            answer_mode = answer_mode.upper() if answer_mode else "TEXT"
            prompt = q.custom_text or (q.question.text if q.question else "Please answer the following question.")

            return {
                "type": "technical",
                "question_id": str(q.id),
                "question_text": prompt,
                "answer_mode": answer_mode,
                "time_limit_sec": time_limit_sec,
                "difficulty": q.question.difficulty.value if q.question else None,
                "category": q.question.category.value if q.question else None,
                "question_number": answered_count_in_section + 1,
                "total_questions": len(questions),
            }


    @staticmethod
    async def get_answered_count(
        session: AsyncSession, session_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> int:
        async with UnitOfWork(session) as uow:
            session_obj, _ = await InterviewSessionSQLService._get_session_and_interview(
                uow, session_id, candidate_id
            )
            # Answered count is total responses across the session
            responses_stmt = select(func.count(InterviewResponse.id)).where(
                InterviewResponse.session_id == session_obj.id
            )
            result = await session.execute(responses_stmt)
            return result.scalar() or 0

    @staticmethod
    async def mark_coding_question_answered(
        session: AsyncSession,
        session_id: uuid.UUID,
        session_question_id: uuid.UUID,
        passed_count: int,
        total_count: int,
    ) -> Dict[str, Any]:
        async with UnitOfWork(session) as uow:
            from app.db.sql.models.interview_session_section import InterviewSessionSection
            
            session_obj = await uow.session.get(InterviewSession, session_id)
            if not session_obj:
                raise HTTPException(status_code=404, detail="Session not found")
            
            interview = await uow.interviews.get_by_id(session_obj.interview_id, with_for_update=True)
                
            sq = await uow.session.get(InterviewSessionQuestion, session_question_id)
            if not sq or sq.interview_session_id != session_id:
                raise HTTPException(status_code=404, detail="Session question not found")
                
            score = (passed_count / total_count * 10.0) if total_count > 0 else 0.0
            
            response = InterviewResponse(
                session_id=session_id,
                question_id=session_question_id,
                answer_mode="CODE",
                ai_score=score,
                ai_feedback=f"Passed {passed_count}/{total_count} test cases",
                evaluation_json={
                    "passed_count": passed_count,
                    "total_count": total_count,
                    "type": "coding"
                }
            )
            session.add(response)
            session_obj.answered_count += 1
            
            # Check if section is complete
            stmt = select(InterviewSessionQuestion.id).where(
                InterviewSessionQuestion.interview_session_id == session_id,
                InterviewSessionQuestion.section_id == sq.section_id
            )
            result = await session.execute(stmt)
            all_q_ids = set(result.scalars().all())
            
            resp_stmt = select(InterviewResponse.question_id).where(
                InterviewResponse.session_id == session_id
            )
            resp_result = await session.execute(resp_stmt)
            answered_q_ids = set(resp_result.scalars().all())
            answered_q_ids.add(session_question_id)
            
            unanswered_count = len(all_q_ids - answered_q_ids)
            is_section_complete = unanswered_count == 0
            
            return_state = "IN_PROGRESS"
            
            if is_section_complete:
                return_state = "SECTION_COMPLETED"
                now = datetime.now(timezone.utc)
                current_section = await uow.session.get(InterviewSessionSection, sq.section_id)
                if current_section:
                    current_section.status = "completed"
                    current_section.completed_at = now
                    
                session_obj.current_section_id = None
                
                # Check if ALL sections are complete
                sections_stmt = select(InterviewSessionSection).where(
                    InterviewSessionSection.interview_session_id == session_id
                )
                sections_res = await session.execute(sections_stmt)
                all_sections = sections_res.scalars().all()
                all_completed = all(s.status == "completed" for s in all_sections)
                
                if all_completed:
                    return_state = "COMPLETED"
                    
                    score_stmt = select(func.avg(InterviewResponse.ai_score)).where(
                        InterviewResponse.session_id == session_id
                    )
                    avg_score_result = await session.execute(score_stmt)
                    avg_score = avg_score_result.scalar() or 0.0
                    overall_score = (avg_score / 10.0) * 100.0
                    
                    session_obj.status = "completed"
                    session_obj.completed_at = now
                    if interview:
                        interview.status = InterviewStatus.COMPLETED
                        interview.completed_at = now
                        interview.overall_score = round(overall_score, 2)
            
            await uow.flush()
            return {"state": return_state}

    @staticmethod
    async def submit_answer(
        session: AsyncSession,
        session_id: uuid.UUID,
        candidate_id: uuid.UUID,
        answer_payload: dict,
    ) -> Dict[str, Any]:
        async with UnitOfWork(session) as uow:
            from app.db.sql.models.interview_session_section import InterviewSessionSection
            
            session_obj, interview = await InterviewSessionSQLService._get_session_and_interview(
                uow, session_id, candidate_id, with_for_update=True
            )

            if not session_obj.current_section_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active section."
                )

            stmt = (
                select(InterviewSessionQuestion)
                .options(
                    selectinload(InterviewSessionQuestion.question),
                    selectinload(InterviewSessionQuestion.coding_problem),
                )
                .where(
                    InterviewSessionQuestion.interview_session_id == session_obj.id,
                    InterviewSessionQuestion.section_id == session_obj.current_section_id
                )
                .order_by(InterviewSessionQuestion.order)
            )
            result = await session.execute(stmt)
            questions = result.scalars().all()

            responses_stmt = select(InterviewResponse.question_id).where(
                InterviewResponse.session_id == session_obj.id
            )
            responses_result = await session.execute(responses_stmt)
            answered_q_ids = set(responses_result.scalars().all())

            unanswered_questions = [q for q in questions if q.id not in answered_q_ids]

            if not unanswered_questions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="All questions in this section already answered"
                )

            current_question = unanswered_questions[0]
            q_type = getattr(current_question, "question_type", None) or "technical"

            if q_type == "coding":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Coding questions must be submitted via the dedicated /coding/submit endpoint"
                )
            # ── CONVERSATIONAL ──
            elif q_type == "conversational":
                candidate = await uow.users.get_by_id(candidate_id)
                resume_data = None
                jd_data = None
                if candidate and candidate.candidate_profile:
                    profile = candidate.candidate_profile
                    resume_data = profile.resume_json or {"text": profile.resume_text or "", "projects": [], "skills": profile.skills or []}
                    jd_data = profile.jd_json or {"text": profile.job_description or "", "requirements": [], "required_skills": []}

                answer_text = answer_payload.get("answer_payload", "") or ""
                answer_audio_url = (
                    answer_payload.get("answer_payload")
                    if answer_payload.get("answer_type") == "AUDIO" else None
                )
                answer_mode = answer_payload.get("answer_type", "AUDIO").lower()

                question_data = {
                    "prompt": current_question.custom_text or (current_question.question.text if current_question.question else ""),
                    "difficulty": current_question.question.difficulty.value.lower() if current_question.question else "medium",
                    "conversation_config": {"round": current_question.conversation_round},
                }

                evaluation = answer_evaluation_service.evaluate_answer(
                    question=question_data,
                    answer_text=answer_text,
                    answer_audio_url=answer_audio_url,
                    resume_data=resume_data,
                    jd_data=jd_data,
                )

                response = InterviewResponse(
                    session_id=session_id,
                    question_id=current_question.id,
                    answer_text=answer_text if not answer_audio_url else None,
                    answer_audio_url=answer_audio_url,
                    answer_mode=answer_mode,
                    ai_score=evaluation.get("score"),
                    ai_feedback=evaluation.get("feedback"),
                    evaluation_json=evaluation,
                )
                session.add(response)
                session_obj.answered_count += 1
            # ── TECHNICAL ──
            else:
                question_data = None
                curated_questions = interview.curated_questions
                if curated_questions and "questions" in curated_questions:
                    for q in curated_questions["questions"]:
                        if q.get("question_id") == str(current_question.id):
                            question_data = q
                            break
                if not question_data:
                    question_data = {
                        "prompt": current_question.custom_text or (current_question.question.text if current_question.question else ""),
                        "difficulty": current_question.question.difficulty.value.lower() if current_question.question else "medium",
                        "conversation_config": {},
                    }

                candidate = await uow.users.get_by_id(candidate_id)
                resume_data = None
                jd_data = None
                if candidate and candidate.candidate_profile:
                    profile = candidate.candidate_profile
                    resume_data = profile.resume_json or {"text": profile.resume_text or "", "projects": [], "skills": profile.skills or []}
                    jd_data = profile.jd_json or {"text": profile.job_description or "", "requirements": [], "required_skills": []}

                answer_text = answer_payload.get("answer_payload", "") if answer_payload.get("answer_type") in ["TEXT", "CODE"] else None
                answer_audio_url = answer_payload.get("answer_payload") if answer_payload.get("answer_type") == "AUDIO" else None
                answer_mode = answer_payload.get("answer_type", "TEXT").lower()

                evaluation = answer_evaluation_service.evaluate_answer(
                    question=question_data,
                    answer_text=answer_text,
                    answer_audio_url=answer_audio_url,
                    resume_data=resume_data,
                    jd_data=jd_data,
                )

                response = InterviewResponse(
                    session_id=session_id,
                    question_id=current_question.id,
                    answer_text=answer_text,
                    answer_audio_url=answer_audio_url,
                    answer_mode=answer_mode,
                    ai_score=evaluation.get("score"),
                    ai_feedback=evaluation.get("feedback"),
                    evaluation_json=evaluation,
                )
                session.add(response)
                session_obj.answered_count += 1
            
            # Check if this section is now complete
            new_unanswered_count = len(unanswered_questions) - 1
            is_section_complete = new_unanswered_count == 0

            return_state = "IN_PROGRESS"

            if is_section_complete:
                return_state = "SECTION_COMPLETED"
                now = datetime.now(timezone.utc)
                current_section = await uow.session.get(InterviewSessionSection, session_obj.current_section_id)
                if current_section:
                    current_section.status = "completed"
                    current_section.completed_at = now
                
                session_obj.current_section_id = None

                # Check if ALL sections are complete
                sections_stmt = select(InterviewSessionSection).where(
                    InterviewSessionSection.interview_session_id == session_obj.id
                )
                sections_res = await session.execute(sections_stmt)
                all_sections = sections_res.scalars().all()
                all_completed = all(s.status == "completed" for s in all_sections)

                if all_completed:
                    return_state = "COMPLETED"
                    
                    # Calculate overall score and complete
                    score_stmt = select(func.avg(InterviewResponse.ai_score)).where(
                        InterviewResponse.session_id == session_id
                    )
                    avg_score_result = await session.execute(score_stmt)
                    avg_score = avg_score_result.scalar() or 0.0
                    overall_score = (avg_score / 10.0) * 100.0
                    
                    feedback_stmt = select(InterviewResponse).where(
                        InterviewResponse.session_id == session_id
                    ).order_by(InterviewResponse.submitted_at)
                    feedback_result = await session.execute(feedback_stmt)
                    all_responses = feedback_result.scalars().all()
                    
                    strengths = []
                    weaknesses = []
                    for resp in all_responses:
                        if resp.evaluation_json:
                            strengths.extend(resp.evaluation_json.get('strengths', []))
                            weaknesses.extend(resp.evaluation_json.get('weaknesses', []))
                    
                    session_obj.status = "completed"
                    session_obj.completed_at = now
                    interview.status = InterviewStatus.COMPLETED
                    interview.completed_at = now
                    interview.overall_score = round(overall_score, 2)
                    
                    strengths_list = list(set(strengths))[:3] if strengths else []
                    weaknesses_list = list(set(weaknesses))[:3] if weaknesses else []
                    
                    interview.feedback = (
                        f"Overall Score: {overall_score:.1f}/100. "
                        f"Key Strengths: {', '.join(strengths_list) if strengths_list else 'N/A'}. "
                        f"Areas for Improvement: {', '.join(weaknesses_list) if weaknesses_list else 'N/A'}."
                    )

            await uow.flush()
            return {"state": return_state}

    @staticmethod
    async def complete_session(
        session: AsyncSession, session_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> Dict[str, Any]:
        async with UnitOfWork(session) as uow:
            session_obj, interview = await InterviewSessionSQLService._get_session_and_interview(
                uow, session_id, candidate_id, with_for_update=True
            )

            now = datetime.now(timezone.utc)
            session_obj.status = "completed"
            session_obj.completed_at = now
            interview.status = InterviewStatus.COMPLETED
            interview.completed_at = now

            return {"state": "COMPLETED"}

    @staticmethod
    async def get_summary(
        session: AsyncSession,
        session_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Return the mock evaluation summary for a completed interview session.
        Score is retrieved from interview.overall_score (written at completion).
        All other fields are regenerated deterministically from the interview ID seed.
        """
        async with UnitOfWork(session) as uow:
            # Allow completed sessions (status != "active") — no active filter here
            stmt = select(InterviewSession).where(InterviewSession.id == session_id)
            result = await uow.session.execute(stmt)
            session_obj = result.scalar_one_or_none()

            if not session_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
                )
            if session_obj.candidate_id != candidate_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Session does not belong to you",
                )

            interview = await uow.interviews.get_by_id(session_obj.interview_id)
            if not interview:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
                )

            if interview.overall_score is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Interview not yet completed",
                )

            # Use persisted score; regenerate other fields deterministically
            mock = _generate_mock_result(interview.id)
            return {
                "final_score": interview.overall_score,
                "recommendation": mock["recommendation"],
                "fraud_risk": mock["fraud_risk"],
                "strengths": mock["strengths"],
                "gaps": mock["gaps"],
                "notes": mock["notes"],
                "completed_at": session_obj.completed_at,
            }
