import uuid
import random
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.sql.models.interview_template import InterviewTemplate
from app.db.sql.models.question import Question, DifficultyEnum, CategoryEnum
from app.db.sql.models.coding_problem import CodingProblem

logger = logging.getLogger(__name__)


# ─── Result types ─────────────────────────────────────────────────────────────

@dataclass
class TechnicalQuestionItem:
    question_type: str = "technical"
    question_id: Optional[uuid.UUID] = None
    question: Optional[Question] = None


@dataclass
class CodingProblemItem:
    question_type: str = "coding"
    coding_problem_id: Optional[uuid.UUID] = None
    coding_problem: Optional[CodingProblem] = None


@dataclass
class ConversationalRoundItem:
    question_type: str = "conversational"
    conversation_round: int = 1


# Union type for all generated items (using Union for Python 3.9 compatibility)
GeneratedItem = Union[TechnicalQuestionItem, CodingProblemItem, ConversationalRoundItem]


# ─── Engine ───────────────────────────────────────────────────────────────────

class TemplateEngineService:

    # ── Public orchestration ──────────────────────────────────────────────────

    @staticmethod
    async def generate_interview_questions(
        template: InterviewTemplate,
        session: AsyncSession
    ) -> List[GeneratedItem]:
        """
        Orchestrates generation of all three interview sections in order:
        1. Technical questions
        2. Coding problems
        3. Conversational rounds
        """
        results: List[GeneratedItem] = []

        technical = await TemplateEngineService._generate_technical_questions(template, session)
        results.extend(technical)

        coding = await TemplateEngineService._generate_coding_questions(template, session)
        results.extend(coding)

        conversational = TemplateEngineService._generate_conversational_rounds(template)
        results.extend(conversational)

        return results

    # ── Backward-compatible shim for legacy callers ───────────────────────────

    @staticmethod
    async def generate_questions_from_template(
        template_id: uuid.UUID,
        session: AsyncSession
    ) -> List[Question]:
        """Legacy shim — returns only technical Question objects for old callers."""
        result = await session.execute(
            select(InterviewTemplate).where(InterviewTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            return []

        items = await TemplateEngineService._generate_technical_questions(template, session)
        return [item.question for item in items if item.question]

    # ── Section generators ────────────────────────────────────────────────────

    @staticmethod
    async def _generate_technical_questions(
        template: InterviewTemplate,
        session: AsyncSession
    ) -> List[TechnicalQuestionItem]:
        """
        Generate technical questions from technical_config (flat difficulty map).
        Falls back to settings.difficulty_distribution for legacy templates.
        """
        distribution: dict = {}
        if template.technical_config and isinstance(template.technical_config, dict):
            distribution = template.technical_config
        elif template.settings and isinstance(template.settings, dict):
            distribution = template.settings.get("difficulty_distribution", {})

        categories = []
        if template.settings and isinstance(template.settings, dict):
            categories = template.settings.get("category_filters", [])

        generated: List[TechnicalQuestionItem] = []

        for difficulty_str, count in distribution.items():
            if not isinstance(count, int) or count <= 0:
                continue
            try:
                difficulty = DifficultyEnum(difficulty_str.upper())
            except ValueError:
                continue

            from app.db.sql.models.question import QuestionType
            
            # Check if coding_problems table exists before joining
            # If table doesn't exist, just filter out coding questions
            try:
                # Try to create a simple query that checks if table exists
                # We'll use a simpler approach: just filter out coding questions
                query = select(Question).where(
                    Question.difficulty == difficulty,
                    Question.is_active == True,
                    Question.question_type != QuestionType.CODING
                )
            except Exception:
                # Fallback: if there's any issue, just filter by difficulty and active status
                query = select(Question).where(
                    Question.difficulty == difficulty,
                    Question.is_active == True
                )

            if generated:
                excluded_ids = [item.question_id for item in generated if item.question_id]
                if excluded_ids:
                    query = query.where(Question.id.not_in(excluded_ids))

            if categories:
                cat_enums = [CategoryEnum(c) for c in categories if c in CategoryEnum.__members__]
                if cat_enums:
                    query = query.where(Question.category.in_(cat_enums))

            query = query.order_by(func.random()).limit(count)
            
            # Execute query with error handling for missing tables
            try:
                res = await session.execute(query)
                batch = res.scalars().all()
            except Exception as e:
                # If query fails due to missing table (e.g., coding_problems), 
                # try a simpler query without the join
                logger.warning(f"Query failed (possibly due to missing table): {e}. Trying simpler query.")
                simple_query = select(Question).where(
                    Question.difficulty == difficulty,
                    Question.is_active == True
                )
                if generated:
                    excluded_ids = [item.question_id for item in generated if item.question_id]
                    if excluded_ids:
                        simple_query = simple_query.where(Question.id.not_in(excluded_ids))
                if categories:
                    cat_enums = [CategoryEnum(c) for c in categories if c in CategoryEnum.__members__]
                    if cat_enums:
                        simple_query = simple_query.where(Question.category.in_(cat_enums))
                simple_query = simple_query.order_by(func.random()).limit(count)
                res = await session.execute(simple_query)
                batch = res.scalars().all()

            if len(batch) < count:
                logger.warning(
                    f"[technical] Requested {count} {difficulty_str} questions, found {len(batch)}."
                )

            for q in batch:
                generated.append(TechnicalQuestionItem(question_id=q.id, question=q))

        return generated

    @staticmethod
    async def _generate_coding_questions(
        template: InterviewTemplate,
        session: AsyncSession
    ) -> List[CodingProblemItem]:
        """
        Generate coding problems from coding_config:
        { "count": 2, "difficulty": ["medium", "hard"] }
        """
        config = template.coding_config or {}
        if not isinstance(config, dict):
            return []

        count = config.get("count", 0)
        difficulties = config.get("difficulty", [])

        if not isinstance(count, int) or count <= 0:
            return []
        if not isinstance(difficulties, list) or not difficulties:
            return []

        valid_diffs = [d.upper() for d in difficulties if isinstance(d, str)]
        if not valid_diffs:
            return []

        # Check if coding_problems table exists before querying
        try:
            query = select(CodingProblem).where(
                func.upper(CodingProblem.difficulty).in_(valid_diffs)
            ).order_by(func.random()).limit(count)

            res = await session.execute(query)
            problems = res.scalars().all()
        except Exception as e:
            # If coding_problems table doesn't exist, return empty list
            logger.warning(f"Coding problems table not available: {e}. Returning empty list.")
            problems = []

        if len(problems) < count:
            logger.warning(
                f"[coding] Requested {count} problems (diffs={valid_diffs}), found {len(problems)}."
            )

        return [
            CodingProblemItem(coding_problem_id=p.id, coding_problem=p)
            for p in problems
        ]

    @staticmethod
    def _generate_conversational_rounds(
        template: InterviewTemplate
    ) -> List[ConversationalRoundItem]:
        """
        Generate placeholder conversational round entries from conversational_config:
        { "rounds": 3 }
        """
        config = template.conversational_config or {}
        if not isinstance(config, dict):
            return []

        rounds = config.get("rounds", 0)
        if not isinstance(rounds, int) or rounds <= 0:
            return []

        return [ConversationalRoundItem(conversation_round=i) for i in range(1, rounds + 1)]


template_engine = TemplateEngineService()
