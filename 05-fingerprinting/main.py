"""Module 05: fingerprinting - "have I seen this bug before?"

A fingerprint must be STABLE for the same bug and DIFFERENT for another bug. So hash only the
things that identify a bug and normalise the things that vary per run:

  keep      exception types (top-level and root cause), innermost application frames
            (function name + file BASE name)
  drop      the message ("no tenant 4411"), line numbers (edits shift them), directories
            (container /app/src vs local C:\\proj\\src), memory addresses, generated class names
            ($$EnhancerBySpringCGLIB$$3fa1b2c4), library frames (a dependency upgrade must not
            change the identity of YOUR bug)

Keep the pre-hash components around so a changed fingerprint can be explained.

Run:  python main.py
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from loader import load  # noqa: E402

m1 = load("01-anatomy-of-a-python-traceback")
m2 = load("02-chained-exceptions")
m4 = load("04-app-vs-library-frames")

HEX_ADDR = re.compile(r"0x[0-9a-fA-F]+")
GENERATED = re.compile(r"\$\$[A-Za-z0-9_$]*|\$\d+")


def norm_function(fn: str) -> str:
    return GENERATED.sub("$gen", HEX_ADDR.sub("0x", fn))


def norm_file(path: str) -> str:
    return path.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]


def components(chain: list, with_lines: bool = False) -> list[str]:
    top, root = chain[0], chain[-1]
    parts = [f"top={top.type}", f"root={root.type}"]
    app = [f for f in root.frames if f.kind == "app"] or root.frames  # no app frames: use anything
    for k, f in enumerate(app[:3]):
        key = f"{norm_function(f.function)}|{norm_file(f.file)}"
        if with_lines:
            key += f":{f.line}"
        parts.append(f"f{k}={key}")
    return parts


def fingerprint(chain: list, with_lines: bool = False) -> str:
    return hashlib.sha256("\n".join(components(chain, with_lines)).encode()).hexdigest()[:16]


def py_chain(text: str) -> list:
    chain = m2.parse_chain(text)
    for exc in chain:
        m4.classify("python", exc)
    return chain


RUN_A = """\
Traceback (most recent call last):
  File "/app/src/orders.py", line 40, in handle
    total = compute(order)
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 99, in validate
    return self._v(x)
  File "/app/src/pricing.py", line 12, in compute
    return order["qty"] * price
KeyError: 'qty'
"""
# same bug, another host, after an edit moved the lines, with a different key in the message
RUN_B = """\
Traceback (most recent call last):
  File "C:\\Users\\fadi\\proj\\src\\orders.py", line 47, in handle
    total = compute(order)
  File "C:\\Users\\fadi\\proj\\src\\pricing.py", line 15, in compute
    return order["quantity"] * price
KeyError: 'quantity'
"""
OTHER_TYPE = RUN_A.replace("KeyError: 'qty'", "TypeError: unsupported operand")
OTHER_FUNC = RUN_A.replace("in compute", "in refund")


def main() -> None:
    a, b = py_chain(RUN_A), py_chain(RUN_B)
    assert fingerprint(a) == fingerprint(b), (components(a), components(b))
    assert fingerprint(a, with_lines=True) != fingerprint(b, with_lines=True)
    assert fingerprint(a) != fingerprint(py_chain(OTHER_TYPE))
    assert fingerprint(a) != fingerprint(py_chain(OTHER_FUNC))
    assert norm_function("com.acme.Svc$$EnhancerBySpringCGLIB$$3fa1b2c4.find") == norm_function(
        "com.acme.Svc$$EnhancerBySpringCGLIB$$99ee0011.find"
    )
    print(f"ok: fingerprint {fingerprint(a)} from {components(a)}")


if __name__ == "__main__":
    main()
