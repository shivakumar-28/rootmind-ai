"""Manual Hindsight integration test; run from backend with configured .env."""
import asyncio

from app.hindsight_client import recall_memories, retain_memory

TEST_INCIDENT = (
    "DevMemory integration test incident: A React frontend at http://localhost:5173 "
    "was blocked by a Django backend CORS policy. The error was a browser CORS "
    "preflight rejection. The fix was to allow the exact frontend origin in Django "
    "CORS_ALLOWED_ORIGINS. This test incident is synthetic and was successfully resolved."
)
RECALL_QUERY = "What was the previous Django CORS preflight error for the React app on localhost:5173, and what fixed it?"
EXPECTED_TERMS = ("localhost:5173", "CORS", "Django")


async def main() -> None:
    print("Retaining a synthetic CORS incident in Hindsight...")
    await retain_memory(TEST_INCIDENT, metadata={"category": "Deployment", "source": "manual-integration-test"})
    print("Retain request completed.")

    print("Recalling the incident with a related CORS question...")
    memories = await recall_memories(RECALL_QUERY, limit=3)
    for index, memory in enumerate(memories, start=1):
        print(f"Memory {index}: {memory['content']}")

    combined = "\n".join(memory.get("content", "") for memory in memories).casefold()
    if not memories or not any(term.casefold() in combined for term in EXPECTED_TERMS):
        raise AssertionError("Hindsight recall did not return the stored CORS incident.")
    print(f"PASS: recalled {len(memories)} memory/memories including the test incident.")


if __name__ == "__main__":
    asyncio.run(main())
