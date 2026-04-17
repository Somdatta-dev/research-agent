# Market Insights Report Generator — System Architecture & Project Plan

> **Purpose:** A self-hosted, scheduled agent that researches the latest trends in AI implementations across the Automobile / Manufacturing sector, synthesizes findings into a LinkedIn-shareable PDF, and emails it to a configured recipient daily. Built with LangGraph, FastAPI, React + Tauri 2, and Docker for VPS deployment.

> **Audience:** This document is the build brief for Claude Code. It is intentionally opinionated and concrete — every major choice is named, every interface is sketched, every directory is laid out.

---

## 1. Goals & Non-Goals

### Goals
- **Daily autonomous research** on a configurable topic (default: "AI in Automobile/Manufacturing").
- **High-signal output**: a 6–10 page PDF formatted for LinkedIn document posts.
- **Email delivery** via Zoho SMTP to a configured inbox each morning.
- **Realtime visibility**: a Tauri 2 desktop GUI that streams live agent progress over WebSocket.
- **Self-contained Docker deployment** on a VPS — `docker compose up` is the entire install.
- **Deduplication** so day-N doesn't repeat day-(N-1).
- **Provider-agnostic LLM** — anything OpenAI-compatible (OpenAI, OpenRouter, Together, local vLLM, etc.).

### Non-Goals (for v1)
- Authentication / multi-user support — defer to v2.
- Direct LinkedIn auto-posting — generate the PDF, user posts manually.
- Mobile app — desktop only.
- Multi-tenant infrastructure — single user, single VPS.

---

## 2. High-Level Architecture

```mermaid
flowchart LR
    subgraph "User Machine"
      TAURI[Tauri 2 + React GUI]
    end

    subgraph "VPS — Docker Compose Stack"
      API[FastAPI Backend<br/>REST + WebSocket]
      SCHED[APScheduler<br/>cron triggers]
      AGENT[LangGraph Agent<br/>research → synthesize → render]
      DB[(PostgreSQL<br/>configs, runs, dedup log)]
      REDIS[(Redis<br/>pub/sub for events)]
      VOL[(Reports Volume<br/>generated PDFs)]
    end

    subgraph "External Services"
      TAVILY[Tavily API]
      BRAVE[Brave Search API]
      LLM[OpenAI-compatible LLM]
      ZOHO[Zoho SMTP]
    end

    TAURI <-->|HTTPS REST| API
    TAURI <-->|WSS events| API
    API --- DB
    API --- REDIS
    SCHED --> AGENT
    API -->|manual trigger| AGENT
    AGENT --> TAVILY
    AGENT --> BRAVE
    AGENT --> LLM
    AGENT --> VOL
    AGENT --> ZOHO
    AGENT -->|stream events| REDIS
    REDIS -->|fanout| API
```

**Key design decisions:**
- Backend and scheduler live in the **same FastAPI process** (APScheduler with the AsyncIO scheduler). Simpler than Celery for a single-node deployment; can be split later.
- **Redis pub/sub** is the event bus between the agent (publisher) and any active WebSocket connections (subscribers). This decouples agent execution from GUI presence — runs continue even if no GUI is connected.
- **PostgreSQL** holds durable state: report configs, run records, event log (for replay), and the deduplication coverage log.
- The Tauri app is a **thin desktop shell** around a React SPA that talks to the remote VPS over HTTPS/WSS. No backend logic in Tauri itself.

---

## 3. Technology Stack

### Backend (Python 3.12)
| Concern | Library | Pinned version | Notes |
|---|---|---|---|
| Web framework | FastAPI | `>=0.115,<0.116` | Async, OpenAPI docs auto-generated |
| ASGI server | Uvicorn (with `uvloop`) | `>=0.32` | Production-ready |
| Agent framework | LangGraph | `>=0.6,<0.7` | Use `StateGraph` with multi-mode streaming (see §6) |
| Agent persistence | `langgraph-checkpoint-postgres` | `>=3.0` | Durable execution + resume — see §6.6 |
| Postgres driver for LG | `psycopg[binary,pool]` | `>=3.2` | Required by the checkpointer; needs `autocommit=True`, `row_factory=dict_row` |
| LLM client | `langchain-openai` + `httpx` | `>=0.3` | Configurable `base_url` for any OpenAI-compatible endpoint |
| Search | `httpx` (custom adapters) | `>=0.27` | Direct API calls to Tavily and Brave |
| ORM | SQLAlchemy 2.0 (async) + Alembic | `>=2.0` / `>=1.13` | Migrations from day one |
| Async PG driver (app) | `asyncpg` | `>=0.29` | For our app's SQLAlchemy models (separate from LG's psycopg) |
| Scheduler | APScheduler 3.x (`AsyncIOScheduler`) | `>=3.10` | `SQLAlchemyJobStore` for persistence |
| PDF generation | WeasyPrint | `>=63` | HTML/CSS → PDF, good typography |
| Templating | Jinja2 | `>=3.1` | For PDF HTML and email bodies |
| Email | `aiosmtplib` | `>=3.0` | Async SMTP for Zoho |
| Validation | Pydantic v2 | `>=2.9` | Settings via `pydantic-settings` |
| Logging | `structlog` | `>=24.4` | JSON logs |
| Retries | `tenacity` | `>=9.0` | Exponential backoff on flaky APIs |
| Redis client | `redis` (with asyncio) | `>=5.1` | For pub/sub event bus |
| Tests | pytest + `pytest-asyncio` + `respx` | latest | HTTP mocking |

> **Note on the two Postgres drivers.** LangGraph's `PostgresSaver` requires `psycopg` (v3) with specific connection settings (`autocommit=True`, `row_factory=dict_row`); our application models use SQLAlchemy with `asyncpg`. They share the same database but use separate connection pools. This is intentional and supported.

### Frontend (Node 20+)
| Concern | Library | Notes |
|---|---|---|
| Desktop shell | Tauri 2 | Rust backend, web frontend |
| UI framework | React 18 + Vite + TypeScript | Standard stack |
| Styling | Tailwind CSS + shadcn/ui | Fast iteration, accessible components |
| Server state | TanStack Query | Caching, mutations, optimistic UI |
| Client state | Zustand | Lightweight, no boilerplate |
| Forms | React Hook Form + Zod | Type-safe validation |
| Charts | Recharts | For metrics dashboard |
| WebSocket | Native `WebSocket` + reconnecting wrapper | Custom hook |
| Date | `date-fns` | Schedule/cron displays |
| PDF preview | `react-pdf` (pdf.js) | Inline preview before download |

