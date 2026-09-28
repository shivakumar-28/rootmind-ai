import logging
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app import groq_client, main
from app.groq_client import GroqServiceError
from app import hindsight_client
from app.hindsight_client import HindsightServiceError
from app.models.schemas import Incident


GROQ_KEY = "gsk_test-secret-that-must-not-be-logged"
SETTINGS = SimpleNamespace(groq_api_key=GROQ_KEY, groq_model="openai/gpt-oss-120b")


def groq_response(status_code=200, *, payload=None, text=None):
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    if text is not None:
        return httpx.Response(status_code, text=text, request=request)
    return httpx.Response(
        status_code,
        json=payload if payload is not None else {
            "choices": [{"message": {"content": "Please share the traceback."}}]
        },
        request=request,
    )


class GroqClientFailureTests(unittest.IsolatedAsyncioTestCase):
    async def run_with_groq_response(self, response=None, *, error=None):
        fake_client = AsyncMock()
        fake_client.__aenter__.return_value = fake_client
        fake_client.__aexit__.return_value = False
        if error:
            fake_client.post.side_effect = error
        else:
            fake_client.post.return_value = response
        with (
            patch.object(groq_client, "get_settings", return_value=SETTINGS),
            patch.object(groq_client.httpx, "AsyncClient", return_value=fake_client),
        ):
            try:
                result = await groq_client.generate_response([{"role": "user", "content": "hello"}])
            except GroqServiceError as exc:
                return exc, fake_client
        return result, fake_client

    async def test_success_uses_configured_model_and_completion_limit(self):
        result, fake_client = await self.run_with_groq_response(groq_response())
        self.assertEqual(result, "Please share the traceback.")
        request_payload = fake_client.post.await_args.kwargs["json"]
        self.assertEqual(request_payload["model"], "openai/gpt-oss-120b")
        self.assertEqual(request_payload["max_completion_tokens"], 500)
        self.assertNotIn("max_tokens", request_payload)
        self.assertEqual(
            fake_client.post.await_args.kwargs["headers"]["Authorization"],
            f"Bearer {GROQ_KEY}",
        )

    async def test_json_mode_is_forwarded_without_changing_chat_messages(self):
        response_format = {"type": "json_object"}
        messages = [
            {"role": "system", "content": "Return structured JSON."},
            {"role": "user", "content": "Analyze this incident."},
        ]
        fake_client = AsyncMock()
        fake_client.__aenter__.return_value = fake_client
        fake_client.__aexit__.return_value = False
        fake_client.post.return_value = groq_response()
        with (
            patch.object(groq_client, "get_settings", return_value=SETTINGS),
            patch.object(groq_client.httpx, "AsyncClient", return_value=fake_client),
        ):
            await groq_client.generate_response(messages, response_format=response_format)

        payload = fake_client.post.await_args.kwargs["json"]
        self.assertEqual(payload["model"], "openai/gpt-oss-120b")
        self.assertEqual(payload["messages"], messages)
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(payload["temperature"], 0.2)
        self.assertEqual(payload["max_completion_tokens"], 500)
        self.assertNotIn("reasoning_effort", payload)

    async def test_missing_groq_key_is_a_clear_configuration_error(self):
        with (
            patch.object(groq_client, "get_settings", return_value=SimpleNamespace(groq_api_key="", groq_model="openai/gpt-oss-120b")),
            patch.object(groq_client.httpx, "AsyncClient") as client,
            self.assertLogs(groq_client.__name__, level="ERROR") as captured,
        ):
            with self.assertRaises(GroqServiceError) as raised:
                await groq_client.generate_response([{"role": "user", "content": "hello"}])
        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("GROQ_API_KEY", str(raised.exception))
        client.assert_not_called()
        self.assertNotIn(GROQ_KEY, "\n".join(captured.output))

    async def test_401_is_diagnosed_and_safe_for_client(self):
        response = groq_response(401, payload={"error": {"message": f"Invalid key {GROQ_KEY}"}})
        with self.assertLogs(groq_client.__name__, level="ERROR") as captured:
            error, _ = await self.run_with_groq_response(response)
        self.assertIsInstance(error, GroqServiceError)
        self.assertEqual(error.status_code, 503)
        self.assertIn("authentication", str(error).lower())
        self.assertIn("http_status=401", "\n".join(captured.output))
        self.assertIn("model=openai/gpt-oss-120b", "\n".join(captured.output))
        self.assertIn("request_parameters=", "\n".join(captured.output))
        self.assertNotIn(GROQ_KEY, "\n".join(captured.output))

    async def test_429_is_diagnosed_as_rate_limit(self):
        with self.assertLogs(groq_client.__name__, level="ERROR") as captured:
            error, _ = await self.run_with_groq_response(groq_response(429, payload={"error": {"message": "Too many requests"}}))
        self.assertEqual(error.status_code, 503)
        self.assertIn("rate limited", str(error))
        self.assertIn("http_status=429", "\n".join(captured.output))

    async def test_provider_5xx_is_logged_and_mapped_to_unavailable(self):
        with self.assertLogs(groq_client.__name__, level="ERROR") as captured:
            error, _ = await self.run_with_groq_response(groq_response(503, payload={"error": {"message": "upstream unavailable"}}))
        self.assertEqual(error.status_code, 503)
        self.assertIn("upstream unavailable", "\n".join(captured.output))

    async def test_bad_provider_request_is_mapped_to_bad_gateway(self):
        with self.assertLogs(groq_client.__name__, level="ERROR") as captured:
            error, _ = await self.run_with_groq_response(groq_response(400, payload={"error": {"message": "invalid model request"}}))
        self.assertEqual(error.status_code, 502)
        self.assertIn("invalid model request", "\n".join(captured.output))

    async def test_timeout_is_mapped_to_gateway_timeout(self):
        with self.assertLogs(groq_client.__name__, level="ERROR") as captured:
            error, _ = await self.run_with_groq_response(error=httpx.ReadTimeout("provider timed out"))
        self.assertEqual(error.status_code, 504)
        self.assertIn("timed out", str(error))
        self.assertIn("ReadTimeout", "\n".join(captured.output))

    async def test_invalid_json_response_has_specific_safe_error(self):
        with self.assertLogs(groq_client.__name__, level="ERROR") as captured:
            error, _ = await self.run_with_groq_response(groq_response(200, text="not json"))
        self.assertEqual(error.status_code, 502)
        self.assertIn("invalid response", str(error))
        self.assertIn("JSONDecodeError", "\n".join(captured.output))


