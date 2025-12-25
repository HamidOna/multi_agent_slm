#!/usr/bin/env python3
"""Quiz App - Multi-Agent Orchestrator with Function Calling."""

import logging
from utils.foundry_client import get_client
from agents.base_agent import BaseAgent
from tools.generator_tools import generate_new_quiz
from tools.interface_tools import launch_quiz_interface
from tools.review_tools import review_quiz_interface

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("gradio").setLevel(logging.WARNING)

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "generate_new_quiz",
            "description": "Creates a new quiz on a topic. Use when user wants to create/generate a quiz.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The quiz topic"},
                    "num_questions": {"type": "integer", "description": "Number of questions", "default": 3}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "launch_quiz_interface",
            "description": "Opens quiz interface for user to take the quiz.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The quiz topic to load"}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "review_quiz_interface",
            "description": "Opens chat interface to review quiz results. Use when user asks to review/grade their quiz.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The quiz topic to review"}
                },
                "required": ["topic"]
            }
        }
    }
]

AVAILABLE_TOOLS = {
    "generate_new_quiz": generate_new_quiz,
    "launch_quiz_interface": launch_quiz_interface,
    "review_quiz_interface": review_quiz_interface
}


def main():
    print("\n" + "=" * 50)
    print("🎓 Quiz App - Multi-Agent Orchestrator")
    print("=" * 50)
    print("\nCommands:")
    print("  • 'Generate a quiz about [topic]'")
    print("  • 'Take the quiz'")
    print("  • 'Review my quiz'")
    print("  • 'quit' to exit")
    print("=" * 50 + "\n")
    
    try:
        client, model_id = get_client()
    except Exception as e:
        print(f"❌ {e}")
        return
    
    print(f"✅ Connected to: {model_id}\n")
    
    orchestrator = BaseAgent(
        name="Orchestrator",
        client=client,
        model_id=model_id,
        tools=TOOLS_SCHEMA,
        available_tools=AVAILABLE_TOOLS
    )
    
    while True:
        user_input = input("👤 You: ").strip()
        
        if user_input.lower() in ["quit", "exit", "q"]:
            print("\n👋 Goodbye!")
            break
        
        if not user_input:
            continue
        
        response = orchestrator.run(user_input)
        print(f"\n🤖 Assistant: {response}\n")


if __name__ == "__main__":
    main()