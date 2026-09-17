# Code Review Board — Multi-Agent POC

Connects to a real GitHub PR, runs three specialist reviewers (correctness,
security, style) in parallel, then a synthesizer agent merges their findings
into one coherent review — instead of three separate walls of comments.

## Structure

```
code-review-board/
├── main.py                          # CLI entry point
├── requirements.txt
└── src/
    ├── orchestrator.py              # runs the panel + synthesis
    ├── agents/
    │   ├── base_agent.py            # same interface as compliance-case-investigator
    │   ├── correctness_agent.py
    │   ├── security_agent.py
    │   ├── style_agent.py
    │   └── synthesizer_agent.py
    └── skills/
        ├── fetch_pr_diff.py         # GitHub API: PR metadata + diff
        ├── review_correctness.py
        ├── review_security.py
        ├── review_style.py
        ├── synthesize_review.py
        └── post_review_comment.py   # opt-in, only runs with --post
```

## Running it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key
export GITHUB_TOKEN=your_token   # optional for public repos; needed for private repos or --post

python main.py --owner YOUR_ORG --repo YOUR_REPO --pr 42
```

Add `--post` to post the synthesized review as a comment on the PR. It will
ask for a y/N confirmation before posting — this tool never writes to a
repo silently.

Try it against a public repo first with no token, e.g.:
```bash
python main.py --owner octocat --repo Hello-World --pr 1
```

## Why three reviewers instead of one

A single "review this PR" prompt tends to blend everything into generic
comments and under-weight security in favor of easier-to-spot style nits.
Splitting into narrow-scope agents (each told to *ignore* the other two
lenses) makes each one focus, and the synthesizer's job — deduplicate,
prioritize by severity, give one verdict — is what turns three lists into
something a human would actually want to read.

## Plugging in a new reviewer

1. Add a skill in `src/skills/` (an LLM call with a narrow system prompt,
   same shape as `review_correctness.py`).
2. Subclass `BaseAgent` in `src/agents/`, call your new skill in `run()`.
3. Add it to the `reviewers` list in `main.py`.
4. Add its output as a parameter to `synthesize_review()` so the synthesizer
   folds it in.

Ideas worth trying next: a **test-coverage agent** (flags changed logic with
no corresponding test diff) or a **performance agent** (flags N+1 queries,
unbounded loops over request data).

## Notes on the GitHub connection

- Read-only fetch (`fetch_pr_diff`) works without a token for public repos,
  rate-limited to 60 requests/hour by GitHub.
- Posting (`post_review_comment`) always requires `GITHUB_TOKEN` and is
  never called unless you pass `--post` and confirm — kept as a deliberate,
  separate action from the review pipeline itself.
