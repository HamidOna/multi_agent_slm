"""Base Agent with Standard Function Calling for Foundry Local."""

import json
import logging
import re
import uuid
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class _TextToolCall:
    """Mimics OpenAI tool_call object for text-parsed tool calls."""

    def __init__(self, name: str, arguments: str):
        self.id = f"call_{uuid.uuid4().hex[:8]}"
        self.function = type("Fn", (), {"name": name, "arguments": arguments})()


def _strip_think_tags(content: str) -> str:
    """Remove <think>...</think> blocks from Qwen3 output."""
    return re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL).strip()


def _parse_text_tool_calls(content: str) -> list:
    """Parse <tool_call>...</tool_call> tags from model output.

    Foundry intercepts these tags server-side for catalog models, but custom
    models pass them through as raw text. This does the same conversion
    client-side: extract the JSON, return objects matching the OpenAI format.
    """
    blocks = re.findall(r"<tool_call>\s*(.*?)\s*</tool_call>", content, re.DOTALL)
    calls = []
    for block in blocks:
        try:
            data = json.loads(block)
            calls.append(_TextToolCall(data["name"], json.dumps(data.get("arguments", {}))))
        except (json.JSONDecodeError, KeyError):
            continue
    return calls


class BaseAgent:
    """Function-calling agent using OpenAI tools API."""

    def __init__(
        self,
        name: str,
        client,
        model_id: str,
        tools: Optional[List[Dict]] = None,
        available_tools: Optional[Dict] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ):
        self.name = name
        self.client = client
        self.model_id = model_id
        self.tools = tools
        self.available_tools = available_tools or {}
        self.history: List[Dict[str, Any]] = []
        self.max_tokens = max_tokens
        self.temperature = temperature

        tool_list = ", ".join(self.available_tools.keys()) or "None"
        self.system_prompt = f"""You are {name}, an AI assistant with access to tools.

Available tools: [{tool_list}]

Instructions:
1. Use the function calling API when a tool is needed - don't write function calls as text
2. Wait for tool results before responding to the user
3. Be concise and helpful
/no_think"""

    def run(self, message: str) -> str:
        """Process user message through tool-calling loop."""
        current_turn: List[Dict[str, Any]] = [{"role": "user", "content": message}]
        messages = [{"role": "system", "content": self.system_prompt}] + self.history + current_turn

        response = self._call_model(messages)
        response_msg = response.choices[0].message
        tool_calls = response_msg.tool_calls
        if not tool_calls and response_msg.content:
            tool_calls = _parse_text_tool_calls(response_msg.content) or None

        while tool_calls:
            logger.info(f"[{self.name}] Executing {len(tool_calls)} tool call(s)...")

            # Add assistant message with tool calls
            assistant_msg = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    }
                    for tc in tool_calls
                ]
            }
            messages.append(assistant_msg)
            current_turn.append(assistant_msg)

            # Execute tools
            for tc in tool_calls:
                tool_result = self._execute_tool(tc)
                messages.append(tool_result)
                current_turn.append(tool_result)

            # Call model again
            response = self._call_model(messages)
            response_msg = response.choices[0].message
            tool_calls = response_msg.tool_calls
            if not tool_calls and response_msg.content:
                tool_calls = _parse_text_tool_calls(response_msg.content) or None

        final_content = _strip_think_tags(response_msg.content) if response_msg.content else "Task completed."
        current_turn.append({"role": "assistant", "content": final_content})
        self.history.extend(current_turn)

        return final_content

    def _call_model(self, messages: List[Dict]):
        """Make API call to model."""
        kwargs = {
            "model": self.model_id,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        if self.tools:
            kwargs["tools"] = self.tools
            kwargs["tool_choice"] = "auto"

        return self.client.chat.completions.create(**kwargs)

    def _execute_tool(self, tool_call) -> Dict[str, Any]:
        """Execute tool and return result message."""
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # Log the call
        print(f"  🔧 Calling: {func_name}({args})")

        if func_name in self.available_tools:
            logger.info(f"[{self.name}] 🔧 Executing: {func_name}({args})")
            result = self.available_tools[func_name](**args)
        else:
            result = f"Error: Tool '{func_name}' not found."

        if not isinstance(result, str):
            result = json.dumps(result)

        return {
            "role": "tool",
            "name": func_name,
            "tool_call_id": tool_call.id,
            "content": result
        }

    def clear_history(self):
        """Clear conversation history."""
        self.history = []
