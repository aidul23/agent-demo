"""Demo 1: Tools that work. The happy path of the agent loop.

    python -m demo1_tools.run --task 1            # preset task 1, 2 or 3
    python -m demo1_tools.run --task "free text"  # a task from the audience
"""

import argparse

from core import replay, trace
from core.agent import MODEL, call_claude, run_agent
from demo1_tools.tools import tools

PRESET_TASKS = {
    "1": "Find how much budget per person the Atlas team has and save a short summary to atlas_summary.md.",
    "2": "Which team has the highest budget per person? Rank all teams and save the ranking to budget_ranking.md.",
    "3": ("The whole Comet team wants to attend the DevDays conference. Using the travel policy, "
          "what would it cost, and does it fit in their remaining budget? Save the answer to comet_devdays.md."),
}

SYSTEM_PROMPT = """You are an assistant for the product organization at Brightloop.
Answer from the company notes: search them instead of guessing.
Use the calculator for every calculation, and save files when the user asks.
Keep your final answer short: two or three sentences."""


def main():
    parser = argparse.ArgumentParser(description="Demo 1: Tools that work")
    parser.add_argument("--task", default="1", help="1, 2, 3 or your own task in quotes")
    replay.add_flags(parser)
    args = parser.parse_args()
    trace.configure(pause=args.pause)

    name = f"demo1_task{args.task}" if args.task in PRESET_TASKS else "demo1_custom"
    task = PRESET_TASKS.get(args.task, args.task)
    model, task = replay.pick_model(args, name, task, call_claude)

    trace.banner("Demo 1 · Tools that work",
                 f"Tools: search_notes, calculator, write_file   ·   model: {MODEL}")
    run_agent(task, tools, SYSTEM_PROMPT, max_steps=10, model=model)


if __name__ == "__main__":
    main()
