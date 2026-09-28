import json
import re
from typing import Any

from app.groq_client import generate_response
from app.models.schemas import Incident

CATEGORIES = [
    "Database", "API", "Deployment", "Authentication", "Frontend", "Backend",
    "Git/GitHub", "Environment Configuration", "Performance", "Dependency/Package",
    "Cloud/Infrastructure", "Other",
]

ANALYSIS_SYSTEM_PROMPT = """Analyze whether the user's latest message describes a concrete software development problem or incident. Extract only facts explicitly stated or strongly evidenced. Never infer a root cause from a symptom alone. For example, an HTTP 500 by itself does not establish a database failure.

Return exactly one valid JSON object and nothing else (no Markdown fences or commentary) with these keys: incident_detected (boolean), problem, category, technology, error, root_cause, solution, outcome. Incident fields must be strings or null. category must be one of: Database, API, Deployment, Authentication, Frontend, Backend, Git/GitHub, Environment Configuration, Performance, Dependency/Package, Cloud/Infrastructure, Other. Only set incident_detected true for a technical problem, error, or explicit troubleshooting request. Unknown values are null."""


def _parse_json(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("Could not parse analyzer response")
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Analyzer response must be a JSON object")
    return parsed


async def analyze_incident(message: str) -> tuple[bool, Incident]:
    content = await generate_response(
        [
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]
    )
    result = _parse_json(content)
    incident = Incident(
        problem=_text_or_none(result.get("problem")),
        category=_valid_category(result.get("category")),
        technology=_text_or_none(result.get("technology")),
        error=_text_or_none(result.get("error")),
        root_cause=_text_or_none(result.get("root_cause")),
        solution=_text_or_none(result.get("solution")),
        outcome=_text_or_none(result.get("outcome")),
    )
    return bool(result.get("incident_detected")), incident


def _text_or_none(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip() or value.strip().lower() in {"unknown", "null", "n/a"}:
        return None
    return value.strip()[:2000]


def _valid_category(value: Any) -> str | None:
    category = _text_or_none(value)
    if not category:
        return None
    return next((item for item in CATEGORIES if item.casefold() == category.casefold()), "Other")
