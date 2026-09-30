"""Scenario 1 - loop: the agent retries forever."""

from core.tools import ToolRegistry
from demo2_failures.scenarios import Setup

TITLE = "Scenario 1 · The agent retries forever"
DESCRIPTION = ("fetch_report ALWAYS fails with a transient-looking 'Service busy' error.\n"
               "The system prompt tells the agent to retry temporary errors. What stops it?")
TASK = "Get the Q3 sales report and tell me the total revenue."

WHAT_WENT_WRONG = ("'Retry temporary errors' plus a tool that never recovers = the agent burns every "
                   "step (and every token) repeating the same call. Only max_steps stopped it.")
WHAT_FIXED_IT = ("A repeated-call guard: after 3 identical calls it blocks the 4th and tells the model "
                 "to stop and report the problem. The agent gives up gracefully and says why.")

SYSTEM_UNGUARDED = """You are a reporting assistant for the sales team.
The reporting service is sometimes flaky. If a call fails with a temporary error, retry it:
the team is counting on you to get the numbers."""

REPEAT_LIMIT = 3


def build(guarded):
    tools = ToolRegistry()

    @tools.tool()
    def fetch_report(report_name: str) -> str:
        """Fetch a report from the reporting service by name, for example 'Q3 sales'."""
        # The service is down for good, but the message makes it look temporary.
        raise ConnectionError("503 Service busy, please try again in a moment.")

    guards = [repeated_call_guard] if guarded else []
    # max_steps is set high on purpose: without the guard it is the only brake.
    return Setup(tools, SYSTEM_UNGUARDED, guards, max_steps=10)


def repeated_call_guard(name, args, history):
    """Same tool + same arguments already failed N times = no progress. Block it."""
    if history.count((name, args)) >= REPEAT_LIMIT:
        return (f"GUARD: {name} was already called {REPEAT_LIMIT} times with identical arguments "
                "and failed every time. Do not retry again. Stop and tell the user the "
                "service is unavailable.")
    return None
