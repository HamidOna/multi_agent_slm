import json
import logging
import re
from typing import List, Dict, Any, Optional

# Configure logging for fallback detection
logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, name: str, client, model_id: str, tools: Optional[List] = None, available_tools: Optional[Dict] = None, max_tokens: int = 2048):
        self.name = name
        self.client = client
        self.model_id = model_id
        self.tools = tools
        self.available_tools = available_tools or {}
        self.history = []
        self.max_tokens = max_tokens

        # Dynamic tool list
        tool_names = ", ".join(f"'{name}'" for name in self.available_tools.keys())

        # --- SYSTEM PROMPT ---
        # Note: The model should use native function calling via the tools API.
        # The functools format below is a FALLBACK for servers that don't return structured tool_calls.
        self.system_prompt = f"""You are {name}, a function-calling AI assistant.

### AVAILABLE TOOLS
You have access to the following functions: [{tool_names}].
Use these EXACT function names when calling tools.

### HOW TO CALL FUNCTIONS
To call a function, output ONLY the function call in this format:
functools[{{"name": "function_name", "arguments": {{"arg": "value"}}}}]

Do NOT output any other text when calling a function - just the functools block.

### RULES
1. Output ONLY the functools block when calling a function (no extra text).
2. Do NOT wrap in markdown code blocks.
3. After receiving tool results, acknowledge them naturally to the user.
4. Do NOT regenerate content that was already created by a tool.
5. If the user's request doesn't require a tool, respond conversationally.

### EXAMPLES

User: "Generate a quiz about space."
functools[{{"name": "generate_new_quiz", "arguments": {{"topic": "space"}}}}]

User: "Help me."
How can I help you today?
"""

    def run(self, message: str) -> str:
        # 1. Prepare Initial Messages
        # Structure: [System, ...OldHistory..., User]
        current_turn_messages = [{"role": "user", "content": message}]
        messages = [{"role": "system", "content": self.system_prompt}] + self.history + current_turn_messages

        # 2. Call Model
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            temperature=0.0
        )

        response_msg = response.choices[0].message
        content = response_msg.content or ""

        # --- HYBRID PARSING LOGIC ---
        tool_calls = response_msg.tool_calls

        if not tool_calls:
            manual_calls = self._extract_functools(content)
            if manual_calls:
                print(f"  ⚠️ Server missed call. Parsing manually...")
                tool_calls = manual_calls
                response_msg.content = None

        # 3. Execution Loop
        while tool_calls:
            print(f"  ⚙️  {self.name} is calling a tool...")

            # Normalize and add the Assistant's "Call" to the local turn
            # Clear functools content from display since it's being processed as a tool call
            assistant_msg = self._normalize_assistant_message(response_msg)
            if assistant_msg.get("content") and "functools" in assistant_msg["content"]:
                assistant_msg["content"] = None

            messages.append(assistant_msg)
            current_turn_messages.append(assistant_msg)

            for tool_call in tool_calls:
                func_name = tool_call.function.name

                # Robust Argument Parsing
                if isinstance(tool_call.function.arguments, str):
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        args = tool_call.function.arguments
                else:
                    args = tool_call.function.arguments

                if func_name in self.available_tools:
                    print(f"  🔧 Executing {func_name}...")
                    try:
                        tool_result = self.available_tools[func_name](**args)
                    except Exception as e:
                        print(f"  ❌ Tool Crash: {e}")
                        tool_result = f"Error executing tool: {e}"
                else:
                    tool_result = f"Error: Tool '{func_name}' not found."

                # Create the Tool Result Message (include name for compatibility)
                tool_msg = {
                    "role": "tool",
                    "name": func_name,
                    "tool_call_id": getattr(tool_call, "id", None),
                    "content": json.dumps(tool_result) if not isinstance(tool_result, str) else tool_result
                }

                # Add Tool Result to local turn
                messages.append(tool_msg)
                current_turn_messages.append(tool_msg)

            # Call Model Again (same parameters for consistency)
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.0
            )
            response_msg = response.choices[0].message
            content = response_msg.content or ""

            # Re-check for new calls
            tool_calls = response_msg.tool_calls
            if not tool_calls:
                tool_calls = self._extract_functools(content)

        # 4. Final Response & History Update
        final_content = response_msg.content
        if not final_content or not final_content.strip():
            final_content = "Task completed successfully."

        # Normalize final message before appending to history
        final_msg = self._normalize_assistant_message(response_msg)
        if not final_msg.get("content"):
            final_msg["content"] = final_content

        current_turn_messages.append(final_msg)

        # Save the FULL chain to history
        self.history.extend(current_turn_messages)

        return final_content

    def _normalize_assistant_message(self, response_msg) -> Dict[str, Any]:
        """Convert response message object to a normalized dict for API compatibility."""
        msg = {
            "role": "assistant",
            "content": getattr(response_msg, "content", None)
        }

        # Handle native tool_calls if present
        if hasattr(response_msg, "tool_calls") and response_msg.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": getattr(tc, "id", f"call_{tc.function.name}"),
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments if isinstance(tc.function.arguments, str) else json.dumps(tc.function.arguments)
                    }
                }
                for tc in response_msg.tool_calls
            ]

        # Handle legacy function_call if present (OpenAI v1 compatibility)
        if hasattr(response_msg, "function_call") and response_msg.function_call:
            msg["function_call"] = {
                "name": response_msg.function_call.name,
                "arguments": response_msg.function_call.arguments
            }

        return msg

    def _extract_functools(self, text: str):
        """
        Fallback parser for when the server doesn't return structured tool_calls.
        This is a workaround for servers with incomplete function-calling support.
        Should be removed once the server reliably supplies tool_calls.
        """
        if not text:
            return None

        # Clean markdown wrappers
        clean_text = re.sub(r'```(?:json|python)?', '', text)
        clean_text = re.sub(r'```', '', clean_text)

        # Try multiple patterns for robustness
        patterns = [
            r'functools\s*(\[.*?\])',           # Standard format
            r'functools\s*(\[\s*\{.*?\}\s*\])', # With extra whitespace
        ]

        for pattern in patterns:
            match = re.search(pattern, clean_text, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1)
                    data = json.loads(json_str)

                    # Log that we're using fallback parsing
                    logger.warning(
                        f"[{self.name}] Using fallback functools parser. "
                        "Server did not return structured tool_calls. "
                        "Consider upgrading server or checking streaming bug (#346)."
                    )

                    class MockToolCall:
                        def __init__(self, name, args):
                            self.id = f"call_manual_{name}"
                            self.function = type('obj', (object,), {'name': name, 'arguments': args})()

                    return [MockToolCall(d['name'], d.get('arguments', {})) for d in data]
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.debug(f"[{self.name}] Fallback parser failed: {e}")
                    continue

        return None