class HindsightClientFailureTests(unittest.IsolatedAsyncioTestCase):
    API_KEY = "hs_test-secret-that-must-not-be-logged"
    SETTINGS = SimpleNamespace(
        hindsight_api_key=API_KEY,
        hindsight_base_url="https://memory.example.test",
        hindsight_bank_id="devmemory-ai",
    )

    async def call_hindsight(self, *, operation, response=None, error=None):
        fake_client = AsyncMock()
        fake_client.__aenter__.return_value = fake_client
        fake_client.__aexit__.return_value = False
        if error:
            fake_client.post.side_effect = error
        else:
            fake_client.post.return_value = response
        with (
            patch.object(hindsight_client, "get_settings", return_value=self.SETTINGS),
            patch.object(hindsight_client.httpx, "AsyncClient", return_value=fake_client),
        ):
            if operation == "recall":
                result = await hindsight_client.recall_memories("Django deployment", limit=3)
            else:
                result = await hindsight_client.retain_memory("Django deployment", metadata={"category": "Deployment"})
        return result, fake_client

    async def test_recall_http_failure_logs_status_and_redacts_secret(self):
        request = httpx.Request("POST", "https://memory.example.test/recall")
        response = httpx.Response(
            401,
            json={"detail": f"Invalid credential {self.API_KEY}"},
            request=request,
        )
        with self.assertLogs(hindsight_client.__name__, level="ERROR") as captured:
            with self.assertRaises(HindsightServiceError) as raised:
                await self.call_hindsight(operation="recall", response=response)
        logs = "\n".join(captured.output)
        self.assertEqual(str(raised.exception), "Memory service is temporarily unavailable.")
        self.assertIn("service=Hindsight operation=recall", logs)
        self.assertIn("http_status=401", logs)
        self.assertIn("[REDACTED]", logs)
        self.assertNotIn(self.API_KEY, logs)

    async def test_retain_http_failure_logs_provider_detail_without_exposing_it_to_client(self):
        request = httpx.Request("POST", "https://memory.example.test/retain")
        response = httpx.Response(503, json={"detail": "memory database is unavailable"}, request=request)
        with self.assertLogs(hindsight_client.__name__, level="ERROR") as captured:
            with self.assertRaises(HindsightServiceError) as raised:
                await self.call_hindsight(operation="retain", response=response)
        logs = "\n".join(captured.output)
        self.assertEqual(str(raised.exception), "Memory service is temporarily unavailable.")
        self.assertIn("service=Hindsight operation=retain", logs)
        self.assertIn("http_status=503", logs)
        self.assertIn("memory database is unavailable", logs)
        self.assertNotIn(self.API_KEY, logs)

    async def test_recall_timeout_logs_exception_and_degrades_as_service_error(self):
        with self.assertLogs(hindsight_client.__name__, level="ERROR") as captured:
            with self.assertRaises(HindsightServiceError):
                await self.call_hindsight(operation="recall", error=httpx.ReadTimeout("memory request timed out"))
        logs = "\n".join(captured.output)
        self.assertIn("service=Hindsight operation=recall", logs)
        self.assertIn("ReadTimeout", logs)
        self.assertNotIn(self.API_KEY, logs)

    async def test_recall_uses_existing_route_payload_and_parses_results(self):
        request = httpx.Request("POST", "https://memory.example.test/recall")
        response = httpx.Response(
            200,
            json={"results": [{"text": "Earlier Django incident", "metadata": {"category": "Deployment"}}]},
            request=request,
        )
        result, fake_client = await self.call_hindsight(operation="recall", response=response)
        self.assertEqual(result, [{"content": "Earlier Django incident", "metadata": {"category": "Deployment"}}])
        call = fake_client.post.await_args
        self.assertEqual(str(call.args[0]), "https://memory.example.test/v1/default/banks/devmemory-ai/memories/recall")
        self.assertEqual(call.kwargs["json"]["query"], "Django deployment")
        self.assertEqual(call.kwargs["json"]["budget"], "low")
        self.assertEqual(call.kwargs["headers"]["Authorization"], f"Bearer {self.API_KEY}")

    async def test_retain_uses_existing_route_payload(self):
        request = httpx.Request("POST", "https://memory.example.test/retain")
        response = httpx.Response(200, json={"success": True}, request=request)
        _, fake_client = await self.call_hindsight(operation="retain", response=response)
        call = fake_client.post.await_args
        self.assertEqual(str(call.args[0]), "https://memory.example.test/v1/default/banks/devmemory-ai/memories")
        self.assertEqual(call.kwargs["json"]["items"][0]["content"], "Django deployment")
        self.assertEqual(call.kwargs["json"]["items"][0]["context"], "developer incident")


