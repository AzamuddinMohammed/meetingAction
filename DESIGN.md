# Design Notes

A short account of the key decisions, the trade-offs behind them, and what I'd do
next to take this to production. The goal was a small, correct, deployable slice
that does one job well: turn a meeting transcript into a reliable, structured
record of decisions and owned action items.

## Goals & non-goals

**Goals**
- Reliable, *structured* extraction (not free-form text a human has to re-parse).
- Usable with a single key; every integration is optional and self-hides.
- One-command local run and a one-push deploy.
- Honest error handling — the user always knows why something failed.

**Non-goals (deliberately out of scope)**
- Auth / multi-tenancy / persistence — this is a stateless transform, so there's
  no database. Adding one before it's needed would be premature.
- A job queue for long audio — see "Production considerations".

## Key decisions & trade-offs

### 1. Structured outputs instead of prompt-and-parse
The model is constrained to a JSON schema (`LlmAnalysis`) rather than asked for
prose that we regex. On the Anthropic path this uses the SDK's `messages.parse`;
on the OpenRouter path we request a JSON object, embed the schema, validate with
Pydantic, and retry once on a bad parse.

*Trade-off:* slightly more setup than "return some JSON", but the payoff is that
the API contract is enforced — the frontend never has to defend against
malformed model output.

### 2. A provider abstraction (Anthropic **or** OpenRouter)
`AnalysisProvider` is a small protocol with one method. The factory in
`services/analysis.py` picks a provider from configuration (Anthropic preferred,
OpenRouter fallback). Both return the *same* validated `MeetingAnalysis`.

*Why:* it decouples the app from a single vendor and made it usable on an
OpenRouter key with zero changes to routers, tests, or the frontend. The mapping
from LLM output to public models lives in one shared place (`_common.py`).

### 3. Feature-gating by configuration
`GET /api/health` reports which features are configured; the frontend enables UI
accordingly, and each endpoint returns `503 feature_unavailable` (not a 500) when
its dependency is missing.

*Why:* the app is fully functional with just an analysis key. Reviewers (or a new
teammate) can run it without hunting for four sets of credentials.

### 4. Two model layers: `Llm*` vs public
The model produces the minimal `Llm*` shapes; the server adds bookkeeping (stable
action-item IDs, default `status`) when mapping to the public models.

*Why:* the model shouldn't invent IDs or status, and the frontend needs stable
keys to edit rows. Keeping these concerns separate keeps the prompt small.

### 5. Typed errors + one JSON envelope
`AppError` subclasses carry an HTTP status and a machine-readable `code`
(`feature_unavailable`, `content_refused`, `transcript_too_large`, …). The
frontend branches on `code`, never on message strings.

### 6. Serverless-shaped choices
Analysis is a single request with a bounded `max_tokens` and `effort: medium` so
it finishes well within the function timeout. `maxDuration` is set in
`vercel.json`. Transcript size is capped (`MAX_TRANSCRIPT_CHARS`) to fail fast
rather than time out.

## Security

- No secrets in the repo: `config.py` reads everything from the environment;
  `.env` is git-ignored; only `.env.example` (placeholders) is committed.
- Keys live locally in `.env` and in Vercel's encrypted env vars — never in code.
- Optional integrations use least-privilege tokens (e.g. a scoped Jira API token).

## Testing strategy

- Backend tests mock the model, so the whole suite runs in CI with **no API key**
  and no network — deterministic and fast.
- Tests cover the happy path, validation (empty/oversized transcript), the
  feature-unavailable and refusal paths, provider selection, and export gating.
- CI (GitHub Actions) runs ruff + pytest for the backend and a type-check + build
  for the frontend on every push.

## Production considerations (what I'd do next)

- **Long audio:** move transcription to a background job (upload → queue →
  webhook/poll) instead of a single synchronous request, to escape function
  timeouts and body-size limits.
- **Auth & rate limiting:** add per-user auth and a rate limiter before exposing
  it publicly.
- **Persistence:** store analyses so users can revisit/edit them; add an
  `analyses` table and a history view.
- **Observability:** structured request logs + basic metrics (latency, token
  usage, error codes) — the pieces are already logged, just not aggregated.
- **Idempotency & retries:** make Jira/Notion export idempotent (dedupe by a
  content hash) so a retry doesn't create duplicate issues.
- **Evaluation:** a small labelled set of transcripts to regression-test
  extraction quality when changing prompts or models.
