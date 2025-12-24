import sys
from utils.foundry_client import get_client
from agents.base_agent import BaseAgent
from tools.generator_tools import generate_new_quiz
from tools.interface_tools import launch_quiz_interface
from tools.review_tools import review_quiz_interface

# --- CONFIGURATION ---

# 1. Define the Tool Definitions (Schema)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "generate_new_quiz",
            "description": "CREATES and SAVES a quiz to a JSON file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The topic of the quiz"}
                },
                "required": ["topic"]
            }
        }
    },
    # --- NEW TOOL SCHEMA ---
    {
        "type": "function",
        "function": {
            "name": "launch_quiz_interface",
            "description": "Launches a visual quiz window for the user to take the quiz. Use this when the user says 'I want to take the quiz' or 'Load the quiz'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The topic of the quiz to load"}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "review_quiz_interface",
            "description": "Launches a chat tutor to review quiz results and explain mistakes. Use when user asks 'How did I do?' or 'Review my quiz'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The topic of the quiz to review"}
                },
                "required": ["topic"]
            }
        }
    }    
]

# 2. Map Tool Names to Functions
AVAILABLE_TOOLS = {
    "generate_new_quiz": generate_new_quiz,
    "launch_quiz_interface": launch_quiz_interface,
    "review_quiz_interface": review_quiz_interface  # <--- Add this
}

def main():
    print("\n" + "="*50)
    print("🤖 Orchestrator Initialized")
    print("="*50)
    
    # 1. Setup Connection
    try:
        client, model_id = get_client()
        print(f"✅ Connected to model: {model_id}\n")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    # 2. Initialize Orchestrator
    orchestrator = BaseAgent(
        name="Orchestrator", 
        client=client, 
        model_id=model_id, 
        tools=TOOLS_SCHEMA,
        available_tools=AVAILABLE_TOOLS 
    )

    # 3. Chat Loop
    while True:
        try:
            user_input = input("👤 User: ").strip()
            if user_input.lower() in ["quit", "exit"]:
                break
            if not user_input:
                continue

            response = orchestrator.run(user_input)
            print(f"🤖 Orchestrator: {response}\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()