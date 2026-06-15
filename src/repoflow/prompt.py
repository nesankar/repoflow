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
    "repo": {"name": "myapp", "root": ".", "summary": "One-paragraph overview of what this codebase does."},
    "nodes": [
        {"id": "app/api.py:handle_login", "label": "handle_login", "kind": "entrypoint",
         "file": "app/api.py", "line": 12, "signature": "def handle_login(req: Request) -> Response",
         "docstring": "HTTP handler that authenticates a user and returns a session token."},
        {"id": "app/auth.py:AuthService", "label": "AuthService", "kind": "class",
         "file": "app/auth.py", "line": 5, "docstring": "Verifies credentials against the users table."},
        {"id": "app/auth.py:AuthService.verify", "label": "verify", "kind": "method",
         "file": "app/auth.py", "line": 9, "parent": "app/auth.py:AuthService",
         "signature": "def verify(self, email: str, password: str) -> User | None",
         "docstring": "Returns the matching User or None."},
        {"id": "db:users", "label": "users", "kind": "datastore", "file": "app/auth.py",
         "docstring": "PostgreSQL `users` table."},
    ],
    "edges": [
        {"source": "app/api.py:handle_login", "target": "app/auth.py:AuthService.verify",
         "kind": "call", "data_type": "(email: str, password: str)",
         "description": "Login handler asks the auth service to verify the submitted credentials."},
        {"source": "app/auth.py:AuthService.verify", "target": "db:users",
         "kind": "dataflow", "data_type": "SELECT email, password_hash",
         "description": "Reads the candidate user row to compare the password hash."},
        {"source": "db:users", "target": "app/api.py:handle_login",
         "kind": "return", "data_type": "User", "description": "Authenticated user flows back to the handler."},
    ],
}


PROMPT_TEMPLATE = """\
================================ REPOFLOW :: STAGE 1 ================================
Paste everything between the lines below into your AI coding assistant.
====================================================================================

ROLE
You are a senior static-analysis engine. Analyze the repository at `{root}` and
produce a single Code Property Graph (CPG) enriched with data-flow, written to a
JSON file at `{output}`. This is read by a visualization tool, so the JSON shape
below is a hard contract — follow it exactly.

PERMISSIONS (granted)
- You MAY read every file in `{root}` and its subdirectories.
- You MAY run read-only commands to explore the tree (ls, grep/ripgrep, find,
  `git ls-files`, language servers, AST/`ast`/tree-sitter parsers, import graphs).
- You MAY create/overwrite exactly one file: `{output}`.
- Do NOT modify, move, or delete any source file. Do NOT run build/test/network
  commands or anything with side effects beyond writing `{output}`.

WHAT TO PRODUCE
Be thorough. Use the full strength of your reasoning, not just regex:
1. Inventory every meaningful component as a NODE: modules, classes, methods,
   free functions, program entry points (CLI/main/HTTP handlers/jobs), external
   third-party dependencies actually used, and data stores (DBs, caches, queues,
   files, env/secret sources).
2. Connect them with EDGES. Two flavors matter most:
   - structural: calls, imports, inheritance, instantiation.
   - DATA FLOW: where data actually moves between components. For every data-flow
     (and every call you can type), fill `data_type` with the most specific type
     you can infer (e.g. "List[User]", "bytes (gzip)", "SELECT * FROM orders",
     "JWT string"). Infer types even when not annotated; say "unknown" only if
     truly unknowable.
3. Write tight, accurate `docstring` text for every node (use the real docstring
   if present; otherwise summarize the behavior in one sentence). Write a
   `signature` for functions/methods.
4. Set `parent` on a method to its class node `id` so the picture nests methods
   inside classes inside files. Set `file` on everything you can — it controls
   spatial grouping in the final graph.
5. Prefer completeness and correctness over speed. Trace flows across files. If
   the repo is large, cover the most important paths first but aim to be exhaustive.

NODE KINDS (use the `kind` field, exactly these strings):
{node_kinds}

EDGE KINDS (use the `kind` field, exactly these strings):
{edge_kinds}

JSON CONTRACT
- One object with keys: "schema_version" (= "{schema_version}"), "repo", "nodes", "edges".
- Each NODE: required `id` (unique, stable, e.g. "path/file.py:Class.method"),
  `label`, `kind`. Optional but strongly encouraged: `file`, `line`, `parent`,
  `signature`, `docstring`, `tags`.
- Each EDGE: required `source`, `target` (both must equal some node `id`), `kind`.
  Optional: `data_type`, `label`, `description`.
- Output VALID JSON only into `{output}` — no markdown fences, no comments.

EXAMPLE (shape only — your real output should be far larger and repo-specific):
{example}

Now analyze `{root}` and write the complete graph to `{output}`.
====================================================================================
When the file is written, return to your terminal and run:  repoflow present {output}
====================================================================================
"""


def build_prompt(root=".", output="repoflow.json"):
    """Render the stage-1 prompt for the given target and output path."""
    return PROMPT_TEMPLATE.format(
        root=root,
        output=output,
        schema_version=SCHEMA_VERSION,
        node_kinds=_kinds_table(NODE_KINDS),
        edge_kinds=_kinds_table(EDGE_KINDS),
        example=json.dumps(_EXAMPLE, indent=2),
    )
