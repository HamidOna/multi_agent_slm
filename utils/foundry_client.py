"""Foundry Client - Connect to Foundry Local or manual OpenAI-compatible server."""

import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

try:
    from foundry_local import FoundryLocalManager
    FOUNDRY_AVAILABLE = True
except ImportError:
    FOUNDRY_AVAILABLE = False

DEFAULT_MODEL_ALIAS = "qwen2.5-7b"


def get_client():
    """Get OpenAI client and model ID."""
    if FOUNDRY_AVAILABLE:
        logger.info(f"Connecting via Foundry Local (model: {DEFAULT_MODEL_ALIAS})...")
        manager = FoundryLocalManager(DEFAULT_MODEL_ALIAS)
        client = OpenAI(base_url=manager.endpoint, api_key=manager.api_key)
        model_id = manager.get_model_info(DEFAULT_MODEL_ALIAS).id
        logger.info(f"Connected to Foundry Local - Model ID: {model_id}")
        return client, model_id
    
