"""
Central LLM factory. Every skill calls get_llm() instead of instantiating
ChatAnthropic/ChatOpenAI directly, so the provider is a one-line env
change, not a code change across every skill file.

.env:
  COMMENTER_LLM=anthropic        # or: openai
  ANTHROPIC_API_KEY=...
  ANTHROPIC_MODEL=claude-sonnet-4-6      # optional, has a default
  OPENAI_API_KEY=...
  OPENAI_MODEL=gpt-4o                    # optional, has a default
"""

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
DEFAULT_OPENAI_MODEL = "gpt-4o"


def get_llm(max_tokens: int = 800):
    provider = os.environ.get("COMMENTER_LLM", "anthropic").strip().lower()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
        return ChatAnthropic(model=model, max_tokens=max_tokens)

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        model = os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        return ChatOpenAI(model=model, max_tokens=max_tokens)

    raise ValueError(
        f"Unknown COMMENTER_LLM '{provider}'. Expected 'anthropic' or 'openai'."
    )