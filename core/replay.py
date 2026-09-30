"""Record runs to JSON and replay them without calling the API.

Insurance for live demos: if the Wi-Fi or the API fails on stage, switch to
--replay. Only the MODEL's responses are recorded. Tools still run for real
during replay, so the loop you see is the same code doing the same work.
"""

import json
import time
from datetime import datetime
from pathlib import Path

from anthropic.types.beta import BetaMessage

from core import trace

RECORDINGS_DIR = Path(__file__).resolve().parent.parent / "recordings"
REPLAY_DELAY_SECONDS = 1.2  # a short pause per step so a replay looks live


def add_flags(parser):
    parser.add_argument("--pause", action="store_true", help="wait for Enter after each step")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--record", action="store_true", help="save this run to recordings/")
    mode.add_argument("--replay", nargs="?", const="default", metavar="FILE",
                      help="replay a recording instead of calling the API")


def pick_model(args, name, task, live_model):
    """Return (model function, task) for live, --record or --replay mode."""
    path = RECORDINGS_DIR / f"{name}.json"
    if args.replay:
        replayer = Replayer(path if args.replay == "default" else Path(args.replay))
        return replayer, replayer.task  # replay the task that was recorded
    if args.record:
        trace.note(f"● RECORDING to recordings/{path.name}")
        return Recorder(live_model, path, task), task
    return live_model, task


class Recorder:
    """Wraps the real model call and saves every response it returns."""

    def __init__(self, model, path, task):
        self.model, self.path = model, path
        self.data = {"task": task, "source": f"live recording, {datetime.now():%Y-%m-%d %H:%M}",
                     "responses": []}

    def __call__(self, **request):
        response = self.model(**request)
        self.data["responses"].append(response.model_dump(mode="json", exclude_none=True))
        # Save after every step, so even a run that crashes halfway is kept.
        self.path.parent.mkdir(exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))
        return response


class Replayer:
    """Pretends to be the model: hands back recorded responses in order."""

    def __init__(self, path):
        data = json.loads(path.read_text())
        self.task, self.responses = data["task"], list(data["responses"])
        trace.note(f"▶ REPLAY from recordings/{path.name} ({data.get('source', 'recording')}), no API calls")

    def __call__(self, **request):
        time.sleep(REPLAY_DELAY_SECONDS)
        if not self.responses:
            raise RuntimeError("The recording ran out of responses: this run diverged from it.")
        return BetaMessage.model_validate(self.responses.pop(0))
