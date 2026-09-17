"""
Skill: review_security

Focuses on injection risks, secrets, unsafe deserialization, auth/authz
gaps, and unsafe dependency usage. Deliberately narrow scope, same reason
as review_correctness.
"""

from langchain_core.prompts import ChatPromptTemplate
from src.llm_config import get_llm

SYSTEM_PROMPT = """You are an application security reviewer looking at a \
pull request diff. Ignore style and general logic — other reviewers \
handle those. Focus on: injection risks (SQL, command, template), hardcoded \
secrets or credentials, unsafe deserialization, missing input validation, \
authn/authz gaps, unsafe use of eval/exec, and risky dependency changes.

For each issue found, output:
- file: <filename>
- line_context: <short quote of the relevant line(s)>
- issue: <what's wrong and the exploit scenario, briefly>
- severity: <blocking | suggestion>

If there are no security issues, say so explicitly."""

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "PR title: {pr_title}\nPR description: {pr_body}\n\nDiff:\n{diff}"),
    ]
)

_chain = _prompt | get_llm(max_tokens=800)

def review_security(pr_title: str, pr_body: str, diff: str) -> str:
    response = _chain.invoke({"pr_title": pr_title, "pr_body": pr_body, "diff": diff})
    return response.content
