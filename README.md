# repoflow

**See what your AI is building.**

When you generate software with an AI assistant, the changes pile up faster than
anyone can read them. `repoflow` is a visual aid for humans: it turns your
codebase into an interactive **code-property + data-flow graph** — functions,
classes, files, external dependencies and data stores, with arrows showing how
data actually moves between them.

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
pip install repoflow
```

From source:

```bash
pip install -e .
```

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
