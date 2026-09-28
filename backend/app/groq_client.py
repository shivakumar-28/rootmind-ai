import json
import logging
import re
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class GroqServiceError(Exception):
    """A safe client-facing message and HTTP status for an AI service failure."""

    def __init__(self, message: str, *, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


def _safe_provider_message(response: httpx.Response, api_key: str) -> str:
    try:
        payload = response.json()
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        message = error.get("message", error) if isinstance(error, dict) else error
        text = message if isinstance(message, str) else json.dumps(message)
    except (ValueError, TypeError):
        text = response.text

    text = text.replace(api_key, "[REDACTED]") if api_key else text
    text = re.sub(r"(?i)bearer\s+[^\s,;]+", "Bearer [REDACTED]", text)
    text = re.sub(
        r"(?i)(api[_ -]?key|authorization|token|password|secret)(\s*[:=]\s*)[^\s,;]+",
        r"\1\2[REDACTED]",
        text,
    )
    return " ".join(text.split())[:500] or "No provider error message returned."


async def generate_response(
    messages: list[dict[str, str]],
    *,
    response_format: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    if not settings.groq_api_key:
        logger.error("AI service configuration missing: GROQ_API_KEY is not set.")
        raise GroqServiceError("AI service is not configured. Check GROQ_API_KEY in the backend environment.")

    payload: dict[str, Any] = {
        "model": settings.groq_model,
        "messages": messages,
        "temperature": 0.2,
        "max_completion_tokens": 500,
    }
    if response_format:
        payload["response_format"] = response_format

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(35.0, connect=8.0)) as client:
            result = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json=payload,
            )
        if result.is_error:
            status = result.status_code
            provider_message = _safe_provider_message(result, settings.groq_api_key)
            logger.error(
                "External request failed service=Groq exception_type=HTTPStatusError http_status=%s model=%s request_parameters=%s provider_error=%s",
                status,
                settings.groq_model,
                sorted(payload.keys()),
                provider_message,
            )
            if status in (401, 403):
                raise GroqServiceError("AI service authentication failed. Check GROQ_API_KEY.", status_code=503)
            if status == 429:
                raise GroqServiceError("AI service is temporarily rate limited. Please try again shortly.", status_code=503)
            if status in (400, 404, 422):
                raise GroqServiceError("AI service rejected the request configuration. Check GROQ_MODEL and request settings.", status_code=502)
            raise GroqServiceError("AI service provider returned an error. Please try again later.", status_code=502 if status < 500 else 503)

        try:
            data = result.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            logger.error(
                "Invalid response from service=Groq exception_type=%s http_status=%s",
                type(exc).__name__,
                result.status_code,
            )
            raise GroqServiceError("AI service returned an invalid response.", status_code=502) from exc
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        if not isinstance(content, str) or not content.strip():
            logger.error("Invalid response from service=Groq exception_type=EmptyContent http_status=%s", result.status_code)
            raise GroqServiceError("AI service returned an empty response.", status_code=502)
        return content.strip()
    except GroqServiceError:
        raise
    except httpx.TimeoutException as exc:
        logger.error("External request failed service=Groq exception_type=%s detail=%s", type(exc).__name__, str(exc)[:300])
        raise GroqServiceError("AI service timed out. Please try again.", status_code=504) from exc
    except httpx.HTTPError as exc:
        logger.error("External request failed service=Groq exception_type=%s detail=%s", type(exc).__name__, str(exc)[:300])
        raise GroqServiceError("AI service is unreachable. Please try again shortly.", status_code=503) from exc
