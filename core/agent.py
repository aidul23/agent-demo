"""THE agent loop. No framework: this one file is the whole "agent".

    ask the model -> it requests a tool -> we check and run the tool ->
    we hand back the result -> repeat, until it answers or we hit max_steps.
"""

import os

import anthropic
from dotenv import load_dotenv

from core import trace

load_dotenv()
MODEL = os.getenv("MODEL", "claude-opus-5-5")


def call_claude(system, messages, tools):
    """One request to the model. The only place we talk to the API."""
    return anthropic.Anthropic().beta.messages.create(  # key comes from ANTHROPIC_API_KEY
        model=MODEL, max_tokens=16000, system=system, messages=messages, tools=tools,
        thinking={"type": "adaptive", "display": "summarized"},  # show a summary of its reasoning
        output_config={"effort": "medium"},
        betas=["server-side-fallback-2026-07-01"], fallbacks="default",  # if a request is refused, retry on a fallback model
    )


def run_agent(task, tools, system, max_steps=10, guards=(), validate=True, model=call_claude):
    """Run until the model gives a final answer. `guards` are functions that can
    veto a tool call before it runs (used by demo 2)."""
    messages = [{"role": "user", "content": task}]  # the agent's short-term memory
    history = []  # every (tool name, arguments) actually executed
    trace.task(task)

    for step in range(1, max_steps + 1):
        trace.step(step, max_steps)
        with trace.waiting():
            response = model(system=system, messages=messages, tools=tools.schema_list())
        # Append the model's turn exactly as returned (thinking blocks included).
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason == "refusal":
            trace.warning("The model declined this request.")
            return None

        calls = [block for block in response.content if block.type == "tool_use"]
        text = "\n".join(block.text for block in response.content if block.type == "text")
        reasoning = [block.thinking for block in response.content if block.type == "thinking" and block.thinking]
        if calls and text:
            reasoning.append(text)  # words written before a tool call are reasoning, not the answer
        if reasoning:
            trace.thinking("\n\n".join(reasoning))

        if not calls:  # no tool requested: this is the final answer
            trace.final_answer(text)
            return text

        # Run every requested tool and return all results in ONE user message.
        results = [run_tool(call, tools, guards, history, validate) for call in calls]
        messages.append({"role": "user", "content": results})
        trace.pause()

    trace.warning(f"Stopped after max_steps={max_steps} without a final answer.")
    return None


def run_tool(call, tools, guards, history, validate):
    """Check a tool call, run it, and package the result for the model."""
    trace.tool_call(call.name, call.input)

    # 1. Validate the arguments against the schema. 2. Let each guard veto the call.
    problem = tools.validate(call.name, call.input) if validate else None
    for guard in guards:
        problem = problem or guard(call.name, call.input, history)
    if problem:
        # Not a crash: the problem goes back to the model as an error it can react to.
        trace.warning(problem)
        return {"type": "tool_result", "tool_use_id": call.id, "content": problem, "is_error": True}

    history.append((call.name, call.input))
    try:
        output, is_error = tools.call(call.name, call.input), False
    except Exception as error:  # a failing tool is information for the model, too
        output, is_error = f"Error: {error}", True
    trace.observation(output, is_error)
    return {"type": "tool_result", "tool_use_id": call.id, "content": output, "is_error": is_error}
