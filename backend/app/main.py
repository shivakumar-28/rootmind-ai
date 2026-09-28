from contextlib import asynccontextmanager
import logging
import re
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent import respond_to_problem
from app.config import get_settings
from app.groq_client import GroqServiceError
from app.hindsight_client import HindsightServiceError, recall_memories, retain_memory
from app.incident_analyzer import analyze_incident
from app.models.schemas import ChatRequest, ChatResponse, Incident
from app.recurring_problems import build_recurring_problems
from app.storage import (
    get_conversation_messages,
    initialize_storage,
    list_incidents,
    save_conversation_message,
    save_incident,
)

logger = logging.getLogger(__name__)


def _safe_memory_query_preview(query: str) -> str:
    preview = re.sub(r"(?i)bearer\s+[^\s,;]+", "Bearer [REDACTED]", query)
    preview = re.sub(r"(?i)\b(?:sk|gsk|ghp|gho|hs)_[A-Za-z0-9_-]+", "[REDACTED]", preview)
    preview = re.sub(
        r"(?i)(api[_ -]?key|token|password|secret)\s*[:=]\s*[^\s,;]+",
        r"\1=[REDACTED]",
        preview,
    )
    return " ".join(preview.split())[:240]


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_storage()
    yield


settings = get_settings()
app = FastAPI(title="DevMemory AI API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")
    conversation_id = str(uuid4())
    if request.conversation_id:
        try:
            conversation_id = str(UUID(request.conversation_id))
        except (ValueError, AttributeError):
            logger.warning("[CHAT] Invalid conversation_id supplied; starting a new conversation.")

    history: list[dict[str, str]] = []

    try:
        history = get_conversation_messages(conversation_id)
        logger.info(
            "[CHAT] Received message conversation_id=%s previous_messages=%d groq_model=%s",
            conversation_id,
            len(history),
            settings.groq_model,
        )
        try:
            detected, incident = await analyze_incident(message)
        except ValueError as exc:
            logger.warning(
                "[CHAT] Incident extraction returned invalid JSON; continuing with conversation context exception_type=%s",
                type(exc).__name__,
            )
            detected, incident = False, Incident()
        memories: list[dict] = []
        memory_status = "available"
        memory_query = message
        logger.info("[MEMORY] Recall query: %s", _safe_memory_query_preview(memory_query))
        try:
            recalled = await recall_memories(memory_query, limit=3)
            memories = [
                {"content": item["content"]}
                for item in recalled[:3]
                if isinstance(item, dict) and isinstance(item.get("content"), str)
            ]
            logger.info("[MEMORY] Retrieved: %d memories", len(memories))
        except HindsightServiceError:
            logger.warning("[MEMORY] Recall unavailable; continuing without previous incidents.")
            memory_status = "unavailable"
        except Exception as exc:
            logger.exception("[MEMORY] Unexpected recall failure service=Hindsight operation=recall exception_type=%s", type(exc).__name__)
            memory_status = "unavailable"

        logger.info(
            "[CHAT] Generating response conversation_id=%s history_messages=%d recalled_memories=%d groq_model=%s",
            conversation_id,
            len(history),
            len(memories),
            settings.groq_model,
        )
        answer = await respond_to_problem(message, incident, memories, history)
        logger.info("[CHAT] Response generated conversation_id=%s", conversation_id)
    except GroqServiceError as exc:
        logger.error("Chat generation failed service=Groq exception_type=%s http_status=%s", type(exc).__name__, exc.status_code)
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except (ValueError, TypeError) as exc:
        logger.exception("Chat analysis failed exception_type=%s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="The assistant returned an unreadable analysis. Please try again.") from exc
    except Exception as exc:
        logger.exception("Unexpected chat failure exception_type=%s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing this message.") from exc

    try:
        save_conversation_message(conversation_id, "user", message)
        save_conversation_message(conversation_id, "assistant", answer)
        logger.info(
            "[CHAT] Saved user and assistant messages conversation_id=%s",
            conversation_id,
        )
    except Exception:
        logger.exception("Could not persist conversation context.")

    if detected:
        incident_data = incident.model_dump(exclude_none=True)
        if incident.problem:
            try:
                save_incident(conversation_id, incident_data)
            except Exception:
                logger.exception("Could not persist structured incident history.")
        useful = incident.problem and any((incident.technology, incident.error, incident.root_cause, incident.solution))
        if useful:
            memory_fields = {
                key: incident_data.get(key)
                for key in ("problem", "technology", "error", "root_cause", "solution", "outcome")
                if incident_data.get(key)
            }
            memory_text = "\n".join(f"{key.replace('_', ' ').title()}: {value}" for key, value in memory_fields.items())
            logger.info(
                "[MEMORY] Retaining incident: category=%s fields=%s",
                incident.category or "Other",
                ",".join(memory_fields),
            )
            try:
                await retain_memory(memory_text, metadata={"category": incident.category, "source": "devmemory-ai"})
                logger.info("[MEMORY] Retain successful")
            except HindsightServiceError:
                logger.warning("[MEMORY] Retention unavailable; returning the generated response without saving this incident.")
                memory_status = "unavailable"
            except Exception as exc:
                logger.exception("[MEMORY] Unexpected retention failure service=Hindsight operation=retain exception_type=%s", type(exc).__name__)
                memory_status = "unavailable"

    return ChatResponse(
        response=answer,
        conversation_id=conversation_id,
        incident_detected=detected,
        category=incident.category if detected else None,
        memory_used=bool(memories),
        memory_status=memory_status,
        relevant_memories=memories,
        incident=incident if detected else None,
    )


@app.get("/api/problems")
async def problems() -> dict:
    return {"problems": build_recurring_problems(list_incidents()), "source": "historical interactions"}


@app.get("/api/memory")
async def memory_summary() -> dict:
    incidents = list_incidents()
    technologies = list(dict.fromkeys(item["technology"] for item in incidents if item.get("technology")))
    categories = build_recurring_problems(incidents)
    solutions = list(dict.fromkeys(item["solution"] for item in incidents if item.get("solution")))
    return {
        "technologies": technologies[:12],
        "frequent_problems": [item["category"] for item in categories if item["count"] > 1][:8],
        "successful_solutions": solutions[:12],
        "incidents_count": len(incidents),
    }
