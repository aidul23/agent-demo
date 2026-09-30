"""Make the agent loop visible: one clearly labeled, color-coded panel per event.

Everything the audience sees on screen goes through this file, so the agent
loop itself stays free of printing code.
"""

import json

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.text import Text  # Text() shows strings literally: '[file.md]' is not markup

console = Console()
MAX_OBSERVATION_CHARS = 1500  # long tool results get cut so the screen stays readable
_settings = {"pause": False}


def configure(pause=False):
    """--pause: wait for Enter after every step, so the presenter can explain it."""
    _settings["pause"] = pause


def _panel(body, title, color):
    console.print(Panel(body, title=title, title_align="left", border_style=color,
                        box=box.HEAVY, padding=(1, 2)))


def banner(title, description, mode=None):
    subtitle = {"guarded": "[bold green]🛡  GUARDED[/]", "unguarded": "[bold red]UNGUARDED[/]"}.get(mode, "")
    console.print(Panel(f"[bold]{title}[/]\n\n{description}", subtitle=subtitle,
                        border_style="white", box=box.DOUBLE, padding=(1, 2)))


def note(text):
    console.print(Text(text, style="dim"))


def task(text):
    _panel(Text(text, style="bold"), "📋 TASK", "white")


def step(number, max_steps):
    console.print()
    console.rule(f"[bold]Step {number} / {max_steps}[/]", style="grey50")


def waiting():
    """Spinner shown while the model (or the replay) is 'thinking'."""
    return console.status("[dim]🤖 waiting for the model…[/]", spinner="dots")


def thinking(text):
    _panel(Text(text), "🧠 THINKING / REASONING", "magenta")


def tool_call(name, args):
    pretty = Syntax(json.dumps(args, indent=2, ensure_ascii=False), "json",
                    theme="ansi_dark", word_wrap=True, background_color="default")
    _panel(pretty, f"🔧 TOOL CALL  →  {name}", "cyan")


def observation(text, is_error=False):
    if len(text) > MAX_OBSERVATION_CHARS:
        text = text[:MAX_OBSERVATION_CHARS] + f"\n… [truncated, {len(text)} chars total]"
    title = "📥 OBSERVATION (error)" if is_error else "📥 OBSERVATION"
    _panel(Text(text), title, "red" if is_error else "blue")


def final_answer(text):
    _panel(Markdown(text), "✅ FINAL ANSWER", "green")


def warning(text):
    _panel(Text(text, style="bold"), "⚠️  WARNING / GUARD TRIGGERED", "yellow")


def confirm(question):
    """Simulated human-in-the-loop approval (a y/n prompt in the terminal)."""
    return Confirm.ask(f"[bold yellow]👤 HUMAN CHECK:[/] {question}")


def summary(went_wrong, fixed_it):
    body = f"[bold red]What went wrong[/]\n{went_wrong}\n\n[bold green]What fixed it[/]\n{fixed_it}"
    console.print()
    _panel(body, "🎓 TAKEAWAY", "white")


def pause():
    if _settings["pause"]:
        console.input("[dim]   ⏎  press Enter for the next step…[/]")
