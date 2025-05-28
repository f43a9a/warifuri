"""LLM integration utilities for AI task execution."""

import os
import logging
from pathlib import Path
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """LLM API error."""

    pass


class LLMClient:
    """LLM API client for AI task execution."""

    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> None:
        self.model = model
        self.temperature = temperature
        self.api_key = self._get_api_key()

    def _get_api_key(self) -> str:
        """Get API key from environment variables."""
        # Try different API key patterns
        api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "LLM_API_KEY"]

        for key_name in api_keys:
            api_key = os.getenv(key_name)
            if api_key:
                logger.debug(f"Using API key from {key_name}")
                return api_key

        raise LLMError(f"No API key found. Set one of: {', '.join(api_keys)}")

    def _detect_provider(self) -> str:
        """Detect LLM provider from model name."""
        model_lower = self.model.lower()

        if "gpt" in model_lower or "openai" in model_lower:
            return "openai"
        elif "claude" in model_lower or "anthropic" in model_lower:
            return "anthropic"
        elif "gemini" in model_lower or "google" in model_lower:
            return "google"
        else:
            # Default to OpenAI-compatible API
            return "openai"

    def _call_openai_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": 4000,
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()

            result = response.json()
            return str(result["choices"][0]["message"]["content"])

        except requests.RequestException as e:
            raise LLMError(f"OpenAI API error: {e}") from e
        except (KeyError, IndexError) as e:
            raise LLMError(f"Invalid OpenAI API response: {e}") from e

    def _call_anthropic_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic API."""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        data = {
            "model": self.model,
            "max_tokens": 4000,
            "temperature": self.temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()

            result = response.json()
            return str(result["content"][0]["text"])

        except requests.RequestException as e:
            raise LLMError(f"Anthropic API error: {e}") from e
        except (KeyError, IndexError) as e:
            raise LLMError(f"Invalid Anthropic API response: {e}") from e

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response from LLM."""
        provider = self._detect_provider()

        logger.info(f"Calling {provider} API with model {self.model}")

        if provider == "openai":
            return self._call_openai_api(system_prompt, user_prompt)
        elif provider == "anthropic":
            return self._call_anthropic_api(system_prompt, user_prompt)
        else:
            # For other providers, try OpenAI-compatible API
            return self._call_openai_api(system_prompt, user_prompt)


def load_prompt_config(task_path: Path) -> Dict[str, Any]:
    """Load prompt.yaml configuration for AI tasks."""
    prompt_file = task_path / "prompt.yaml"

    if not prompt_file.exists():
        raise LLMError(f"prompt.yaml not found in {task_path}")

    try:
        from .yaml_utils import load_yaml

        config = load_yaml(prompt_file)

        # Validate required fields
        if "model" not in config:
            config["model"] = "gpt-3.5-turbo"  # Default model

        if "temperature" not in config:
            config["temperature"] = 0.7  # Default temperature

        return config

    except Exception as e:
        raise LLMError(f"Failed to load prompt config: {e}") from e


def save_ai_response(response: str, output_path: Path) -> None:
    """Save AI response to output/response.md."""
    output_file = output_path / "output" / "response.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Add metadata header
    import datetime

    timestamp = datetime.datetime.now().isoformat()

    content = f"""# AI Task Response

**Generated**: {timestamp}

---

{response}
"""

    output_file.write_text(content, encoding="utf-8")
    logger.info(f"AI response saved to {output_file}")


def log_ai_error(error: Exception, task_path: Path) -> None:
    """Log AI task execution error."""
    logs_dir = task_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    import datetime

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = logs_dir / f"failed_{timestamp}.log"

    error_content = f"""AI Task Execution Failed
=========================

Timestamp: {datetime.datetime.now().isoformat()}
Task Path: {task_path}
Error Type: {type(error).__name__}
Error Message: {str(error)}

"""

    error_file.write_text(error_content, encoding="utf-8")
    logger.error(f"AI task error logged to {error_file}")
