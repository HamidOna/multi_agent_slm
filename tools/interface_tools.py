import json
import gradio as gr
from pathlib import Path

# Define paths
QUIZ_DIR = Path("data/quizzes")
RESPONSE_DIR = Path("data/responses")
RESPONSE_DIR.mkdir(parents=True, exist_ok=True)

def launch_quiz_interface(topic: str) -> str:
    """
    Launches a graphical quiz interface for the given topic.
    Blocks execution until the user closes the window.
    """
    clean_topic = topic.replace(' ', '_').lower()
    filename = f"{clean_topic}_quiz.json"
    filepath = QUIZ_DIR / filename
    
    # 1. Check if quiz exists
    if not filepath.exists():
        return f"ERROR: Quiz file '{filename}' not found. Please generate the quiz first."

    print(f"\n🖥️ [Tool: launch_quiz] Loading {filepath}...")
    
    # 2. Load Quiz Data
    try:
        with open(filepath, 'r') as f:
            quiz_data = json.load(f)
    except Exception as e:
        return f"ERROR: Corrupted quiz file: {e}"

    questions = quiz_data.get("questions", [])
    if not questions:
        return "ERROR: Quiz file has no questions."

    # 3. Define the Gradio Interface
    # We use a closure here to capture the questions list
    def save_results(*user_answers):
        """Internal helper to save inputs to JSON"""
        results = []
        for i, ans in enumerate(user_answers):
            q_text = questions[i]["question"]
            results.append({
                "question_id": i + 1,
                "question": q_text,
                "selected_option": ans if ans else "No Answer"
            })
        
        output_path = RESPONSE_DIR / f"{clean_topic}_results.json"
        
        with open(output_path, "w") as f:
            json.dump({
                "topic": topic,
                "answers": results
            }, f, indent=2)
            
        return f"✅ Answers Saved to {output_path}! You can now close this window and ask the Orchestrator to grade it."

    # Build the UI dynamically based on the number of questions
    print("  🔹 Launching Gradio Window... (Script will pause until you close it)")
    
    with gr.Blocks(title=f"Quiz: {quiz_data.get('topic', topic)}") as demo:
        gr.Markdown(f"# 📝 Quiz: {quiz_data.get('topic', topic)}")
        
        input_components = []
        
        for q in questions:
            # Create a radio button for each question
            radio = gr.Radio(
                choices=q["options"], 
                label=q["question"]
            )
            input_components.append(radio)
        
        submit_btn = gr.Button("Submit Answers", variant="primary")
        output_msg = gr.Textbox(label="Status", interactive=False)
        
        # Link button to save function
        submit_btn.click(
            fn=save_results, 
            inputs=input_components, 
            outputs=output_msg
        )

    # 4. Launch (Blocking Mode)
    # prevent_thread_lock=False forces the script to wait here until the UI is closed
    demo.launch(prevent_thread_lock=False, height=800)
    
    return f"User completed the quiz interface for '{topic}'. Responses saved."