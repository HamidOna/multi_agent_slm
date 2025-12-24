import os
from openai import OpenAI

# Try to import Foundry, fallback if missing (good for testing)
try:
    from foundry_local import FoundryLocalManager
    USING_FOUNDRY = True
except ImportError:
    USING_FOUNDRY = False

MODEL_ALIAS = "phi-4-cuda-gpu"

def get_client():
    """Returns a configured OpenAI client pointing to Foundry Local."""
    if USING_FOUNDRY:
        manager = FoundryLocalManager(MODEL_ALIAS)
        return OpenAI(
            base_url=manager.endpoint,
            api_key=manager.api_key
        ), manager.get_model_info(MODEL_ALIAS).id
    else:
        # Fallback for manual local servers (like Llama.cpp or manual Foundry start)
        return OpenAI(base_url="http://localhost:8000/v1", api_key="none"), MODEL_ALIAS