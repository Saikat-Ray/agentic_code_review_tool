from typing import Any, Dict

from src.agents.base_agent import BaseAgent
from src.skills.moderate_comments import moderate_comments
from src.skills.post_review_comment import post_review_comment
from src.skills.save_review_to_db import get_comments_for_review, update_review_status
from src.skills.update_comment_status import update_comment_status


class ModeratorAgent(BaseAgent):
    name = "moderator_agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        review_id = context["review_id"]
        comments = get_comments_for_review(review_id)

        verdicts = moderate_comments(comments)
        update_comment_status(verdicts)

        verdict_by_id = {v["id"]: v["status"] for v in verdicts}
        approved = [c for c in comments if verdict_by_id.get(c["id"]) == "approved"]
        rejected_count = len(comments) - len(approved)

        self.log(context, f"moderated {len(comments)} comments: {len(approved)} approved, {rejected_count} rejected")

        if approved:
            body = "\n\n".join(f"**[{c['agent_name']}]**\n{c['comment']}" for c in approved)
            post_review_comment(context["owner"], context["repo"], context["pr_number"], body)
            update_review_status(review_id, "posted", f"{len(approved)} comment(s) posted after moderation")
            self.log(context, "posted approved comments to PR")
        else:
            update_review_status(review_id, "moderated", "all comments rejected by moderator")
            self.log(context, "no approved comments — nothing posted")

        context["approved_count"] = len(approved)
        context["rejected_count"] = rejected_count
        return context