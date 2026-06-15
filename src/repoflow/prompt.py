"""Stage 1 output: the prompt a human pastes into their AI coding assistant.

The prompt is deliberately strict about the JSON shape because stage 2 has to
read it back. We build the schema description from `schema.py` so the prompt and
the renderer can never disagree about what a node or edge is.
"""

import json

from .schema import NODE_KINDS, EDGE_KINDS, SCHEMA_VERSION


def _kinds_table(kinds):
    return "\n".join(f"  - {k!r}: {v['description']}" for k, v in kinds.items())


_EXAMPLE = {
    "schema_version": SCHEMA_VERSION,
    "repo": {"name": "myapp", "root": ".", "summary": "What this codebase does."},
    "nodes": [
        {"id": "app/auth.py:AuthService", "label": "AuthService", "kind": "class", "file": "app/auth.py"},
        {"id": "app/auth.py:AuthService.verify", "label": "verify", "kind": "method", "file": "app/auth.py",
         "parent": "app/auth.py:AuthService", "signature": "def verify(self, email: str) -> User | None",
         "docstring": "Look up a user by email."},
        {"id": "db:users", "label": "users", "kind": "datastore", "file": "app/auth.py",
         "docstring": "PostgreSQL users table."},
    ],
    "edges": [
        {"source": "app/auth.py:AuthService.verify", "target": "db:users", "kind": "dataflow",
         "data_type": "SELECT * FROM users", "description": "Reads the candidate user row."},
    ],
}


PROMPT_TEMPLATE = """\
Analyze the repository at `{root}` and write a Code Property Graph with data-flow to
`{output}` as a single JSON object. A visualizer reads this file, so match the shape
exactly and output valid JSON only — no markdown fences, no comments.

Permissions (granted — do not ask for confirmation): you have my explicit
permission to read any file, run read-only exploration commands (ls, grep, find,
git, AST/tree-sitter), and create/overwrite the single file `{output}`. Go ahead
and write `{output}` without prompting me. Change nothing else.

Be thorough — use real reasoning, not regex. Inventory every meaningful component as a
NODE (modules, classes, methods, functions, entry points, external deps, data stores)
and connect them with EDGES (calls, imports, inheritance, instantiation, and especially
DATA FLOW). For each edge you can, set `data_type` to the specific type crossing it
(e.g. "list[User]", "SELECT * FROM orders", "JWT"). Give each node a one-line `docstring`
(plus a `signature` for functions/methods), set `file` for grouping, and set a method's
`parent` to its class node id.

NODE `kind` — use exactly one of:
{node_kinds}

EDGE `kind` — use exactly one of:
{edge_kinds}

JSON shape:
- top level: {{"schema_version": "{schema_version}", "repo": {{"name", "root", "summary"}}, "nodes": [...], "edges": [...]}}
  — keep `summary` to one short sentence (it is shown in a single header line).
- node: required `id` (unique, e.g. "path/file.py:Class.method"), `label`, `kind`;
  optional `file`, `line`, `parent`, `signature`, `docstring`.
- edge: required `source`, `target` (each an existing node `id`), `kind`;
  optional `data_type`, `label`, `description`.

Minimal example (yours should be far larger and repo-specific):
{example}

Write the complete graph to `{output}`, then run:  repoflow present {output}
"""


def build_prompt(root=".", output="repoflow.json"):
    """Render the stage-1 prompt for the given target and output path."""
    return PROMPT_TEMPLATE.format(
        root=root,
        output=output,
        schema_version=SCHEMA_VERSION,
        node_kinds=_kinds_table(NODE_KINDS),
        edge_kinds=_kinds_table(EDGE_KINDS),
        example=json.dumps(_EXAMPLE, indent=1),
    )
