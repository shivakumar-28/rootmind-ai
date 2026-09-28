import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

from fastapi import HTTPException

from app import main
from app import agent
from app import incident_analyzer
from app.models.schemas import ChatRequest, Incident
from app.recurring_problems import build_recurring_problems
from app.storage import initialize_storage, list_incidents, save_incident


class ChatFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_incident_analyzer_requests_json_without_groq_json_mode(self):
        generated_json = (
            '{"incident_detected": true, "problem": "CORS blocks the frontend", '
            '"category": "API", "technology": "React and Django", '
            '"error": "CORS blocked request", "root_cause": null, '
            '"solution": null, "outcome": null}'
        )
        with patch.object(
            incident_analyzer,
            "generate_response",
            new=AsyncMock(return_value=generated_json),
        ) as generate:
            detected, incident = await incident_analyzer.analyze_incident(
                "React request to Django is blocked by CORS"
            )

        self.assertTrue(detected)
        self.assertEqual(incident.technology, "React and Django")
        self.assertIn("exactly one valid JSON object", generate.await_args.args[0][0]["content"])
        self.assertEqual(generate.await_args.args[0][1]["content"], "React request to Django is blocked by CORS")
        self.assertNotIn("response_format", generate.await_args.kwargs)

    async def test_incident_uses_and_retains_hindsight_memory(self):
        incident = Incident(
            problem="Django API returns HTTP 500 after deployment",
            category="Deployment",
            technology="Django",
            error="HTTP 500",
            root_cause="DATABASE_URL was missing",
            solution="Added DATABASE_URL to production environment",
            outcome="API recovered",
        )
        recalled = [{"content": "Prior Django deploy failed because DATABASE_URL was missing."}]
        with (
            patch.object(main, "get_conversation_messages", return_value=[]),
            patch.object(main, "save_conversation_message"),
            patch.object(main, "save_incident"),
            patch.object(main, "analyze_incident", new=AsyncMock(return_value=(True, incident))),
            patch.object(main, "recall_memories", new=AsyncMock(return_value=recalled)) as recall,
            patch.object(main, "respond_to_problem", new=AsyncMock(return_value="Check DATABASE_URL first.")) as respond,
            patch.object(main, "retain_memory", new=AsyncMock()) as retain,
        ):
            result = await main.chat(ChatRequest(message="My Django API returns 500 again"))

        self.assertTrue(result.incident_detected)
        self.assertTrue(result.memory_used)
        self.assertEqual(result.relevant_memories, recalled)
        self.assertEqual(result.response, "Check DATABASE_URL first.")
        self.assertIsNotNone(result.conversation_id)
        recall.assert_awaited_once()
        self.assertEqual(recall.await_args.kwargs["limit"], 3)
        self.assertEqual(recall.await_args.args[0], "My Django API returns 500 again")
        respond.assert_awaited_once()
        retain.assert_awaited_once()
        retained_text = retain.await_args.args[0]
        for expected in ("Problem:", "Technology:", "Error:", "Root Cause:", "Solution:", "Outcome:"):
            self.assertIn(expected, retained_text)

    async def test_memory_question_recalls_even_when_latest_message_is_not_an_incident(self):
        recalled = [{"content": "Previous CORS incident: React at localhost:5173 was blocked by Django CORS settings."}]
        with (
            patch.object(main, "get_conversation_messages", return_value=[]),
            patch.object(main, "save_conversation_message"),
            patch.object(main, "analyze_incident", new=AsyncMock(return_value=(False, Incident()))),
            patch.object(main, "recall_memories", new=AsyncMock(return_value=recalled)) as recall,
            patch.object(main, "respond_to_problem", new=AsyncMock(return_value="A previous incident involved CORS between React and Django.")) as respond,
        ):
            result = await main.chat(ChatRequest(message="Do you remember any previous CORS issue I had?"))

        recall.assert_awaited_once_with("Do you remember any previous CORS issue I had?", limit=3)
        self.assertEqual(respond.await_args.args[2], recalled)
        self.assertFalse(result.incident_detected)
        self.assertTrue(result.memory_used)
        self.assertEqual(result.relevant_memories, recalled)
        self.assertIn("previous incident", result.response)

    async def test_non_incident_memory_recall_outage_still_returns_ai_response(self):
        with (
            patch.object(main, "get_conversation_messages", return_value=[]),
            patch.object(main, "save_conversation_message"),
            patch.object(main, "analyze_incident", new=AsyncMock(return_value=(False, Incident()))),
            patch.object(main, "recall_memories", new=AsyncMock(side_effect=main.HindsightServiceError("offline"))),
            patch.object(main, "respond_to_problem", new=AsyncMock(return_value="I can help with that.")),
        ):
            result = await main.chat(ChatRequest(message="Do you remember a CORS issue?"))

        self.assertEqual(result.response, "I can help with that.")
        self.assertEqual(result.memory_status, "unavailable")
        self.assertFalse(result.memory_used)

    async def test_memory_recall_outage_does_not_block_ai_or_retention(self):
        incident = Incident(problem="API returns 500", category="API", error="HTTP 500")
        with (
            patch.object(main, "get_conversation_messages", return_value=[]),
            patch.object(main, "save_conversation_message"),
            patch.object(main, "save_incident"),
            patch.object(main, "analyze_incident", new=AsyncMock(return_value=(True, incident))),
            patch.object(main, "recall_memories", new=AsyncMock(side_effect=main.HindsightServiceError("offline"))),
            patch.object(main, "respond_to_problem", new=AsyncMock(return_value="Please share the traceback.")),
            patch.object(main, "retain_memory", new=AsyncMock()) as retain,
        ):
            result = await main.chat(ChatRequest(message="My API returns 500"))

        self.assertEqual(result.response, "Please share the traceback.")
        self.assertEqual(result.memory_status, "unavailable")
        self.assertFalse(result.memory_used)
        retain.assert_awaited_once()

    async def test_agent_limits_and_labels_memory_context(self):
        memories = [
            {"content": "x" * 1500, "metadata": {"secret": "internal"}}
            for index in range(5)
        ]
        with patch.object(agent, "generate_response", new=AsyncMock(return_value="What error are you seeing?")) as generate:
            response = await agent.respond_to_problem(
                "My Django deployment is failing",
                Incident(problem="Django deployment fails", category="Deployment", technology="Django"),
                memories,
            )

        prompt = generate.await_args.args[0]
        system_prompt = prompt[0]["content"]
        user_prompt = prompt[-1]["content"]
        self.assertIn("100–200 words maximum", system_prompt)
        self.assertIn("unless the developer explicitly asks", system_prompt)
        self.assertIn("Treat retrieved memories as candidate context", system_prompt)
        self.assertIn("Never claim that no incident is stored when relevant memory context is present", system_prompt)
        self.assertIn("explicitly acknowledge that previous incident", system_prompt)
        self.assertIn("Candidate previous incident 1", system_prompt)
        self.assertIn("Candidate previous incident 3", system_prompt)
        self.assertNotIn("Candidate previous incident 4", system_prompt)
        self.assertNotIn("not-for-client", system_prompt)
        self.assertIn("x" * agent.MAX_MEMORY_CHARS, system_prompt)
        self.assertNotIn("x" * 1201, system_prompt)
        self.assertEqual(user_prompt, "My Django deployment is failing")
        self.assertEqual(response, "What error are you seeing?")

    async def test_agent_does_not_imply_memory_when_none_was_recalled(self):
        with patch.object(agent, "generate_response", new=AsyncMock(return_value="What error are you seeing?")) as generate:
            await agent.respond_to_problem(
                "My Django deployment is failing",
                Incident(problem="Django deployment fails", category="Deployment", technology="Django"),
                [],
            )

        system_prompt = generate.await_args.args[0][0]["content"]
        user_prompt = generate.await_args.args[0][-1]["content"]
        self.assertIn("If no supplied memory is relevant, do not imply", system_prompt)
        self.assertIn("No previous memories were retrieved", system_prompt)
        self.assertEqual(user_prompt, "My Django deployment is failing")

    async def test_rejects_whitespace_only_message(self):
        with self.assertRaises(HTTPException) as raised:
            await main.chat(ChatRequest(message="   "))
        self.assertEqual(raised.exception.status_code, 422)


