"""Module 06: mapping frames onto files - safely.

The naive version of "show me the code for this frame" is `open(frame.file)`. That is a
file-read primitive controlled by whoever wrote the trace text:

    File "../../../../etc/passwd", line 1, in evil

The safe design never opens a path that came from the trace. Instead:

  1. walk the project directory ONCE and index the files that really exist there
     (never following symlinked directories);
  2. match each frame against that index by TRAILING path components - which also solves the
     container problem: /app/src/pricing.py matches ./src/pricing.py on `src/pricing.py`;
  3. before reading a matched file, resolve symlinks (realpath) and check the result is still
     inside the project directory.

Whatever a frame claims, it can only ever select a file that is already inside the sandbox.

Run:  python main.py
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from loader import load  # noqa: E402

m1 = load("01-anatomy-of-a-python-traceback")

SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__"}


def build_index(root: str) -> dict[str, list[str]]:
    """lower-case base name -> list of project-relative posix paths"""
    index: dict[str, list[str]] = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):  # never follow dir symlinks
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel_dir = os.path.relpath(dirpath, root)
        for fn in filenames:
            rel = fn if rel_dir == "." else rel_dir.replace(os.sep, "/") + "/" + fn
            index.setdefault(fn.lower(), []).append(rel)
    return index


def segments(path: str) -> list[str]:
    """Normalise separators and drop everything that could mean 'somewhere else'."""
    p = path.replace("\\", "/")
    if len(p) > 1 and p[1] == ":":  # C:
        p = p[2:]
    return [s for s in p.split("/") if s not in ("", ".", "..")]


def match(index: dict[str, list[str]], path: str) -> tuple[str | None, str]:
    segs = [s.lower() for s in segments(path)]
    if not segs:
        return None, "empty path"
    cands = index.get(segs[-1], [])
    if not cands:
        return None, f"no file named {segs[-1]!r} in the project"
    best, best_score = [], 0
    for c in cands:
        parts = c.lower().split("/")
        score = 0
        while score < min(len(parts), len(segs)) and parts[-1 - score] == segs[-1 - score]:
            score += 1
        if score > best_score:
            best, best_score = [c], score
        elif score == best_score:
            best.append(c)
    if len(best) > 1:
        return None, f"ambiguous: {sorted(best)}"  # never guess between equally good matches
    return best[0], f"matched {best_score} trailing component(s)"


def read_lines(root: str, rel: str) -> list[str]:
    real_root = os.path.realpath(root)
    real = os.path.realpath(os.path.join(real_root, *rel.split("/")))
    if os.path.commonpath([real_root, real]) != real_root:
        raise PermissionError(f"{rel} resolves outside the project directory")
    with open(real, "rb") as fh:
        data = fh.read(2_000_000)
    return data.decode("utf-8", errors="replace").splitlines()


def show(root: str, frame: m1.Frame, context: int = 2) -> str:
    rel, why = match(build_index(root), frame.file)
    if rel is None:
        return f"NOT FOUND {frame.file}: {why}"
    lines = read_lines(root, rel)
    if not 1 <= frame.line <= len(lines):
        return f"{rel}: line {frame.line} does not exist (file has {len(lines)} lines)"
    lo, hi = max(1, frame.line - context), min(len(lines), frame.line + context)
    body = "\n".join(f"{'>' if n == frame.line else ' '} {n:>4} | {lines[n - 1]}" for n in range(lo, hi + 1))
    return f"{rel} ({why})\n{body}"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = os.path.join(tmp, "proj")
        os.makedirs(os.path.join(project, "src"))
        with open(os.path.join(project, "src", "pricing.py"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("def compute(order):\n    price = 2\n    return order['qty'] * price\n")
        secret = os.path.join(tmp, "secret.txt")
        with open(secret, "w", encoding="utf-8") as fh:
            fh.write("TOP-SECRET\n" * 5)

        # container path -> local file
        out = show(project, m1.Frame(file="/app/src/pricing.py", line=3, function="compute"))
        assert "src/pricing.py" in out and ">    3 |     return order['qty'] * price" in out
        # Windows path
        out = show(project, m1.Frame(file="C:\\Users\\me\\proj\\src\\pricing.py", line=2, function="compute"))
        assert "src/pricing.py" in out
        # line that does not exist
        assert "does not exist" in show(project, m1.Frame(file="src/pricing.py", line=99, function="f"))
        # missing file
        assert "NOT FOUND" in show(project, m1.Frame(file="/app/nope.py", line=1, function="f"))

        # traversal attempts select nothing outside the sandbox
        for evil in ("../secret.txt", "../../secret.txt", "..\\..\\secret.txt", secret, "/../../secret.txt"):
            out = show(project, m1.Frame(file=evil, line=1, function="evil"))
            assert "TOP-SECRET" not in out, (evil, out)

        # a symlink inside the project that points outside is refused at read time
        link = os.path.join(project, "src", "linked.py")
        try:
            os.symlink(secret, link)
        except (OSError, NotImplementedError):
            print("note: this account cannot create symlinks; skipping the symlink check")
        else:
            try:
                show(project, m1.Frame(file="/x/linked.py", line=1, function="evil"))
            except PermissionError as e:
                assert "outside the project directory" in str(e)
            else:
                raise AssertionError("symlink escape was not blocked")
    print("ok: container/Windows paths mapped, traversal and symlink escapes blocked")


if __name__ == "__main__":
    main()
