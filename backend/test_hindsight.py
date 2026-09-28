import asyncio

from app.hindsight_client import retain_memory, recall_memories


async def main():

    print("1. Saving test memory...")

    await retain_memory(
        "TEST INCIDENT: Django API returned HTTP 500 because DATABASE_URL was missing from the production environment. The solution was to add DATABASE_URL to the deployment environment variables.",
        metadata={
            "category": "deployment",
            "technology": "Django",
            "test": True
        }
    )

    print("✅ Memory saved")

    print("\n2. Searching memory...")

    memories = await recall_memories(
        "Django API 500 DATABASE_URL deployment problem",
        limit=5
    )

    print("\nRECALLED MEMORIES:")

    for i, memory in enumerate(memories, start=1):
        print(f"\nMemory {i}:")
        print(memory["content"])

    if memories:
        print("\n🧠 HINDSIGHT WORKING!")
    else:
        print("\n⚠️ No memories returned.")


if __name__ == "__main__":
    asyncio.run(main())