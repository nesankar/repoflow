"""Command line entry point: `repoflow compute` and `repoflow present`."""

import argparse

from . import __version__
from .compute import compute
from .present import present


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="repoflow",
        description="See what your AI is building: an AI-assisted code-property + "
                    "data-flow graph, rendered as an interactive picture.",
    )
    parser.add_argument("--version", action="version", version="repoflow " + __version__)
    sub = parser.add_subparsers(dest="command")

    # ---- stage 1 -----------------------------------------------------------
    c = sub.add_parser(
        "compute",
        help="Print the prompt to feed your AI assistant (it writes the graph JSON).",
    )
    c.add_argument("root", nargs="?", default=".", help="Repository root to analyze (default: .).")
    c.add_argument("-o", "--output", default="repoflow.json",
                   help="Where the AI should write the graph (default: repoflow.json).")
    c.add_argument("--no-copy", action="store_true", help="Do not copy the prompt to the clipboard.")
    c.add_argument("--no-gitignore", action="store_true",
                   help="Do not add the generated graph files to the repo's .gitignore.")

    # ---- stage 2 -----------------------------------------------------------
    p = sub.add_parser(
        "present",
        help="Render a graph JSON into an interactive HTML page and open it.",
    )
    p.add_argument("source", nargs="?", default="repoflow.json",
                   help="Graph JSON to read (default: repoflow.json).")
    p.add_argument("-o", "--output", default=None,
                   help="HTML file to write (default: alongside the JSON).")
    p.add_argument("--no-open", action="store_true", help="Write the HTML but do not open a browser.")
    p.add_argument("--demo", action="store_true", help="Render the bundled demo graph instead of a file.")
    p.add_argument("--no-gitignore", action="store_true",
                   help="Do not add the generated graph files to the repo's .gitignore.")

    args = parser.parse_args(argv)

    if args.command == "compute":
        compute(root=args.root, output=args.output, copy=not args.no_copy,
                gitignore=not args.no_gitignore)
    elif args.command == "present":
        present(source=args.source, output=args.output, open_browser=not args.no_open,
                demo=args.demo, gitignore=not args.no_gitignore)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
