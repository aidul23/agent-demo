"""Demo 1 tools: search the notes, do math, save a file.

Each tool is an ordinary Python function. The docstring is what the model reads
to decide WHEN to use it, so it is written for the model, not for us.
"""

import ast
import operator
import re
from pathlib import Path

from core.tools import ToolRegistry

HERE = Path(__file__).parent
NOTES_DIR = HERE / "data" / "notes"  # our offline "knowledge base"
OUTPUT_DIR = HERE / "output"  # the only folder the agent may write to

tools = ToolRegistry()


@tools.tool()
def search_notes(query: str) -> str:
    """Keyword search over the company knowledge base (team sizes, budgets, policies,
    deadlines). Returns the best-matching lines, each tagged with its file name.
    Use short keyword queries such as 'Atlas budget' or 'travel policy'."""
    query_words = _words(query)
    hits = []
    for path in sorted(NOTES_DIR.glob("*.md")):
        for line in path.read_text().splitlines():
            score = len(query_words & _words(line))  # how many query words this line contains
            if score and not line.startswith("#"):
                hits.append((score, f"[{path.name}] {line.strip()}"))
    hits.sort(key=lambda hit: -hit[0])  # most matching words first
    return "\n".join(text for _, text in hits[:5]) or "No matching notes."


def _words(text):
    """Lowercase words with a trailing 's' removed, so 'budgets' matches 'budget'."""
    return {w.removesuffix("s") for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 2}


# Safe arithmetic: we parse the expression and only allow numbers and operators.
# Using eval() here would let the model run ANY Python code on our machine.
OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
             ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow,
             ast.USub: operator.neg}


def _evaluate(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_evaluate(node.operand))
    raise ValueError("only numbers, + - * / % ** and parentheses are allowed (no commas in numbers)")


@tools.tool()
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression such as '84000 / 6' or '8 * (450 + 600)'.
    Always use this for arithmetic instead of calculating in your head."""
    result = _evaluate(ast.parse(expression, mode="eval").body)
    result = round(result, 2)
    if result == int(result):
        result = int(result)
    return f"{expression} = {result}"


@tools.tool()
def write_file(filename: str, content: str) -> str:
    """Save a text file (for example a markdown summary) into the output/ folder.
    Use a plain file name like 'summary.md', with no folders."""
    if Path(filename).name != filename or filename.startswith("."):
        return "Error: use a plain file name like 'summary.md' (no folders or '..')."
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / filename).write_text(content)
    return f"Saved {len(content)} characters to output/{filename}"
