"""Tools for launching quiz interface."""

import json
import logging
from pathlib import Path
import gradio as gr

logger = logging.getLogger(__name__)

QUIZ_DIR = Path("data/quizzes")
RESPONSE_DIR = Path("data/responses")
RESPONSE_DIR.mkdir(parents=True, exist_ok=True)


def launch_quiz_interface(topic: str) -> str:
    """Launch graphical quiz interface."""
    clean_topic = topic.replace(' ', '_').lower()
    filepath = QUIZ_DIR / f"{clean_topic}_quiz.json"
    
    if not filepath.exists():
        return f"Error: Quiz file not found. Please generate the quiz first."
    
    logger.info(f"[Tool: launch_quiz_interface] Loading quiz from {filepath}")
    
    with open(filepath, 'r') as f:
        quiz_data = json.load(f)
    
    questions = quiz_data.get("questions", [])
    
    with gr.Blocks(title=f"Quiz: {quiz_data.get('topic', topic)}") as demo:
        gr.Markdown(f"# 📝 Quiz: {quiz_data.get('topic', topic)}")
        
        inputs = [gr.Radio(choices=q["options"], label=f"Q{i+1}: {q['question']}") for i, q in enumerate(questions)]
        submit_btn = gr.Button("Submit & Close", variant="primary")
        output_msg = gr.Textbox(label="Status", interactive=False)
        
        def save_and_close(*user_answers):
            results = [
                {"question_id": i + 1, "question": questions[i]["question"], "selected_option": ans or "No Answer"}
                for i, ans in enumerate(user_answers)
            ]
            output_path = RESPONSE_DIR / f"{clean_topic}_results.json"
            with open(output_path, "w") as f:
                json.dump({"topic": topic, "answers": results}, f, indent=2)
            
            # Schedule close after returning message
            demo.close()
            return "✅ Answers saved! Window closing..."
        
        submit_btn.click(fn=save_and_close, inputs=inputs, outputs=output_msg)
    
    logger.info("[Tool: launch_quiz_interface] Launching Gradio interface...")
    demo.launch(prevent_thread_lock=False, share=False)
    return f"Quiz completed for '{topic}'. Responses saved."