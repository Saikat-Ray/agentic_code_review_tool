"""
Runs the full graph: generate → moderate → (post if anything approved).

Usage:
  python run_pipeline.py --owner OWNER --repo REPO --pr PR_NUMBER
"""

import argparse

from src.top_orchestrator import build_graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True, type=int)
    args = parser.parse_args()

    graph = build_graph()
    final_state = graph.invoke(
        {"owner": args.owner, "repo": args.repo, "pr_number": args.pr}
    )

    print(f"Review id: {final_state['review_id']}")
    print(f"Approved comments posted: {final_state['approved_count']}")
    print(f"Rejected by moderator: {final_state['rejected_count']}")
    print("\nTrace:")
    for line in final_state["trace"]:
        print(f"  {line}")


if __name__ == "__main__":
    main()