import logging
from sqlalchemy import select, literal
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sql.models.interview_template import InterviewTemplate, TemplateQuestion
from app.db.sql.models.question import Question, CategoryEnum, DifficultyEnum

logger = logging.getLogger(__name__)

async def seed_templates(session: AsyncSession):
    """Seed default interview templates if none exist."""
    logger.info("Checking for existing interview templates...")
    
    stmt = (
        select(literal(1))
        .select_from(InterviewTemplate)
        .where(InterviewTemplate.is_active == True)
        .limit(1)
    )
    result = await session.execute(stmt)
    already_exists = result.scalar() is not None

    if already_exists:
        logger.info("[template_seed] Active template already exists. Checking for Default Rule Template...")
    
    # 1. Ensure a rule-based template exists
    rule_stmt = select(InterviewTemplate).where(InterviewTemplate.title == "Default Rule Template")
    rule_res = await session.execute(rule_stmt)
    if not rule_res.scalar_one_or_none():
        logger.info("[template_seed] Creating 'Default Rule Template'...")
        rule_template = InterviewTemplate(
            title="Default Rule Template",
            description="Automatic question selection based on complexity",
            is_active=True,
            is_rule_based=True,
            settings={
                "difficulty_distribution": {
                    "EASY": 2,
                    "MEDIUM": 2,
                    "HARD": 1
                }
            }
        )
        session.add(rule_template)
        await session.flush()

    if already_exists:
        return

    logger.info("[template_seed] No active templates found. Creating default template...")
    template = InterviewTemplate(
        title="Default Data Science Interview",
        description="Baseline template with coding + conversational questions",
        is_active=True,
        settings={"total_duration_sec": 3600},
    )
    session.add(template)
    await session.flush() # Get template ID

    # Create Question objects first
    question_data = [
        {
            "text": "Explain a machine learning project you worked on.",
            "category": CategoryEnum.MACHINE_LEARNING,
            "difficulty": DifficultyEnum.MEDIUM,
            "question_type": "CONVERSATIONAL",
            "time_limit_sec": 120,
            "order": 1,
        },
        {
            "text": "Write a SQL query to find the second highest salary.",
            "category": CategoryEnum.SQL,
            "difficulty": DifficultyEnum.MEDIUM,
            "question_type": "CODING",
            "time_limit_sec": 300,
            "order": 2,
        },
        {
            "text": "How do you handle model overfitting?",
            "category": CategoryEnum.MACHINE_LEARNING,
            "difficulty": DifficultyEnum.MEDIUM,
            "question_type": "CONVERSATIONAL",
            "time_limit_sec": 120,
            "order": 3,
        },
    ]
    
    questions = []
    template_questions = []
    
    for q_data in question_data:
        # Create Question object
        question = Question(
            text=q_data["text"],
            category=q_data["category"],
            difficulty=q_data["difficulty"],
            is_active=True,
        )
        session.add(question)
        questions.append(question)
    
    await session.flush()  # Flush to get question IDs
    
    # Create TemplateQuestion objects that reference the Question objects
    for i, q_data in enumerate(question_data):
        template_question = TemplateQuestion(
            template_id=template.id,
            question_id=questions[i].id,
            question_type=q_data["question_type"],
            time_limit_sec=q_data["time_limit_sec"],
            order=q_data["order"],
        )
        template_questions.append(template_question)
    
    session.add_all(template_questions)
    logger.info("[OK] Default template created successfully.")
