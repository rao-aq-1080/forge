(https://github.com/user-attachments/files/34754482/README.md)
# 🔨 Forge

> **A multi-agent AI software engineering team that plans, builds, tests, reviews, and repairs your code.**

**v2.0.0** — five AI specialists collaborate in a sequential pipeline, with seven
production-grade features layered on top of the core workflow.

```
You → RAG → ① PM → ② Architect → ③ Developer → ④ QA → ⑤ Reviewer
                            ⟳ Repair Loop (Dev → QA → Reviewer, up to N rounds) ⟳
                       → You approve → Files written → (optional) Docker test / GitHub export
```

---

## What's new in v2 (the 7 features)

| # | Feature | What it does |
|---|---------|--------------|
| 1 | **Auto-repair loop** | After the first review, if the score is below `REPAIR_SCORE_THRESHOLD`, the Repair Developer fixes the flagged findings, QA re-runs, the Reviewer re-scores — up to `MAX_REPAIR_ITERATIONS` rounds. You see the full score progression. |
| 2 | **Token / cost telemetry** | Every agent call records input/output tokens and estimated USD cost. A telemetry bar + per-agent table are shown in the dashboard and stored with each project. |
| 3 | **SSE streaming** | `POST /generate/stream` pushes live `stage_start` / `stage_end` / `repair_*` / `telemetry` / `done` events to the dashboard while agents run. |
| 4 | **Project diff viewer** | `GET /projects/{id}/diff` shows a unified diff of the current awaiting-approval code against the last approved snapshot — per-file status, additions/deletions, full patch. |
| 5 | **GitHub export** | `POST /projects/{id}/export/github` initializes a local git repo, commits, and (if `GITHUB_TOKEN` is set) creates a remote repo and pushes. |
| 6 | **Docker sandboxed tests** | `POST /projects/{id}/test/sandbox` runs pytest inside an isolated container — `--network none`, memory/cpu limits, read-only root, non-root user. Safe for untrusted generated code. |
| 7 | **RAG over past projects** | Before planning, a pure-Python TF-IDF retriever pulls the most similar *approved* projects and feeds them as inspiration to the PM and Architect. The corpus auto-rebuilds on every approval. |

---

## The agents

| Step | Agent | Responsibility |
|------|-------|----------------|
| 1 | **Product Manager** | Understand the requirement, identify the problem and users |
| 2 | **Software Architect** | Design components, data flow, folder structure, security |
| 3 | **Senior Developer** | Write complete, runnable source files |
| 4 | **QA Engineer** | Design test cases, edge cases, risk areas |
| 5 | **Code Reviewer & Security Auditor** | Find bugs, security risks, maintainability issues, score 0–100 |
| ⟳ | **Repair Developer** | Fix every actionable finding, return the full updated bundle |

---

## Requirements

- **Python 3.12** (`>=3.12,<3.13`)
- **UV** — https://docs.astral.sh/uv/
- A **Groq API key** — https://console.groq.com/
- **Docker** (only for the sandboxed test feature)

---

## Installation

```bash
cd forge
uv sync
cp .env.example .env          # Windows: Copy-Item .env.example .env
```

Open `.env` and set at minimum `GROQ_API_KEY=gsk_...`. The feature toggles all
default to safe values (host execution off, Docker off, GitHub off, RAG on,
repair loop on).

---

## Running Forge

Two terminals.

**Terminal 1 — backend:**
```bash
uv run uvicorn forge.api:app --reload --host 127.0.0.1 --port 8000
```
- API: http://127.0.0.1:8000
- Health (lists enabled features): http://127.0.0.1:8000/health
- Docs: http://127.0.0.1:8000/docs

**Terminal 2 — dashboard:**
```bash
uv run streamlit run ui/app.py
```
- Dashboard: http://localhost:8501

---

## Using the dashboard

1. Open http://localhost:8501.
2. (Optional) toggle **RAG** and **Auto-repair loop**.
3. Describe your software, click **🔥 Run the five agents (live)**.
4. Watch the live stream fill the log box; the telemetry bar updates as agents finish.
5. Review nine tabs: **Plan · Architecture · Code · QA · Review · Repair · Telemetry · Diff · RAG**.
6. Click **✅ Approve & write files**, then optionally **🐳 Run tests (Docker sandbox)** and **📤 Export to GitHub**.

---

## API reference

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/health` | Health + feature flags |
| `GET`  | `/projects` | List recent projects |
| `GET`  | `/projects/{id}` | Full project result |
| `POST` | `/generate` | Run agents (blocking, returns final result) |
| `POST` | `/generate/stream` | Run agents (SSE stream of events) |
| `POST` | `/projects/{id}/approve` | Write files + snapshot + rebuild RAG |
| `POST` | `/projects/{id}/test` | Host pytest (dangerous, off by default) |
| `POST` | `/projects/{id}/test/sandbox` | Docker sandboxed pytest |
| `GET`  | `/projects/{id}/diff` | Diff vs last approved snapshot |
| `GET`  | `/projects/{id}/telemetry` | Token/cost telemetry |
| `POST` | `/projects/{id}/export/github?repo_name=&visibility=` | Git init + optional remote push |
| `GET`  | `/rag/search?q=&k=` | Search the approved-project corpus |
| `POST` | `/rag/rebuild` | Rebuild RAG corpus from approved projects |
| `GET`  | `/rag/stats` | Corpus document count |

`POST /generate` body:
```json
{
  "requirement": "Build a ... (min 20, max 12000 chars)",
  "project_name": "Document Manager",
  "preferred_language": "Python",
  "additional_context": "",
  "enable_rag": true,
  "enable_repair_loop": true
}
```

SSE event types: `stage_start`, `stage_end` (with `data` + `usage`),
`repair_start`, `repair_end`, `telemetry`, `done`, `error`.

---

## Project structure

```
forge/
├── forge/
│   ├── __init__.py
│   ├── config.py          # all settings incl. feature toggles
│   ├── llm.py             # Groq + OpenAI Agents SDK
│   ├── schemas.py         # Pydantic models + telemetry/iteration/diff
│   ├── json_utils.py      # robust JSON extraction
│   ├── agents.py          # 5 specialists + repair_developer
│   ├── paths.py           # safe path validation + file writing
│   ├── storage.py         # SQLite + approved snapshots
│   ├── telemetry.py       # token + cost accounting
│   ├── rag.py             # pure-Python TF-IDF retriever
│   ├── diff_utils.py      # unified-diff helpers
│   ├── pipeline.py        # sequential orchestration + repair loop + emit
│   ├── streaming.py       # SSE async generator
│   ├── service.py         # approval, host/sandbox tests, diff, GitHub export
│   └── api.py             # FastAPI app with all endpoints
├── ui/app.py              # Streamlit dashboard (9 tabs + live stream)
├── tests/                 # json_utils, paths, schemas, telemetry, rag, diff
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## Tests and linting

```bash
uv run pytest -q
uv run ruff check .
```

Unit tests cover JSON parsing, path safety, schema validation, telemetry
arithmetic, the RAG retriever, and the diff utilities. They do **not** call
Groq, Docker, or GitHub.

---

## Configuration

All settings live in `.env` (see `.env.example`). Highlights:

| Variable | Default | Meaning |
|----------|---------|---------|
| `GROQ_API_KEY` | — | Required |
| `ENABLE_REPAIR_LOOP` | `true` | Auto-repair loop on/off |
| `MAX_REPAIR_ITERATIONS` | `2` | Max repair rounds |
| `REPAIR_SCORE_THRESHOLD` | `80` | Stop repairing once score ≥ this |
| `INPUT_COST_PER_MTOK` / `OUTPUT_COST_PER_MTOK` | `0.10` / `0.15` | Cost rates |
| `ENABLE_RAG` / `RAG_TOP_K` | `true` / `3` | RAG toggle + k |
| `ENABLE_GITHUB_EXPORT` / `GITHUB_TOKEN` | `false` / — | GitHub export |
| `ENABLE_DOCKER_SANDBOX` | `false` | Docker sandbox tests |
| `DOCKER_NETWORK_DISABLED` / `DOCKER_MEMORY_LIMIT` / `DOCKER_CPUS` | `true` / `512m` / `1.0` | Sandbox limits |
| `ALLOW_HOST_TEST_EXECUTION` | `false` | Host pytest (dangerous) |

---

## Security model

- Generated code is **never executed automatically**.
- Files are **never written** until a human clicks **Approve**.
- AI-generated paths are validated against traversal and confined to `WORKSPACE_ROOT`.
- The **Docker sandbox** runs generated code with no network, read-only root,
  non-root user, and hard memory/cpu limits — the safe path for untrusted code.
- `ALLOW_HOST_TEST_EXECUTION` is for trusted code only and stays off by default.

> ⚠️ The host test runner is **not** a sandbox. For any untrusted generated code,
> use the Docker sandbox.

---

## Roadmap

- Streaming per-token (not just per-stage)
- Multi-LLM routing (fast model for Dev, reasoning model for Reviewer)
- Approval audit log
- Webhook on project completion

---

## License

Provided as-is for educational and development use.