### Infrastructure
- Docker + Docker Compose v2
- PostgreSQL 16
- Redis 7
- Nginx (later, for TLS termination — out of scope for v1)

---

## 4. Project Structure

```
market-insights/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docker-compose.dev.yml
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app factory + lifespan
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic settings
│   │   │   ├── logging.py             # structlog config
│   │   │   └── events.py              # Redis pub/sub helpers
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── routes/
│   │   │       ├── configs.py         # CRUD report configs
│   │   │       ├── runs.py            # trigger, list, detail
│   │   │       ├── reports.py         # download PDFs
│   │   │       ├── ws.py              # WebSocket endpoint
│   │   │       └── health.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── base.py
│   │   ├── models/                    # SQLAlchemy models
│   │   │   ├── report_config.py
│   │   │   ├── run.py
│   │   │   ├── run_event.py
│   │   │   └── coverage.py
│   │   ├── schemas/                   # Pydantic schemas
│   │   │   ├── config.py
│   │   │   ├── run.py
│   │   │   └── event.py
│   │   ├── agent/
│   │   │   ├── graph.py               # LangGraph StateGraph definition
│   │   │   ├── state.py               # TypedDict for shared state
│   │   │   ├── runner.py              # Wraps graph execution + event emission
│   │   │   ├── nodes/
│   │   │   │   ├── plan.py
│   │   │   │   ├── research.py
│   │   │   │   ├── dedup.py
│   │   │   │   ├── enrich.py
│   │   │   │   ├── synthesize.py
│   │   │   │   ├── write.py
│   │   │   │   ├── render_pdf.py
│   │   │   │   └── deliver.py
│   │   │   └── prompts/               # Externalized prompt templates
│   │   │       ├── plan.j2
│   │   │       ├── synthesize.j2
│   │   │       └── write.j2
│   │   ├── adapters/
│   │   │   ├── search/
│   │   │   │   ├── base.py            # SearchAdapter ABC
│   │   │   │   ├── tavily.py
│   │   │   │   └── brave.py
│   │   │   ├── llm/
│   │   │   │   └── openai_compat.py   # Single class, configurable base_url
│   │   │   └── email/
│   │   │       └── zoho_smtp.py
│   │   ├── pdf/
│   │   │   ├── render.py              # Jinja2 → HTML → WeasyPrint
│   │   │   └── templates/
│   │   │       ├── linkedin_carousel.html
│   │   │       └── styles.css
│   │   ├── scheduler/
│   │   │   ├── service.py             # APScheduler lifecycle
│   │   │   └── jobs.py                # Job factory from configs
│   │   └── services/
│   │       ├── config_service.py
│   │       ├── run_service.py
│   │       └── coverage_service.py
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       └── integration/
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── routes.tsx
│   │   ├── api/
│   │   │   ├── client.ts              # axios/fetch wrapper
│   │   │   ├── configs.ts
│   │   │   ├── runs.ts
│   │   │   └── ws.ts                  # WebSocket client
│   │   ├── hooks/
│   │   │   ├── useRunStream.ts        # subscribes to /ws/runs/{id}
│   │   │   └── useReportConfig.ts
│   │   ├── store/
│   │   │   └── settings.ts            # backend URL, theme
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn primitives
│   │   │   ├── RunTimeline.tsx        # node-by-node progress
│   │   │   ├── EventLogPane.tsx
│   │   │   ├── PdfPreview.tsx
│   │   │   └── CronBuilder.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx          # active configs + recent runs
│   │   │   ├── ConfigList.tsx
│   │   │   ├── ConfigEdit.tsx
│   │   │   ├── RunDetail.tsx          # the live-feedback view
│   │   │   └── Settings.tsx
│   │   └── types/
│   │       └── api.ts
│   └── src-tauri/
│       ├── tauri.conf.json
│       ├── Cargo.toml
│       └── src/
│           └── main.rs
│
└── docs/
    ├── architecture.md                # this document
    ├── api.md                         # endpoint reference
    └── prompts.md                     # prompt design notes
```

---

## 5. Data Model

### Tables (PostgreSQL)

> **Two schemas, one database.** Our application tables (below) live in the `public` schema, managed via Alembic. **LangGraph's checkpointer creates its own tables** (`checkpoints`, `checkpoint_writes`, `checkpoint_blobs`, `checkpoint_migrations`) on first `setup()` call — pass `schema="langgraph"` to `AsyncPostgresSaver` to keep them in their own namespace. Do **not** put LG's tables under Alembic management; they're maintained by the library and have their own migration mechanism.

#### `report_configs`
The user-defined recipe for a report.
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | text | "Daily AI in Automotive" |
| topic | text | Free-text topic description |
| focus_areas | jsonb | `["OEMs", "Tier-1 suppliers", "factory automation"]` |
| schedule_cron | text | e.g. `"0 7 * * *"` |
| timezone | text | IANA tz, e.g. `"Asia/Kolkata"` |
| recipients | jsonb | `[{"email": "...", "name": "..."}]` |
| search_config | jsonb | `{"providers": ["tavily","brave"], "max_results_per_query": 10, "recency_days": 2}` |
| llm_config | jsonb | Per-config overrides; see §6.7. Example: `{"primary": {"model": "anthropic/claude-3-5-sonnet"}, "fast": {"model": "openai/gpt-4o-mini", "temperature": 0.2}}`. Any unset field falls back to env defaults. |
| dedup_window_days | int | default 7 |
| pdf_template | text | template name, default `linkedin_carousel` |
| max_pages | int | default 8 |
| active | bool | scheduler ignores inactive configs |
| created_at, updated_at | timestamptz | |

#### `runs`
One row per execution (manual or scheduled).
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| config_id | UUID FK | |
| status | enum | `pending, running, completed, failed, cancelled` |
| trigger | enum | `manual, scheduled` |
| started_at, completed_at | timestamptz | |
| current_node | text | nullable |
| pdf_path | text | nullable until rendered |
| email_status | jsonb | `{"sent": true, "message_id": "...", "errors": []}` |
| metrics | jsonb | tokens, costs, durations per node |
| error | text | nullable |

