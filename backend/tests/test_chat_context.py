import asyncio
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID

from app import agent, main, storage
from app.models.schemas import ChatRequest, Incident


class ChatContextTests(unittest.TestCase):
    def test_malformed_incident_analysis_does_not_abort_followup_response(self):
        with TemporaryDirectory() as directory:
            settings = SimpleNamespace(database_path=str(Path(directory) / "malformed.db"))
            with patch.object(storage, "get_settings", return_value=settings):
                storage.initialize_storage()
                conversation_id = str(UUID(int=12345))
                storage.save_conversation_message(
                    conversation_id,
                    "user",
                    "The request is returning 503 after CORS checks.",
                )
                storage.save_conversation_message(
                    conversation_id,
                    "assistant",
                    "Check the upstream service and backend logs.",
                )

                async def recall(*args, **kwargs):
                    return []

                with (
                    patch.object(main, "analyze_incident", new=AsyncMock(side_effect=ValueError("bad JSON"))),
                    patch.object(main, "recall_memories", new=AsyncMock(side_effect=recall)),
                    patch.object(agent, "generate_response", new=AsyncMock(return_value="Check the API logs for the 503 source.")) as generate,
                ):
                    result = asyncio.run(main.chat(ChatRequest(
                        conversation_id=conversation_id,
                        message="What should I check next?",
                    )))

                self.assertEqual(result.response, "Check the API logs for the 503 source.")
                self.assertFalse(result.incident_detected)
                self.assertEqual(result.conversation_id, conversation_id)
                sent_messages = generate.await_args.args[0]
                self.assertEqual([item["role"] for item in sent_messages], ["system", "user", "assistant", "user"])
                self.assertEqual(sent_messages[-3]["content"], "The request is returning 503 after CORS checks.")
                self.assertEqual(sent_messages[-1]["content"], "What should I check next?")

    def test_followups_use_persisted_roles_in_order_with_memories_as_separate_context(self):
        with TemporaryDirectory() as directory:
            settings = SimpleNamespace(database_path=str(Path(directory) / "context.db"))
            with patch.object(storage, "get_settings", return_value=settings):
                storage.initialize_storage()
                responses = [
                    "Check the CORS middleware allow_origins.",
                    "Check the browser Network tab.",
                    "A 503 means the backend or an upstream dependency failed.",
                    "Inspect the backend log for the error at the failing request.",
                    "This is a new conversation.",
                ]
                memory = {"content": "A previous FastAPI CORS incident was caused by an incorrect origin."}
                recalled_query: list[str] = []

                async def recall(query: str, *, limit: int = 5):
                    recalled_query.append(query)
                    return [memory]

                with (
                    patch.object(main, "analyze_incident", new=AsyncMock(return_value=(False, Incident()))),
                    patch.object(main, "recall_memories", new=AsyncMock(side_effect=recall)),
                    patch.object(agent, "generate_response", new=AsyncMock(side_effect=responses)) as generate,
                ):
                    first = asyncio.run(main.chat(ChatRequest(message="I have a CORS error in my FastAPI backend.")))
                    self.assertTrue(first.conversation_id)
                    UUID(first.conversation_id)
                    second = asyncio.run(main.chat(ChatRequest(
                        conversation_id=first.conversation_id,
                        message="I already checked the CORS middleware.",
                    )))
                    third = asyncio.run(main.chat(ChatRequest(
                        conversation_id=first.conversation_id,
                        message="The request is returning 503.",
                    )))
                    fourth = asyncio.run(main.chat(ChatRequest(
                        conversation_id=first.conversation_id,
                        message="What should I check next?",
                    )))
                    fresh = asyncio.run(main.chat(ChatRequest(
                        conversation_id="not-a-valid-uuid",
                        message="Start a different conversation.",
                    )))

                self.assertEqual(second.conversation_id, first.conversation_id)
                self.assertEqual(third.conversation_id, first.conversation_id)
                self.assertEqual(fourth.conversation_id, first.conversation_id)
                self.assertNotEqual(fresh.conversation_id, first.conversation_id)
                UUID(fresh.conversation_id)

                fourth_prompt = generate.await_args_list[3].args[0]
                self.assertEqual(
                    [message["role"] for message in fourth_prompt],
                    ["system", "user", "assistant", "user", "assistant", "user", "assistant", "user"],
                )
                self.assertEqual(
                    [message["content"] for message in fourth_prompt[1:]],
                    [
                        "I have a CORS error in my FastAPI backend.",
                        responses[0],
                        "I already checked the CORS middleware.",
                        responses[1],
                        "The request is returning 503.",
                        responses[2],
                        "What should I check next?",
                    ],
                )
                system_context = fourth_prompt[0]["content"]
                self.assertIn(memory["content"], system_context)
                self.assertIn("Current conversation history", system_context)
                self.assertEqual(recalled_query[3], "What should I check next?")

                fresh_prompt = generate.await_args_list[4].args[0]
                self.assertEqual([message["role"] for message in fresh_prompt], ["system", "user"])
                self.assertNotIn("I have a CORS error", str(fresh_prompt))

                stored = storage.get_conversation_messages(first.conversation_id)
                self.assertEqual(len(stored), 8)
                self.assertEqual([entry["role"] for entry in stored], ["user", "assistant"] * 4)
                self.assertEqual(stored[-2]["content"], "What should I check next?")
                self.assertEqual(stored[-1]["content"], responses[3])
                self.assertEqual(first.incident_detected, False)
                self.assertEqual(fourth.memory_used, True)

    def test_history_sent_to_model_is_bounded_without_pruning_stored_history(self):
        history = [
            {"role": "user", "content": f"message-{index}: " + ("x" * 3000)}
            for index in range(agent.MAX_HISTORY_MESSAGES + 4)
        ]
        bounded = agent._bounded_history(history)
        self.assertLessEqual(len(bounded), agent.MAX_HISTORY_MESSAGES)
        self.assertLessEqual(sum(len(item["content"]) for item in bounded), agent.MAX_HISTORY_CHARS + 40)
        self.assertIn(f"message-{len(history) - 1}", bounded[-1]["content"])
        self.assertNotIn("message-0:", str(bounded))


if __name__ == "__main__":
    unittest.main()
