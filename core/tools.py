"""Tool registry: turn plain Python functions into tools the model can call.

To the model, a tool is just three things: a name, a description, and a JSON
schema for its arguments. The decorator below reads all three straight from the
function signature and docstring, so the Python function IS the documentation.
"""

import inspect
import re

# Python type hints -> JSON-schema types (the only ones our demos need).
PY_TO_JSON = {str: "string", int: "integer", float: "number", bool: "boolean"}
JSON_TO_PY = {"string": str, "integer": int, "number": (int, float), "boolean": bool}


class ToolRegistry:
    def __init__(self):
        self.functions = {}  # name -> the Python function we actually run
        self.schemas = {}  # name -> the description the model sees
        self.hints = {}  # name -> extra advice added to validation errors

    def tool(self, params=None, hint=""):
        """Decorator. `params` adds per-argument details, for example
        {"customer_id": {"description": "...", "pattern": "^CUS-\\d{4}$"}}.
        `hint` is appended to validation errors: error messages are prompts too."""

        def register(fn):
            properties, required = {}, []
            for name, param in inspect.signature(fn).parameters.items():
                extra = (params or {}).get(name, {})
                properties[name] = {"type": PY_TO_JSON[param.annotation], **extra}
                if param.default is inspect.Parameter.empty:
                    required.append(name)

            self.functions[fn.__name__] = fn
            self.hints[fn.__name__] = hint
            self.schemas[fn.__name__] = {
                "name": fn.__name__,
                "description": inspect.getdoc(fn),
                "input_schema": {"type": "object", "properties": properties, "required": required},
            }
            return fn

        return register

    def schema_list(self):
        """What we send to the model on every request."""
        return list(self.schemas.values())

    def validate(self, name, args):
        """Return None if the arguments match the schema, else an error message.

        The model WILL sometimes send bad arguments. We don't crash: we explain
        the problem so the model can fix it on the next step."""
        if name not in self.schemas:
            return f"Unknown tool '{name}'. Available tools: {', '.join(self.schemas)}."
        schema = self.schemas[name]["input_schema"]
        problem = None
        for key in schema["required"]:
            if key not in args:
                problem = f"missing required argument '{key}'"
        for key, value in args.items():
            spec = schema["properties"].get(key)
            if spec is None:
                problem = f"unexpected argument '{key}'"
            elif not isinstance(value, JSON_TO_PY[spec["type"]]):
                problem = f"'{key}' must be a {spec['type']}"
            elif "pattern" in spec and not re.fullmatch(spec["pattern"], value):
                problem = f"'{key}'={value!r} does not match the required format {spec['pattern']}"
        if problem is None:
            return None
        return f"Invalid arguments for {name}: {problem}. {self.hints[name]}".strip()

    def call(self, name, args):
        return str(self.functions[name](**args))
