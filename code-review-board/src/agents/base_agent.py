"""
Same interface as the compliance-case-investigator POC: every agent
implements run(context) -> context. Keeping this identical across
projects means an orchestrator or agent written for one POC is easy to
port to the other.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    name: str = "base_agent"

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def log(self, context: Dict[str, Any], message: str) -> None:
        context.setdefault("trace", []).append(f"[{self.name}] {message}")
