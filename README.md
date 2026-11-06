# Stack Traces — The Hard Way

Build an MCP server that turns pasted crash output into a root-cause report, step by step.
No parsing library, no framework: just regular expressions you can read, a small data model,
and the handful of design decisions that make the difference between a toy and a tool an AI
agent can trust.

At the end you will have built a minimal version of
[stacktrace-mcp](https://github.com/0xmortuex/stacktrace-mcp) yourself, and you will know why
the real one is shaped the way it is.

## Why This Exists

Most "log analysis" demos run a regex over text and call it done. A stack trace is harder than
that, and the hard parts are the interesting ones:

- one bug prints differently in six languages, innermost frame first in some and last in others;
- the line that matters is rarely the first line: the **root cause** is at the end of a chain of
  wrapped exceptions, and **your** code is buried in dozens of library frames;
- "have I seen this before?" needs a fingerprint that survives a redeploy, a different host and a
  moved line number;
- the input is **untrusted text** and the frames contain **paths**. A careless "show me the code"
  feature is a file-read hole.

## Who This Is For

- Developers who built a "hello world" MCP server and want a real one.
- Anyone who debugs production crashes from pasted logs.
- Anyone who has to parse hostile text safely.

**Prerequisites:** Python 3.10+ and basic regular expressions. `pip install -r requirements.txt`
(only the `mcp` SDK is needed, and only for module 07).

## Modules

| # | Module | What You'll Build |
|---|--------|-------------------|
| 01 | [Anatomy of a Python Traceback](01-anatomy-of-a-python-traceback/) | A frame/exception model and a parser, including 3.11 caret lines |
| 02 | [Chained Exceptions](02-chained-exceptions/) | `raise ... from`, implicit context, root cause, and ExceptionGroup boxes |
| 03 | [Other Languages](03-other-languages/) | Java `Caused by` + `... N more`, Node frames, Go goroutine dumps, auto-detect |
| 04 | [App vs Library Frames](04-app-vs-library-frames/) | Per-language classification and the innermost application frame |
| 05 | [Fingerprinting](05-fingerprinting/) | A stable bug identity: what to keep, what to normalise |
| 06 | [Mapping Frames to Files Safely](06-mapping-frames-safely/) | Container-path rewriting without ever opening a path from the trace |
| 07 | [MCP Wrapper and Testing](07-mcp-wrapper-and-testing/) | Tools with actionable errors, tested over a real stdio session |

Each module contains:
- **`README.md`**: the concepts and the design decisions
- **`main.py`**: working, commented code that checks its own results with `assert`
- **`break-it.md`**: challenges that break your code, with hints

## How To Use This Course

**Option A: Build along.** Read each module, run its `main.py`, then try the break-it challenges.

**Option B: Reference.** Modules load earlier ones through `loader.py`, so you can jump to any
single module and read it against the stage before it.

Everything is checked by one command:

```
pip install -r requirements.txt
python verify.py
```

`verify.py` runs every `main.py` for real (module 07 launches an MCP server subprocess and talks
to it over stdio). CI runs it on Linux and Windows.

## License

MIT
