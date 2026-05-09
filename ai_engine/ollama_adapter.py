import requests
import logging

logger = logging.getLogger(__name__)

# Default Ollama endpoint when running locally
OLLAMA_API_URL = "http://localhost:11434/api/generate"
# You can change this to 'llama3', 'mistral', or any model you have pulled in Ollama
DEFAULT_MODEL = "llama3"

def generate_text_open_source(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Calls a local Open Source LLM via Ollama.
    If Ollama is not running or the model is missing, falls back to a simulated response.
    """
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=15  # Reasonable timeout for local inference
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Ollama API not available or failed: {e}. Falling back to stub.")
        return None
