"""
Azure OpenAI Service
--------------------
Service to interact with Azure OpenAI GPT-4o for question generation.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from openai import AzureOpenAI
from app.core.config import settings

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env file from project root (mock_backend directory)
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logging.getLogger(__name__).debug(f"Loaded .env file from: {env_path}")
    else:
        # Try parent directory (project root)
        env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logging.getLogger(__name__).debug(f"Loaded .env file from: {env_path}")
except ImportError:
    # python-dotenv not installed, will rely on environment variables or pydantic-settings
    pass

logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """Service to interact with Azure OpenAI."""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client."""
        try:
            # Try multiple environment variable names for compatibility
            azure_endpoint = (
                os.getenv("AZURE_OPENAI_ENDPOINT") or 
                os.getenv("OPENAI_API_BASE") or
                getattr(settings, "OPENAI_API_BASE", None) or
                ""
            )
            api_key = (
                os.getenv("AZURE_OPENAI_API_KEY") or 
                os.getenv("OPENAI_API_KEY") or
                getattr(settings, "OPENAI_API_KEY", None) or
                ""
            )
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            
            # Debug logging
            logger.debug(f"Azure OpenAI Endpoint: {'***SET***' if azure_endpoint else 'NOT SET'}")
            logger.debug(f"Azure OpenAI API Key: {'***SET***' if api_key else 'NOT SET'}")
            
            if not azure_endpoint or not api_key:
                logger.warning("Azure OpenAI credentials not configured. Question generation will use mock data.")
                logger.warning(f"  - AZURE_OPENAI_ENDPOINT or OPENAI_API_BASE: {'SET' if azure_endpoint else 'NOT SET'}")
                logger.warning(f"  - AZURE_OPENAI_API_KEY or OPENAI_API_KEY: {'SET' if api_key else 'NOT SET'}")
                logger.warning(f"  - Check your .env file in: {Path(__file__).resolve().parent.parent.parent}")
                return None
            
            # Clean endpoint (remove trailing slash if present)
            azure_endpoint = azure_endpoint.rstrip('/')
            
            self.client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                api_version=api_version
            )
            logger.info("✅ Azure OpenAI client initialized successfully")
            logger.info(f"   Endpoint: {azure_endpoint}")
            logger.info(f"   API Version: {api_version}")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}", exc_info=True)
            self.client = None
    
    def generate_conversational_questions(
        self,
        resume_data: Dict[str, Any],
        jd_data: Dict[str, Any],
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate conversational questions based on resume and JD.
        
        Args:
            resume_data: Parsed resume data
            jd_data: Parsed job description data
            num_questions: Number of questions to generate (default: 5)
            
        Returns:
            List of question dictionaries with difficulty progression
        """
        if not self.client:
            logger.warning("Azure OpenAI not configured, returning mock questions")
            return self._generate_mock_questions(resume_data, jd_data, num_questions)
        
        try:
            # Extract projects from resume
            projects = resume_data.get('projects', [])
            if not projects:
                # Fallback to skills if no projects found
                projects = [{'name': 'General Experience', 'description': resume_data.get('text', '')[:500]}]
            
            # Build prompt for question generation
            prompt = self._build_question_generation_prompt(
                projects=projects,
                resume_skills=resume_data.get('skills', []),
                jd_requirements=jd_data.get('requirements', []),
                jd_skills=jd_data.get('required_skills', []) 
            )
            
            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o",  # or your deployment name
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical interviewer. Generate conversational interview questions based on the candidate's resume and job requirements. Focus on projects and technologies mentioned."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse response
            questions = self._parse_question_response(response.choices[0].message.content)
            
            # Ensure we have the right number and difficulty progression: 1-2 medium, then hard
            return self._format_questions_with_difficulty(questions, num_questions, projects, medium_first=2)
            
        except Exception as e:
            logger.error(f"Error generating questions with Azure OpenAI: {e}")
            return self._generate_mock_questions(resume_data, jd_data, num_questions)
    
    def _build_question_generation_prompt(
        self,
        projects: List[Dict[str, Any]],
        resume_skills: List[str],
        jd_requirements: List[str],
        jd_skills: List[str]
    ) -> str:
        """Build the prompt for question generation."""
        projects_text = "\n".join([
            f"Project: {p.get('name', 'Unknown')}\nDescription: {p.get('description', '')[:300]}\nTechnologies: {', '.join(p.get('technologies', []))}"
            for p in projects[:3]  # Focus on top 3 projects
        ])
        
        prompt = f"""Generate 5 conversational interview questions based on the following information:

CANDIDATE PROJECTS:
{projects_text}

CANDIDATE SKILLS:
{', '.join(resume_skills[:20])}

JOB REQUIREMENTS:
{chr(10).join(jd_requirements[:5]) if jd_requirements else 'Not specified'}

REQUIRED SKILLS:
{', '.join(jd_skills[:20])}

INSTRUCTIONS:
1. First 2 questions should be MEDIUM difficulty - ask about project overview, technologies used, and basic implementation details
2. Next 3 questions should be HARD difficulty - test deep understanding of:
   - Architecture decisions and trade-offs
   - Performance optimization
   - Problem-solving approaches
   - Edge cases and challenges faced
   - Advanced concepts related to technologies used

Format your response as JSON array with this structure:
[
  {{
    "question": "Question text here",
    "difficulty": "medium" or "hard",
    "focus_area": "Brief description of what this tests",
    "follow_up_depth": 3
  }}
]

Return ONLY the JSON array, no additional text."""
        
        return prompt
    
    def _parse_question_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse the response from Azure OpenAI."""
        import json
        import re
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group())
                return questions
            else:
                # Fallback: try to parse entire response
                questions = json.loads(response_text)
                return questions
        except Exception as e:
            logger.error(f"Error parsing question response: {e}")
            return []
    
    def _format_questions_with_difficulty(
        self,
        questions: List[Dict[str, Any]],
        num_questions: int,
        projects: List[Dict[str, Any]],
        medium_first: int = 2
    ) -> List[Dict[str, Any]]:
        """Format questions with proper difficulty progression: 1-2 medium, then hard."""
        formatted = []
        
        # Ensure we have medium questions first (1-2), then hard
        medium_questions = [q for q in questions if q.get('difficulty', '').lower() == 'medium'][:medium_first]
        hard_questions = [q for q in questions if q.get('difficulty', '').lower() == 'hard'][:(num_questions - len(medium_questions))]
        
        # If we don't have enough, generate some
        while len(medium_questions) < medium_first:
            medium_questions.append({
                'question': f"Tell me about one of your projects involving {projects[0].get('name', 'your work') if projects else 'your experience'}. What technologies did you use and why?",
                'difficulty': 'medium',
                'focus_area': 'Project overview and technology selection',
                'follow_up_depth': 2
            })
        
        while len(hard_questions) < 3:
            hard_questions.append({
                'question': f"Deep dive into the architecture of {projects[0].get('name', 'your project') if projects else 'your most complex project'}. What were the main challenges and how did you solve them?",
                'difficulty': 'hard',
                'focus_area': 'Deep technical understanding and problem-solving',
                'follow_up_depth': 3
            })
        
        # Combine and format: medium first, then hard
        all_questions = medium_questions[:medium_first] + hard_questions[:(num_questions - medium_first)]
        
        for i, q in enumerate(all_questions[:num_questions], 1):
            formatted.append({
                'question_id': f"conv_q_{i:03d}",
                'question_type': 'conversational',
                'order': i,
                'prompt': q.get('question', ''),
                'difficulty': q.get('difficulty', 'medium'),
                'time_limit_sec': 300 if q.get('difficulty') == 'medium' else 600,
                'conversation_config': {
                    'follow_up_depth': q.get('follow_up_depth', 3),
                    'ai_model': 'gpt-4o',
                    'evaluation_mode': 'contextual',
                    'focus_area': q.get('focus_area', '')
                }
            })
        
        return formatted
    
    def _generate_mock_questions(
        self,
        resume_data: Dict[str, Any],
        jd_data: Dict[str, Any],
        num_questions: int
    ) -> List[Dict[str, Any]]:
        """Generate mock questions when Azure OpenAI is not available."""
        projects = resume_data.get('projects', [])
        project_name = projects[0].get('name', 'your project') if projects else 'your experience'
        
        questions = [
            {
                'question_id': 'conv_q_001',
                'question_type': 'conversational',
                'order': 1,
                'prompt': f"Tell me about {project_name}. What was your role and what technologies did you use?",
                'difficulty': 'medium',
                'time_limit_sec': 300,
                'conversation_config': {
                    'follow_up_depth': 2,
                    'ai_model': 'gpt-4o',
                    'evaluation_mode': 'contextual'
                }
            },
            {
                'question_id': 'conv_q_002',
                'question_type': 'conversational',
                'order': 2,
                'prompt': f"Walk me through the implementation approach for {project_name}. What were the key design decisions?",
                'difficulty': 'medium',
                'time_limit_sec': 300,
                'conversation_config': {
                    'follow_up_depth': 2,
                    'ai_model': 'gpt-4o',
                    'evaluation_mode': 'contextual'
                }
            },
            {
                'question_id': 'conv_q_003',
                'question_type': 'conversational',
                'order': 3,
                'prompt': f"Deep dive into the architecture of {project_name}. What were the main scalability challenges and how did you address them?",
                'difficulty': 'hard',
                'time_limit_sec': 600,
                'conversation_config': {
                    'follow_up_depth': 3,
                    'ai_model': 'gpt-4o',
                    'evaluation_mode': 'contextual'
                }
            },
            {
                'question_id': 'conv_q_004',
                'question_type': 'conversational',
                'order': 4,
                'prompt': f"Explain the most complex technical problem you faced in {project_name}. How did you debug and solve it?",
                'difficulty': 'hard',
                'time_limit_sec': 600,
                'conversation_config': {
                    'follow_up_depth': 3,
                    'ai_model': 'gpt-4o',
                    'evaluation_mode': 'contextual'
                }
            },
            {
                'question_id': 'conv_q_005',
                'question_type': 'conversational',
                'order': 5,
                'prompt': f"If you had to redesign {project_name} today, what would you do differently and why? What advanced patterns or technologies would you consider?",
                'difficulty': 'hard',
                'time_limit_sec': 600,
                'conversation_config': {
                    'follow_up_depth': 3,
                    'ai_model': 'gpt-4o',
                    'evaluation_mode': 'contextual'
                }
            }
        ]
        
        return questions[:num_questions]
    
    def generate_project_drilldown_questions(
        self,
        project: Dict[str, Any],
        resume_data: Dict[str, Any],
        jd_data: Dict[str, Any],
        num_questions: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Generate drill-down hard questions for a specific project.
        These are follow-up questions that test deep understanding.
        """
        if not self.client:
            logger.warning("Azure OpenAI not configured, returning mock questions")
            return self._generate_mock_drilldown_questions(project, num_questions)
        
        try:
            project_name = project.get('name', 'the project')
            project_desc = project.get('description', '')
            technologies = project.get('technologies', [])
            
            system_prompt = """You are an expert technical interviewer conducting a deep-dive interview.
Generate HARD difficulty follow-up questions that drill into technical depth, architecture decisions, 
problem-solving approaches, and advanced concepts. These questions should test:
- Deep technical understanding
- Architecture and design decisions
- Performance optimization strategies
- Edge cases and challenges
- Trade-offs and alternatives considered

Return ONLY valid JSON array with this structure:
[
  {
    "question": "Question text",
    "difficulty": "hard",
    "focus_area": "What this question tests",
    "follow_up_depth": 3
  }
]"""

            user_prompt = f"""Generate {num_questions} HARD difficulty drill-down questions for this project:

PROJECT: {project_name}
DESCRIPTION: {project_desc[:500]}
TECHNOLOGIES: {', '.join(technologies[:10])}

JOB REQUIREMENTS:
{chr(10).join(jd_data.get('requirements', [])[:5]) if jd_data.get('requirements') else 'Not specified'}

Generate questions that:
1. Test deep understanding of the technologies used
2. Probe architecture and design decisions
3. Explore challenges faced and how they were solved
4. Test knowledge of alternatives and trade-offs
5. Evaluate problem-solving approach
6. Assess understanding of scalability, performance, and optimization

Return ONLY the JSON array, no additional text."""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            import json
            parsed = json.loads(content)
            
            # Handle both {"questions": [...]} and [...] formats
            questions_list = parsed.get('questions', []) if isinstance(parsed, dict) else parsed
            
            formatted = []
            for i, q in enumerate(questions_list[:num_questions], 1):
                formatted.append({
                    'question_id': f"drilldown_{project_name.lower().replace(' ', '_')}_{i:03d}",
                    'question_type': 'conversational',
                    'prompt': q.get('question', ''),
                    'difficulty': 'hard',
                    'time_limit_sec': 360,  # 6 minutes for hard
                    'conversation_config': {
                        'follow_up_depth': q.get('follow_up_depth', 3),
                        'ai_model': 'gpt-4o',
                        'evaluation_mode': 'contextual',
                        'focus_area': q.get('focus_area', ''),
                        'project_name': project_name
                    }
                })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error generating drill-down questions: {e}")
            return self._generate_mock_drilldown_questions(project, num_questions)
    
    def _generate_mock_drilldown_questions(
        self,
        project: Dict[str, Any],
        num_questions: int
    ) -> List[Dict[str, Any]]:
        """Generate mock drill-down questions when LLM is not available."""
        project_name = project.get('name', 'your project')
        questions = []
        
        for i in range(1, num_questions + 1):
            questions.append({
                'question_id': f"drilldown_mock_{i:03d}",
                'question_type': 'conversational',
                'prompt': f"Deep dive into the architecture of {project_name}. What were the main scalability challenges and how did you address them?",
                'difficulty': 'hard',
                'time_limit_sec': 360,
                'conversation_config': {
                    'follow_up_depth': 3,
                    'ai_model': 'gpt-4o',
                    'evaluation_mode': 'contextual',
                    'focus_area': 'Architecture and scalability',
                    'project_name': project_name
                }
            })
        
        return questions


azure_openai_service = AzureOpenAIService()
