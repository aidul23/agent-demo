"""Scenario 2 - bad_args: the agent invents tool arguments."""

import json

from core.tools import ToolRegistry
from demo2_failures.scenarios import DATA_DIR, Setup

TITLE = "Scenario 2 · The agent invents tool arguments"
DESCRIPTION = ("get_customer needs an ID like CUS-0042, but the task only gives a NAME.\n"
               "A lookup tool exists, but its description is vague. Will the agent guess an ID?")
TASK = "Maria Lindqvist says her plan renews soon. Which plan is she on, and when does it renew?"

WHAT_WENT_WRONG = ("The agent passed a name where an ID belongs. With no validation, the legacy backend "
                   "silently returned a default account, and the agent confidently reported wrong data.")
WHAT_FIXED_IT = ("Schema validation rejected the invented ID before the tool ran, and the error message "
                 "pointed to find_customer. Error messages are prompts: write them for the model.")

SYSTEM_PROMPT = """You are a customer support assistant. Be quick: answer with as few tool calls as possible."""

CUSTOMERS = json.loads((DATA_DIR / "customers.json").read_text())


def build(guarded):
    tools = ToolRegistry()

    @tools.tool(
        params={"customer_id": {"description": "The customer id.", "pattern": r"^CUS-\d{4}$"}},
        hint="You only know the customer's NAME, so look up their ID with find_customer(q=<name>) first.",
    )
    def get_customer(customer_id: str) -> str:
        """Get a customer's account record: plan, seats and renewal date."""
        # Legacy backend quirk: an unknown ID silently falls back to the default account.
        record = CUSTOMERS.get(customer_id, CUSTOMERS["CUS-0000"])
        return json.dumps(record, indent=2)

    @tools.tool()
    def find_customer(q: str) -> str:
        """Directory utility."""  # a deliberately poor description
        matches = [{"customer_id": cid, "name": c["name"]} for cid, c in CUSTOMERS.items()
                   if "name" in c and q.lower() in c["name"].lower()]
        return json.dumps(matches, indent=2)

    # The whole difference: is the tool call checked against the schema before it runs?
    return Setup(tools, SYSTEM_PROMPT, validate=guarded, max_steps=6)
