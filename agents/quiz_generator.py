import json
from .base_agent import BaseAgent

class QuizGeneratorAgent(BaseAgent):
    def __init__(self, client, model_id):
        # Initialize BaseAgent (tools=None by default)
        super().__init__("Generator", client, model_id)
        
        # Override system prompt for JSON generation
        self.system_prompt = """You are a Quiz Generator API.
You DO NOT write chatty responses. 
You ONLY output valid JSON.
Format:
{
  "topic": "...",
  "questions": [
    {
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ..."],
      "correct": "A"
    }
  ]
}"""

    def generate(self, topic: str, num_questions: int) -> dict:
        prompt = f"Create a quiz about '{topic}' with {num_questions} questions."
        
        # Prepare messages manually since we are bypassing BaseAgent.run
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Call model directly (No tools needed for the Generator itself)
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=0.1 
            )
            
            content = response.choices[0].message.content.strip()
            
            # Cleanup: sometimes models wrap JSON in markdown blocks like ```json ... ```
            if "```" in content:
                # Robustly find the start and end of the code block
                if "```json" in content:
                    content = content.split("```json")[-1]
                else:
                    content = content.split("```")[-1]
                
                content = content.split("```")[0].strip()
            
            return json.loads(content)

        except Exception as e:
            print(f"❌ Generator Agent Error: {e}")
            return None