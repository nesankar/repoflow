"""Stage 2: turn a repoflow JSON graph into an interactive HTML page."""

import json
import os
import sys
import webbrowser
from importlib import resources

from . import schema
from .ignore import protect
from .schema import NODE_KINDS, EDGE_KINDS


def _load_template():
    return resources.files("repoflow.templates").joinpath("graph.html").read_text(encoding="utf-8")


def load_sample():
    """The bundled demo graph, used by `repoflow present --demo`."""
    return json.loads(resources.files("repoflow.data").joinpath("sample.json").read_text(encoding="utf-8"))


def build_elements(graph):
    """Flatten the graph into Cytoscape elements.

    Spatial grouping is the whole point of this step: we synthesize one compound
    "file" container per file path, parent each component into its file (or into
    its class, when the node declares one), and let class nodes act as compound
    containers for their methods. The result nests methods inside classes inside
    files — components live next to the code they belong to.
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_ids = {n["id"] for n in nodes}

    elements = []

    # One compound container per distinct file path.
    files = {}
    for n in nodes:
        path = n.get("file")
        if path and path not in files:
            fid = "file::" + path
            files[path] = fid
            elements.append({
                "data": {"id": fid, "label": path.split("/")[-1], "fullpath": path, "kind": "file-group"},
                "classes": "group",
            })

    for n in nodes:
        # A method may name its class as `parent`; otherwise fall back to the file
        # container. Drop dangling parents so Cytoscape never sees a bad id.
        parent = n.get("parent")
        if parent not in node_ids:
            parent = None
        if not parent and n.get("file"):
            parent = files.get(n["file"])

        data = {
            "id": n["id"],
            "label": n.get("label") or n["id"],
            "kind": n.get("kind", "function"),
            "file": n.get("file", ""),
            "line": n.get("line", ""),
            "signature": n.get("signature", ""),
            "docstring": n.get("docstring", ""),
        }
        if parent:
            data["parent"] = parent
        elements.append({"data": data})

    for i, e in enumerate(edges):
        if e.get("source") not in node_ids or e.get("target") not in node_ids:
            continue  # validate() already warned; skip so the picture still renders
        elements.append({"data": {
            "id": e.get("id", "edge-%d" % i),
            "source": e["source"],
            "target": e["target"],
            "kind": e.get("kind", "call"),
            "label": e.get("label", ""),
            "data_type": e.get("data_type", ""),
            "description": e.get("description", ""),
        }})

    return elements


def render_html(graph):
    """Return a complete, self-contained HTML document for the graph."""
    repo = graph.get("repo", {})
    payload = {
        "meta": {
            "name": repo.get("name", "repository"),
            "root": repo.get("root", ""),
            "summary": repo.get("summary", ""),
            "counts": {"nodes": len(graph.get("nodes", [])), "edges": len(graph.get("edges", []))},
        },
        "elements": build_elements(graph),
        "nodeKinds": NODE_KINDS,
        "edgeKinds": EDGE_KINDS,
    }
    template = _load_template()
    title = "repoflow — " + payload["meta"]["name"]
    # json.dumps is safe to drop into a <script> as long as we neutralize the one
    # sequence that could close the tag early.
    blob = json.dumps(payload).replace("</", "<\\/")
    return template.replace("__TITLE__", title).replace("__DATA__", blob)


def present(source=None, output=None, open_browser=True, demo=False, gitignore=True):
    """Read a graph JSON (or the bundled demo), write HTML, and open it."""
    if demo:
        graph = load_sample()
        default_out = "repoflow-demo.html"
    else:
        if not source:
            source = "repoflow.json"
        if not os.path.exists(source):
            raise SystemExit(
                "[repoflow] No graph found at %r.\n"
                "Run `repoflow compute` first, give your AI assistant the prompt,\n"
                "then run `repoflow present %s`." % (source, source)
            )
        with open(source, encoding="utf-8") as fh:
            try:
                graph = json.load(fh)
            except json.JSONDecodeError as exc:
                raise SystemExit("[repoflow] %s is not valid JSON: %s" % (source, exc))
        default_out = os.path.splitext(source)[0] + ".html"

    problems = schema.validate(graph)
    if problems:
        print("[repoflow] Graph loaded with %d warning(s):" % len(problems), file=sys.stderr)
        for p in problems[:20]:
            print("  - " + p, file=sys.stderr)
        if len(problems) > 20:
            print("  ... and %d more." % (len(problems) - 20), file=sys.stderr)

    out = output or default_out
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(render_html(graph))

    # Generated graph + its source JSON are artifacts — keep them out of git.
    protect([out] + ([] if demo else [source]), enabled=gitignore)

    abspath = os.path.abspath(out)
    print("[repoflow] Wrote %s" % abspath, file=sys.stderr)
    if open_browser:
        webbrowser.open("file://" + abspath)
    return abspath
