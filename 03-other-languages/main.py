"""Module 03: other languages, same model.

Every language gets a small parser that returns the same `Exc` (type, message, frames
innermost-first). Differences you have to handle:

  Java    frames are `at pkg.Class.method(File.java:12)`, innermost FIRST, causes are
          `Caused by:`, and `... 23 more` means "the last 23 frames are the same as the
          enclosing exception's" - we copy them in so the cause is complete.
  Node    `at fn (file:line:col)` or `at file:line:col`, innermost first; `async`, `new`.
  Go      panic text, then `goroutine N [running]:` followed by PAIRS of lines:
          `pkg.fn(args)` and `<tab>/path/file.go:12 +0x1d`.

Run:  python main.py
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import replace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from loader import load  # noqa: E402

m1 = load("01-anatomy-of-a-python-traceback")
Exc, Frame = m1.Exc, m1.Frame

# ---------------------------------------------------------------- Java

JAVA_FRAME = re.compile(r"^\s*at ([\w$.<>/]+)\(([^)]*)\)")
JAVA_LOC = re.compile(r"^([\w$.\-]+\.\w+):(\d+)$")
MORE = re.compile(r"^\s*\.\.\. (\d+) more$")


def parse_java(text: str) -> list[Exc]:
    chain: list[Exc] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        m = JAVA_FRAME.match(line)
        if m and chain:
            qual = m.group(1).rsplit("/", 1)[-1]  # drop a module prefix like java.base/
            loc = JAVA_LOC.match(m.group(2))
            chain[-1].frames.append(
                Frame(file=loc.group(1) if loc else "", line=int(loc.group(2)) if loc else 0, function=qual)
            )
            continue
        mm = MORE.match(line)
        if mm and len(chain) > 1:
            n = int(mm.group(1))
            chain[-1].frames.extend(replace(f) for f in chain[-2].frames[-n:])
            continue
        header = s.removeprefix("Caused by: ")
        header = re.sub(r'^Exception in thread "[^"]*" ', "", header)
        typ, _, msg = header.partition(": ")
        chain.append(Exc(type=typ, message=msg, via="cause" if s.startswith("Caused by:") else None))
    return chain  # outermost first, root cause last


# ---------------------------------------------------------------- Node

NODE_FRAME = re.compile(r"^\s*at (?:async )?(?:(.+?) \()?(.+?):(\d+):(\d+)\)?$")


def parse_node(text: str) -> Exc:
    lines = text.splitlines()
    typ, _, msg = lines[0].partition(": ")
    exc = Exc(type=typ, message=msg)
    for line in lines[1:]:
        m = NODE_FRAME.match(line)
        if m:
            exc.frames.append(Frame(file=m.group(2), line=int(m.group(3)), function=m.group(1) or "<anonymous>"))
    return exc


# ---------------------------------------------------------------- Go

GO_FILE = re.compile(r"^\s+(\S.*?):(\d+)(?: \+0x[0-9a-f]+)?$")


def go_func_name(s: str) -> str:
    """'main.(*T).run(0xc000, {0x1})' -> 'main.(*T).run': drop the argument list at the END."""
    if not s.endswith(")"):
        return s
    depth = 0
    for k in range(len(s) - 1, -1, -1):
        depth += (s[k] == ")") - (s[k] == "(")
        if depth == 0:
            return s[:k]
    return s


def parse_go(text: str) -> Exc:
    lines = text.splitlines()
    first = next(ln for ln in lines if ln.startswith(("panic: ", "fatal error: ")))
    kind, _, msg = first.partition(": ")
    exc = Exc(type=kind, message=msg)
    i = next(k for k, ln in enumerate(lines) if ln.startswith("goroutine ")) + 1
    while i + 1 < len(lines):
        fm = GO_FILE.match(lines[i + 1])
        if not fm or not lines[i].strip():
            break
        exc.frames.append(Frame(file=fm.group(1), line=int(fm.group(2)), function=go_func_name(lines[i].strip())))
        i += 2
    return exc


def detect(text: str) -> str:
    """Pick a parser from the strongest signal in the text."""
    if "Traceback (most recent call last):" in text:
        return "python"
    if re.search(r"^goroutine \d+ \[", text, re.M) or text.startswith(("panic: ", "fatal error: ")):
        return "go"
    if re.search(r"^\s+at .*\(.*\.(java|kt|scala):\d+\)", text, re.M):
        return "java"
    if re.search(r"^\s+at .*:\d+:\d+\)?$", text, re.M):
        return "node"
    raise ValueError("no known stack trace format recognised")


JAVA_TEXT = """\
java.lang.RuntimeException: failed to process order 42
\tat com.acme.OrderService.process(OrderService.java:81)
\tat com.acme.OrderController.post(OrderController.java:30)
\tat com.acme.Main.main(Main.java:10)
Caused by: java.sql.SQLException: Connection refused
\tat com.acme.Db.connect(Db.java:19)
\tat com.acme.OrderService.process(OrderService.java:79)
\t... 2 more
"""

NODE_TEXT = """\
TypeError: Cannot read properties of undefined (reading 'name')
    at getUserName (/srv/app/src/users.js:23:20)
    at /srv/app/src/routes.js:8:15
    at async main (/srv/app/src/index.js:4:3)
"""

GO_TEXT = """\
panic: runtime error: index out of range [5] with length 3

goroutine 1 [running]:
main.process(...)
\t/app/main.go:12
main.(*Server).handle(0xc000012345, {0x4d6a3a, 0x5})
\t/app/server.go:42 +0x2c
main.main()
\t/app/main.go:20 +0x1d
exit status 2
"""


def main() -> None:
    chain = parse_java(JAVA_TEXT)
    assert [e.type for e in chain] == ["java.lang.RuntimeException", "java.sql.SQLException"]
    root = chain[-1]
    assert [f.function for f in root.frames] == [
        "com.acme.Db.connect",
        "com.acme.OrderService.process",
        "com.acme.OrderController.post",  # copied in from the enclosing trace by "... 2 more"
        "com.acme.Main.main",
    ]

    n = parse_node(NODE_TEXT)
    assert n.type == "TypeError" and [f.function for f in n.frames] == ["getUserName", "<anonymous>", "main"]
    assert n.frames[0].line == 23

    g = parse_go(GO_TEXT)
    assert g.type == "panic" and "index out of range" in g.message
    assert [f.function for f in g.frames] == ["main.process", "main.(*Server).handle", "main.main"]
    assert g.frames[1].file == "/app/server.go" and g.frames[1].line == 42

    assert (detect(JAVA_TEXT), detect(NODE_TEXT), detect(GO_TEXT)) == ("java", "node", "go")
    print("ok: java chain with '... 2 more' rebuilt, node frames, go goroutine pairs, auto-detect")


if __name__ == "__main__":
    main()