#### `run_events`
Append-only log of every event emitted during a run. Powers replay if a GUI connects mid-run.
| Column | Type | Notes |
|---|---|---|
| id | bigserial PK | |
| run_id | UUID FK | indexed |
| ts | timestamptz | |
| node | text | nullable for system events |
| event_type | text | `node_start, node_end, llm_token, search_result, log, error, ...` |
| payload | jsonb | |

#### `coverage_log`
Deduplication memory. Every URL/article ever surfaced.
| Column | Type | Notes |
|---|---|---|
| id | bigserial PK | |
| config_id | UUID FK | |
| url | text | unique per config |
| url_hash | text | sha256(normalized_url) |
| title | text | |
| title_hash | text | for near-dup detection |
| first_seen_at | timestamptz | |
| last_seen_at | timestamptz | |
| run_ids | jsonb | array of runs that surfaced it |

Indexes: `(config_id, url_hash)`, `(config_id, first_seen_at desc)`.

---

## 6. The LangGraph Agent

This is the heart of the system. Get this right and everything else is plumbing.

### 6.1 State

```python
from typing import TypedDict, List, Optional, Annotated
from operator import add

class SearchHit(TypedDict):
    url: str
    title: str
    snippet: str
    published_at: Optional[str]
    source: str          # "tavily" | "brave"
    score: float

class EnrichedHit(TypedDict):
    url: str
    title: str
    full_text: str
    summary: str
    key_points: List[str]
    entities: List[str]  # companies, products mentioned

class Section(TypedDict):
    heading: str
    body_md: str
    citations: List[str]   # urls

class ReportState(TypedDict):
    run_id: str
    config: dict                                 # snapshot of report_config
    plan: List[dict]                             # [{"subtopic": "...", "queries": [...]}]
    raw_hits: Annotated[List[SearchHit], add]    # accumulator across parallel research
    deduped_hits: List[SearchHit]
    enriched_hits: List[EnrichedHit]
    sections: List[Section]
    cover_blurb: str
    draft_markdown: str
    pdf_path: Optional[str]
    email_result: Optional[dict]
    errors: Annotated[List[dict], add]
```

### 6.2 Graph Topology

```mermaid
flowchart TD
    START([START]) --> PLAN[plan]
    PLAN --> RESEARCH{{research<br/>fan-out per subtopic}}
    RESEARCH --> DEDUP[dedup]
    DEDUP -->|hits remaining| ENRICH[enrich top N]
    DEDUP -->|nothing new| FAIL_SOFT[soft_fail]
    ENRICH --> SYNTH[synthesize sections]
    SYNTH --> WRITE[write LinkedIn copy]
    WRITE --> RENDER[render_pdf]
    RENDER --> DELIVER[deliver email]
    DELIVER --> END([END])
    FAIL_SOFT --> END
```

### 6.3 Node Responsibilities

**`plan`** — LLM call that decomposes the topic into 3–5 subtopics, each with 2–3 search queries. Reads `config.focus_areas` and the *titles* of items already covered in the last 7 days (to bias toward freshness). Returns the plan in state.

**`research`** — Map-reduce fan-out using LangGraph's `Send` API. The conditional edge from `plan` returns a list of `Send("research_one", {...})` objects, one per subtopic. Each parallel branch calls Tavily and Brave concurrently. Results merge back via the `Annotated[List[...], add]` reducer on `raw_hits`. Use `max_concurrency` in the run config to cap parallelism (default 4).

```python
from langgraph.types import Send

def fan_out_to_research(state: ReportState) -> list[Send]:
    return [
        Send("research_one", {"subtopic": s, "config": state["config"]})
        for s in state["plan"]
    ]

graph.add_conditional_edges("plan", fan_out_to_research, ["research_one"])
```

**`dedup`** — Marked with `defer=True` so it acts as a **synchronization barrier** — it only runs after every `research_one` branch completes (critical for map-reduce correctness, otherwise it might run partway through fan-out). Pulls `coverage_log` for the config, filters out hits whose `url_hash` or near-match `title_hash` exists in the dedup window. Writes new hits to `coverage_log` as it accepts them.

```python
graph.add_node("dedup", dedup_node, defer=True)
```

**`enrich`** — For the top 8–12 deduped hits (ranked by score × recency), call Tavily Extract for full article text. LLM summarizes each into `key_points` + `entities`. Run as a second `Send` fan-out with concurrency capped at 4 to respect rate limits.

**`synthesize`** — One LLM call per section. Groups enriched hits by theme. Produces `Section` objects with citations. Tag the LLM with `tags=["synthesize"]` so its tokens are identifiable in the `messages` stream.

**`write`** — Single LLM call (also tagged) that converts sections into the final LinkedIn-ready structure: punchy cover blurb, one idea per page, a closing CTA. Emits `draft_markdown`.

**`render_pdf`** — Jinja2 renders `draft_markdown` + metadata into `linkedin_carousel.html`. WeasyPrint converts to PDF. Saves to `/data/reports/{run_id}.pdf`. Updates `runs.pdf_path` (in our app DB, not the checkpointer).

**`deliver`** — Composes a short email body (Jinja2 template), attaches the PDF, sends via Zoho SMTP using `aiosmtplib`. Records result in `runs.email_result`.

**Routing after `dedup`:** if the deduped hits count is below a threshold (default 3), route to a `soft_fail` node that sends a "no significant new developments" email and ends. This is a `add_conditional_edges` call on `dedup`.

### 6.4 Event Streaming

Use LangGraph's **multi-mode streaming** API (`stream_mode` parameter on `.astream()`). This replaces the older `astream_events(version="v2")` approach, which still works but is more verbose and harder to filter. The runner combines three modes simultaneously:

| Mode | Purpose | What we use it for |
|---|---|---|
| `updates` | Per-node state updates after each super-step | `node_started` / `node_completed` events, durations |
| `messages` | LLM token-level streaming | Live token feed during the `synthesize` and `write` nodes |
| `custom` | User-defined events emitted from inside nodes via `get_stream_writer()` | Everything else: search calls, dedup summaries, PDF rendered, email sent |

**Inside a node**, emit custom events like this:

```python
from langgraph.config import get_stream_writer

async def research_node(state: ReportState) -> dict:
    writer = get_stream_writer()
    for query in state["plan"]:
        writer({"type": "search_query", "provider": "tavily", "query": query})
        results = await tavily.search(query)
        writer({"type": "search_results", "provider": "tavily", "count": len(results)})
        # ...
    return {"raw_hits": all_results}
```

