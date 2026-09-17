"""
CLI entry point.

Usage:
  export ANTHROPIC_API_KEY=your_key
  export GITHUB_TOKEN=your_token          # optional for public repos, required to --post
  python main.py --owner OWNER --repo REPO --pr PR_NUMBER [--post]

Example:
  python main.py --owner octocat --repo Hello-World --pr 1
"""

import argparse

from src.agents.correctness_agent import CorrectnessAgent
from src.agents.security_agent import SecurityAgent
from src.agents.style_agent import StyleAgent
from src.agents.synthesizer_agent import SynthesizerAgent
from src.orchestrator import Orchestrator
from src.skills.fetch_pr_diff import fetch_pr_diff
from src.skills.post_review_comment import post_review_comment
from src.skills.save_review_to_db import save_review_to_db
from src.skills.filter_reviewable_files import filter_reviewable_files, rebuild_diff_from_files
from src.skills.filter_reviewable_files import filter_reviewable_files, rebuild_diff_from_files
from src.skills.save_excluded_files import save_excluded_files



import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True, help="repo owner, e.g. 'octocat'")
    parser.add_argument("--repo", required=True, help="repo name, e.g. 'Hello-World'")
    parser.add_argument("--pr", required=True, type=int, help="PR number")
    parser.add_argument(
        "--post",
        action="store_true",
        help="post the synthesized review as a comment on the PR (requires GITHUB_TOKEN)",
    )
    args = parser.parse_args()

    print(f"Fetching PR #{args.pr} from {args.owner}/{args.repo}...")
    pr = fetch_pr_diff(args.owner, args.repo, args.pr)

    filtered = filter_reviewable_files(pr["files"])
    pr["files"] = filtered["included"]
    pr["diff"] = rebuild_diff_from_files(pr["files"])

    save_excluded_files(args.owner, args.repo, args.pr, filtered["excluded"])

    if filtered["excluded"]:
        print(f"Excluded {len(filtered['excluded'])} file(s) from review, logged to pr_review_excl.")

    if not pr["files"]:
        print("No reviewable files in this PR after filtering. Skipping review.")
        return
    
    print(f"PR title: {pr['title']}")
    print(f"Files changed: {len(pr['files'])}\n")

    orchestrator = Orchestrator(
        reviewers=[CorrectnessAgent(), SecurityAgent(), StyleAgent()],
        synthesizer=    SynthesizerAgent(),
    )

    result = orchestrator.run_review(pr)

    review_id = save_review_to_db(
            owner=args.owner,
            repo=args.repo,
            pr_number=args.pr,
            agent_comments={
                "correctness_agent": result["correctness_review"],
                "security_agent": result["security_review"],
                "style_agent": result["style_review"],
            },
            final_review=result["final_review"],
        )
    print(f"\nSaved as pending review #{review_id}. Awaiting moderation.")

    """
    print("=" * 70)
    print("FINAL REVIEW")
    print("=" * 70)
    print(result["final_review"])
    print()
    print("Trace:")
    for line in result["trace"]:
        print(f"  {line}")

    if args.post:
        confirm = input(
            f"\nAbout to post this review as a comment on {args.owner}/{args.repo}#{args.pr}. Proceed? [y/N] "
        )
        if confirm.strip().lower() == "y":
            post_review_comment(args.owner, args.repo, args.pr, result["final_review"])
            print("Posted.")
        else:
            print("Not posted.")
    """

if __name__ == "__main__":
    main()
