"""Tests for LLM utilities."""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from warifuri.utils.llm import (
    LLMError,
    LLMClient,
    load_prompt_config,
    save_ai_response,
    log_ai_error,
)


class TestLLMClient:
    """Test LLMClient class."""

    def test_init_with_defaults(self) -> None:
        """Test LLMClient initialization with defaults."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient()
            assert client.model == "gpt-3.5-turbo"
            assert client.temperature == 0.7
            assert client.api_key == "test-key"

    def test_init_with_custom_params(self) -> None:
        """Test LLMClient initialization with custom parameters."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(model="gpt-4", temperature=0.5)
            assert client.model == "gpt-4"
            assert client.temperature == 0.5

    def test_get_api_key_openai(self) -> None:
        """Test getting OpenAI API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "openai-key"}, clear=True):
            client = LLMClient()
            assert client.api_key == "openai-key"

    def test_get_api_key_anthropic(self) -> None:
        """Test getting Anthropic API key."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "anthropic-key"}, clear=True):
            client = LLMClient()
            assert client.api_key == "anthropic-key"

    def test_get_api_key_gemini(self) -> None:
        """Test getting Gemini API key."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "gemini-key"}, clear=True):
            client = LLMClient()
            assert client.api_key == "gemini-key"

    def test_get_api_key_generic(self) -> None:
        """Test getting generic LLM API key."""
        with patch.dict(os.environ, {"LLM_API_KEY": "generic-key"}, clear=True):
            client = LLMClient()
            assert client.api_key == "generic-key"

    def test_get_api_key_not_found(self) -> None:
        """Test when no API key is found."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LLMError, match="No API key found"):
                LLMClient()

    def test_detect_provider_openai(self) -> None:
        """Test detecting OpenAI provider."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(model="gpt-4")
            assert client._detect_provider() == "openai"

            client = LLMClient(model="openai-model")
            assert client._detect_provider() == "openai"

    def test_detect_provider_anthropic(self) -> None:
        """Test detecting Anthropic provider."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(model="claude-3")
            assert client._detect_provider() == "anthropic"

            client = LLMClient(model="anthropic-model")
            assert client._detect_provider() == "anthropic"

    def test_detect_provider_google(self) -> None:
        """Test detecting Google provider."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(model="gemini-pro")
            assert client._detect_provider() == "google"

            client = LLMClient(model="google-model")
            assert client._detect_provider() == "google"

    def test_detect_provider_default(self) -> None:
        """Test default provider detection."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(model="unknown-model")
            assert client._detect_provider() == "openai"

    @patch("warifuri.utils.llm.requests.post")
    def test_call_openai_api_success(self, mock_post: Mock) -> None:
        """Test successful OpenAI API call."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "AI response"}}]
            }
            mock_post.return_value = mock_response

            client = LLMClient()
            result = client._call_openai_api("system prompt", "user prompt")

            assert result == "AI response"
            mock_post.assert_called_once()

    @patch("warifuri.utils.llm.requests.post")
    def test_call_openai_api_request_error(self, mock_post: Mock) -> None:
        """Test OpenAI API request error."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            mock_post.side_effect = requests.RequestException("Network error")

            client = LLMClient()
            with pytest.raises(LLMError, match="OpenAI API error"):
                client._call_openai_api("system prompt", "user prompt")

    @patch("warifuri.utils.llm.requests.post")
    def test_call_openai_api_invalid_response(self, mock_post: Mock) -> None:
        """Test OpenAI API invalid response."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            mock_response = Mock()
            mock_response.json.return_value = {"invalid": "response"}
            mock_post.return_value = mock_response

            client = LLMClient()
            with pytest.raises(LLMError, match="Invalid OpenAI API response"):
                client._call_openai_api("system prompt", "user prompt")

    @patch("warifuri.utils.llm.requests.post")
    def test_call_anthropic_api_success(self, mock_post: Mock) -> None:
        """Test successful Anthropic API call."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            mock_response = Mock()
            mock_response.json.return_value = {
                "content": [{"text": "AI response"}]
            }
            mock_post.return_value = mock_response

            client = LLMClient(model="claude-3")
            result = client._call_anthropic_api("system prompt", "user prompt")

            assert result == "AI response"
            mock_post.assert_called_once()

    @patch("warifuri.utils.llm.requests.post")
    def test_call_anthropic_api_request_error(self, mock_post: Mock) -> None:
        """Test Anthropic API request error."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            mock_post.side_effect = requests.RequestException("Network error")

            client = LLMClient(model="claude-3")
            with pytest.raises(LLMError, match="Anthropic API error"):
                client._call_anthropic_api("system prompt", "user prompt")

    @patch("warifuri.utils.llm.requests.post")
    def test_call_anthropic_api_invalid_response(self, mock_post: Mock) -> None:
        """Test Anthropic API invalid response."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            mock_response = Mock()
            mock_response.json.return_value = {"invalid": "response"}
            mock_post.return_value = mock_response

            client = LLMClient(model="claude-3")
            with pytest.raises(LLMError, match="Invalid Anthropic API response"):
                client._call_anthropic_api("system prompt", "user prompt")

    @patch("warifuri.utils.llm.LLMClient._call_openai_api")
    def test_generate_response_openai(self, mock_call: Mock) -> None:
        """Test generate_response with OpenAI provider."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            mock_call.return_value = "OpenAI response"

            client = LLMClient(model="gpt-4")
            result = client.generate_response("system", "user")

            assert result == "OpenAI response"
            mock_call.assert_called_once_with("system", "user")

    @patch("warifuri.utils.llm.LLMClient._call_anthropic_api")
    def test_generate_response_anthropic(self, mock_call: Mock) -> None:
        """Test generate_response with Anthropic provider."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            mock_call.return_value = "Anthropic response"

            client = LLMClient(model="claude-3")
            result = client.generate_response("system", "user")

            assert result == "Anthropic response"
            mock_call.assert_called_once_with("system", "user")

    @patch("warifuri.utils.llm.LLMClient._call_openai_api")
    def test_generate_response_unknown_provider(self, mock_call: Mock) -> None:
        """Test generate_response with unknown provider defaults to OpenAI."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            mock_call.return_value = "Default response"

            client = LLMClient(model="unknown-model")
            result = client.generate_response("system", "user")

            assert result == "Default response"
            mock_call.assert_called_once_with("system", "user")


class TestLoadPromptConfig:
    """Test load_prompt_config function."""

    def test_load_prompt_config_success(self, tmp_path: Path) -> None:
        """Test loading prompt config successfully."""
        prompt_file = tmp_path / "prompt.yaml"
        prompt_content = """