**The runner** consumes all three streams in one async loop:

```python
async for chunk in graph.astream(
    initial_state,
    config={"configurable": {"thread_id": run_id}, "max_concurrency": 4},
    stream_mode=["updates", "custom", "messages"],
):
    # chunk is (mode, payload) — normalize to our Event envelope and publish
    await publish_event(run_id, normalize(chunk))
```

**Normalized event envelope** (what hits Redis and the DB):

```python
class Event(TypedDict):
    run_id: str
    ts: str          # ISO8601
    node: Optional[str]
    type: str
    payload: dict
```

**Event types we emit:**
- `run_started`, `run_completed`, `run_failed` (lifecycle, emitted by runner not nodes)
- `node_started`, `node_completed`, `node_failed` (derived from `updates` mode + timing)
- `search_query`, `search_results` (custom, from `research`)
- `dedup_summary` `{"in": N, "kept": M, "rejected": K}` (custom, from `dedup`)
- `enrichment_progress` `{"completed": N, "total": M}` (custom, from `enrich`)
- `llm_token` `{"node": "synthesize", "text": "..."}` (from `messages` mode, filtered by tag)
- `section_drafted` `{"heading": "..."}` (custom, from `synthesize`)
- `pdf_rendered` `{"path": "...", "pages": N}` (custom, from `render_pdf`)
- `email_sent` `{"to": [...], "message_id": "..."}` (custom, from `deliver`)
- `log` `{"level": "info", "message": "..."}` (custom, from anywhere)

Every event is **(a)** persisted to the `run_events` table and **(b)** published to Redis channel `run:{run_id}`. WebSocket subscribers read history from the table on connect, then switch to live Redis.

> **Why `messages` mode requires LLM tagging.** When you have multiple LLM calls across different nodes, you tell them apart by tagging the LangChain runnable: `llm.with_config(tags=["synthesize"])`. The `messages` stream chunks include metadata you can filter on. Without tagging, you can't tell which node a token came from.

### 6.5 Prompt Design (sketches)

**`plan.j2`** — given topic, focus areas, and a list of titles already covered in the last week, return a JSON plan of subtopics + queries. Bias toward unexplored angles.

**`synthesize.j2`** — given a theme name and a list of enriched hits, produce one section: a 2-paragraph synthesis + 3–5 bullet "what it means" + a list of citations. Strict instruction: never invent attributions.

**`write.j2`** — given all sections and a target page count, produce LinkedIn carousel structure: cover hook, page-per-idea, scannable, ends with a question to drive engagement.

Externalize all prompts to `app/agent/prompts/*.j2` so they can be tuned without code changes.

### 6.6 Checkpointer & Durable Execution

LangGraph has a first-class **persistence layer** that snapshots graph state at every super-step. Compile the graph with `AsyncPostgresSaver` and we get fault tolerance, time-travel debugging, and the ability to resume crashed runs — for free.

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Lifespan-managed singleton in app/agent/runner.py
async with AsyncPostgresSaver.from_conn_string(LG_CHECKPOINT_DB_URL) as checkpointer:
    await checkpointer.setup()  # idempotent — creates LG-managed tables once
    compiled_graph = graph.compile(checkpointer=checkpointer)

# Each run uses its run_id as the thread_id
config = {
    "configurable": {"thread_id": run_id},
    "max_concurrency": 4,
}
async for chunk in compiled_graph.astream(initial_state, config=config, stream_mode=[...]):
    ...
```

**What this gives us:**
- **Crash recovery.** If the API container restarts mid-run, calling `astream` again with the same `thread_id` resumes from the last successful super-step. Successful nodes don't re-execute; their outputs are restored from the checkpoint.
- **Inspection.** `graph.aget_state(config)` returns the latest state of any run; `graph.aget_state_history(config)` returns the full timeline. Use this in the `/runs/{id}` endpoint to surface the live state shape.
- **Time travel.** For debugging bad runs, replay from any prior checkpoint with a modified state.

**Two persistence layers, two purposes — keep them straight:**
| Layer | What it stores | Why we need it | Owner |
|---|---|---|---|
| `AsyncPostgresSaver` (LG-managed) | Graph channel values at each super-step | Resume / replay / inspect graph state | LangGraph creates and maintains its own tables via `setup()` |
| `run_events` table (our schema) | Stream of UI-facing events (search calls, dedup summaries, etc.) | Live GUI feedback + audit log | Our Alembic migrations |

They share the same Postgres database (one fewer service to run) but use different schemas. LangGraph's tables live under the `public` schema by default — we can also pass `schema="langgraph"` when constructing the saver to keep them isolated, which is recommended.

**Connection requirements** (gotcha from the docs): the underlying `psycopg` connection MUST have `autocommit=True` and `row_factory=dict_row`. The `from_conn_string()` helper handles this automatically. If you build the connection manually (e.g. via a pool), you must set both explicitly or the checkpointer will throw `TypeError: tuple indices must be integers`.

**Connection pooling for production:**

```python
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

pool = AsyncConnectionPool(
    conninfo=LG_CHECKPOINT_DB_URL,
    max_size=20,
    kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
)
checkpointer = AsyncPostgresSaver(pool)
```

**Checkpoint lifecycle.** Each super-step creates a checkpoint, so a single full run produces ~10 checkpoints. At one daily run that's ~300/month per config — trivial. Add a periodic cleanup job (Phase 8 polish) that deletes checkpoints for runs older than 30 days, since the PDF and event log are the durable artifacts users care about long-term.

### 6.7 LLM Configuration & Resolution

> **Strict rule for Claude Code: model names, base URLs, API keys, and other LLM settings are NEVER hardcoded in the codebase.** No literal `"gpt-4o"`, no literal `"claude-3-5-sonnet"`, no inline `base_url="https://..."` anywhere inside `app/agent/`, `app/adapters/llm/`, or any node. Every value is resolved at runtime through the layered system below. If a code review finds a hardcoded model string, it must be moved to settings or `report_configs.llm_config`.

LLM settings are resolved in **three layers**, from highest to lowest precedence:

| Layer | Source | When to use |
|---|---|---|
| 1. Per-config override | `report_configs.llm_config` JSON column | "This specific report uses Claude via OpenRouter" |
| 2. Environment default | `LLM_*` env vars (see §11) | The global fallback applied when the config doesn't override |
| 3. Hardcoded fallback | **Not allowed** | Use Pydantic `Field(...)` with `validation_error` instead — fail loudly at startup if a required setting is missing |

#### `llm_config` JSON shape (Pydantic schema)

```python
# app/schemas/llm_config.py
from typing import Optional
from pydantic import BaseModel, Field

