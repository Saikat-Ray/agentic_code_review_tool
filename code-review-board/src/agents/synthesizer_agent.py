from typing import Any, Dict

from src.agents.base_agent import BaseAgent
from src.skills.synthesize_review import synthesize_review


class SynthesizerAgent(BaseAgent):
    name = "synthesizer_agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        final_review = synthesize_review(
            pr_title=context["pr"]["title"],
            correctness_review=context["correctness_review"],
            security_review=context["security_review"],
            style_review=context["style_review"],
        )
        context["final_review"] = final_review
        self.log(context, "synthesized final review")
        return context
