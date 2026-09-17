"""
Skill: synthesize_review

Merges correctness, security, and style findings into one review a human
would actually want to read: deduplicated, prioritized, and with an
overall verdict — instead of three separate walls of text.
"""

from langchain_core.prompts import ChatPromptTemplate
from src.llm_config import get_llm

SYSTEM_PROMPT = """You are the lead reviewer synthesizing three specialist \
reviews (correctness, security, style) of the same pull request into one \
coherent review comment.

Rules:
- Deduplicate overlapping findings (specialists sometimes flag the same line).
- Order findings by severity: blocking issues first, then suggestions, \
then nitpicks.
- Attribute each finding to its lens in brackets, e.g. "[security]".
- End with an overall verdict: "Approve", "Approve with suggestions", or \
"Request changes" — and one sentence justifying it.
- Be concise. This should read like a real senior engineer's PR comment, \
not a report."""


def synthesize_review(
    pr_title: str,
    correctness_review: str,
    security_review: str,
    style_review: str,
) -> str:
    _prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                """PR title: {pr_title}

Correctness review:
{correctness_review}

Security review:
{security_review}

Style review:
{style_review}
""",
            ),
        ]
    )
    _chain = _prompt | get_llm(max_tokens=800)
    response = _chain.invoke(
        {
            "pr_title": pr_title,
            "correctness_review": correctness_review,
            "security_review": security_review,
            "style_review": style_review,
        }
    )
    return response.content
