# Copilot instructions for agentic_code_review_tool

## Project overview

This repository contains a Python prototype for reviewing GitHub pull requests with a multi-agent workflow. The main app lives in `code-review-board/` and is driven by a CLI entry point in `code-review-board/main.py`.

At a high level, the app does three things:

- fetches PR metadata and diff content from the GitHub API via `src/skills/fetch_pr_diff.py`
- runs specialist reviewer agents (`correctness`, `security`, `style`) against the diff
- synthesizes their findings into one final review with `Orchestrator` + a synthesizer agent

The repository is intentionally small and modular: `src/agents/` holds agent implementations, `src/skills/` holds narrow side-effecting or external-call logic, and `src/orchestrator.py` sequences the review flow.

## Commands

From the repo root:

```bash
cd code-review-board
python3 -m pip install -r requirements.txt
```

Runtime configuration is via environment variables and a local `.env` file at the repo root. The app calls `load_dotenv()` in both `main.py` and `src/llm_config.py`.

Typical run:

```bash
cd code-review-board
python3 main.py --owner octocat --repo Hello-World --pr 1
```

Optional PR comment posting:

```bash
cd code-review-board
python3 main.py --owner octocat --repo Hello-World --pr 1 --post
```

This prompts for confirmation before posting to GitHub and requires `GITHUB_TOKEN`.

### Environment variables

Use the repo-root `.env` file for local credentials:

```env
ANTHROPIC_API_KEY=...
GITHUB_TOKEN=...
COMMENTER_LLM=anthropic    # optional; anthropic or openai
ANTHROPIC_MODEL=claude-sonnet-4-6  # optional
OPENAI_MODEL=gpt-4o  # optional
```

### Build, test, and lint

There is no dedicated pytest, tox, ruff, black, or mypy configuration in this repository. There are no automated unit tests checked in for the review workflow. The practical validation path is to exercise the CLI against a public PR and confirm the review output is generated successfully.

## Architecture and conventions

### Agent pattern

Every agent subclasses `BaseAgent` from `code-review-board/src/agents/base_agent.py` and implements `run(context) -> context`.

Key conventions:

- `context` is the shared state object passed through the review pipeline
- each agent appends trace messages via `self.log(context, ...)`
- agents should be narrow-scope specialists; the synthesizer is responsible for deduplication and prioritization

### Orchestration flow

`code-review-board/src/orchestrator.py` is the central control point:

- initialize the reviewer list
- run each reviewer in sequence
- pass the unified context into the synthesizer
- return the final review payload

When extending the project, add a new reviewer by creating a new skill and agent, then registering it in `main.py` and/or the synthesizer input pipeline.

### LLM configuration

`code-review-board/src/llm_config.py` centralizes model/provider selection. Do not instantiate providers directly in individual skills when a shared helper can be used.

The selection is driven by `COMMENTER_LLM`:

- `anthropic` -> `langchain_anthropic.ChatAnthropic`
- `openai` -> `langchain_openai.ChatOpenAI`

This is the preferred extension point for model changes.

### Skills and GitHub access

Each skill file in `code-review-board/src/skills/` is intentionally narrow and focused:

- `fetch_pr_diff.py`: GitHub REST API fetch for PR metadata, diff, and per-file patch data
- `post_review_comment.py`: optional posting step only run with `--post`
- `review_correctness.py`, `review_security.py`, `review_style.py`: targeted reviewer prompts
- `synthesize_review.py`: merges reviewer output into a final, prioritized review

The GitHub client uses `GITHUB_TOKEN` when present and behaves read-only for public repos without it. Private repos and posting require a token.

### Repo conventions specific to this project

- Keep reviewer responsibilities narrow and non-overlapping; do not merge security, correctness, and style into one agent.
- Keep the final synthesized review as the canonical output; individual reviewer output is intermediate.
- Prefer adding new functionality in the `src/skills/` + `src/agents/` structure rather than branching logic in the CLI.
- Use `.env` for local secrets, and treat the repo as a local tooling prototype rather than a production service.

## Working style for this repo

When making changes here, prefer isolated edits that preserve the agent/skill split. The project is small enough that cross-file context matters: a change to a reviewer often needs to be reflected in its skill prompt, the agent wrapper, and the synthesizer contract.