class ChatEndpointFailureTests(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch.object(main, "get_conversation_messages", return_value=[]),
            patch.object(main, "save_conversation_message"),
            patch.object(main, "save_incident"),
            patch.object(main, "analyze_incident", new=AsyncMock(return_value=(
                True,
                Incident(problem="Test incident", category="Deployment", technology="Django", error="failed"),
            ))),
            patch.object(main, "recall_memories", new=AsyncMock(return_value=[
                {"content": "A similar earlier incident was resolved.", "metadata": {"private": "not-for-client"}}
            ])),
            patch.object(main, "respond_to_problem", new=AsyncMock(return_value="What error do you see?")),
            patch.object(main, "retain_memory", new=AsyncMock()),
        ]
        self.mocks = [item.start() for item in self.patches]
        self.addCleanup(self.stop_patches)
        self.client = TestClient(main.app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def stop_patches(self):
        for item in reversed(self.patches):
            item.stop()

    def test_chat_success_preserves_json_contract_and_hides_memory_metadata(self):
        response = self.client.post("/api/chat", json={"message": "My Django deployment is failing"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            set(payload),
            {"response", "conversation_id", "incident_detected", "category", "memory_used", "memory_status", "relevant_memories", "incident"},
        )
        self.assertEqual(payload["response"], "What error do you see?")
        self.assertTrue(payload["incident_detected"])
        self.assertTrue(payload["memory_used"])
        self.assertNotIn("private", response.text)
        self.assertEqual(payload["relevant_memories"], [{"content": "A similar earlier incident was resolved."}])

    def test_hindsight_recall_failure_still_returns_ai_and_attempts_retain(self):
        self.mocks[4].side_effect = HindsightServiceError("offline")
        response = self.client.post("/api/chat", json={"message": "My Django deployment is failing"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["response"], "What error do you see?")
        self.assertEqual(payload["memory_status"], "unavailable")
        self.assertEqual(payload["relevant_memories"], [])
        self.mocks[6].assert_awaited_once()

    def test_hindsight_retain_failure_keeps_successful_response(self):
        self.mocks[6].side_effect = HindsightServiceError("offline")
        response = self.client.post("/api/chat", json={"message": "My Django deployment is failing"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], "What error do you see?")
        self.assertEqual(response.json()["memory_status"], "unavailable")

    def test_unexpected_retention_exception_is_logged_but_response_succeeds(self):
        self.mocks[6].side_effect = RuntimeError("local retain adapter bug")
        with self.assertLogs(main.__name__, level=logging.ERROR) as captured:
            response = self.client.post("/api/chat", json={"message": "My Django deployment is failing"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], "What error do you see?")
        self.assertEqual(response.json()["memory_status"], "unavailable")
        self.assertIn("Unexpected retention failure", "\n".join(captured.output))

    def test_groq_error_preserves_safe_status_and_message(self):
        self.mocks[3].side_effect = GroqServiceError("AI service authentication failed. Check GROQ_API_KEY.", status_code=503)
        with self.assertLogs(main.__name__, level=logging.ERROR):
            response = self.client.post("/api/chat", json={"message": "My Django deployment is failing"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("Check GROQ_API_KEY", response.json()["detail"])
        self.assertNotIn("gsk_", response.text)

    def test_unexpected_application_error_returns_500_with_server_traceback(self):
        self.mocks[3].side_effect = RuntimeError("unexpected test failure")
        with self.assertLogs(main.__name__, level=logging.ERROR) as captured:
            response = self.client.post("/api/chat", json={"message": "My Django deployment is failing"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "An unexpected error occurred while processing this message.")
        self.assertIn("Traceback", "\n".join(captured.output))
        self.assertNotIn("unexpected test failure", response.text)

    def test_invalid_request_returns_422(self):
        response = self.client.post("/api/chat", json={"message": "   "})
        self.assertEqual(response.status_code, 422)

    def test_cors_preflight_allows_local_frontend(self):
        response = self.client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")

    def test_reported_frontend_scenarios_reach_chat_and_keep_response_contract(self):
        samples = [
            "My Django deployment is failing.",
            "I already have CORSMiddleware configured in main.py with http://localhost:5173, but I'm still getting the CORS error. The backend works when I test /api/chat from Swagger. What should I check next?",
            "My React app is getting a 500 error when calling the backend.",
        ]
        for message in samples:
            with self.subTest(message=message):
                response = self.client.post("/api/chat", json={"message": message})
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertTrue(payload["response"])
                self.assertIn("memory_status", payload)
                self.assertIn("incident", payload)
        self.assertEqual(self.mocks[3].await_count, len(samples))
        self.assertEqual(self.mocks[4].await_count, len(samples))
        self.assertEqual(self.mocks[5].await_count, len(samples))
        self.assertEqual(self.mocks[6].await_count, len(samples))


if __name__ == "__main__":
    unittest.main()