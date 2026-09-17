"""
Skill: review_correctness

Focuses on logic bugs, edge cases, error handling — not style and not
security (those are separate skills/agents so each stays focused and the
synthesizer can attribute findings to a specific lens).
"""

from langchain_core.prompts import ChatPromptTemplate
from src.llm_config import get_llm

#client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a senior engineer reviewing a pull request for \
correctness only. Ignore style, formatting, and naming — another reviewer \
handles those. Focus on: logic errors, incorrect edge-case handling, \
off-by-one errors, unhandled exceptions, race conditions, and incorrect \
assumptions about inputs.

For each issue found, output:
- file: <filename>
- line_context: <short quote of the relevant line(s)>
- issue: <what's wrong>
- severity: <blocking | suggestion>

If there are no correctness issues, say so explicitly."""

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "PR title: {pr_title}\nPR description: {pr_body}\n\nDiff:\n{diff}"),
    ]
)

_chain = _prompt | get_llm(max_tokens=800)


def review_correctness(pr_title: str, pr_body: str, diff: str) -> str:
    response = _chain.invoke({"pr_title": pr_title, "pr_body": pr_body, "diff": diff})
    return response.content
