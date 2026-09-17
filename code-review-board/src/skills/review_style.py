"""
Skill: review_style

Focuses on naming, formatting, dead code, and convention consistency.
Lowest-severity lens of the three, but kept as its own agent so it can't
drown out correctness/security findings in the synthesized review.
"""

from langchain_core.prompts import ChatPromptTemplate
from src.llm_config import get_llm

SYSTEM_PROMPT = """You are reviewing a pull request diff for style and \
convention only. Ignore logic correctness and security — other reviewers \
handle those. Focus on: naming clarity, dead/commented-out code, \
inconsistent formatting, overly long functions, missing docstrings/comments \
where the code isn't self-explanatory, and repeated code that could be \
extracted.

For each issue found, output:
- file: <filename>
- line_context: <short quote of the relevant line(s)>
- issue: <what to improve>
- severity: <suggestion | nitpick>

If there are no style issues, say so explicitly. Keep this list short —
don't nitpick every line."""

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "PR title: {pr_title}\nPR description: {pr_body}\n\nDiff:\n{diff}"),
    ]
)

_chain = _prompt | get_llm(max_tokens=800)

def review_style(pr_title: str, pr_body: str, diff: str) -> str:
    response = _chain.invoke({"pr_title": pr_title, "pr_body": pr_body, "diff": diff})
    return response.content