class LLMTierOverride(BaseModel):
    """All fields optional — anything unset falls back to env defaults."""
    base_url: Optional[str] = None
    api_key: Optional[str] = None        # rarely overridden; useful for per-config provider switching
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout_s: Optional[int] = None

class LLMConfig(BaseModel):
    """Stored as the `llm_config` JSON column on report_configs."""
    primary: LLMTierOverride = Field(default_factory=LLMTierOverride)
    fast: LLMTierOverride = Field(default_factory=LLMTierOverride)
```

Examples of valid `llm_config` values:

```json
// Use all env defaults — most reports
{}

// Override only the primary model for this one report
{"primary": {"model": "anthropic/claude-3-5-sonnet"}}

// Run this report against an entirely different provider (e.g. OpenRouter)
{
  "primary": {
    "base_url": "https://openrouter.ai/api/v1",
    "api_key": "sk-or-...",
    "model": "anthropic/claude-3-5-sonnet",
    "temperature": 0.4
  },
  "fast": {
    "base_url": "https://openrouter.ai/api/v1",
    "api_key": "sk-or-...",
    "model": "openai/gpt-4o-mini"
  }
}
```

#### The resolver

A single function, used by every node and every adapter that needs an LLM:

```python
# app/adapters/llm/openai_compat.py
from typing import Literal
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.schemas.llm_config import LLMConfig, LLMTierOverride

Tier = Literal["primary", "fast"]

def _env_defaults(tier: Tier) -> LLMTierOverride:
    if tier == "primary":
        return LLMTierOverride(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model_primary,
            temperature=0.3,
            timeout_s=settings.llm_timeout_s,
        )
    return LLMTierOverride(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model_fast,
        temperature=0.2,
        timeout_s=settings.llm_timeout_s,
    )

def resolve_llm(
    tier: Tier,
    config: LLMConfig | None = None,
    *,
    tags: list[str] | None = None,
) -> ChatOpenAI:
    """Single source of truth for building an LLM client.
    Layer 1 (config) overrides Layer 2 (env). No hardcoded fallbacks."""
    env = _env_defaults(tier)
    override = (config.primary if tier == "primary" else config.fast) if config else LLMTierOverride()

    return ChatOpenAI(
        base_url=override.base_url or env.base_url,
        api_key=override.api_key or env.api_key,
        model=override.model or env.model,
        temperature=override.temperature if override.temperature is not None else env.temperature,
        timeout=override.timeout_s or env.timeout_s,
        max_retries=settings.llm_max_retries,
    ).with_config(tags=tags or [])
```

#### Usage in nodes

Nodes never know what model they're running against — they just ask for a tier:

```python
# app/agent/nodes/synthesize.py
from app.adapters.llm.openai_compat import resolve_llm

async def synthesize_node(state: ReportState) -> dict:
    llm_config = LLMConfig.model_validate(state["config"].get("llm_config") or {})
    llm = resolve_llm("primary", llm_config, tags=["synthesize"])
    # ... use llm.ainvoke(...) or llm.astream(...)
```

#### Visibility in the GUI

The `ConfigEdit` page in the frontend should show the resolved values (with a clear distinction between "from environment" and "overridden") so the user always knows which model a report will actually use. Show this on the dry-run "test" button result too — surface the model name in the first event of the run so the user catches misconfigurations immediately.

#### Cost/token attribution

Because tier and model are resolved per-call, the `runs.metrics` JSON should record `{"primary_model": "...", "fast_model": "...", "tokens_by_tier": {...}}` so cost analysis works even when reports use different providers.

---

## 7. API Surface

All endpoints under `/api/v1`. JSON in/out. OpenAPI spec auto-served at `/docs`.

### Configs
| Method | Path | Purpose |
|---|---|---|
| POST | `/configs` | Create a report config |
| GET | `/configs` | List (with `?active=true` filter) |
| GET | `/configs/{id}` | Detail |
| PUT | `/configs/{id}` | Update |
| DELETE | `/configs/{id}` | Soft-delete (sets `active=false`) |
| POST | `/configs/{id}/test` | Dry-run with `max_results=2`, no email |

### Runs
| Method | Path | Purpose |
|---|---|---|
| POST | `/configs/{id}/runs` | Manually trigger a run |
| GET | `/runs` | List with filters: `config_id`, `status`, `since` |
| GET | `/runs/{id}` | Detail incl. metrics |
| GET | `/runs/{id}/events` | Paginated event log (for replay on connect) |
| POST | `/runs/{id}/cancel` | Set status to cancelled (best-effort) |

### Reports
| Method | Path | Purpose |
|---|---|---|
| GET | `/reports/{run_id}.pdf` | Download PDF |
| GET | `/reports/{run_id}/preview` | First-page PNG for thumbnail |

### Realtime
| Method | Path | Purpose |
|---|---|---|
| WS | `/ws/runs/{run_id}` | Subscribe to live events. On connect, server replays buffered events from DB then switches to live Redis stream. |

### Health
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness — returns DB + Redis status |

**CORS:** wide-open (`*`) for v1 since no auth. Lock down in v2.

---

## 8. Frontend Pages

### `Dashboard`
- Cards for each active config showing: next run time, last run status, latest PDF thumbnail.
- "Run now" button per config.
- Recent runs table (last 20).

### `ConfigList` / `ConfigEdit`
- CRUD for report configs.
- `CronBuilder` component with human-readable preview ("Every day at 7:00 AM IST").
- Recipient list with add/remove.
- Live "test run" button that triggers a no-email dry run and opens `RunDetail`.

### `RunDetail` — the marquee feature
Layout: split pane.
- **Left:** vertical `RunTimeline` showing every node with status icon (queued / running / done / failed) and duration. Click a node to filter the right pane.
- **Right:** `EventLogPane` — chronological event stream, color-coded by type. Auto-scroll with pause-on-hover. Search box.
- **Bottom strip:** when `pdf_rendered` fires, show inline `PdfPreview` (react-pdf) with download button. When `email_sent` fires, show toast + recipient list.

Realtime via `useRunStream(runId)`:
1. Fetch `/runs/{id}/events` to seed history.
2. Open `WS /ws/runs/{id}` for live updates.
3. Reconnect with backoff if dropped.

### `Settings`
- Backend URL (stored in Tauri's local store).
- Theme toggle.
- Connection status indicator.

---

## 9. PDF Layout Spec

LinkedIn document posts render best at **1080×1350 (4:5 portrait)**. Use that as the page size in WeasyPrint via CSS:

```css
@page {
  size: 1080px 1350px;
  margin: 80px 80px 100px 80px;
}
```

**Page sequence (target 8 pages):**
1. **Cover** — bold title, date, subtitle, author handle.
2. **Executive snapshot** — 3–5 bullets of "what changed today."
3–7. **Theme pages** — one per `Section`. Heading, 2-paragraph synthesis, 3 bullet takeaways, citation footer.
8. **Closing** — "What to watch next," CTA question, sources index.

Typography: a clean sans-serif (Inter or similar — bundle the font in the Docker image, don't rely on system fonts). Strong visual hierarchy. Consistent footer with page number and date.

Build the template as `linkedin_carousel.html` + `styles.css` and parameterize everything via Jinja.

---

## 10. Deduplication Strategy

The single biggest failure mode of a daily-research agent is repetition. Layered defense:

1. **URL normalization** — strip tracking params (`utm_*`, `gclid`, etc.), lowercase host, drop trailing slash. Hash the result with SHA-256.
2. **Exact dedup** — reject any hit whose `url_hash` exists in `coverage_log` for this config within `dedup_window_days`.
3. **Title near-dup** — compute `title_hash` as a normalized form (lowercase, strip punctuation, sort tokens). Reject if a high-similarity match exists. For v1, use a simple normalized exact match; upgrade to MinHash/SimHash in v2 if needed.
4. **LLM-side awareness** — the `plan` node receives the last week's coverage titles in its prompt and is explicitly told to seek *new angles*.
5. **Soft-fail path** — if `dedup` leaves fewer than 3 hits, the graph routes to `soft_fail`: send a brief email saying "no significant new developments today," skip the PDF.

---

## 11. Configuration & Secrets

All runtime config flows through environment variables (12-factor). Pydantic `BaseSettings` reads them in `app/core/config.py`. Secrets are **never** committed.

### Required Deliverables

**Claude Code: create exactly two files at the repo root** — `.env.example` (committed, with placeholder values) and a `.gitignore` entry for `.env` (the real file the user creates on the VPS). Both filenames are literal and must match exactly so `docker-compose.yml` picks `.env` up automatically.

#### `.env.example` — full content (verbatim)

```bash
# =============================================================================
# Market Insights — environment configuration
# Copy this file to `.env` and fill in real values. Never commit `.env`.
# =============================================================================

