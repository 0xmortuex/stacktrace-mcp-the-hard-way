"""Module 02: chained exceptions, and finding the root cause.

Python prints the *cause first*:

    Traceback ... ValueError: invalid literal        <- where it started (the root cause)
    The above exception was the direct cause of the following exception:
    Traceback ... RuntimeError: config load failed   <- what finally escaped

We split on those two separator lines, parse each block with module 01, and reverse the
list so chain[0] is what was raised and chain[-1] is the root cause. 3.11 ExceptionGroup
output is drawn in a box of `|` characters; we peel the box apart recursively.

Run:  python main.py
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from loader import load  # noqa: E402

m1 = load("01-anatomy-of-a-python-traceback")
Exc = m1.Exc

CAUSE = "The above exception was the direct cause of the following exception:"
CONTEXT = "During handling of the above exception, another exception occurred:"


def parse_chain(text: str) -> list[Exc]:
    """Return exceptions outermost-first; chain[-1] is the root cause."""
    blocks: list[list[str]] = [[]]
    seps: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s in (CAUSE, CONTEXT):
            seps.append("cause" if s == CAUSE else "context")
            blocks.append([])
        else:
            blocks[-1].append(line)
    excs: list[Exc] = []
    for k, block in enumerate(blocks):
        exc = m1.parse_traceback("\n".join(block))
        if k < len(seps):
            exc.via = seps[k]  # this exception is the cause/context of the NEXT one printed
        excs.append(exc)
    excs.reverse()
    return excs


# ---------------------------------------------------------------- ExceptionGroup boxes

PIPE = re.compile(r"^( *)\|(?: (.*))?$")
HEAD = re.compile(r"^( *)\+ (.*)$")
CHILD = re.compile(r"^( *)\+-\+-+")
SEP = re.compile(r"^( *)\+-+ *(\d+)? *-*$")


def peel(lines: list[str], i: int, col: int) -> tuple[list[str], list[tuple[list[str], list]], int]:
    """Read one box layer at column `col`: its own text, and its children (text, grandchildren)."""
    own: list[str] = []
    kids: list[tuple[list[str], list]] = []
    while i < len(lines):
        m = PIPE.match(lines[i]) or HEAD.match(lines[i])
        if m and len(m.group(1)) == col and not CHILD.match(lines[i]) and not SEP.match(lines[i]):
            own.append(m.group(2) or "")
            i += 1
            continue
        m = CHILD.match(lines[i])
        if m and len(m.group(1)) == col:
            i += 1
            while True:
                kid_own, kid_kids, i = peel(lines, i, col + 2)
                kids.append((kid_own, kid_kids))
                s = SEP.match(lines[i]) if i < len(lines) else None
                if s and len(s.group(1)) == col + 2:
                    i += 1
                    if s.group(2) is None:  # the closing +------ line has no number
                        break
                    continue
                break
        break
    return own, kids, i


def parse_group(text: str) -> tuple[Exc, list[list[Exc]]]:
    """Return the group exception and one chain per sub-exception."""
    lines = text.splitlines()
    start = next(k for k, ln in enumerate(lines) if "Exception Group Traceback" in ln)
    col = len(lines[start]) - len(lines[start].lstrip())
    own, kids, _ = peel(lines, start, col)
    group = parse_chain("\n".join(own).replace("Exception Group Traceback", "Traceback"))[0]
    chains: list[list[Exc]] = []
    for kid_own, _kid_kids in kids:
        body = "\n".join(kid_own)
        if not body.startswith("Traceback"):
            # a sub-exception that was never raised has no traceback, only "Type: message"
            t, _, msg = body.partition(": ")
            chains.append([Exc(type=t, message=msg)])
        else:
            chains.append(parse_chain(body))
    return group, chains


CHAINED = """\
Traceback (most recent call last):
  File "/app/src/config.py", line 42, in parse_port
    port = int(raw)
           ^^^^^^^^
ValueError: invalid literal for int() with base 10: 'abc'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/main.py", line 10, in <module>
    main()
  File "/app/main.py", line 6, in main
    raise RuntimeError("config load failed") from e
RuntimeError: config load failed
"""

GROUP = """\
  + Exception Group Traceback (most recent call last):
  |   File "/app/t.py", line 12, in <module>
  |     asyncio.run(main())
  | ExceptionGroup: unhandled errors in a TaskGroup (2 sub-exceptions)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "/app/t.py", line 4, in boom
    |     raise ValueError("a")
    | ValueError: a
    +---------------- 2 ----------------
    | KeyError: 'b'
    +------------------------------------
"""


def main() -> None:
    chain = parse_chain(CHAINED)
    assert [e.type for e in chain] == ["RuntimeError", "ValueError"]
    root = chain[-1]
    assert root.type == "ValueError" and root.frames[0].function == "parse_port"
    assert root.via == "cause"  # ValueError was the direct cause of the RuntimeError

    group, kids = parse_group(GROUP)
    assert group.type == "ExceptionGroup" and "2 sub-exceptions" in group.message
    assert [c[0].type for c in kids] == ["ValueError", "KeyError"]
    assert kids[0][0].frames[0].function == "boom"
    print(f"ok: chain {' <- '.join(e.type for e in chain)}; group of {[c[0].type for c in kids]}")


if __name__ == "__main__":
    main()
