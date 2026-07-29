# MeetingAction

Turn a raw meeting transcript (or audio) into a structured record — **summary,
key points, decisions, owned action items, risks, and a ready-to-send follow-up
email** — powered by Claude, with optional one-click export of action items to
**Jira** and **Notion**.

- **Backend:** FastAPI (Python) using the Anthropic SDK with structured outputs.
- **Frontend:** React + TypeScript (Vite).
- **Deploy target:** Vercel (React static build + Python serverless function).

**Author:** Azamuddin Mohammed · **Live demo:** https://meeting-action.vercel.app

📄 Further reading: [DESIGN.md](DESIGN.md) (decisions & trade-offs) ·
[AI_USAGE.md](AI_USAGE.md) (how AI assistance was used)

## Demo

A short (~1 minute) walkthrough video is included with this submission at
[`docs/demo.mp4`](docs/demo.mp4). Or try it live:
**https://meeting-action.vercel.app** → click **Load sample** → **Analyze meeting**.

## Reviewing this in 5 minutes

1. **See it work** — watch [`docs/demo.mp4`](docs/demo.mp4), or open the live demo
   and run the sample.
2. **The reasoning** — [DESIGN.md](DESIGN.md) covers the key decisions, trade-offs,
   and what I'd do next in production.
3. **The core code** — `server/schemas.py` (the API contract),
   `server/services/analysis.py` + `claude.py` / `openrouter.py` (the provider
   abstraction and structured-output validation), and `web/src/App.tsx` (the UI flow).
4. **Verify it yourself** — no API key needed; the model is mocked in tests:
   ```bash
   pip install -r requirements-dev.txt && ruff check server tests api && pytest -q
   npm --prefix web install && npm --prefix web run build
   ```
