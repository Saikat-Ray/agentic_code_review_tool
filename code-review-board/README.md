# AI Code Review

This repository implements a GitHub PR review pipeline using a small set of specialist reviewer agents and a moderator. It fetches a pull request diff, filters out low-value files, runs reviewer prompts for correctness/security/style, stores the results, and then posts only the comments that survive moderation.

The project is designed as a lightweight prototype for automated PR review workflows, with a local CLI and a GitHub Actions entry point triggered by a repository dispatch event.

## What the system does

1. Fetches PR metadata and patch data from the GitHub API.
2. Filters reviewable files to keep the review focused on meaningful changes.
3. Runs the reviewer agents:
   - correctness
   - security
   - style
4. Combines their findings in a synthesizer.
5. Stores the generated review in the database.
6. Moderates the comments and posts only approved comments back to the PR.

This makes the final output a curated review instead of a raw stack of agent comments.

## Repository structure

```text
code-review-board/
├── main.py                         # legacy CLI entry point
├── run_pipeline.py                 # current minimal pipeline runner
├── README.md
├── requirements.txt
├── .env.example?                  # optional local environment template
├── src/
│   ├── __init__.py
│   ├── llm_config.py              # shared LLM provider setup
│   ├── orchestrator.py            # reviewer orchestration
│   ├── top_orchestrator.py        # LangGraph wrapper around review + moderation
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── correctness_agent.py
│   │   ├── moderator_agent.py
│   │   ├── security_agent.py
│   │   ├── style_agent.py
│   │   └── synthesizer_agent.py
│   └── skills/
│       ├── fetch_pr_diff.py
│       ├── filter_reviewable_files.py
│       ├── moderate_comments.py
│       ├── post_review_comment.py
│       ├── review_correctness.py
│       ├── review_security.py
│       ├── review_style.py
│       ├── save_excluded_files.py
│       ├── save_review_to_db.py
│       ├── synthesize_review.py
│       └── update_comment_status.py
└── .github/
    └── workflows/
        └── ai-review.yml          # GitHub Action for repository_dispatch
```

## Local setup

Install dependencies:

```bash
cd code-review-board
python3 -m pip install -r requirements.txt
```

Set environment variables in a local `.env` file at the repo root or export them in your shell:

```bash
export COMMENTER_LLM=anthropic
export ANTHROPIC_API_KEY=your_key
export OPENAI_API_KEY=your_key
export GITHUB_TOKEN=your_token
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
```
The code loads `.env` automatically via `load_dotenv()` in the app entry points.

## Database schema

```sql
CREATE TABLE pr_reviews (
    id              SERIAL PRIMARY KEY,
    owner           TEXT NOT NULL,
    repo            TEXT NOT NULL,
    pr_number       INTEGER NOT NULL,
    final_review    TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending_moderation',
    -- pending_moderation | moderated | posted
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    moderated_at    TIMESTAMPTZ,
    moderator_notes TEXT
);

CREATE TABLE pr_review_comments (
    id              SERIAL PRIMARY KEY,
    review_id       INTEGER NOT NULL REFERENCES pr_reviews(id) ON DELETE CASCADE,
    agent_name      TEXT NOT NULL,       -- 'correctness_agent', 'security_agent', 'style_agent'
    comment         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending_moderation',
    -- pending_moderation | approved | rejected
    moderator_notes TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_pr_review_comments_review_id ON pr_review_comments(review_id);

CREATE TABLE pr_review_excl (
    id              SERIAL PRIMARY KEY,
    owner           TEXT NOT NULL,
    repo            TEXT NOT NULL,
    pr_number       INTEGER NOT NULL,
    filename        TEXT NOT NULL,
    matched_pattern TEXT,
    excluded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

One row per comment, not one row per review — adding a new reviewer agent later needs zero schema changes, just a new `agent_name` value.



## Run the pipeline locally

The current pipeline entry point is:

```bash
cd code-review-board
python run_pipeline.py --owner octocat --repo Hello-World --pr 1
```

This executes the review generation step and moderation flow in order.

A more direct legacy CLI also exists:

```bash
cd code-review-board
python main.py --owner octocat --repo Hello-World --pr 1
```

The legacy CLI is useful for local manual review generation, while `run_pipeline.py` reflects the current end-to-end workflow run by the GitHub Action.

## GitHub Actions workflow

The repository includes a workflow at `.github/workflows/ai-review.yml` that listens for `repository_dispatch` events and runs the review pipeline for the requested PR.

Example trigger payload contains:

- `owner`
- `repo`
- `pr_number`

The workflow sets up Python, installs deps, verifies that `TARGET_REPO_PAT` is available, and then runs:

```bash
python run_pipeline.py \
  --owner "${{ github.event.client_payload.owner }}" \
  --repo "${{ github.event.client_payload.repo }}" \
  --pr "${{ github.event.client_payload.pr_number }}"
```

The action expects these GitHub repository secrets:

- `TARGET_REPO_PAT`
- `COMMENTER_LLM`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `DATABASE_URL`

## Review flow in detail

The pipeline is composed of a few stages:

- `fetch_pr_diff`: pulls the PR metadata and diff from GitHub.
- `filter_reviewable_files`: removes obvious non-reviewable files before the LLM review.
- `CorrectnessAgent`, `SecurityAgent`, `StyleAgent`: produce targeted review comments.
- `SynthesizerAgent`: consolidates the three agent outputs into a final review.
- `save_review_to_db`: persists the review and per-agent findings.
- `ModeratorAgent`: reviews the saved comments and approves or rejects them.
- `post_review_comment`: posts only the approved comments to the PR.

This moderation stage is important because it helps catch duplicate or vague comments before they are sent to the PR.

## Why the moderator exists

The final comment set is not just the raw output of each reviewer. The moderator checks for:

- duplicate findings across agents
- vague or generic suggestions
- comments that are not actionable

It keeps only the strongest comments and rejects the rest before posting to GitHub.

## Notes on authentication and permissions

- Public repositories can often be read without a token for fetch operations, though GitHub rate limits still apply.
- Posting comments to a PR requires a GitHub token.
- In GitHub Actions, the workflow uses `TARGET_REPO_PAT` as the token source for the target repo.
- Private repos and write operations require valid credentials and the corresponding repo permissions.

## Extending

- **New reviewer agent**: add a skill in `src/skills/`, a matching agent in `src/agents/` (subclass `BaseAgent`), add it to the `reviewers` list in `src/orchestrator.py`, and add its output as a parameter to `synthesize_review()`. No schema change needed — the comments table already supports any `agent_name`.
- **New LLM provider**: add a branch in `src/llm_config.py`'s `get_llm()`.
- **Change excluded file types**: edit `EXCLUDED_FILE_PATTERNS` in `.env` — no code change.
- **Moderation loop-back**: currently one-shot by design (approve/reject, no revision). Adding a rejection → re-draft loop would mean adding a conditional edge in `top_orchestrator.py` instead of the current linear `generate → moderate → END`.

This repo intentionally keeps reviewer responsibilities narrow so the final review remains easier to interpret and prioritize.

## Typical usage

```bash
cd code-review-board
python run_pipeline.py --owner my-org --repo my-repo --pr 42
```

If the moderator approves at least one comment, it will post those approved comments to the PR and update the review status in the database.
