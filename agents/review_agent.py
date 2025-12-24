import json
from .base_agent import BaseAgent

class ReviewAgent(BaseAgent):
    def __init__(self, client, model_id, quiz_data, user_responses):
        super().__init__("Reviewer", client, model_id)
        
        # We format the data into a readable string for the System Prompt
        context_str = self._format_context(quiz_data, user_responses)
        
        self.system_prompt = f"""You are a Quiz Review Tutor.
Your goal is to help the user understand their mistakes and reinforce their learning.

### QUIZ DATA
{context_str}

### INSTRUCTIONS
1. Analyze the user's answers against the correct answers.
2. Provide a summary of their score (e.g., "You got 2/3 correct").
3. For each incorrect answer, explain WHY it is wrong and what the correct answer is.
4. Be encouraging but educational.
5. After the initial review, answer any follow-up questions the user has about the topic.
"""

    def _format_context(self, quiz_data, user_responses):
        """Helper to convert JSON data into a clean text block for the prompt."""
        text = f"TOPIC: {quiz_data.get('topic', 'Unknown')}\n\n"
        
        # Create a lookup for correct answers
        questions = quiz_data.get('questions', [])
        
        text += "--- QUESTIONS & CORRECT ANSWERS ---\n"
        for i, q in enumerate(questions):
            text += f"Q{i+1}: {q['question']}\n"
            text += f"   Options: {', '.join(q['options'])}\n"
            text += f"   Correct Answer: {q['correct']}\n\n"
            
        text += "--- USER RESPONSES ---\n"
        # We assume user_responses is the loaded JSON from the results file
        answers = user_responses.get('answers', [])
        for ans in answers:
            text += f"Q{ans['question_id']}: User selected '{ans['selected_option']}'\n"
            
        return text