class RecurringProblemsTests(unittest.TestCase):
    def test_groups_incidents_and_keeps_unique_resolutions(self):
        result = build_recurring_problems([
            {"category": "Deployment", "technology": "Django", "error": "HTTP 500", "solution": "Set DATABASE_URL"},
            {"category": "Deployment", "technology": "Django", "error": "HTTP 500", "solution": "Set DATABASE_URL"},
            {"category": "Database", "technology": "PostgreSQL", "error": None, "solution": None},
        ])
        self.assertEqual(result[0]["category"], "Deployment")
        self.assertEqual(result[0]["count"], 2)
        self.assertEqual(result[0]["technologies"], ["Django"])
        self.assertEqual(result[0]["successful_solutions"], ["Set DATABASE_URL"])
        self.assertEqual(result[1]["category"], "Database")

    def test_follow_up_updates_incident_instead_of_double_counting(self):
        with TemporaryDirectory() as directory, patch(
            "app.storage.get_settings",
            return_value=SimpleNamespace(database_path=str(Path(directory) / "test.db")),
        ):
            initialize_storage()
            save_incident("conversation-1", {
                "problem": "Django returns HTTP 500", "category": "API", "technology": "Django", "error": "HTTP 500",
            })
            save_incident("conversation-1", {
                "problem": "Django returns HTTP 500", "category": "Deployment", "technology": "Django",
                "root_cause": "Missing DATABASE_URL", "solution": "Set DATABASE_URL",
            })
            incidents = list_incidents()

        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["category"], "Deployment")
        self.assertEqual(incidents[0]["error"], "HTTP 500")
        self.assertEqual(incidents[0]["root_cause"], "Missing DATABASE_URL")


if __name__ == "__main__":
    unittest.main()
