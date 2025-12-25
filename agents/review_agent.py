"""Review Agent - Reviews quiz results and helps users learn."""

import logging

logger = logging.getLogger(__name__)


class ReviewAgent:
    """Reviews quiz results and provides educational feedback."""
    
    def __init__(self, client, model_id: str, quiz_data: dict, user_responses: dict):
        self.client = client
        self.model_id = model_id
        self.history = []
        
        context = self._format_context(quiz_data, user_responses)
        self.system_prompt = f"""You are a helpful Quiz Review Tutor.

## Quiz Data
{context}

## Instructions
1. Provide a clear score summary (e.g., "You scored 3/5")
2. For incorrect answers, explain why and provide the correct answer
3. Be encouraging and educational
4. Answer follow-up questions about the topic
"""

    def _format_context(self, quiz_data: dict, user_responses: dict) -> str:
        """Format quiz data and user responses into context string."""
        lines = [f"Topic: {quiz_data.get('topic', 'Unknown')}"]
        
        questions = quiz_data.get('questions', [])
        user_answers = {ans['question_id']: ans['selected_option'] for ans in user_responses.get('answers', [])}
        
        for i, q in enumerate(questions, 1):
            user_ans = user_answers.get(i, "No answer")
            is_correct = user_ans.startswith(q['correct']) if user_ans != "No answer" else False
            status = "✓" if is_correct else "✗"
            
            lines.append(f"\nQ{i}: {q['question']}")
            lines.append(f"Options: {', '.join(q['options'])}")
            lines.append(f"Correct: {q['correct']} | User: {user_ans} {status}")
        
        return "\n".join(lines)

    def run(self, message: str) -> str:
        """Process user message and return response."""
        self.history.append({"role": "user", "content": message})
        
        messages = [{"role": "system", "content": self.system_prompt}] + self.history
        
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            temperature=0.3,
            max_tokens=2048
        )
        
        content = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": content})
        return content