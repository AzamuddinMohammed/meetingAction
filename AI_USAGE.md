# AI Usage

Author: **Azamuddin Mohammed**

This project was built with the help of an AI coding assistant (Anthropic's
Claude, via Claude Code). This document is an honest, specific account of how AI
was used, in the interest of transparency.

## How AI was used

- **Scaffolding & implementation.** The assistant generated much of the initial
  code across the FastAPI backend, the React/TypeScript frontend, and the
  deployment configuration, based on my direction.
- **Deployment troubleshooting.** It helped diagnose and fix a Vercel deployment
  issue (the Python serverless function was missing its dependencies because a
  custom frontend build command caused the root `requirements.txt` to be skipped;
  the fix was a co-located `api/requirements.txt`).
- **Tests & tooling.** It produced the pytest suite (which mocks the model, so it
  runs without API keys), the ruff config, and the GitHub Actions CI workflow.
- **Docs.** It drafted the README and this file.

## What I directed and own

- **Product and scope decisions:** the feature set (summary, decisions, action
  items, follow-up email, optional Jira/Notion export), the stack choice
  (FastAPI + React on Vercel), and the "works with just one analysis key"
  constraint.
- **Provider design:** adding OpenRouter as an alternative analysis provider so
  the app runs on an OpenRouter key without a direct Anthropic key.
- **Review and integration:** I reviewed the generated code, ran it, tested it
  against real inputs, deployed it, and iterated on issues (e.g. the date-picker
  UX, the deployment failure).

## Why this is disclosed

Using AI assistance is a normal part of how I work, and I'd rather be upfront
about it than hide it. I understand the codebase and the decisions behind it and
can walk through any part of it — the architecture, the provider abstraction, the
structured-output validation, and the deployment model.

## How to verify the project independently

```bash
# Backend: lint + tests (no API key required — the model is mocked)
pip install -r requirements-dev.txt
ruff check server tests api
pytest -q

# Frontend: type-check + production build
npm --prefix web install && npm --prefix web run build
```
