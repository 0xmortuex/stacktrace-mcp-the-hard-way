"""Module 07: the MCP wrapper, and testing it for real.

Two tools on top of everything built so far:

  parse_trace(text)                 root cause, innermost app frame, fingerprint
  map_to_code(text, project_dir)    the frame's code from the sandbox directory

Design points that matter for an agent:

  * Only a ToolError's message reaches the client (mcp>=2 hides every other exception behind
    a bare "Error executing tool"), so EXPECTED failures are converted at the tool boundary
    into messages that say what to do next.
  * Input is untrusted text: cap its size, and test that hostile shapes finish quickly.
  * The sandbox directory comes from the server's command line (--dir), never from the model.

Run:  python main.py            starts a real server subprocess and talks to it over stdio
      python main.py --serve --dir PATH      (what the test launches)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from loader import load  # noqa: E402

m1 = load("01-anatomy-of-a-python-traceback")
m2 = load("02-chained-exceptions")
m4 = load("04-app-vs-library-frames")
m5 = load("05-fingerprinting")
m6 = load("06-mapping-frames-safely")

MAX_CHARS = 1_000_000
SANDBOX: str | None = None


class UserError(ValueError):
    """An expected failure with an actionable message."""


def analyse(text: str) -> list:
    if len(text) > MAX_CHARS:
        raise UserError(f"input is {len(text):,} characters; the limit is {MAX_CHARS:,}")
    try:
        chain = m2.parse_chain(text)
    except ValueError as e:
        raise UserError(f"no Python traceback recognised ({e}). Paste the raw traceback text.") from e
    for exc in chain:
        m4.classify("python", exc)
    return chain


def report(text: str) -> str:
    chain = analyse(text)
    root = chain[-1]
    inner = m4.innermost_app_frame(root)
    lines = [f"Exception: {chain[0].type}: {chain[0].message}"]
    if len(chain) > 1:
        lines.append("Chain: " + " <- ".join(e.type for e in chain) + f"   (root cause: {root.type})")
    lines.append(
        f"Innermost application frame: {inner.file}:{inner.line} in {inner.function}"
        if inner
        else "Innermost application frame: none (all library code)"
    )
    lines.append(f"Fingerprint: {m5.fingerprint(chain)}")
    return "\n".join(lines)


def code_for(text: str) -> str:
    if SANDBOX is None:
        raise UserError("start the server with --dir <project> to enable map_to_code")
    inner = m4.innermost_app_frame(analyse(text)[-1])
    if inner is None:
        raise UserError("the trace has no application frame to map")
    return m6.show(SANDBOX, inner)


def serve(sandbox: str | None) -> None:
    global SANDBOX
    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError

    SANDBOX = os.path.realpath(sandbox) if sandbox else None
    server = MCPServer("stacktrace-tutorial")

    @server.tool()
    def parse_trace(text: str) -> str:
        """Parse a Python traceback: exception chain, root cause, innermost application frame, fingerprint."""
        try:
            return report(text)
        except UserError as e:
            raise ToolError(str(e)) from e

    @server.tool()
    def map_to_code(text: str) -> str:
        """Show the source around the innermost application frame, from the --dir project directory."""
        try:
            return code_for(text)
        except (UserError, PermissionError, OSError) as e:
            raise ToolError(str(e)) from e

    server.run()


TRACE = """\
Traceback (most recent call last):
  File "/app/src/pricing.py", line 3, in compute
    return order['qty'] * price
KeyError: 'qty'
"""


async def client_session(project: str) -> None:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.abspath(__file__), "--serve", "--dir", project],
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        names = {t.name for t in (await session.list_tools()).tools}
        assert names == {"parse_trace", "map_to_code"}, names

        res = await session.call_tool("parse_trace", {"text": TRACE})
        assert not res.is_error and "KeyError" in res.content[0].text and "Fingerprint:" in res.content[0].text

        res = await session.call_tool("map_to_code", {"text": TRACE})
        assert not res.is_error and ">    3 |     return order['qty'] * price" in res.content[0].text

        # errors reach the agent WITH their message
        res = await session.call_tool("parse_trace", {"text": "hello"})
        assert res.is_error and "no Python traceback recognised" in res.content[0].text
        res = await session.call_tool("parse_trace", {"text": "x" * (MAX_CHARS + 1)})
        assert res.is_error and "limit is 1,000,000" in res.content[0].text

        # hostile frame paths cannot read outside the sandbox
        evil = TRACE.replace("/app/src/pricing.py", "../../secret.txt")
        res = await session.call_tool("map_to_code", {"text": evil})
        assert "TOP-SECRET" not in res.content[0].text

        # pathological input finishes quickly (linear parsing)
        t0 = time.perf_counter()
        await session.call_tool("parse_trace", {"text": 'Traceback (most recent call last):\n  File "' + '", line 1, in "' * 50_000})
        assert time.perf_counter() - t0 < 10


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = os.path.join(tmp, "proj")
        os.makedirs(os.path.join(project, "src"))
        with open(os.path.join(project, "src", "pricing.py"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("def compute(order):\n    price = 2\n    return order['qty'] * price\n")
        with open(os.path.join(tmp, "secret.txt"), "w", encoding="utf-8") as fh:
            fh.write("TOP-SECRET\n")
        asyncio.run(client_session(project))
    print("ok: MCP server answered over real stdio; errors, sandbox and timing checks passed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--dir")
    args = ap.parse_args()
    if args.serve:
        serve(args.dir)
    else:
        self_test()