# --- App ---
APP_ENV=production               # production | development
LOG_LEVEL=INFO                   # DEBUG | INFO | WARNING | ERROR
TIMEZONE=Asia/Kolkata            # IANA tz used as default for new report configs
API_HOST=0.0.0.0
API_PORT=8000

# --- Application database (SQLAlchemy + asyncpg) ---
# Used by our app models, Alembic migrations, APScheduler jobstore.
DATABASE_URL=postgresql+asyncpg://mi:mi_pw@postgres:5432/market_insights

# --- LangGraph checkpointer database (psycopg v3) ---
# Same Postgres instance; psycopg-style URL; LG manages its own tables.
# Use a separate schema to keep LG-managed tables isolated from ours.
LG_CHECKPOINT_DB_URL=postgresql://mi:mi_pw@postgres:5432/market_insights
LG_CHECKPOINT_SCHEMA=langgraph

# --- Redis (event pub/sub) ---
REDIS_URL=redis://redis:6379/0

# --- LLM (OpenAI-compatible endpoint) ---
# Works with OpenAI, OpenRouter, Together, Groq, local vLLM, etc.
# These are the GLOBAL DEFAULTS. Per-report overrides live in
# `report_configs.llm_config` JSON column — see §6.7.
# Model names must NEVER be hardcoded anywhere in the codebase.
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-replace-me
LLM_MODEL_PRIMARY=gpt-4o         # synthesize + write — strongest model
LLM_MODEL_FAST=gpt-4o-mini       # plan + enrichment summaries — cheap & fast
LLM_TIMEOUT_S=60
LLM_MAX_RETRIES=3

# --- Hard cost guard (per run) ---
# Aborts a run if estimated token spend exceeds this. Cheap insurance.
RUN_TOKEN_BUDGET=200000
RUN_USD_BUDGET=2.50

# --- Search providers ---
TAVILY_API_KEY=tvly-replace-me
BRAVE_API_KEY=BSA-replace-me
SEARCH_DEFAULT_RECENCY_DAYS=2
SEARCH_MAX_RESULTS_PER_QUERY=10

# --- Concurrency caps ---
AGENT_MAX_CONCURRENCY=4          # passed as max_concurrency to graph.astream
ENRICH_MAX_PARALLEL=4

# --- Email (Zoho SMTP) ---
# For Zoho India: smtp.zoho.in. For global: smtp.zoho.com.
SMTP_HOST=smtp.zoho.in
SMTP_PORT=465
SMTP_USE_SSL=true                # true=465 implicit TLS, false=587 STARTTLS
SMTP_USERNAME=you@yourdomain.com
SMTP_PASSWORD=replace-me         # use a Zoho app-specific password, not your login password
EMAIL_FROM_NAME=Market Insights Bot
EMAIL_FROM_ADDRESS=you@yourdomain.com

# --- Storage ---
REPORTS_DIR=/data/reports        # mounted as a Docker volume

# --- CORS (v1 wide-open — LOCK DOWN BEFORE PUBLIC EXPOSURE) ---
CORS_ALLOW_ORIGINS=*

# --- Auth (placeholder for v2) ---
# AUTH_ENABLED=false
# API_KEY=
```

#### `.gitignore` additions

Append (do not replace) to the standard Python/Node `.gitignore`:

```gitignore
# Local secrets
.env
.env.local
.env.*.local

# Generated reports & local data
data/
/reports/

