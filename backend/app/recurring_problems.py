from collections import Counter, defaultdict
from typing import Any


def build_recurring_problems(incidents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for incident in incidents:
        groups[incident.get("category") or "Other"].append(incident)

    results = []
    for category, items in groups.items():
        technologies = Counter(item["technology"] for item in items if item.get("technology"))
        errors = Counter(item["error"] for item in items if item.get("error"))
        solutions = list(dict.fromkeys(item["solution"] for item in items if item.get("solution")))[:3]
        results.append({
            "category": category,
            "count": len(items),
            "technologies": [name for name, _ in technologies.most_common(4)],
            "common_errors": [name for name, _ in errors.most_common(4)],
            "successful_solutions": solutions,
        })
    return sorted(results, key=lambda item: (-item["count"], item["category"].casefold()))
