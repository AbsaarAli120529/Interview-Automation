"""
Question Generator Service
--------------------------
Generates interview questions: first 5-6 from question bank, then conversational questions
using Azure OpenAI GPT-4o based on parsed resume and JD.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.sql.models.question import Question, DifficultyEnum, CategoryEnum
from app.services.resume_jd_parser import resume_jd_parser
from app.services.azure_openai_service import azure_openai_service

logger = logging.getLogger(__name__)


class QuestionGeneratorService:
    """Service to generate interview questions from resume and JD."""
    
    # Directory where resumes are stored
    RESUME_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "resumes")
    
    @staticmethod
    async def generate_curated_questions(
        session: AsyncSession,
        template_id: str,
        candidate_id: str,
        resume_id: Optional[str] = None,
        resume_text: Optional[str] = None,
        job_description: Optional[str] = None,
        resume_json: Optional[Dict[str, Any]] = None,
        jd_json: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        Generate curated questions: first 5-6 from question bank, then conversational questions.
        
        Args:
            session: Database session
            template_id: UUID string of the interview template
            candidate_id: UUID string of the candidate
            resume_id: Resume identifier (used as fallback to find resume file)
            resume_text: Parsed resume text from database (preferred)
            job_description: Job description text
            resume_json: Pre-parsed structured resume data
            jd_json: Pre-parsed structured job description data
            
        Returns:
            dict conforming to CuratedQuestionsPayload schema
        """
        try:
            all_questions = []
            
            # Step 1: Prepare resume and JD data
            if resume_json:
                resume_data = resume_json
                if resume_text and 'text' not in resume_data:
                    resume_data['text'] = resume_text
            elif resume_text:
                resume_data = {
                    'text': resume_text,
                    'projects': [],
                    'skills': [],
                    'experience': {},
                    'education': {}
                }
            else:
                resume_data = QuestionGeneratorService._parse_resume(resume_id)
            
            # Parse job description
            if jd_json:
                jd_data = jd_json
            else:
                jd_data = resume_jd_parser.parse_job_description(job_description or "")
            
            # Extract role and skills for filtering question bank
            role_name = jd_data.get('job_title') or jd_data.get('role_name', '')
            required_skills = jd_data.get('required_skills', []) or jd_data.get('technologies', [])
            
            # Step 2: Get first 5-6 questions from question bank (role/tech specific) - TEMPLATE QUESTIONS
            question_bank_questions = await QuestionGeneratorService._get_questions_from_bank(
                session, 
                num_questions=6,  # Get 5-6 template questions first
                role_name=role_name,
                required_skills=required_skills
            )
            # Ensure proper ordering for template questions
            for idx, q in enumerate(question_bank_questions, 1):
                q['order'] = idx
            all_questions.extend(question_bank_questions)
            
            # Step 3: Generate 10 conversational questions with drill-down - AFTER TEMPLATE QUESTIONS
            # For each project, generate 5-6 hard questions
            conversational_questions = await QuestionGeneratorService._generate_conversational_with_drilldown(
                resume_data=resume_data,
                jd_data=jd_data,
                total_questions=10
            )
            
            # Adjust order numbers for conversational questions (start after template questions)
            start_order = len(all_questions) + 1
            for q in conversational_questions:
                q['order'] = start_order
                start_order += 1
            
            all_questions.extend(conversational_questions)
            
            # Final sort by order to ensure correct sequence
            all_questions.sort(key=lambda x: x.get('order', 999))
            
            return {
                "template_id": template_id,
                "generated_from": {
                    "resume_id": resume_id or candidate_id,
                    "jd_id": "jd_from_registration",
                },
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "generation_method": "question_bank_and_azure_openai_gpt4o",
                "questions": all_questions
            }
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            # Fallback to mock questions
            return await QuestionGeneratorService._generate_fallback_questions(session, template_id, candidate_id, resume_id)
    
    @staticmethod
    async def _get_questions_from_bank(
        session: AsyncSession, 
        num_questions: int = 5,
        role_name: Optional[str] = None,
        required_skills: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get questions from the question bank, filtered by role and technologies."""
        try:
            import random
            
            # Build query with filters
            stmt = select(Question).where(Question.is_active == True)
            
            # Filter by category if we have required skills
            if required_skills:
                # Map skills to categories
                skill_to_category = {
                    'python': CategoryEnum.PYTHON,
                    'sql': CategoryEnum.SQL,
                    'machine learning': CategoryEnum.MACHINE_LEARNING,
                    'ml': CategoryEnum.MACHINE_LEARNING,
                    'data structures': CategoryEnum.DATA_STRUCTURES,
                    'system design': CategoryEnum.SYSTEM_DESIGN,
                    'statistics': CategoryEnum.STATISTICS,
                }
                matching_categories = []
                for skill in required_skills:
                    skill_lower = skill.lower()
                    for key, cat in skill_to_category.items():
                        if key in skill_lower:
                            matching_categories.append(cat)
                            break
                
                if matching_categories:
                    stmt = stmt.where(Question.category.in_(matching_categories))
            
            result = await session.execute(stmt)
            all_questions = result.scalars().all()
            
            # Randomly select questions
            selected_questions = random.sample(all_questions, min(num_questions, len(all_questions))) if len(all_questions) > num_questions else all_questions
            
            formatted_questions = []
            for i, q in enumerate(selected_questions, 1):
                # Randomly assign answer mode (voice or written) - 50/50 chance
                import random as rnd
                answer_mode_random = rnd.choice(["AUDIO", "TEXT"])
                
                # Override for coding questions - they should be written
                if q.category in [CategoryEnum.SQL, CategoryEnum.DATA_STRUCTURES]:
                    answer_mode = "CODE"
                else:
                    answer_mode = answer_mode_random
                
                # Time limits based on difficulty: easy 2min, medium 4min, hard 6min
                time_limits = {
                    DifficultyEnum.EASY: 120,  # 2 minutes
                    DifficultyEnum.MEDIUM: 240,  # 4 minutes
                    DifficultyEnum.HARD: 360  # 6 minutes
                }
                time_limit_sec = time_limits.get(q.difficulty, 240)
                
                formatted_questions.append({
                    "question_id": str(q.id),
                    "question_type": "static",
                    "order": i,
                    "prompt": q.text,
                    "difficulty": q.difficulty.value.lower(),
                    "time_limit_sec": time_limit_sec,
                    "answer_mode": answer_mode.lower(),
                    "evaluation_mode": "text" if answer_mode == "TEXT" else ("code" if answer_mode == "CODE" else "audio"),
                    "source": "question_bank",
                    "category": q.category.value
                })
            
            return formatted_questions
        except Exception as e:
            logger.error(f"Error getting questions from bank: {e}")
            return []
    
    @staticmethod
    async def _generate_conversational_with_drilldown(
        resume_data: Dict[str, Any],
        jd_data: Dict[str, Any],
        total_questions: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate conversational questions with drill-down follow-ups for each project."""
        import random
        
        projects = resume_data.get('projects', [])
        if not projects:
            projects = [{'name': 'General Experience', 'description': resume_data.get('text', '')[:500]}]
        
        all_questions = []
        questions_per_project = max(1, total_questions // len(projects))
        
        for project_idx, project in enumerate(projects[:3]):  # Focus on top 3 projects
            # Generate questions for this project
            project_questions = azure_openai_service.generate_project_drilldown_questions(
                project=project,
                resume_data=resume_data,
                jd_data=jd_data,
                num_questions=min(questions_per_project, 6)  # Max 6 per project
            )
            
            # Randomly assign answer mode (voice or written) for each question
            for q in project_questions:
                q['answer_mode'] = random.choice(['audio', 'text']).lower()
                # Time limits: easy 2min, medium 4min, hard 6min
                difficulty = q.get('difficulty', 'medium').lower()
                time_limits = {
                    'easy': 120,
                    'medium': 240,
                    'hard': 360
                }
                q['time_limit_sec'] = time_limits.get(difficulty, 240)
                q['evaluation_mode'] = 'contextual'
            
            all_questions.extend(project_questions)
            
            # Stop if we have enough questions
            if len(all_questions) >= total_questions:
                break
        
        # Ensure we have exactly total_questions
        return all_questions[:total_questions]
    
    @staticmethod
    def _parse_resume(resume_id: Optional[str]) -> Dict[str, Any]:
        """Parse resume file if available."""
        if not resume_id:
            return {
                'text': '',
                'projects': [],
                'skills': [],
                'experience': {},
                'education': {}
            }
        
        try:
            # Try to find resume file
            resume_path = os.path.join(QuestionGeneratorService.RESUME_UPLOAD_DIR, f"{resume_id}.pdf")
            
            if os.path.exists(resume_path):
                return resume_jd_parser.parse_resume_pdf(resume_path)
            else:
                logger.warning(f"Resume file not found: {resume_path}")
                return {
                    'text': '',
                    'projects': [],
                    'skills': [],
                    'experience': {},
                    'education': {}
                }
        except Exception as e:
            logger.error(f"Error parsing resume: {e}")
            return {
                'text': '',
                'projects': [],
                'skills': [],
                'experience': {},
                'education': {}
            }
    
    @staticmethod
    async def _generate_fallback_questions(
        session: AsyncSession,
        template_id: str,
        candidate_id: str,
        resume_id: Optional[str]
    ) -> dict:
        """Generate fallback mock questions if generation fails."""
        return {
            "template_id": template_id,
            "generated_from": {
                "resume_id": resume_id or candidate_id,
                "jd_id": "fallback",
            },
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "generation_method": "fallback_mock",
            "questions": [
                {
                    "question_id": "conv_q_001",
                    "question_type": "conversational",
                    "order": 1,
                    "prompt": "Tell me about a challenging project you worked on. What technologies did you use?",
                    "difficulty": "medium",
                    "time_limit_sec": 300,
                    "conversation_config": {
                        "follow_up_depth": 2,
                        "ai_model": "gpt-4o",
                        "evaluation_mode": "contextual"
                    }
                },
                {
                    "question_id": "conv_q_002",
                    "question_type": "conversational",
                    "order": 2,
                    "prompt": "Walk me through your approach to solving a complex technical problem.",
                    "difficulty": "medium",
                    "time_limit_sec": 300,
                    "conversation_config": {
                        "follow_up_depth": 2,
                        "ai_model": "gpt-4o",
                        "evaluation_mode": "contextual"
                    }
                },
                {
                    "question_id": "conv_q_003",
                    "question_type": "conversational",
                    "order": 3,
                    "prompt": "Deep dive into the architecture of your most complex project. What were the main challenges?",
                    "difficulty": "hard",
                    "time_limit_sec": 600,
                    "conversation_config": {
                        "follow_up_depth": 3,
                        "ai_model": "gpt-4o",
                        "evaluation_mode": "contextual"
                    }
                },
                {
                    "question_id": "conv_q_004",
                    "question_type": "conversational",
                    "order": 4,
                    "prompt": "Explain how you would optimize a system for scalability and performance.",
                    "difficulty": "hard",
                    "time_limit_sec": 600,
                    "conversation_config": {
                        "follow_up_depth": 3,
                        "ai_model": "gpt-4o",
                        "evaluation_mode": "contextual"
                    }
                },
                {
                    "question_id": "conv_q_005",
                    "question_type": "conversational",
                    "order": 5,
                    "prompt": "If you had to redesign a system you built, what would you do differently and why?",
                    "difficulty": "hard",
                    "time_limit_sec": 600,
                    "conversation_config": {
                        "follow_up_depth": 3,
                        "ai_model": "gpt-4o",
                        "evaluation_mode": "contextual"
                    }
                }
            ]
        }


question_generator_service = QuestionGeneratorService()
