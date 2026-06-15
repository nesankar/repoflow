# repoflow

**See what your AI is building.**

When you generate software with an AI assistant, the changes pile up faster than
anyone can read them. `repoflow` is a visual aid for humans: it turns your
codebase into an interactive **code-property + data-flow graph** — functions,
classes, files, external dependencies and data stores, with arrows showing how
data actually moves between them.

## Demo

See it instantly, no setup:

```bash
pip install repoflow-graph
repoflow present --demo      # opens an interactive graph in your browser
```

That renders a bundled example. Here's the idea in miniature — a tiny
`request → service → database` flow:

```json
{
  "nodes": [
    { "id": "api:create_task", "label": "create_task", "kind": "entrypoint" },
    { "id": "svc:add",         "label": "add",         "kind": "method",
      "docstring": "Persist a new task." },
    { "id": "db:tasks",        "label": "tasks",       "kind": "datastore" }
  ],
  "edges": [
    { "source": "api:create_task", "target": "svc:add",  "kind": "call",
      "data_type": "title: str" },
    { "source": "svc:add",         "target": "db:tasks", "kind": "dataflow",
      "data_type": "INSERT INTO tasks" }
  ]
}
```

…which becomes an interactive graph. Hover a node for its docstring, hover an
edge for the data flowing across it:

```
  ⬡ create_task ──call (title: str)──▶  ◯ add ──dataflow (INSERT INTO tasks)──▶  ⛁ tasks
   entrypoint                            method                                   datastore
```

It works in two stages.

### 1. `repoflow compute`

Prints a carefully-built prompt (and copies it to your clipboard). Paste it into
your AI coding assistant. The assistant does deep static analysis and writes a
graph to `repoflow.json`.

```bash
repoflow compute            # analyze the current directory
repoflow compute ./src -o graph.json
```

The prompt grants the assistant **read-only** permissions plus permission to
write exactly one file — the JSON graph. It asks for nodes (functions, methods,
classes, modules, entry points, external deps, data stores), edges (calls,
imports, inheritance, instantiation, and **typed data flows**), docstrings, and
signatures.

### 2. `repoflow present`

Reads that JSON and renders a self-contained, beautiful HTML page that opens in
your browser.

```bash
repoflow present            # reads repoflow.json, opens the graph
repoflow present graph.json -o report.html
repoflow present --demo     # see it instantly with a bundled example
```

In the graph:

- **Different shapes for different things** — see the legend (functions are
  ellipses, classes are rounded boxes, data stores are barrels, entry points are
  stars, external deps are diamonds).
- **Spatial grouping** — methods nest inside their class, classes inside their
  file. Code lives next to the code it belongs to.
- **Hover a node** to read its docstring and signature.
- **Hover an edge** to see the *type of data* flowing across it.
- **Click a node** to spotlight its neighborhood; **search** to find anything.

## Install

```bash
pip install repoflow-graph     # the command is still `repoflow`
```

From source:

```bash
pip install -e .
```

## Generated files stay out of git and Docker images

The JSON graph and the HTML render are build artifacts, not source. Whenever
repoflow writes (or is about to write) them, it adds them to the right ignore
files automatically, in any project you run it in:

- inside a git repo → its `.gitignore`
- inside a Docker build context (a dir with a `Dockerfile` / compose file /
  existing `.dockerignore`) → that context's `.dockerignore`

So the artifacts are never committed or baked into an image by accident. Pass
`--no-gitignore` to opt out.

## Design

- **Zero runtime dependencies.** Pure Python standard library.
- Rendering uses [Cytoscape.js](https://js.cytoscape.org) (loaded from a CDN in
  the generated HTML) with the `fcose` layout for compound-node grouping.
- The node/edge "visual language" lives in one place (`repoflow/schema.py`) and
  drives the prompt, the legend, and the graph styling — so they can never drift.

## The graph format

A single JSON document with `repo`, `nodes`, and `edges`. The full contract,
including every field and kind, is documented in `repoflow/schema.py`.

## License

MIT
