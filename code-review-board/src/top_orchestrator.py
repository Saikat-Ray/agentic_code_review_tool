"""
Top-level LangGraph orchestrator. Wraps the existing (plain-Python)
Orchestrator as one node, then runs the moderator as a second node.
Linear, one-shot, no loop-back — matches the current design: moderation
either approves-and-posts or rejects, nothing gets sent back for revision.

Deliberately NOT rebuilding the review panel in LangGraph — the existing
Orchestrator's internals stay exactly as they are. This graph only
decides what runs before and after it.
"""

from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.correctness_agent import CorrectnessAgent
from src.agents.moderator_agent import ModeratorAgent
from src.agents.security_agent import SecurityAgent
from src.agents.style_agent import StyleAgent
from src.agents.synthesizer_agent import SynthesizerAgent
from src.orchestrator import Orchestrator
from src.skills.fetch_pr_diff import fetch_pr_diff
from src.skills.filter_reviewable_files import filter_reviewable_files, rebuild_diff_from_files
from src.skills.save_excluded_files import save_excluded_files
from src.skills.save_review_to_db import save_review_to_db


class GraphState(TypedDict):
    owner: str
    repo: str
    pr_number: int
    review_id: int
    approved_count: int
    rejected_count: int
    trace: List[str]


def generate_comments_node(state: GraphState) -> GraphState:
    """Wraps the existing Orchestrator as a single opaque step."""
    owner, repo, pr_number = state["owner"], state["repo"], state["pr_number"]

    pr = fetch_pr_diff(owner, repo, pr_number)
    filtered = filter_reviewable_files(pr["files"])
    pr["files"] = filtered["included"]
    pr["diff"] = rebuild_diff_from_files(pr["files"])
    save_excluded_files(owner, repo, pr_number, filtered["excluded"])

    review_orchestrator = Orchestrator(
        reviewers=[CorrectnessAgent(), SecurityAgent(), StyleAgent()],
        synthesizer=SynthesizerAgent(),
    )
    result = review_orchestrator.run_review(pr)

    review_id = save_review_to_db(
        owner=owner,
        repo=repo,
        pr_number=pr_number,
        agent_comments={
            "correctness_agent": result["correctness_review"],
            "security_agent": result["security_review"],
            "style_agent": result["style_review"],
        },
        final_review=result["final_review"],
    )

    state["review_id"] = review_id
    state.setdefault("trace", []).append(f"[top_orchestrator] generated review, id={review_id}")
    return state


def moderate_comments_node(state: GraphState) -> GraphState:
    """Runs only after generate_comments_node fully completes — LangGraph's
    sequential edge already guarantees this ordering."""
    moderator = ModeratorAgent()
    context: Dict[str, Any] = {
        "owner": state["owner"],
        "repo": state["repo"],
        "pr_number": state["pr_number"],
        "review_id": state["review_id"],
        "trace": state.get("trace", []),
    }
    context = moderator.run(context)
    state["approved_count"] = context["approved_count"]
    state["rejected_count"] = context["rejected_count"]
    state["trace"] = context["trace"]
    return state


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("generate_comments", generate_comments_node)
    graph.add_node("moderate_comments", moderate_comments_node)
    graph.add_edge(START, "generate_comments")
    graph.add_edge("generate_comments", "moderate_comments")
    graph.add_edge("moderate_comments", END)
    return graph.compile()