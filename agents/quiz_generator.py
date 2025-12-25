"""Quiz Generator Agent - Generates quiz questions in JSON format."""

import json
import logging

logger = logging.getLogger(__name__)


class QuizGeneratorAgent:
    """Generates quiz questions on a given topic."""
    
    def __init__(self, client, model_id: str):
        self.client = client
        self.model_id = model_id
        self.system_prompt = """You are a Quiz Generator that outputs ONLY valid JSON.

Output format:
{
  "topic": "The quiz topic",
  "questions": [
    {
      "question": "The question text?",
      "options": ["A) First option", "B) Second option", "C) Third option", "D) Fourth option"],
      "correct": "A"
    }
  ]
}

Rules:
1. Output ONLY the JSON object - no explanations, no markdown
2. Each question must have exactly 4 options (A, B, C, D)
3. The "correct" field must be a single letter (A, B, C, or D)
"""

    def generate(self, topic: str, num_questions: int = 5) -> dict:
        """Generate a quiz on the given topic."""
        logger.info(f"[QuizGenerator] Generating {num_questions} questions about '{topic}'...")
        
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Create a quiz about '{topic}' with exactly {num_questions} questions."}
            ],
            temperature=0.1,
            max_tokens=2048
        )
        
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code fences if present
        if "```" in content:
            content = content.split("```json")[-1] if "```json" in content else content.split("```")[-1]
            content = content.split("```")[0].strip()
        
        quiz_data = json.loads(content)
        logger.info(f"[QuizGenerator] Successfully generated {len(quiz_data['questions'])} questions")
        return quiz_data