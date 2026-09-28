"""Live Groq connectivity check; run manually from the backend directory."""
import asyncio

from app.config import get_settings
from app.groq_client import GroqServiceError, generate_response


async def main() -> None:
    settings = get_settings()
    print(f"Testing Groq chat completion with model {settings.groq_model!r}...")
    try:
        response = await generate_response([
            {"role": "system", "content": "Follow the user's instruction exactly."},
            {"role": "user", "content": "Reply with exactly: Groq connection successful"},
        ])
    except GroqServiceError as exc:
        print(f"Groq check failed (HTTP {exc.status_code}): {exc}")
        raise SystemExit(1) from exc

    print(f"Groq response: {response}")


if __name__ == "__main__":
    asyncio.run(main())