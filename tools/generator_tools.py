"""Tools for creating quizzes."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/quizzes")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def generate_new_quiz(topic: str, num_questions: int = 3, **kwargs) -> str:
    """Generate a new quiz on the given topic."""
    from utils.foundry_client import get_client
    from agents.quiz_generator import QuizGeneratorAgent
    
    logger.info(f"[Tool: generate_new_quiz] Starting... Topic: '{topic}', Questions: {num_questions}")
    
    client, model_id = get_client()
    generator = QuizGeneratorAgent(client, model_id)
    quiz_data = generator.generate(topic, num_questions=num_questions)
    
    filename = f"{topic.replace(' ', '_').lower()}_quiz.json"
    filepath = DATA_DIR / filename
    
    with open(filepath, "w") as f:
        json.dump(quiz_data, f, indent=2)
    
    logger.info(f"[Tool: generate_new_quiz] Quiz saved to: {filepath}")
    return f"Success! Generated a quiz on '{topic}' with {len(quiz_data['questions'])} questions. Saved as '{filename}'."