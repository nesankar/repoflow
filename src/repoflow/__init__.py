"""repoflow — see what your AI is building.

Two stages:

  1. ``repoflow compute``  prints a prompt for your AI coding assistant. The
     assistant does deep static analysis and writes a code-property + data-flow
     graph to a JSON file.

  2. ``repoflow present``  reads that JSON and renders an interactive HTML graph
     that opens in your browser.
"""

__version__ = "0.1.1"

# The single contract between the two stages. Both the prompt (stage 1) and the
# renderer (stage 2) are built from these. Keep them here so there is exactly
# one source of truth for "what kinds of things can appear in the graph".
from .schema import NODE_KINDS, EDGE_KINDS, SCHEMA_VERSION  # noqa: E402

__all__ = ["__version__", "NODE_KINDS", "EDGE_KINDS", "SCHEMA_VERSION"]
