from typing import Any, Dict

from src.agents.base_agent import BaseAgent
from src.skills.review_style import review_style


class StyleAgent(BaseAgent):
    name = "style_agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pr = context["pr"]
        result = review_style(pr["title"], pr["body"], pr["diff"])
        context["style_review"] = result
        self.log(context, "completed style review")
        return context