model: gpt-4
temperature: 0.8
max_tokens: 2000
system_prompt: "You are a helpful assistant"
"""
        prompt_file.write_text(prompt_content)

        with patch("warifuri.utils.yaml_utils.load_yaml") as mock_load:
            mock_load.return_value = {
                "model": "gpt-4",
                "temperature": 0.8,
                "max_tokens": 2000,
                "system_prompt": "You are a helpful assistant"
            }

            config = load_prompt_config(tmp_path)

            assert config["model"] == "gpt-4"
            assert config["temperature"] == 0.8
            assert config["max_tokens"] == 2000
            assert config["system_prompt"] == "You are a helpful assistant"

    def test_load_prompt_config_with_defaults(self, tmp_path: Path) -> None:
        """Test loading prompt config with default values."""
        prompt_file = tmp_path / "prompt.yaml"
        prompt_file.write_text("system_prompt: 'Test prompt'")

        with patch("warifuri.utils.yaml_utils.load_yaml") as mock_load:
            mock_load.return_value = {"system_prompt": "Test prompt"}

            config = load_prompt_config(tmp_path)

            assert config["model"] == "gpt-3.5-turbo"  # Default
            assert config["temperature"] == 0.7  # Default
            assert config["system_prompt"] == "Test prompt"

    def test_load_prompt_config_file_not_found(self, tmp_path: Path) -> None:
        """Test loading prompt config when file doesn't exist."""
        with pytest.raises(LLMError, match="prompt.yaml not found"):
            load_prompt_config(tmp_path)

    def test_load_prompt_config_yaml_error(self, tmp_path: Path) -> None:
        """Test loading prompt config with YAML error."""
        prompt_file = tmp_path / "prompt.yaml"
        prompt_file.touch()

        with patch("warifuri.utils.yaml_utils.load_yaml") as mock_load:
            mock_load.side_effect = Exception("YAML error")

            with pytest.raises(LLMError, match="Failed to load prompt config"):
                load_prompt_config(tmp_path)


class TestSaveAiResponse:
    """Test save_ai_response function."""

    @patch("datetime.datetime")
    def test_save_ai_response(self, mock_datetime: Mock, tmp_path: Path) -> None:
        """Test saving AI response."""
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"

        response = "This is the AI response"
        save_ai_response(response, tmp_path)

        output_file = tmp_path / "output" / "response.md"
        assert output_file.exists()

        content = output_file.read_text(encoding="utf-8")
        assert "# AI Task Response" in content
        assert "**Generated**: 2024-01-01T12:00:00" in content
        assert "This is the AI response" in content


class TestLogAiError:
    """Test log_ai_error function."""

    @patch("datetime.datetime")
    def test_log_ai_error(self, mock_datetime: Mock, tmp_path: Path) -> None:
        """Test logging AI error."""
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"

        error = ValueError("Test error message")
        log_ai_error(error, tmp_path)

        error_file = tmp_path / "logs" / "failed_20240101_120000.log"
        assert error_file.exists()

        content = error_file.read_text(encoding="utf-8")
        assert "AI Task Execution Failed" in content
        assert "Timestamp: 2024-01-01T12:00:00" in content
        assert f"Task Path: {tmp_path}" in content
        assert "Error Type: ValueError" in content
        assert "Error Message: Test error message" in content
