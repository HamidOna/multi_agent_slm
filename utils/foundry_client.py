"""Foundry Client - Connect to Foundry Local or manual OpenAI-compatible server."""

import logging
import re
import subprocess
from openai import OpenAI

logger = logging.getLogger(__name__)

try:
    from foundry_local import FoundryLocalManager
    FOUNDRY_AVAILABLE = True
except ImportError:
    FOUNDRY_AVAILABLE = False

DEFAULT_MODEL_ALIAS = "qwen3-0.6b-int4"


def _discover_endpoint():
    """Discover running Foundry service endpoint via CLI."""
    result = subprocess.run(
        ["foundry", "service", "status"],
        capture_output=True, text=True, timeout=10
    )
    match = re.search(r"(http://\S+?)(?:/openai)?/status", result.stdout)
    if not match:
        raise ConnectionError(
            "Foundry service is not running.\n"
            f"Start it with: foundry model run {DEFAULT_MODEL_ALIAS}"
        )
    return match.group(1)


def get_client():
    """Get OpenAI client and model ID.

    For catalog models: uses FoundryLocalManager (auto-starts service).
    For custom models: discovers the running service endpoint directly.
    """
    # Try FoundryLocalManager first (works for catalog models)
    if FOUNDRY_AVAILABLE:
        try:
            manager = FoundryLocalManager(DEFAULT_MODEL_ALIAS)
            client = OpenAI(base_url=manager.endpoint, api_key=manager.api_key)
            model_id = manager.get_model_info(DEFAULT_MODEL_ALIAS).id
            logger.info(f"Connected via SDK - Model ID: {model_id}")
            return client, model_id
        except (ValueError, Exception) as e:
            if "not found in the catalog" not in str(e):
                raise
            logger.info(f"Model not in catalog, trying direct connection...")

    # Fallback: discover running service (for custom models)
    endpoint = _discover_endpoint()
    base_url = f"{endpoint}/v1"
    client = OpenAI(base_url=base_url, api_key="foundry-local")

    # Verify the model is actually loaded
    models = client.models.list()
    model_ids = [m.id for m in models.data]

    if DEFAULT_MODEL_ALIAS in model_ids:
        model_id = DEFAULT_MODEL_ALIAS
    elif model_ids:
        model_id = model_ids[0]
        logger.info(f"Using loaded model: {model_id}")
    else:
        raise ConnectionError(
            f"No models loaded. Run: foundry model run {DEFAULT_MODEL_ALIAS}"
        )

    logger.info(f"Connected to {base_url} - Model: {model_id}")
    return client, model_id
