"""Foundry Client - Connect to Foundry Local or manual OpenAI-compatible server."""

import os
import logging
import threading
from openai import OpenAI

logger = logging.getLogger(__name__)

try:
    from foundry_local import FoundryLocalManager
    FOUNDRY_AVAILABLE = True
except ImportError:
    FOUNDRY_AVAILABLE = False

DEFAULT_MODEL_ALIAS = "qwen2.5-7b"
CONNECTION_TIMEOUT = 30


def get_client():
    """Get OpenAI client and model ID."""
    if FOUNDRY_AVAILABLE:
        logger.info(f"Connecting via Foundry Local (model: {DEFAULT_MODEL_ALIAS})...")
        
        result = {}
        error = {}
        
        def connect():
            try:
                manager = FoundryLocalManager(DEFAULT_MODEL_ALIAS)
                result['manager'] = manager
            except Exception as e:
                error['msg'] = str(e)
        
        thread = threading.Thread(target=connect, daemon=True)  # daemon=True allows exit
        thread.start()
        thread.join(timeout=CONNECTION_TIMEOUT)
        
        if thread.is_alive():
            raise TimeoutError(f"Connection timed out after {CONNECTION_TIMEOUT}s. Is the model running?")
        
        if error:
            raise ConnectionError(error['msg'])
        
        manager = result['manager']
        client = OpenAI(base_url=manager.endpoint, api_key=manager.api_key)
        model_id = manager.get_model_info(DEFAULT_MODEL_ALIAS).id
        logger.info(f"Connected to Foundry Local - Model ID: {model_id}")
        return client, model_id