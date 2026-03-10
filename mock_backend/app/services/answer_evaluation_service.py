"""
Answer Evaluation Service
--------------------------
Evaluates candidate answers using Azure OpenAI LLM and assigns scores (0-10).
"""

import os
import logging
from typing import Dict, Any, Optional
from app.services.azure_openai_service import azure_openai_service

logger = logging.getLogger(__name__)

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"


class AnswerEvaluationService:
    """Service to evaluate candidate answers and assign scores."""
    
    @staticmethod
    def evaluate_answer(
        question: Dict[str, Any],
        answer_text: Optional[str] = None,
        answer_audio_url: Optional[str] = None,
        resume_data: Optional[Dict[str, Any]] = None,
        jd_data: Optional[Dict[str, Any]] = None,
        previous_answers: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a candidate's answer and assign a score (0-10).
        
        Args:
            question: Question dictionary with prompt, difficulty, etc.
            answer_text: Text answer (if written)
            answer_audio_url: URL to audio answer (if voice)
            resume_data: Candidate's resume data for context
            jd_data: Job description data for context
            previous_answers: List of previous answers for context
            
        Returns:
            Dictionary with score, feedback, and evaluation details
        """
        if DEV_MODE:
            logger.info("DEV_MODE is enabled. Returning mock evaluation.")
            return {
                "score": 7,
                "feedback": "Dev mode evaluation placeholder.",
                "strengths": ["Clear explanation"],
                "weaknesses": ["Needs deeper detail"],
                "suggestions": ["Expand on architecture decisions"],
            }

        if not azure_openai_service.client:
            logger.warning("Azure OpenAI not configured, returning mock evaluation")
            return AnswerEvaluationService._generate_mock_evaluation(question)
        
        try:
            # Prepare answer content
            answer_content = answer_text or f"[Audio answer available at: {answer_audio_url}]"
            
            # Build evaluation prompt
            system_prompt = """You are an expert technical interviewer evaluating a candidate's answer.
Evaluate the answer on a scale of 0-10 based on:
- Technical correctness and accuracy
- Depth of understanding
- Clarity and communication
- Relevance to the question
- Problem-solving approach
- Use of appropriate examples and explanations

Return ONLY valid JSON with this structure:
{
    "score": <number between 0 and 10>,
    "feedback": "Detailed feedback on the answer",
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "suggestions": "Suggestions for improvement"
}"""

            question_prompt = question.get('prompt', '')
            difficulty = question.get('difficulty', 'medium')
            focus_area = question.get('conversation_config', {}).get('focus_area', '')
            
            user_prompt = f"""Evaluate this candidate's answer:

QUESTION: {question_prompt}
DIFFICULTY: {difficulty}
FOCUS AREA: {focus_area}

CANDIDATE'S ANSWER:
{answer_content[:2000]}

JOB REQUIREMENTS:
{chr(10).join(jd_data.get('requirements', [])[:5]) if jd_data and jd_data.get('requirements') else 'Not specified'}

REQUIRED SKILLS:
{', '.join(jd_data.get('required_skills', [])[:10]) if jd_data and jd_data.get('required_skills') else 'Not specified'}

Evaluate the answer and provide:
1. A score from 0-10 (0 = completely incorrect, 10 = excellent)
2. Detailed feedback
3. Strengths and weaknesses
4. Suggestions for improvement

Return ONLY the JSON object, no additional text."""

            response = azure_openai_service.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for consistent evaluation
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            import json
            evaluation = json.loads(response.choices[0].message.content)
            
            # Ensure score is between 0-10
            score = max(0, min(10, float(evaluation.get('score', 5))))
            
            return {
                "score": round(score, 2),
                "feedback": evaluation.get('feedback', ''),
                "strengths": evaluation.get('strengths', []),
                "weaknesses": evaluation.get('weaknesses', []),
                "suggestions": evaluation.get('suggestions', ''),
                "evaluated_at": None,  # Will be set by caller
                "evaluation_method": "azure_openai_gpt4o"
            }
            
        except Exception as e:
            logger.error(f"Error evaluating answer: {e}")
            return AnswerEvaluationService._generate_mock_evaluation(question)
    
    @staticmethod
    def _generate_mock_evaluation(question: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock evaluation when LLM is not available."""
        return {
            "score": 7.0,
            "feedback": "Answer demonstrates good understanding of the topic.",
            "strengths": ["Clear explanation", "Relevant examples"],
            "weaknesses": ["Could go deeper into technical details"],
            "suggestions": "Consider providing more specific technical examples.",
            "evaluated_at": None,
            "evaluation_method": "mock"
        }


answer_evaluation_service = AnswerEvaluationService()
