# Module 07: The MCP Wrapper, and Testing It For Real

## The Concept

The parsing is done; now give an agent two tools, `parse_trace` and `map_to_code`. MCP is
JSON-RPC over the server's stdin/stdout. With `MCPServer`, a tool is a decorated function and the
SDK builds the schema from the signature and the docstring. **The docstring is the agent's whole
manual** for the tool, so write it for the model: what it accepts, what it returns, limits.

## Errors Are Instructions

In `mcp>=2`, the client only receives the message of a `ToolError`. Any other exception turns
into a bare "Error executing tool X". So the boundary looks like this:

```python
try:
    return report(text)
except UserError as e:          # expected: bad input, missing --dir, too big
    raise ToolError(str(e)) from e
```

Expected failures get messages that say what to do next ("start the server with `--dir`",
"paste the raw traceback text", "the limit is 1,000,000 characters"). Unexpected exceptions are
real bugs and are deliberately **not** caught, so they surface in your logs instead of being
dressed up as user errors.

## Untrusted Input Is Part of the API

The text parameter is attacker-controlled. Three rules, all tested here:

1. **Cap the size** (here 1,000,000 characters; the real server uses 5,000,000) and say so.
2. **Linear time.** The test sends 50,000 repeated `", line 1, in "` fragments, the shape that
   makes a sloppy `File "(.*)", line (\d+)` regex quadratic, and requires an answer in seconds.
3. **Never execute or import anything from the text.** Paths and messages are data.

## Test It Over the Real Wire

`main.py` is both the server and its test client:

- `python main.py --serve --dir PATH` runs the server.
- `python main.py` starts that as a subprocess with `stdio_client`, then initialises a
  `ClientSession`, lists tools, calls them, and checks results, error messages, the sandbox and
  timing.

A unit test of `report()` can pass while the server is broken (wrong schema, a print to stdout
corrupting the protocol, an exception hidden by the SDK). Only a real session catches those.

Two pitfalls this avoids:

- **stdout is the protocol.** Never `print()` in the server path; use stderr.
- **Child processes on Windows consoles** default to cp1252; the test sets
  `PYTHONIOENCODING=utf-8` so non-ASCII trace text does not crash it.

## The Finished Server

[stacktrace-mcp](https://github.com/0xmortuex/stacktrace-mcp) is this plus Node, Java, Go, Rust and
.NET parsers, log-file scanning that streams and groups by fingerprint, comparison, an exception
reference table and a redactor, with 290 tests.

## Run It

```
python main.py
python ../verify.py        # everything
```

## What You Learned

- Docstrings are the agent's interface; errors are its guidance.
- Expected failures become `ToolError`; bugs stay bugs.
- Test the server as a client would: a real subprocess, a real session.
