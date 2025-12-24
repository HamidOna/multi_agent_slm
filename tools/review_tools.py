import json
import gradio as gr
from pathlib import Path
from utils.foundry_client import get_client
from agents.review_agent import ReviewAgent

# Define paths
QUIZ_DIR = Path("data/quizzes")
RESPONSE_DIR = Path("data/responses")

def review_quiz_interface(topic: str) -> str:
    """
    Launches a chat interface to review the user's quiz performance.
    """
    clean_topic = topic.replace(' ', '_').lower()
    quiz_file = QUIZ_DIR / f"{clean_topic}_quiz.json"
    results_file = RESPONSE_DIR / f"{clean_topic}_results.json"
    
    # 1. Validation
    if not quiz_file.exists():
        return f"ERROR: Original quiz file for '{topic}' not found."
    if not results_file.exists():
        return f"ERROR: No results found for '{topic}'. Please take the quiz first."

    print(f"\n👨‍🏫 [Tool: review_quiz] Loading data for '{topic}'...")
    print(f"  🔹 Gradio version: {gr.__version__}")

    # 2. Load Data
    try:
        with open(quiz_file, 'r') as f:
            quiz_data = json.load(f)
        with open(results_file, 'r') as f:
            user_data = json.load(f)
    except Exception as e:
        return f"ERROR: Failed to read files: {e}"

    # 3. Initialize the Review Agent
    client, model_id = get_client()
    reviewer = ReviewAgent(client, model_id, quiz_data, user_data)
    
    # 4. Generate the Initial Review
    print("  🔹 Generating analysis from AI...")
    initial_review = reviewer.run("Please provide my quiz review now.")
    
    # 5. Launch Interface using Blocks
    print(f"  🔹 Opening Review Chat at http://127.0.0.1:7860 ...")
    
    with gr.Blocks() as demo:
        gr.Markdown(f"# Review: {topic}")
        gr.Markdown("Ask me anything about your quiz results!")
        
        # Create chatbot with initial message using gr.ChatMessage for proper typing
        chatbot = gr.Chatbot(
            value=[gr.ChatMessage(role="assistant", content=initial_review)],
            height=500
        )
        
        msg = gr.Textbox(
            placeholder="Ask a follow-up question...",
            show_label=False
        )
        
        with gr.Row():
            submit_btn = gr.Button("Send", variant="primary")
            clear_btn = gr.ClearButton([msg, chatbot], value="Clear")
        
        gr.Examples(
            examples=["Why was my answer to Q2 wrong?", "Tell me more about this topic."],
            inputs=msg
        )
        
        def respond(message, chat_history):
            if not message.strip():
                return "", chat_history
            
            # Add user message using ChatMessage
            chat_history.append(gr.ChatMessage(role="user", content=message))
            
            # Get bot response
            bot_response = reviewer.run(message)
            chat_history.append(gr.ChatMessage(role="assistant", content=bot_response))
            
            return "", chat_history
        
        # Bind events
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        submit_btn.click(respond, [msg, chatbot], [msg, chatbot])

    demo.launch(prevent_thread_lock=False)

    return f"User reviewed the quiz '{topic}'."