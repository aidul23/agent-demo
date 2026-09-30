"""Demo 2: When agents fail. The same scenario, without and with a guard.

    python -m demo2_failures.run --scenario loop             # watch it fail
    python -m demo2_failures.run --scenario loop --guarded   # watch the guard catch it
"""

import argparse
import importlib

from core import replay, trace
from core.agent import MODEL, call_claude, run_agent

SCENARIOS = ["loop", "bad_args", "injection", "memory"]


def main():
    parser = argparse.ArgumentParser(description="Demo 2: When agents fail")
    parser.add_argument("--scenario", required=True, choices=SCENARIOS)
    parser.add_argument("--guarded", action="store_true", help="turn the scenario's guard on")
    replay.add_flags(parser)
    args = parser.parse_args()
    trace.configure(pause=args.pause)

    scenario = importlib.import_module(f"demo2_failures.scenarios.{args.scenario}")
    setup = scenario.build(args.guarded)
    mode = "guarded" if args.guarded else "unguarded"
    model, task = replay.pick_model(args, f"demo2_{args.scenario}_{mode}", scenario.TASK, call_claude)

    trace.banner(scenario.TITLE, f"{scenario.DESCRIPTION}\n\n[dim]model: {MODEL}[/]", mode)
    run_agent(task, setup.tools, setup.system, setup.max_steps, setup.guards, setup.validate, model)
    trace.summary(scenario.WHAT_WENT_WRONG, scenario.WHAT_FIXED_IT)


if __name__ == "__main__":
    main()
