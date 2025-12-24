import json
import traceback
from pathlib import Path
from utils.foundry_client import get_client
from agents.quiz_generator import QuizGeneratorAgent

# Setup file paths
DATA_DIR = Path("data/quizzes")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- FIX: Update signature to accept num_questions and extra args ---
def generate_new_quiz(topic: str, num_questions: int = 3, **kwargs) -> str:
    """
    Spins up the Generator Agent to create a quiz on the given topic.
    Returns: A confirmation message with the filename.
    """
    # This print should now appear!
    print(f"\n⚙️ [Tool: generate_new_quiz] STARTING... Topic: '{topic}'")

    if kwargs:
        print(f"  ⚠️ Note: Ignoring extra arguments: {kwargs}")

    try:
        # 1. Connect
        print("  🔹 Connecting to Foundry client...")
        client, model_id = get_client()
        
        # 2. Wake up the Specialist Agent
        print("  🔹 Initializing Generator Agent...")
        generator = QuizGeneratorAgent(client, model_id)
        
        # 3. Do the work
        print(f"  🔹 Requesting {num_questions} questions from AI...")
        # Pass the dynamic number of questions
        quiz_data = generator.generate(topic, num_questions=num_questions)
        
        if not quiz_data:
            raise ValueError("Generator Agent returned empty data.")
            
        print(f"  🔹 Received Data: {str(quiz_data)[:100]}...") 
        
        # 4. Save file
        filename = f"{topic.replace(' ', '_').lower()}_quiz.json"
        filepath = DATA_DIR / filename
        
        print(f"  🔹 Saving to file: {filepath.absolute()}")
        with open(filepath, "w") as f:
            json.dump(quiz_data, f, indent=2)
            
        print(f"✅ [Tool] SUCCESS! Quiz saved.")
        return f"Success! I have generated a quiz on '{topic}' and saved it as {filename}."

    except Exception as e:
        error_msg = f"❌ [Tool Error] Failed to generate quiz: {e}"
        print(error_msg)
        traceback.print_exc()
        return error_msg