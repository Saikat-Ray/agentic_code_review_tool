from typing import Any, Dict

from src.agents.base_agent import BaseAgent
from src.skills.review_correctness import review_correctness


class CorrectnessAgent(BaseAgent):
    name = "correctness_agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pr = context["pr"]
        result = review_correctness(pr["title"], pr["body"], pr["diff"])
        context["correctness_review"] = result
        self.log(context, "completed correctness review")
        return context
