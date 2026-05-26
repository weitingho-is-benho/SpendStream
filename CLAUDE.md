# SpendStream — AI Assistant Guide

## Project Overview

SpendStream is a personal finance automation system that extracts transaction notifications from Gmail, normalizes and categorizes them using rules + AI, and syncs structured spending data to Google Sheets.

**Current state**: Early incubation. Only `.gitignore` and `README.md` exist. No source code, dependencies, or infrastructure has been committed yet.

---

## Intended Architecture

### Core Pipeline
```
Gmail → Extract transactions → Normalize merchants → Categorize (rules + AI) → Google Sheets
```

### Key Integrations
- **Gmail API** — read transaction notification emails
- **Google Sheets API** — output/sync destination for MVP
- **AI categorization** — rules-based fallback + LLM for ambiguous cases

---

## Tech Stack (inferred from `.gitignore` patterns)

| Layer | Tool |
|---|---|
| Language | Python 3.x |
| Package manager | UV (preferred based on `.gitignore` comments) |
| Linter/formatter | Ruff |
| Type checker | mypy |
| Testing | pytest |
| Task queue (future) | Celery + Redis |
| Notebook/exploration | Marimo or Jupyter |
| UI (optional) | Streamlit |

> When starting implementation, choose one package manager (UV is recommended for speed) and commit `pyproject.toml` + lock file. Do not mix `requirements.txt` with `pyproject.toml`.

---

## Development Setup (to be implemented)

When scaffolding the project, follow this structure:

```
SpendStream/
├── pyproject.toml          # single source of truth for deps + tool config
├── uv.lock                 # committed lock file
├── .env.example            # template for secrets (never commit .env)
├── CLAUDE.md               # this file
├── README.md
├── src/
│   └── spendstream/
│       ├── __init__.py
│       ├── gmail.py        # Gmail API client + email fetching
│       ├── parser.py       # transaction extraction from email body
│       ├── normalizer.py   # merchant name normalization
│       ├── categorizer.py  # rules engine + AI fallback
│       ├── sheets.py       # Google Sheets sync
│       └── models.py       # data classes / Pydantic models
├── tests/
│   ├── conftest.py
│   ├── test_parser.py
│   ├── test_normalizer.py
│   └── test_categorizer.py
└── scripts/
    └── run_pipeline.py     # entrypoint
```

---

## Conventions

### Python Style
- Format and lint with **Ruff** (`ruff check .` and `ruff format .`)
- Type-annotate all function signatures
- Use **Pydantic** models for data structures (Transaction, Category, etc.)
- Prefer `dataclasses` or `pydantic.BaseModel` over plain dicts for internal data
- No bare `except:` — always catch specific exceptions

### Secrets and Credentials
- All credentials go in `.env` (gitignored)
- Document every required env var in `.env.example` with a description
- Use `python-dotenv` or UV's env loading; never hardcode credentials
- OAuth tokens for Gmail/Sheets must be stored outside the repo (e.g., `~/.config/spendstream/`)

### AI Categorization
- Implement a deterministic rules layer first; call the LLM only when rules yield no match
- Cache LLM responses for identical merchant strings to avoid redundant API calls
- The Claude API (`anthropic` SDK) is preferred for AI categorization tasks

### Testing
- Run tests with `pytest`
- Unit-test the parser and normalizer with fixture email bodies (no live Gmail calls in unit tests)
- Mock external API calls (Gmail, Sheets, Anthropic) in tests
- Aim for >80% coverage on core pipeline modules

### Commits
- Use conventional commit style: `feat:`, `fix:`, `chore:`, `docs:`, `test:`
- Keep commits atomic — one logical change per commit
- Never commit `.env`, credentials, or OAuth token files

---

## Common Commands (once project is scaffolded)

```bash
# Install dependencies
uv sync

# Run linter
uv run ruff check .

# Run formatter
uv run ruff format .

# Type check
uv run mypy src/

# Run tests
uv run pytest

# Run full pipeline
uv run python scripts/run_pipeline.py
```

---

## Environment Variables (expected)

| Variable | Description |
|---|---|
| `GOOGLE_CLIENT_ID` | OAuth client ID for Gmail + Sheets |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret |
| `ANTHROPIC_API_KEY` | API key for AI categorization |
| `SPREADSHEET_ID` | Target Google Sheets document ID |
| `GMAIL_LABEL` | Gmail label to filter transaction emails |

---

## Key Design Decisions

1. **Google Sheets as MVP storage** — avoids a database dependency for the initial version; migrate to SQLite or PostgreSQL if query complexity grows.
2. **Rules before AI** — deterministic category rules are cheaper and faster; AI is the fallback, not the default.
3. **Single pipeline script** — MVP runs as a scheduled script (cron/launchd), not a long-running service. Celery/Redis is in `.gitignore` for future async expansion only.
4. **UV for package management** — faster than pip, lock-file reproducibility, no separate virtualenv step needed.

---

## Branch Strategy

- `main` — stable, deployable state
- Feature branches use the `claude/` prefix for AI-assisted work, `feat/` for human-authored features
- All changes go through PRs; do not push directly to `main`
