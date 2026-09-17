"""
Orchestrator: runs the review panel against a fetched PR.

Same pluggable structure as the compliance-case-investigator POC: to add
a new reviewer (e.g. a performance or test-coverage agent), subclass
BaseAgent, add it to `self.reviewers`, and the synthesizer prompt just
needs an extra parameter to include its output.
"""

from typing import Any, Dict, List

from src.agents.base_agent import BaseAgent


class Orchestrator:
    def __init__(self, reviewers: List[BaseAgent], synthesizer: BaseAgent):
        self.reviewers = reviewers
        self.synthesizer = synthesizer

    def run_review(self, pr: Dict[str, Any]) -> Dict[str, Any]:
        context: Dict[str, Any] = {"pr": pr, "trace": []}

        # Sequential here for simplicity; independent so easy to
        # parallelize with asyncio/threads once you care about latency.
        for reviewer in self.reviewers:
            context = reviewer.run(context)

        context = self.synthesizer.run(context)
        return context
