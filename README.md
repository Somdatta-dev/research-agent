# Market Insights Report Generator

Daily autonomous research agent that surveys the latest AI activity across the Automobile / Manufacturing sector, synthesizes a LinkedIn-ready PDF, and emails it.

Full architecture and build plan: [planning-docs/market-insights-architecture.md](planning-docs/market-insights-architecture.md).

## Quickstart

```bash
cp .env.example .env        # fill in API keys, SMTP creds, LLM settings
make up                     # starts Postgres, Redis, and the API
make migrate                # runs Alembic migrations
make logs                   # tail API logs
```

Then install the desktop app from [frontend/](frontend/) and point it at your backend URL in Settings.

## Repo layout

- [backend/](backend/) — FastAPI, LangGraph agent, APScheduler, Alembic
- [frontend/](frontend/) — Tauri 2 + React + Vite desktop client
- [docker-compose.yml](docker-compose.yml) — one-command VPS deploy
- [planning-docs/](planning-docs/) — architecture, API reference, prompt notes
