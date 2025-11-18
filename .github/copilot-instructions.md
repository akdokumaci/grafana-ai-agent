<!-- Copilot instructions for contributors and AI coding agents -->
# Grafana AI Agent — Copilot instructions

These concise instructions help AI coding agents be immediately productive in this repository.

High-level architecture
- Purpose: conversational assistant that uses LLMs to generate and summarize Grafana dashboards.
- Major components (see `grafana_agent/`):
  - `cli.py` — Click-based CLI entrypoints (commands: `chat`, `create`, `summarize`).
  - `chat_interface.py` — Conversation layer: keeps conversation history and routes create/summarize requests.
  - `dashboard_generator.py` — Uses LLM client to generate or summarize dashboard JSON. Handles JSON extraction (removes ```json blocks) and enforces minimal Grafana schema fields.
  - `llm_client.py` — Provider abstraction (OpenAI and Anthropic). Factory is `get_llm_client(provider, **kwargs)`.
  - `grafana_client.py` — Thin requests-based Grafana API client used for create/get/search/delete dashboard operations.

Key patterns and project-specific conventions
- LLM interaction: system prompts are defined in `DashboardGenerator._get_system_prompt()` and `ChatInterface._get_system_prompt()`; use these when building tests or changes that affect prompts.
- LLM responses are expected to be JSON (sometimes wrapped in markdown). `dashboard_generator.create_dashboard` strips code fences and attempts to parse JSON — keep this behavior when modifying output handling.
- Tests avoid external network calls. Look at tests (e.g. `tests/test_llm_client.py`, `tests/test_grafana_client.py`) for mocking patterns:
  - `openai` / `anthropic` modules are patched in tests; follow similar fixtures when adding network logic.
  - `requests.Session` is mocked via test fixtures for Grafana API calls.
- CLI conventions: `main.py` calls `grafana_agent.cli:cli`. The package exports a console script `grafana-agent` (see `pyproject.toml` [project.scripts]).

Developer workflows (commands and expectations)
- Install & dev: `pip install -e .` or `pip install -e "[dev]"` (see `README.md` and `pyproject.toml`).
- Run CLI locally:
  - Interactive chat: `python main.py chat` (or `grafana-agent chat` after install)
  - Create dashboard: `python main.py create "desc" --output out.json`
  - Summarize: `python main.py summarize dashboard.json`
- Tests: `pytest` (project configured with pytest options in `pyproject.toml` and `pytest.ini`). Use `pip install -r requirements-dev.txt` first.
- Lint/typecheck: formatting uses Black (line-length 100) and isort; mypy settings are in `pyproject.toml`.

Integration & external dependencies
- LLM providers: OpenAI and Anthropic. API keys are read from env vars (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) or passed via CLI `--api-key`.
- Grafana: `GRAFANA_URL`, `GRAFANA_API_KEY` (preferred) or `GRAFANA_USER`/`GRAFANA_PASSWORD` for basic auth.
- Network interactions should be isolated in `grafana_client.py` and `llm_client.py` so tests can mock them easily.

What to watch for when editing code
- When changing prompts or LLM message formats, update tests in `tests/test_dashboard_generator.py` and `tests/test_chat_interface.py` that assert system prompt inclusion or expected chat payloads.
- Keep JSON parsing tolerant to code fence wrappers and stray whitespace — `dashboard_generator.py` contains the extraction logic.
- Changes to the Grafana API surface should preserve `create_dashboard` payload format (payload has keys: `dashboard`, `folderId`, `overwrite`).
- Avoid importing heavy SDKs at module import time in library modules; the code imports `openai` / `anthropic` inside their client constructors to make missing-dependency errors explicit and testable.

Quick examples (copyable)
- Create LLM client in code:
  from grafana_agent.llm_client import get_llm_client
  client = get_llm_client('openai', api_key='...')
- Generate a dashboard programmatically:
  from grafana_agent.dashboard_generator import DashboardGenerator
  gen = DashboardGenerator(client)
  dashboard = gen.create_dashboard('CPU and memory dashboard', dashboard_title='Servers')

Files to inspect when making changes
- `grafana_agent/cli.py` — user-facing behavior and CLI flags
- `grafana_agent/dashboard_generator.py` — JSON parsing, prompts, schema fixes
- `grafana_agent/llm_client.py` — provider adapters and their import patterns
- `grafana_agent/grafana_client.py` — HTTP API surface, session handling
- `tests/` — look at fixtures and mocks for how external calls are faked

If something is unclear, ask for:
- Desired change to prompts or expected JSON schema
- Whether a change should affect both OpenAI and Anthropic flows
- Any additional real Grafana behavior that should be modelled in tests (e.g., folder IDs, dashboards with panels referencing specific data sources)

End of instructions — please review and tell me which sections you want expanded or any missing details to add.
