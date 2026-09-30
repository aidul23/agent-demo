"""Failure scenarios for demo 2. Each module in this folder defines:

    TITLE, DESCRIPTION, TASK            what the audience sees at the start
    WHAT_WENT_WRONG, WHAT_FIXED_IT      the takeaway panel at the end
    build(guarded) -> Setup             tools, system prompt and guards for one run
"""

from dataclasses import dataclass, field
from pathlib import Path

from core.tools import ToolRegistry

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


@dataclass
class Setup:
    tools: ToolRegistry
    system: str
    guards: list = field(default_factory=list)
    validate: bool = True
    max_steps: int = 8
