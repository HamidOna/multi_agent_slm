import json
import re
from typing import List, Dict, Any, Optional

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
        
        # --- FEW-SHOT PROMPT ---
        self.system_prompt = f"""You are {name}, a function-calling AI.

### AVAILABLE TOOLS
You have access to the following functions: [{tool_names}].
You MUST use these EXACT names.

### INSTRUCTIONS
To call a tool, you must output a JSON list with the specific prefix 'functools'.
Format: functools[{{"name": "exact_tool_name", "arguments": {{"arg": "value"}}}}]

### RULES
1. Output ONLY the functools block when you want to CALL a function.
2. Do not wrap the output in markdown (NO ```json).
3. Do not include introductory text.
4. IMPORTANT: When the tool execution is complete, the tool will return a confirmation message. You should simply acknowledge this to the user. Do not regenerate the content.

### EXAMPLES (Follow these strictly)

User: "Generate a quiz about space."
Bad Response: ```json [{{ "name": "generate_new_quiz", ... }}] ```
Correct Response: functools[{{"name": "generate_new_quiz", "arguments": {{"topic": "space"}}}}]

User: "Help me."
Correct Response: How can I help you today?
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
            
            if response_msg.content and "functools" in response_msg.content:
                response_msg.content = "" 

            # Add the Assistant's "Call" to the local turn
            messages.append(response_msg)
            current_turn_messages.append(response_msg)
            
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

                # Create the Tool Result Message
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                }
                
                # Add Tool Result to local turn
                messages.append(tool_msg)
                current_turn_messages.append(tool_msg)

            # Call Model Again
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                tools=self.tools
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
             response_msg.content = final_content

        current_turn_messages.append(response_msg)
        
        # Save the FULL chain to history
        self.history.extend(current_turn_messages)
        
        return final_content

    def _extract_functools(self, text: str):
        if not text: return None
        clean_text = re.sub(r'```(?:json|python)?', '', text)
        clean_text = re.sub(r'```', '', clean_text)
        match = re.search(r'functools\s*(\[.*?\])', clean_text, re.DOTALL)
        
        if match:
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                class MockToolCall:
                    def __init__(self, name, args):
                        self.id = "call_manual_" + name
                        self.function = type('obj', (object,), {'name': name, 'arguments': args})
                return [MockToolCall(d['name'], d['arguments']) for d in data]
            except Exception:
                pass
        return None