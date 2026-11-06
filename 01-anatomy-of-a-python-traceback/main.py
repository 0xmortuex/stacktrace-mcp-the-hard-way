"""Module 01: the anatomy of a Python traceback.

Parse ONE traceback into data: a list of frames (file, line, function, source line) and the
exception type and message. Frames are stored innermost-first, because that is the order you
want when asking "where did it blow up?" - Python prints them the other way round.

Run:  python main.py        (checks itself with assert)
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field

# Anchored, no nested quantifiers: this stays linear even on hostile input (module 07 tests it).
FRAME_RE = re.compile(r'^\s*File "(.*)", line (\d+)(?:, in (.*))?$')
EXC_RE = re.compile(r"^([A-Za-z_][\w.]*)(?::[ ]?(.*))?$")


@dataclass
class Frame:
    file: str
    line: int
    function: str
    source: str | None = None
    kind: str = "unknown"  # filled in by module 04: app / library / stdlib / ...


@dataclass
class Exc:
    type: str
    message: str = ""
    frames: list[Frame] = field(default_factory=list)  # innermost first
    via: str | None = None  # module 02: how it relates to the exception that wraps it


def is_caret_line(s: str) -> bool:
    """Python 3.11+ underlines the failing expression with ^^^^ and ~~~~ on its own line."""
    s = s.strip()
    return bool(s) and set(s) <= set("~^ ")


def parse_traceback(text: str) -> Exc:
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not lines[i].startswith("Traceback (most recent call last):"):
        i += 1
    if i == len(lines):
        raise ValueError("no 'Traceback (most recent call last):' line found")
    i += 1
    frames: list[Frame] = []
    while i < len(lines):
        m = FRAME_RE.match(lines[i])
        if not m:
            break
        frame = Frame(file=m.group(1), line=int(m.group(2)), function=m.group(3) or "<module>")
        i += 1
        # the source line (and maybe a caret line) follow, indented by four spaces
        while i < len(lines) and lines[i].startswith("    ") and not FRAME_RE.match(lines[i]):
            if not is_caret_line(lines[i]) and frame.source is None:
                frame.source = lines[i].strip()
            i += 1
        frames.append(frame)
    if i >= len(lines):
        raise ValueError("traceback has frames but no exception line (truncated input?)")
    m2 = EXC_RE.match(lines[i])
    if not m2:
        raise ValueError(f"expected an exception line, got {lines[i]!r}")
    frames.reverse()  # innermost first
    return Exc(type=m2.group(1), message=m2.group(2) or "", frames=frames)


SAMPLE = """\
Traceback (most recent call last):
  File "/app/main.py", line 14, in <module>
    print(compute(0))
          ^^^^^^^^^^
  File "/app/main.py", line 10, in compute
    return 100 / x
           ~~~~^~~
ZeroDivisionError: division by zero
"""


def main() -> None:
    exc = parse_traceback(SAMPLE)
    assert exc.type == "ZeroDivisionError"
    assert exc.message == "division by zero"
    assert [f.function for f in exc.frames] == ["compute", "<module>"]  # innermost first
    assert exc.frames[0].line == 10
    assert exc.frames[0].source == "return 100 / x"  # the caret line did not become the source
    # a missing exception line is an error, not a guess
    try:
        parse_traceback(SAMPLE.rsplit("ZeroDivisionError", 1)[0])
    except ValueError as e:
        assert "truncated" in str(e)
    else:
        raise AssertionError("truncated input must raise")
    print(f"ok: {exc.type}: {exc.message}, innermost frame {exc.frames[0].file}:{exc.frames[0].line}")


if __name__ == "__main__":
    main()
    sys.exit(0)
