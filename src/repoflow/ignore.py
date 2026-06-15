"""Keep generated graphs out of version control *and* container images.

The JSON graph and the HTML render are build artifacts, not source. Wherever
repoflow writes (or is about to write) them:

  * inside a git repo, it adds them to that repo's ``.gitignore``;
  * inside a Docker build context (a directory with a Dockerfile / compose file /
    existing ``.dockerignore``), it adds them to that context's ``.dockerignore``.

So the artifacts are never committed or baked into an image by accident, in any
project repoflow runs in. Best-effort and side-effect-light: it only touches a
``.gitignore`` when in a git repo and a ``.dockerignore`` when Docker is actually
in use, and it never raises into the main command flow.
"""

import os
import sys

MARKER = "# repoflow — generated graph artifacts"

# Files whose presence means "this directory is a Docker build context".
_DOCKER_FILES = frozenset({
    "Dockerfile", "Containerfile", ".dockerignore",
    "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml",
})


def _git_root(start):
    """Walk up from ``start`` to the enclosing git repo root, or None.

    ``.git`` is a directory in a normal clone and a file in worktrees/submodules,
    so we just test for its presence either way.
    """
    d = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def _is_docker_context(d):
    try:
        names = os.listdir(d)
    except OSError:
        return False
    return any(
        n in _DOCKER_FILES or n.endswith(".Dockerfile") or n.startswith("Dockerfile.")
        for n in names
    )


def _docker_context(start, stop):
    """Nearest ancestor of ``start`` (up to ``stop``) that is a Docker build context.

    Bounding the search at the git root (``stop``) keeps us from wandering into an
    unrelated Dockerfile higher up the filesystem. When there is no git root we
    only consider the artifact's own directory.
    """
    d = os.path.abspath(start)
    stop = os.path.abspath(stop) if stop else d
    while True:
        if _is_docker_context(d):
            return d
        if d == stop:
            return None
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def _add_entries(ignore_file, root, abs_paths, anchor):
    """Add each path (relative to ``root``) to ``ignore_file`` if not already there.

    ``anchor`` prefixes a leading ``/`` (git anchors patterns to the repo root;
    Docker matches relative to the context root, so no slash is needed). Returns
    the lines actually added.
    """
    text = ""
    if os.path.exists(ignore_file):
        with open(ignore_file, encoding="utf-8") as fh:
            text = fh.read()
    existing = {line.strip() for line in text.splitlines()}

    prefix = "/" if anchor else ""
    entries = [prefix + os.path.relpath(p, root).replace(os.sep, "/") for p in abs_paths]
    new = [e for e in dict.fromkeys(entries) if e not in existing]  # dedupe, keep order
    if not new:
        return []

    block = ""
    if text and not text.endswith("\n"):
        block += "\n"
    if MARKER not in existing:
        block += "\n" + MARKER + "\n"
    block += "\n".join(new) + "\n"
    with open(ignore_file, "a", encoding="utf-8") as fh:
        fh.write(block)
    return new


def _report(ignore_file, added):
    if added:
        print("[repoflow] added to %s: %s" % (os.path.relpath(ignore_file), ", ".join(added)),
              file=sys.stderr)


def protect(paths, enabled=True):
    """Ensure the given artifacts are ignored by git and Docker, where applicable."""
    if not enabled:
        return
    try:
        abs_paths = [os.path.abspath(p) for p in paths if p]

        # git: one .gitignore per repo root, patterns anchored to that root.
        git_groups = {}
        for p in abs_paths:
            root = _git_root(os.path.dirname(p))
            if root:
                git_groups.setdefault(root, []).append(p)
        for root, group in git_groups.items():
            _report(os.path.join(root, ".gitignore"),
                    _add_entries(os.path.join(root, ".gitignore"), root, group, anchor=True))

        # docker: one .dockerignore per build context, patterns relative to it.
        docker_groups = {}
        for p in abs_paths:
            ctx = _docker_context(os.path.dirname(p), _git_root(os.path.dirname(p)))
            if ctx:
                docker_groups.setdefault(ctx, []).append(p)
        for ctx, group in docker_groups.items():
            _report(os.path.join(ctx, ".dockerignore"),
                    _add_entries(os.path.join(ctx, ".dockerignore"), ctx, group, anchor=False))
    except Exception:
        return  # housekeeping must never break the actual command
