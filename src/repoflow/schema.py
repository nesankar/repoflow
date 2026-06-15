"""The graph schema — the one contract shared by both stages.

A repoflow graph is a JSON document::

    {
      "schema_version": "1.0",
      "repo": {"name": "...", "root": "...", "summary": "..."},
      "nodes": [ {node}, ... ],
      "edges": [ {edge}, ... ]
    }

A *node* is a component of the codebase::

    {
      "id":        "unique string, stable",      # required
      "label":     "display name",               # required
      "kind":      "function|method|class|...",  # required, see NODE_KINDS
      "file":      "relative/path.py",           # optional, drives spatial grouping
      "line":      42,                            # optional
      "parent":    "id of the class this method belongs to",  # optional
      "signature": "def foo(a: int) -> str",     # optional, shown on hover
      "docstring": "what it does",               # optional, shown on hover
      "tags":      ["..."]                        # optional
    }

An *edge* is a relationship — a call, or a flow of data::

    {
      "id":          "unique string",            # optional (auto-assigned)
      "source":      "node id",                  # required
      "target":      "node id",                  # required
      "kind":        "call|dataflow|...",        # required, see EDGE_KINDS
      "data_type":   "List[User]",               # optional, shown on hover
      "label":       "short edge label",         # optional
      "description": "longer note"               # optional, shown on hover
    }

NODE_KINDS / EDGE_KINDS below are the *single source of truth* for the visual
language: shape + colour + legend text. The prompt advertises them to the AI and
the renderer styles the graph from them, so they can never drift apart.
"""

SCHEMA_VERSION = "1.0"

# kind -> how it looks and what it means. `shape` values are Cytoscape.js shapes.
# A calm, rounded geometry — no spiky shapes — keeps the picture elegant.
NODE_KINDS = {
    "module":     {"shape": "round-rectangle", "color": "#64748b", "description": "Module / file-level scope"},
    "class":      {"shape": "round-rectangle", "color": "#a78bfa", "description": "Class definition"},
    "function":   {"shape": "ellipse",         "color": "#60a5fa", "description": "Free function"},
    "method":     {"shape": "ellipse",         "color": "#22d3ee", "description": "Class method"},
    "entrypoint": {"shape": "round-hexagon",   "color": "#fbbf24", "description": "Entry point (CLI / main / handler)"},
    "external":   {"shape": "round-diamond",   "color": "#f472b6", "description": "External / third-party dependency"},
    "datastore":  {"shape": "barrel",          "color": "#34d399", "description": "Data store (DB, file, cache, queue)"},
}

# kind -> how the relationship is drawn and what it means.
EDGE_KINDS = {
    "call":          {"color": "#94a3b8", "style": "solid",  "description": "Function / method call"},
    "dataflow":      {"color": "#2563eb", "style": "solid",  "description": "Data flows from source to target"},
    "import":        {"color": "#cbd5e1", "style": "dashed", "description": "Import / module dependency"},
    "inheritance":   {"color": "#8b5cf6", "style": "solid",  "description": "Subclass → superclass"},
    "instantiation": {"color": "#f59e0b", "style": "dotted", "description": "Creates an instance of"},
    "return":        {"color": "#10b981", "style": "solid",  "description": "Returns a value to caller"},
}


def validate(graph):
    """Return a list of human-readable problems. Empty list means the graph is
    usable. We are lenient: unknown kinds and missing optional fields are fine
    (the renderer degrades gracefully); we only flag what would actually break
    the picture — bad structure or edges pointing at nodes that don't exist."""
    errors = []

    if not isinstance(graph, dict):
        return ["Top level of the JSON must be an object."]

    nodes = graph.get("nodes")
    edges = graph.get("edges", [])

    if not isinstance(nodes, list) or not nodes:
        errors.append("`nodes` must be a non-empty list.")
        nodes = []
    if not isinstance(edges, list):
        errors.append("`edges` must be a list.")
        edges = []

    ids = set()
    for i, n in enumerate(nodes):
        where = f"nodes[{i}]"
        if not isinstance(n, dict):
            errors.append(f"{where} is not an object.")
            continue
        nid = n.get("id")
        if not nid:
            errors.append(f"{where} is missing required `id`.")
            continue
        if nid in ids:
            errors.append(f"{where} has duplicate id {nid!r}.")
        ids.add(nid)
        if not n.get("label"):
            errors.append(f"{where} ({nid!r}) is missing `label`.")
        if n.get("kind") not in NODE_KINDS:
            # Not fatal — renderer falls back — but worth telling the user.
            errors.append(
                f"{where} ({nid!r}) has unknown kind {n.get('kind')!r}; "
                f"expected one of {sorted(NODE_KINDS)}."
            )

    for i, e in enumerate(edges):
        where = f"edges[{i}]"
        if not isinstance(e, dict):
            errors.append(f"{where} is not an object.")
            continue
        for end in ("source", "target"):
            ref = e.get(end)
            if not ref:
                errors.append(f"{where} is missing `{end}`.")
            elif ref not in ids:
                errors.append(f"{where} {end} {ref!r} does not match any node id.")

    return errors
