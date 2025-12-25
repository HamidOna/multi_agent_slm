# 🎓 Quiz App - Multi-Agent System with Function Calling

A multi-agent quiz application demonstrating standard function calling with Small Language Models (SLMs) using Microsoft Foundry Local.

## Overview

This project showcases a multi-agent architecture where an orchestrator agent coordinates specialist agents to generate quizzes, administer them through a UI, and provide personalized feedback on results.

## Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                         User                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                       │
│                      (BaseAgent)                            │
│         • Interprets user intent                            │
│         • Routes to appropriate tools                       │
│         • Uses standard function calling API                │
└───────┬─────────────────┬─────────────────┬─────────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  generate_    │ │  launch_quiz_ │ │  review_quiz_ │
│  new_quiz     │ │  interface    │ │  interface    │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ QuizGenerator │ │   Gradio UI   │ │  ReviewAgent  │
│    Agent      │ │  (Take Quiz)  │ │  + Gradio UI  │
└───────────────┘ └───────────────┘ └───────────────┘
```

## Features

- **Quiz Generation**: Create quizzes on any topic with customizable number of questions
- **Interactive Quiz UI**: Take quizzes through a clean Gradio interface
- **AI-Powered Review**: Get personalized feedback and explanations from an AI tutor
- **Function Calling**: Uses standard OpenAI-compatible tool calling API
- **Local LLM**: Runs entirely on your machine using Foundry Local

## Project Structure
```
my_quiz_app/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py        # Core agent with function calling
│   ├── quiz_generator.py    # Generates quiz JSON
│   └── review_agent.py      # Reviews results with user
├── tools/
│   ├── __init__.py
│   ├── generator_tools.py   # Quiz generation tool
│   ├── interface_tools.py   # Quiz-taking UI tool
│   └── review_tools.py      # Quiz review UI tool
├── utils/
│   ├── __init__.py
│   └── foundry_client.py    # Model client setup
├── data/
│   ├── quizzes/             # Generated quiz JSON files
│   └── responses/           # User response JSON files
├── main.py                  # Application entry point
├── requirements.txt
└── README.md
```

## Prerequisites

### System Requirements

1. **Foundry Local** (version 0.8.117 or later)
   
   Install Foundry Local on your system:
   
   **Windows:**
```bash
   winget install Microsoft.FoundryLocal
```
   
   **macOS:**
```bash
   brew tap microsoft/foundrylocal
   brew install foundrylocal
```
   
   Verify installation:
```bash
   foundry --version
```
   
   Documentation: https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started

2. **Python Dependencies**
```bash
   pip install -r requirements.txt
```

## Setup

1. **Clone the repository**
```bash
   git clone <repository-url>
   cd my_quiz_app
```

2. **Install dependencies**
```bash
   pip install -r requirements.txt
```

3. **Start the model**
```bash
   foundry model run qwen2.5-7b-instruct-cuda-gpu
```
   
   > Note: First run will download the model (~4GB). Use a model that supports tool calling - check with `foundry model list`.

4. **Run the app**
```bash
   python main.py
```

## Usage
```
==================================================
🎓 Quiz App - Multi-Agent Orchestrator
==================================================

Commands:
  • 'Generate a quiz about [topic]'
  • 'Take the quiz'
  • 'Review my quiz'
  • 'quit' to exit
==================================================

👤 You: Generate a 5 question quiz about photosynthesis

  🔧 Calling: generate_new_quiz({'topic': 'photosynthesis', 'num_questions': 5})

🤖 Assistant: Success! Generated a quiz on 'photosynthesis' with 5 questions.

👤 You: Take the quiz

  🔧 Calling: launch_quiz_interface({'topic': 'photosynthesis'})

[Gradio UI opens - answer questions and submit]

🤖 Assistant: Quiz completed for 'photosynthesis'. Responses saved.

👤 You: Review my quiz

  🔧 Calling: review_quiz_interface({'topic': 'photosynthesis'})

[Review chat UI opens with AI tutor]

🤖 Assistant: Review session completed for 'photosynthesis'.
```

## How It Works

### Function Calling Flow

1. User sends a message to the Orchestrator
2. Orchestrator calls the model with available tools
3. Model returns structured `tool_calls` (not text)
4. Orchestrator executes the tool and gets results
5. Results are sent back to the model
6. Model provides final response to user

### Agents

| Agent | Purpose |
|-------|---------|
| **BaseAgent** | Handles function calling loop, tool execution, conversation history |
| **QuizGeneratorAgent** | Generates quiz questions in JSON format |
| **ReviewAgent** | Conversational tutor that explains quiz results |

### Tools

| Tool | Function |
|------|----------|
| `generate_new_quiz` | Creates quiz JSON file on any topic |
| `launch_quiz_interface` | Opens Gradio UI to take the quiz |
| `review_quiz_interface` | Opens chat UI with AI tutor for feedback |

## Configuration

Change the default model in `utils/foundry_client.py`:
```python
DEFAULT_MODEL_ALIAS = "qwen2.5-7b-instruct-cuda-gpu"
```

Available models with tool calling support:
```bash
foundry model list
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection timeout | Start the model first: `foundry model run <model-name>` |
| No tool_calls returned | Use a model that supports tool calling (e.g., qwen2.5-7b) |
| Gradio errors | Ensure `gradio>=6.0.0` is installed |

## Requirements

- Python 3.10+
- Foundry Local 0.8.117+
- ~8GB RAM (for qwen2.5-7b model)
- GPU recommended but not required

## License

MIT