# Tauri build artifacts
frontend/src-tauri/target/
```

### How the app reads these

Single source of truth in `app/core/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # App
    app_env: str = "production"
    log_level: str = "INFO"
    timezone: str = "UTC"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Databases
    database_url: str
    lg_checkpoint_db_url: str
    lg_checkpoint_schema: str = "langgraph"
    redis_url: str

    # LLM
    llm_base_url: str
    llm_api_key: str
    llm_model_primary: str
    llm_model_fast: str
    llm_timeout_s: int = 60
    llm_max_retries: int = 3

    # Budgets
    run_token_budget: int = 200_000
    run_usd_budget: float = 2.50

    # Search
    tavily_api_key: str
    brave_api_key: str
    search_default_recency_days: int = 2
    search_max_results_per_query: int = 10

    # Concurrency
    agent_max_concurrency: int = 4
    enrich_max_parallel: int = 4

    # Email
    smtp_host: str
    smtp_port: int = 465
    smtp_use_ssl: bool = True
    smtp_username: str
    smtp_password: str
    email_from_name: str
    email_from_address: str

    # Storage
    reports_dir: str = "/data/reports"

    # CORS
    cors_allow_origins: str = "*"

settings = Settings()
```

---

## 12. Docker & Deployment

### `docker-compose.yml` (production)

```yaml
services:
  api:
    build: ./backend
    restart: unless-stopped
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8080:8000"            # bind to localhost in real prod, expose via nginx
    volumes:
      - reports_data:/data/reports
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"

  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: mi
      POSTGRES_PASSWORD: mi_pw
      POSTGRES_DB: market_insights
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mi"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  postgres_data:
  redis_data:
  reports_data:
```

### `backend/Dockerfile`

Multi-stage: builder installs deps and compiles WeasyPrint's heavy native deps (Cairo, Pango, GDK-PixBuf), runtime is slim.

```dockerfile
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpango-1.0-0 libpangoft2-1.0-0 libcairo2 \
    libgdk-pixbuf2.0-0 libffi-dev fonts-inter shared-mime-info \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Important:** the scheduler runs in-process, so **only one `api` worker**. If you scale workers later, move APScheduler to its own service or migrate to Celery Beat with a Redis broker.

### Frontend deployment
The Tauri app is **not in Docker**. It's a desktop binary the user installs on their Mac/Windows/Linux machine. The build command produces `.dmg` / `.msi` / `.AppImage` installers via `tauri build`. The user points it at the VPS URL in Settings on first launch.

For development, `tauri dev` runs Vite + the Rust shell locally with hot reload.

---

## 13. Observability

- **Logging:** structlog → JSON to stdout. Docker captures it. For long-term, ship to a syslog or Loki later.
- **Run metrics:** stored in `runs.metrics`:
  ```json
  {
    "duration_ms": 184321,
    "tokens": {"prompt": 12450, "completion": 3890},
    "cost_usd": 0.0712,
    "node_durations_ms": {"plan": 4100, "research": 22300, ...},
    "search_calls": {"tavily": 12, "brave": 12}
  }
  ```
- **Errors:** every node wraps in try/except, appends to `state.errors`, emits `node_failed` event. Run continues if recoverable, halts if not.
- **Health:** `/health` checks DB ping and Redis ping. Optional: add a `/health/last-run` that returns the freshest run per active config — useful for external monitoring.

---

## 14. Security Notes (for v1, with v2 in mind)

For v1 testing, the API is **unauthenticated**. Acceptable only if:
- The VPS firewall restricts the API port to your IP, **or**
- You front it with Tailscale / Wireguard, **or**
- You bind it to localhost and SSH-tunnel from the Tauri client.

**Do not expose `0.0.0.0:8080` to the open internet without auth.** A public, unauthenticated agent endpoint is a wallet-drain waiting to happen — anyone can trigger LLM-spending runs.

For v2, plan to add:
- API key auth (`X-API-Key` header) on all routes.
- Rate limiting (slowapi).
- TLS via nginx + Let's Encrypt.
- Per-config secret scoping.

---

## 15. Phased Implementation Plan

Build in vertical slices. Each phase ends with something runnable.

### Phase 0 — Skeleton (½ day)
- Repo scaffold, `pyproject.toml`, `package.json`, Docker compose with empty services up and healthy.
- Hello-world FastAPI route, hello-world React app inside Tauri shell connecting to it.
- Alembic initialized with empty migration.

### Phase 1 — Persistence & Config CRUD (1 day)
- All SQLAlchemy models + first real migration.
- `/configs` CRUD endpoints with Pydantic schemas.
- Frontend `ConfigList` + `ConfigEdit` pages backed by TanStack Query.
- **Acceptance:** can create, edit, list a report config from the GUI.

### Phase 2 — Adapters (1 day)
- `SearchAdapter` ABC + Tavily and Brave implementations with unit tests using `respx`.
- `OpenAICompatLLM` adapter with configurable `base_url`.
- `ZohoSMTP` adapter with a CLI smoke-test script.
- **Acceptance:** standalone scripts can search, summarize, and send a test email.

### Phase 3 — LangGraph agent, no scheduling, no GUI streaming (2 days)
- Full graph implementation in `app/agent/graph.py` using `StateGraph` (§6.1–6.3).
- `AsyncPostgresSaver` checkpointer wired up in app lifespan, with `setup()` called once on startup (§6.6).
- Use `Send` API for fan-out from `plan` → `research_one`, `defer=True` on `dedup`.
- Multi-mode streaming (`updates`, `custom`, `messages`) consumed by the runner; events written to `run_events` table.
- Runnable via a CLI: `python -m app.cli run --config-id <uuid>`.
- PDF renders with a placeholder template.
- **Acceptance:** end-to-end run from CLI produces a PDF and sends an email; killing the process mid-run and re-invoking with the same `run_id` resumes from the last super-step.

### Phase 4 — Realtime events (1 day)
- Redis pub/sub wiring.
- WebSocket endpoint with replay-then-stream pattern.
- `useRunStream` hook + `RunDetail` page.
- **Acceptance:** trigger a run from GUI, see live timeline + event log update.

### Phase 5 — Scheduler (½ day)
- APScheduler service, jobs auto-loaded from active configs on startup.
- Config CRUD reschedules on update.
- **Acceptance:** create a config with cron `* * * * *`, observe automatic runs.

### Phase 6 — PDF polish (1 day)
- Real `linkedin_carousel.html` template with bundled Inter font.
- Cover, theme pages, closing — all matching spec in §9.
- `react-pdf` preview in `RunDetail`.
- **Acceptance:** generated PDFs look genuinely shareable.

