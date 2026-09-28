# DevMemory AI

A developer incident-response assistant that combines Groq for analysis and responses with Hindsight Cloud for long-term semantic memory. It looks for related past incidents before answering and remembers useful technical details rather than indiscriminately storing every chat message.

## Architecture

```text
React + Vite browser
        │  HTTP /api/* (no secrets in browser)
        ▼
FastAPI backend ─── Groq Chat Completions API
        │
        ├────────── Hindsight Cloud (semantic recall + selective retain)
        └────────── SQLite (conversation context + structured incident history)
```

The backend's `storage.py` keeps SQLite access behind a small persistence layer. The database contains local conversation context and structured incident records used by the recurring-problems dashboard; Hindsight remains the semantic memory system. The SQLite file is ignored by Git.

## Features

- Incident analysis distinguishes stated facts from hypotheses and leaves unknown root causes unset.
- Hindsight recall is used as context for responses; the UI shows concise memory details.
- Useful incident summaries are retained only when analysis found an incident with meaningful technical detail.
- Conversation turns are stored locally so later turns can supply a root cause, solution, or outcome.
- Recurring problem groups show counts, technologies, errors, and previously reported solutions from SQLite incident history.
- Developer memory summarizes technologies and confirmed solutions observed in that history.
- Responsive chat UI with markdown, code, loading/error states, and browser-local recent conversations.

## Tech stack

- Frontend: React, Vite, JavaScript/JSX, Tailwind CSS v4, Lucide React, React Markdown
- Backend: Python, FastAPI, Uvicorn, httpx, python-dotenv, Pydantic Settings
- AI: Groq API, `openai/gpt-oss-120b`
- Memory: Hindsight Cloud HTTP API
- MVP persistence: SQLite; PostgreSQL can replace the persistence implementation later

## Prerequisites

- Node.js 20+ and npm
- Python 3.11+
- A Groq API key with access to `openai/gpt-oss-120b`
- A Hindsight Cloud account, API key, and the API base URL shown for your workspace

## Environment variables

Copy `backend/.env.example` to `backend/.env`. Configure the values there; do not put them in frontend files or `VITE_*` variables.

| Variable | Purpose |
| --- | --- |
| `GROQ_API_KEY` | Backend-only Groq API key |
| `GROQ_MODEL` | Groq model; defaults to `openai/gpt-oss-120b` |
| `HINDSIGHT_API_KEY` | Backend-only Hindsight API key |
| `HINDSIGHT_BASE_URL` | Hindsight Cloud API base URL from your workspace settings; do not append `/v1/...` |
| `HINDSIGHT_BANK_ID` | Memory bank identifier; defaults to `devmemory-ai` |
| `FRONTEND_ORIGINS` | Comma-separated allowed frontend origins; defaults to `http://localhost:5173` |
| `DATABASE_PATH` | Local SQLite file path; defaults to `./data/devmemory.db` (relative to `backend/`) |

The backend uses Hindsight's documented `POST /v1/default/banks/{bank_id}/memories/recall` and `POST /v1/default/banks/{bank_id}/memories` APIs. The adapter is isolated in `backend/app/hindsight_client.py` so API-version changes stay localized. Hindsight creates a bank on first write if it does not exist.

## Backend setup (PowerShell)

```powershell
cd devmemory-ai\backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` and enter your Groq key, Hindsight key, and Hindsight Cloud base URL. Start the API:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: `http://localhost:8000/api/health`. Interactive API docs: `http://localhost:8000/docs`.

Run the backend unit tests from `backend/` with `python -m unittest discover -s tests`.

## Frontend setup (PowerShell)

Open a second terminal:

```powershell
cd devmemory-ai\frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal (normally `http://localhost:5173`). The frontend calls the backend at `http://localhost:8000`. To use a different backend origin, set `VITE_API_BASE_URL` before starting Vite; it is a URL only and must never contain API credentials.

## Run locally

1. Configure `backend/.env` with the Groq API key, Hindsight Cloud API key, and workspace API base URL.
2. Start the backend in one terminal.
3. Start the frontend in a second terminal.
4. Send a technical issue in the chat. Check that `/api/health` responds before troubleshooting connection errors.

## Example memory loop

1. Ask: “My Django API returns 500 after deployment.” With no traceback, the assistant should ask for evidence instead of asserting a database or environment cause. The useful problem, technology, and error may be retained as an unresolved incident.
2. Continue with details such as: “The traceback says the production DATABASE_URL is missing. I added it and the API is working.” The backend retains the cross-turn problem, confirmed cause, fix, and outcome.
3. In a later conversation, ask: “My Django API is returning 500 again.” Hindsight recall can surface the previous incident; the assistant can recommend checking `DATABASE_URL` while making clear that the previous cause is not confirmed for this occurrence.

## API endpoints

- `GET /api/health` — liveness response `{ "status": "ok" }`
- `POST /api/chat` — validates the user message, analyzes it with Groq, recalls relevant Hindsight memories for incidents, responds, and selectively retains useful incident information. Request: `{ "message": "...", "conversation_id": "optional-id" }`.
- `GET /api/problems` — grouped local incident counts and common technologies/errors/solutions.
- `GET /api/memory` — summary of local incident history for the developer-memory view.

No API keys or internal prompts are returned by these endpoints. If Hindsight is unavailable, Groq can still answer and the API marks memory status as unavailable. If Groq is unavailable, the chat endpoint returns a safe service error rather than fabricating an answer.

## Future improvements

- Add authentication and per-user Hindsight bank isolation before deploying beyond a local, trusted demo.
- Replace SQLite persistence with PostgreSQL behind the same storage interface.
- Add migrations, retention controls, and deletion/export controls for conversation data.
- Add streaming responses, configurable history limits, and more robust incident lifecycle updates.
- Add integration tests against a Hindsight test bank and provider contract tests.

## Security note

This MVP is intended for local development and trusted demos. CORS is restricted to the local Vite origin by default, but CORS is not authentication. Add user authentication, authorization, rate limits, and deployment-specific secret management before exposing the backend publicly. Conversation context is stored in the backend's local SQLite database and recent conversations are stored in browser local storage.
