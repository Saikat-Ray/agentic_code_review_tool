from typing import Any, Dict

from src.agents.base_agent import BaseAgent
from src.skills.review_security import review_security


class SecurityAgent(BaseAgent):
    name = "security_agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pr = context["pr"]
        result = review_security(pr["title"], pr["body"], pr["diff"])
        context["security_review"] = result
        self.log(context, "completed security review")
        return context