5. **Try the API** — `GET /api/health` lists configured features; `POST /api/analyze`
   does the work (curl example under [API reference](#api-reference)).

---

## How it works

```
┌──────────────┐   POST /api/analyze    ┌───────────────────────┐   messages.parse   ┌─────────┐
│  React app   │ ─────────────────────▶ │  FastAPI (serverless) │ ─────────────────▶ │ Claude  │
│  (web/)      │ ◀───────────────────── │  (server/ via api/)   │ ◀───────────────── │ Opus 4.8│
└──────────────┘   MeetingAnalysis JSON └───────────────────────┘  structured output └─────────┘
         │                                        │
         │  POST /api/export/{jira,notion}        ├─▶ Jira Cloud REST API   (optional)
         └───────────────────────────────────────┴─▶ Notion API            (optional)
```

The model is constrained to a strict JSON schema via the Anthropic SDK's
structured-output parsing (`messages.parse`), so responses are validated — never
free-form text that has to be scraped.

## Features

| Feature | Requires | Behavior when unconfigured |
| --- | --- | --- |
| Transcript → structured analysis | `ANTHROPIC_API_KEY` **or** `OPENROUTER_API_KEY` | `/api/analyze` returns `503 feature_unavailable` |
| Audio upload → transcript | `OPENAI_API_KEY` (Whisper) | Upload button hidden; endpoint returns `503` |
| Export action items → Jira | `JIRA_*` env vars | Jira button hidden; endpoint returns `503` |
| Export action items → Notion | `NOTION_API_KEY` + `NOTION_DATABASE_ID` | Notion button hidden; endpoint returns `503` |

The frontend reads `GET /api/health` on load and enables UI only for configured
features — so the app is fully usable with just an analysis key.

### Analysis providers

Analysis works with either provider; the backend picks one automatically
(Anthropic preferred when both are set):

- **Anthropic** (`ANTHROPIC_API_KEY`) — the direct API, using structured-output
  parsing (`messages.parse`).
- **OpenRouter** (`OPENROUTER_API_KEY`) — an OpenAI-compatible gateway that routes
  to Claude models (`OPENROUTER_MODEL`, default `anthropic/claude-sonnet-4.5`).
  The reply is validated against the same schema, with one corrective retry.

## Project structure

```
meetingAction/
├── api/index.py           # Vercel serverless entrypoint (exposes the ASGI `app`)
├── server/                # FastAPI application package
│   ├── main.py            # app factory, CORS, error handling, router wiring
│   ├── config.py          # env-driven settings + feature detection
│   ├── schemas.py         # LLM output contract + public API models
│   ├── prompts.py         # system/user prompt construction
│   ├── errors.py          # typed errors + JSON error envelope
│   ├── routers/           # health, analyze, transcribe, export
│   └── services/          # claude, transcription, jira, notion
├── web/                   # React + Vite + TypeScript frontend
├── tests/                 # pytest suite (mocks the model — no API key needed)
├── vercel.json            # build + function + rewrite config
├── requirements.txt       # backend runtime deps
└── .github/workflows/ci.yml
```

## Local development

### 1. Backend

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env      # add ANTHROPIC_API_KEY (and any optional keys)
uvicorn api.index:app --reload --port 8000
```

The API is now at `http://localhost:8000/api/health`.

### 2. Frontend

```bash
cd web
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies `/api/*` to the
backend on `:8000` (see `web/vite.config.ts`).

## Testing & linting

```bash
# Backend — no API key required; the Claude service is mocked
pytest -q
ruff check server tests api

# Frontend — type-check + production build
npm --prefix web run build
```

CI (`.github/workflows/ci.yml`) runs all of the above on every push and PR.

## Deploying to Vercel

1. Push this repo to GitHub and import it in Vercel (no extra settings needed —
   `vercel.json` defines the build, the Python function, and the `/api/*` rewrite).
2. In **Project → Settings → Environment Variables**, add at minimum
   `ANTHROPIC_API_KEY`, plus any optional integration keys from `.env.example`.
3. Deploy. Vercel builds `web/` to static assets and runs `api/index.py` as a
   Python serverless function; both are served from the same origin, so the
   frontend's relative `/api/...` calls work in production with no CORS setup.

> **Serverless note:** analysis runs as a single request. `maxDuration` is set to
> 60s in `vercel.json`; keep `ANALYSIS_EFFORT` at `medium` (default) for snappy
> responses, or raise it for deeper analysis on a plan with a higher timeout.

## API reference

| Method & path | Body | Returns |
| --- | --- | --- |
| `GET /api/health` | — | `{status, version, features}` |
| `POST /api/analyze` | `{transcript, meeting_title?, attendees?, meeting_date?}` | `{analysis, model, usage}` |
| `POST /api/transcribe` | multipart `file` | `{transcript}` |
| `POST /api/export/jira` | `{meeting_title?, action_items[]}` | `{target, created[]}` |
| `POST /api/export/notion` | `{meeting_title?, action_items[]}` | `{target, created[]}` |

Errors use a consistent envelope: `{"error": {"code": "...", "message": "..."}}`.
Interactive docs (OpenAPI/Swagger) are available at `/docs` when running the backend.

### Try it with curl

```bash
curl -s -X POST https://meeting-action.vercel.app/api/analyze \
  -H "Content-Type: application/json" \
  --data-binary @- <<'JSON'
{
  "transcript": "Alex: Ship the redesign Friday. Priya, wire analytics by Wednesday. Jordan, load-test signup before Thursday, high priority.",
  "meeting_title": "Q3 sync",
  "meeting_date": "2026-07-30",
  "attendees": ["Alex", "Priya", "Jordan"]
}
JSON
```

Abbreviated response:

```json
{
  "analysis": {
    "summary": "The team committed to shipping the redesign on Friday...",
    "decisions": [{ "decision": "Ship the redesign Friday", "rationale": null }],
    "action_items": [
      { "id": "ai-1", "task": "Load-test the signup service", "owner": "Jordan",
        "due_date": "2026-07-30", "priority": "high", "status": "open" }
    ],
    "risks": ["Signup service not yet load-tested"],
    "follow_up_email": { "subject": "Q3 sync — next steps", "body": "Hi team, ..." }
  },
  "model": "anthropic/claude-sonnet-4.5 (via OpenRouter)",
  "usage": { "input_tokens": 1035, "output_tokens": 589 }
}
```

A sample transcript for manual testing lives in
[`examples/sample-transcript.txt`](examples/sample-transcript.txt) (also loadable
in the UI via the **Load sample** button).

## Notes on the integrations

- **Jira:** uses the Cloud REST API v3 with Basic auth (`JIRA_EMAIL` +
  `JIRA_API_TOKEN`). Creates one issue per action item in `JIRA_PROJECT_KEY`.
- **Notion:** creates one page per action item in `NOTION_DATABASE_ID`. Optional
  `Owner` (rich text), `Due` (date), and `Priority` (select) properties are set
  only if they exist on the database, so it works with any database that has a
  title property.
- **Transcription** is intentionally provider-pluggable and optional; Anthropic's
  API does not transcribe audio, so Whisper is used behind a feature flag while
  the analysis pipeline stays Claude-first.

## AI usage

This project was built with the help of an AI coding assistant. See
[AI_USAGE.md](AI_USAGE.md) for a transparent account of what the assistant did
and which decisions and review I own.

## License

MIT — see [LICENSE](LICENSE).
