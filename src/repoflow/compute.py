"""Stage 1: print the analysis prompt for the user's AI assistant."""

import shutil
import subprocess
import sys

from .prompt import build_prompt


def _try_clipboard(text):
    """Best-effort copy to the system clipboard. Returns True on success.
    Never raises — clipboard support is a nicety, not a requirement."""
    candidates = (
        ["pbcopy"],                       # macOS
        ["wl-copy"],                      # Wayland
        ["xclip", "-selection", "clipboard"],  # X11
        ["clip"],                         # Windows
    )
    for cmd in candidates:
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, input=text.encode("utf-8"), check=True)
                return True
            except Exception:
                return False
    return False


def compute(root=".", output="repoflow.json", copy=True):
    """Build the prompt, print it, and (best effort) put it on the clipboard."""
    prompt = build_prompt(root=root, output=output)
    print(prompt)

    if copy and _try_clipboard(prompt):
        print("\n[repoflow] Prompt copied to your clipboard — paste it into your AI assistant.",
              file=sys.stderr)
    else:
        print("\n[repoflow] Copy the text above into your AI assistant.", file=sys.stderr)
    return prompt
