# From Answering to Doing: agent demos

Two live demos for the workshop *"From Answering to Doing: How AI agents use tools, remember, and act."*

- **Demo 1, Tools that work:** the happy path. The model reasons, picks tools, reads the results and chains steps.
- **Demo 2, When agents fail:** four realistic failures, each shown first without a guard and then with a simple guard.

There is no agent framework. The whole agent is one plain Python loop in [core/agent.py](core/agent.py).

```
core/agent.py     THE agent loop: ask model -> validate -> run tool -> append result -> repeat
core/tools.py     @tool decorator: a Python function becomes a JSON tool schema, plus argument validation
core/trace.py     color-coded panels for each step (THINKING, TOOL CALL, OBSERVATION, FINAL ANSWER, WARNING)
core/replay.py    --record / --replay, so a demo still works without Wi-Fi or the API
demo1_tools/      search_notes, calculator, write_file, plus a fictional company knowledge base
demo2_failures/   scenarios/{loop,bad_args,injection,memory}.py, plus planted data
recordings/       saved runs used by --replay
```

## Setup

Requires Python 3.11+.

```bash
cd agent-demos
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your ANTHROPIC_API_KEY in .env
```

`MODEL` in `.env` is optional and defaults to `claude-opus-5-5`. Any Claude model from 4.6 onward works (the loop uses adaptive thinking).

Run every command from the `agent-demos/` folder.

## Commands

Each command below runs in one of three modes. Add a flag to switch:

| Mode | Flag | Use it for |
|---|---|---|
| live | *(none)* | calls the API for real |
| pause | `--pause` | waits for Enter after every step so you can explain it (works with live and replay) |
| replay | `--replay` | plays `recordings/<name>.json` with no API calls and no key needed |
| record | `--record` | a live run that also saves itself to `recordings/` |

### Demo 1: Tools that work

```bash
python -m demo1_tools.run --task 1                  # Atlas budget per person -> atlas_summary.md
python -m demo1_tools.run --task 2                  # rank all teams by budget per person (parallel tool calls)
python -m demo1_tools.run --task 3                  # can Comet afford DevDays? (3 notes + 3 calculations)
python -m demo1_tools.run --task "How many engineers do we have in total?"   # audience task

python -m demo1_tools.run --task 1 --pause          # presenter mode
python -m demo1_tools.run --task 1 --replay         # no API
python -m demo1_tools.run --task 1 --replay --pause # no API, presenter mode
```

Saved files appear in `demo1_tools/output/`.

### Demo 2: When agents fail

Run each scenario twice: first without the guard, then with `--guarded`.

```bash
python -m demo2_failures.run --scenario loop                   # retries until max_steps
python -m demo2_failures.run --scenario loop --guarded         # stopped after 3 identical calls

python -m demo2_failures.run --scenario bad_args               # invents an ID, reports the wrong plan
python -m demo2_failures.run --scenario bad_args --guarded     # validation error points it to find_customer

python -m demo2_failures.run --scenario injection              # hidden text on the page -> secrets published
python -m demo2_failures.run --scenario injection --guarded    # untrusted-data labels + human y/n before public writes

python -m demo2_failures.run --scenario memory                 # trusts the stale date in memory
python -m demo2_failures.run --scenario memory --guarded       # checks the notes, catches the conflict, fixes memory
```

Add `--pause` and/or `--replay` to any of these, for example:

```bash
python -m demo2_failures.run --scenario memory --guarded --replay --pause
```

**Guaranteed injection success:** modern models often resist the injection when run live. This recording always shows the attack succeeding:

```bash
python -m demo2_failures.run --scenario injection --replay recordings/demo2_injection_attack_succeeds.json
```

`--record` never writes to that file, so re-recording can't overwrite it.

Output from demo 2 (the published "public" file and the working copy of memory) goes to `demo2_failures/output/`.

## Presenter cheat-sheet

| Run | Point this out on screen |
|---|---|
| Demo 1, task 1 | The model doesn't know the answer, so it runs a *loop*: search, notice "budgets are per team", search again for the headcount, calculate, save. Each panel is one pass through `run_agent`. |
| Demo 1, task 2 | Step 3 has **three tool calls in a single step**. The model spotted that the divisions don't depend on each other. |
| Demo 1, task 3 | It combines three notes (team, budget, policy) and correctly concludes "doesn't fit, EUR 900 short, needs VP approval". |
| Demo 1, custom | Let the audience pick a task. The loop code doesn't change, only the task does. |
| loop, unguarded | Every step is the same call and the same 503 error. Nothing in the loop notices that there's no progress. Only `max_steps` stops it. |
| loop, guarded | Watch the yellow GUARD panel on step 4. Ten lines of Python turn an endless loop into an honest "the service is down". |
| bad_args, unguarded | It passed a **name** as `customer_id`. There was no error, and the "Free plan, no renewal" answer is confidently wrong. Silent failures are the dangerous ones. |
| bad_args, guarded | The validation error message *tells the model what to do next*. Error messages are prompts. |
| injection, unguarded | Point at the white-on-white `<div>` in the OBSERVATION. The agent obeyed a web page, read `secrets.txt`, and published it, then said nothing about it in the final answer. |
| injection, guarded | The observation is wrapped in `<untrusted_web_content>`, the model calls out the hidden text, and the human check shows exactly what is about to be published. **Answer `y`** (the summary is clean). |
| memory, unguarded | Two steps and a wrong date. The memory entry had no source and no date, and the prompt told the agent to trust it. |
| memory, guarded | The entry now shows *who* wrote it and *when*. The agent verifies it, finds the 22 Sep change, answers 3 Nov, and writes the correction back to memory. |

Every demo 2 run ends with a **🎓 TAKEAWAY** panel ("What went wrong / What fixed it") that you can talk over.

## Pre-workshop checklist

- [ ] `pip install -r requirements.txt` in a fresh venv on the presentation laptop.
- [ ] Run every command once in replay mode (no key needed) to check the terminal font, colors and width on the projector. About 100 columns works well.
- [ ] Back up the hand-made recordings first: `cp -r recordings recordings_handmade`.
- [ ] Put your key in `.env` and **re-record every run live** so the recordings contain real model output. The shipped recordings were written by hand to show the intended behavior.
  ```bash
  for t in 1 2 3; do python -m demo1_tools.run --task $t --record; done
  for s in loop bad_args injection memory; do
    python -m demo2_failures.run --scenario $s --record
    python -m demo2_failures.run --scenario $s --guarded --record
  done
  ```
- [ ] Replay each new recording once. If a live run misbehaved (for example, the model resisted the injection, which is good news but a weaker demo), copy the hand-made file back from `recordings_handmade/`.
- [ ] Keep `demo2_injection_attack_succeeds.json` as your fallback for the injection demo.
- [ ] Keep a second terminal open with a `--replay` command ready to go in case the Wi-Fi fails.

## Replay notes

- Replay substitutes only the **model**. Tools still run for real, so files are written and the guards fire exactly as they would live.
- The human y/n prompt in `injection --guarded` still appears in replay. Answer `y` to match the recording.
- If a replay says *"the recording ran out of responses"*, the run went differently from the recording (for example, the data files were edited after recording). Re-record it.
