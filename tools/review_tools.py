"""Tools for launching quiz review interface."""

import json
import logging
from pathlib import Path
import gradio as gr

logger = logging.getLogger(__name__)

QUIZ_DIR = Path("data/quizzes")
RESPONSE_DIR = Path("data/responses")


def review_quiz_interface(topic: str) -> str:
    """Launch chat interface to review quiz results."""
    from utils.foundry_client import get_client
    from agents.review_agent import ReviewAgent
    
    clean_topic = topic.replace(' ', '_').lower()
    quiz_file = QUIZ_DIR / f"{clean_topic}_quiz.json"
    results_file = RESPONSE_DIR / f"{clean_topic}_results.json"
    
    if not quiz_file.exists():
        return f"Error: Quiz file for '{topic}' not found."
    if not results_file.exists():
        return f"Error: No results found for '{topic}'. Please take the quiz first."
    
    with open(quiz_file, 'r') as f:
        quiz_data = json.load(f)
    with open(results_file, 'r') as f:
        user_data = json.load(f)
    
    client, model_id = get_client()
    reviewer = ReviewAgent(client, model_id, quiz_data, user_data)
    initial_review = reviewer.run("Please provide my quiz review now.")
    
    with gr.Blocks(title=f"Review: {topic}") as demo:
        gr.Markdown(f"# 📊 Quiz Review: {topic}")
        
        chatbot = gr.Chatbot(value=[{"role": "assistant", "content": initial_review}], height=400)
        msg = gr.Textbox(placeholder="Ask a follow-up question...", show_label=False)
        
        with gr.Row():
            submit_btn = gr.Button("Send", variant="primary")
            done_btn = gr.Button("Done - Close Review", variant="secondary")
        
        def respond(message: str, chat_history: list):
            if not message.strip():
                return "", chat_history
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": reviewer.run(message)})
            return "", chat_history
        
        def close_review():
            demo.close()
        
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        submit_btn.click(respond, [msg, chatbot], [msg, chatbot])
        done_btn.click(close_review)
    
    demo.launch(prevent_thread_lock=False, share=False)
    return f"Review session completed for '{topic}'."