### Phase 7 — Dedup hardening (½ day)
- Coverage log fully wired.
- `plan` prompt receives recent titles.
- Soft-fail branch tested.
- **Acceptance:** running twice in a row produces meaningfully different reports.

### Phase 8 — Deployment dry run (½ day)
- Deploy to the VPS.
- Run for 3 consecutive days.
- Tune prompts based on actual output quality.

**Total: ~8 working days for a solo build with Claude Code assistance.**

---

## 16. Testing Strategy

- **Unit:** every adapter, every node's pure logic, the dedup hasher, the Jinja templates (snapshot tests).
- **Integration:** spin up Postgres + Redis via `pytest-docker`, run the graph end-to-end with `respx`-mocked external APIs.
- **Smoke (manual, pre-deploy):** `make smoke` runs a full real-world run with `max_results=2` against a throwaway config.
- **No frontend e2e tests for v1** — defer Playwright until UI stabilizes.

---

## 17. Known Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM cost runs away on a stuck loop | $$$ | Hard token budget per run in `runner.py`; abort if exceeded |
| Search APIs return junk for vague queries | Empty/poor reports | `plan` node generates *specific* queries; fail-soft path catches empties |
| WeasyPrint fonts render boxes | Ugly PDFs | Bundle Inter in the Docker image; explicit `@font-face` |
| Zoho SMTP rate limits or bounces | Missed delivery | `tenacity` retries; record `email_status`; surface failures in GUI |
| Single-worker uvicorn becomes a bottleneck | Slow GUI during runs | Agent runs are I/O-bound (mostly waiting on APIs); single worker is fine for v1 |
| Daily reports become repetitive | User stops reading | Layered dedup (§10); rotate focus areas; consider weekly + daily mix in v2 |
| Tauri app can't reach VPS (NAT, firewall) | GUI dead | Settings page surfaces connection status; document Tailscale option |

---

## 18. v2 Roadmap (out of scope, noted for context)

- API key auth + multi-user.
- Multiple report configs running concurrently with priority queue.
- Direct LinkedIn posting via official API.
- Web dashboard (host the React app behind nginx alongside the API) so Tauri becomes optional.
- Pluggable "writer voice" — store style guides per config.
- Vector store of all enriched articles for "ask the archive" queries.
- Slack delivery in addition to email.

---

## Appendix A — Quickstart for Claude Code

When handing this to Claude Code, suggested first prompt:

> Read `docs/architecture.md`. Implement Phase 0 and Phase 1. Use the exact directory structure in §4. Create `.env.example` with the **exact verbatim content** from §11 and add `.env` to `.gitignore`. Write Alembic migrations for the models in §5. Pin all Python dependencies to the versions in §3. Add a `Makefile` with targets: `up`, `down`, `logs`, `migrate`, `test`, `smoke`. Stop when the Tauri app can list and create configs against the running backend.

**Hard rules to enforce on every phase:**
- **No hardcoded LLM model names, base URLs, or API keys** anywhere in the codebase. All LLM access goes through `resolve_llm(tier, llm_config, tags=...)` per §6.7. If you find yourself writing `ChatOpenAI(model="...")` with a literal string, stop and use the resolver.
- **No hardcoded secrets** of any kind — everything via Pydantic `Settings`.
- **No `print()` for diagnostics** — use `structlog` so output is JSON-structured and Docker-loggable.
- **No catch-all `except Exception: pass`** — node failures must emit a `node_failed` event with the exception class and message.

Then iterate phase by phase, reviewing diffs before merging.

## Appendix B — Cron Examples for `schedule_cron`

| Intent | Expression |
|---|---|
| 7:00 AM daily (server tz) | `0 7 * * *` |
| Weekdays 7:00 AM | `0 7 * * 1-5` |
| Twice daily (7 AM and 5 PM) | `0 7,17 * * *` |
| Every Monday 8:00 AM | `0 8 * * 1` |

The `timezone` field on `report_configs` is what APScheduler uses — the cron expression is interpreted in that zone, not UTC.

## Appendix C — LangGraph API Notes (verified against v0.6.x, April 2026)

The LangGraph API has evolved quickly through 2025–2026. This architecture was verified against the latest docs; key things Claude Code should know to avoid using outdated patterns from older blog posts:

1. **Streaming: prefer `stream_mode` over `astream_events`.** Pass `stream_mode=["updates", "custom", "messages"]` to `.astream()`. The older `astream_events(version="v2")` API still works but is more verbose. Use `get_stream_writer()` from `langgraph.config` inside nodes to emit custom events — do **not** dispatch custom callbacks via the `langchain_core.callbacks` module unless you have a specific reason.

2. **`Send` lives in `langgraph.types`**, not `langgraph.constants` or `langgraph.graph`. Fan-out is done by returning a list of `Send` objects from a *conditional edge function*, not from a node.

3. **`defer=True` on `add_node`** is the correct way to make a node act as a synchronization barrier after a fan-out. Without it, the node may run before all parallel branches complete in map-reduce flows.

4. **Reducers via `Annotated`.** `Annotated[List[X], operator.add]` (or just `add` from `operator`) is the standard pattern for accumulating fan-out results into a list channel. Without a reducer, parallel writes to the same key will race and only one wins.

5. **Checkpointer connection requirements.** `AsyncPostgresSaver` requires `psycopg` v3 with `autocommit=True` and `row_factory=dict_row`. `from_conn_string()` sets these for you; manual pools must set them explicitly. Call `await checkpointer.setup()` once at startup — it's idempotent.

6. **`max_concurrency` is passed at the top level of the run config**, not inside `configurable`. Example: `config={"configurable": {"thread_id": run_id}, "max_concurrency": 4}`.

7. **`Command` for combined updates + routing** (optional). A node can `return Command(update={...}, goto="next_node")` to update state and force a transition in one step. Useful for `dedup → soft_fail` branching, though we use plain conditional edges in this architecture for simplicity.

8. **Pin LangGraph.** Use `langgraph>=0.6,<0.7`. The 0.5 → 0.6 transition deprecated `config_schema` in favor of `context_schema` (we use neither, so no impact, but worth noting). Major versions can shift APIs — pin tightly and upgrade deliberately.

If anything in the implementation conflicts with the live docs at `docs.langchain.com/oss/python/langgraph`, **trust the docs** and adjust. This document was accurate at time of writing but the framework moves fast.
