"""Hindsight Cloud adapter. Keep endpoint and payload changes isolated here."""
import logging
import re
from typing import Any
from urllib.parse import quote

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class HindsightServiceError(Exception):
    """Raised when the Hindsight memory service is unavailable or misconfigured."""


def _safe_error_text(response: httpx.Response, api_key: str) -> str:
    try:
        payload = response.json()
        detail = payload.get("detail", payload.get("error", payload)) if isinstance(payload, dict) else payload
        text = detail if isinstance(detail, str) else str(detail)
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


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _endpoint(base_url: str, bank_id: str, operation: str) -> str:
    if not base_url or not isinstance(base_url, str) or not base_url.strip():
        logger.error("Memory service configuration missing: HINDSIGHT_BASE_URL is not set.")
        raise HindsightServiceError("Memory service is not configured.")
    if not bank_id or not isinstance(bank_id, str) or not bank_id.strip():
        logger.error("Memory service configuration missing: HINDSIGHT_BANK_ID is not set.")
        raise HindsightServiceError("Memory service is not configured.")
    return f"{base_url.rstrip('/')}/v1/default/banks/{quote(bank_id, safe='')}/{operation}"


async def recall_memories(query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.hindsight_api_key:
        logger.error("Memory service configuration missing: HINDSIGHT_API_KEY is not set.")
        raise HindsightServiceError("Memory service is not configured.")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(18.0, connect=6.0)) as client:
            response = await client.post(
                _endpoint(settings.hindsight_base_url, settings.hindsight_bank_id, "memories/recall"),
                headers=_headers(settings.hindsight_api_key),
                json={"query": query, "max_tokens": 2048, "budget": "low"},
            )
        response.raise_for_status()
        payload = response.json()
        memories = payload.get("results", [])
        if isinstance(memories, dict):
            memories = memories.get("results", [])
        if not isinstance(memories, list):
            return []
        normalized = []
        for item in memories[:limit]:
            if isinstance(item, dict):
                content = item.get("text")
                if content:
                    normalized.append({"content": str(content)[:4000], "metadata": item.get("metadata", {})})
            elif isinstance(item, str) and item.strip():
                normalized.append({"content": item[:4000], "metadata": {}})
        return normalized
    except httpx.HTTPStatusError as exc:
        logger.error(
            "External request failed service=Hindsight operation=recall exception_type=%s http_status=%s provider_error=%s",
            type(exc).__name__,
            exc.response.status_code,
            _safe_error_text(exc.response, settings.hindsight_api_key),
        )
        raise HindsightServiceError("Memory service is temporarily unavailable.") from exc
    except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
        response = getattr(exc, "response", None)
        body = _safe_error_text(response, settings.hindsight_api_key) if isinstance(response, httpx.Response) else ""
        logger.error(
            "External request failed service=Hindsight operation=recall exception_type=%s http_status=%s provider_error=%s",
            type(exc).__name__,
            response.status_code if isinstance(response, httpx.Response) else None,
            body or str(exc)[:300],
        )
        raise HindsightServiceError("Memory service is temporarily unavailable.") from exc


async def retain_memory(content: str, *, metadata: dict[str, Any]) -> None:
    settings = get_settings()
    if not settings.hindsight_api_key:
        logger.error("Memory service configuration missing: HINDSIGHT_API_KEY is not set.")
        raise HindsightServiceError("Memory service is not configured.")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(18.0, connect=6.0)) as client:
            response = await client.post(
                _endpoint(settings.hindsight_base_url, settings.hindsight_bank_id, "memories"),
                headers=_headers(settings.hindsight_api_key),
                json={
                    "items": [
                        {
                            "content": content,
                            "context": "developer incident"
                        }
                    ]
                },
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "External request failed service=Hindsight operation=retain exception_type=%s http_status=%s provider_error=%s",
            type(exc).__name__,
            exc.response.status_code,
            _safe_error_text(exc.response, settings.hindsight_api_key),
        )
        raise HindsightServiceError("Memory service is temporarily unavailable.") from exc
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        response = getattr(exc, "response", None)
        body = _safe_error_text(response, settings.hindsight_api_key) if isinstance(response, httpx.Response) else ""
        logger.error(
            "External request failed service=Hindsight operation=retain exception_type=%s http_status=%s provider_error=%s",
            type(exc).__name__,
            response.status_code if isinstance(response, httpx.Response) else None,
            body or str(exc)[:300],
        )
        raise HindsightServiceError("Memory service is temporarily unavailable.") from exc
