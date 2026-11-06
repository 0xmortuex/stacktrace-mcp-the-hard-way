# Module 06: Mapping Frames onto Files, Safely

## The Concept

You have `/app/src/pricing.py:8` from a production container and a checkout on your laptop at
`C:\Users\you\proj`. "Show me line 8" sounds like `open(path)`. It is not.

## The Hole

The path comes from **text an attacker may have written**. A log line, a bug report, a pasted
snippet:

```
File "../../../../etc/passwd", line 1, in evil
File "C:\Windows\win.ini", line 1, in evil
```

If the tool opens frame paths, any trace is a file-read primitive, and the tool then helpfully
prints the contents into the model's context.

## The Design: Look Up, Don't Open

1. **Index** the project directory once: every file that actually exists, keyed by lower-case base
   name. Do not follow symlinked directories (`followlinks=False`). Skip `node_modules`, `.git`,
   `.venv`.
2. **Match** a frame by *trailing path components*. Normalise separators, strip drive letters,
   drop `.`, `..` and empty segments, then compare from the right:

   ```
   frame:  /app/src/pricing.py     -> [app, src, pricing.py]
   local:  src/pricing.py          -> [src, pricing.py]      2 components match
   ```

   This is what makes container paths, Windows paths and bundler URLs work, and **it also means
   the frame text never reaches `open()`**: the traversal string is reduced to segments to compare
   against files that are already known to be inside the sandbox.
3. **Never guess.** If two files tie for the best match, say so and list them.
4. **Re-check at read time.** A file inside the project can be a symlink to `/etc/passwd`.
   `os.path.realpath` the match and require that it is still inside the real project root
   (`commonpath`) before reading. Cap how much you read.

## The Sandbox Comes From the Operator

The server's `--dir` is chosen by the person who installed it, not by the model or the trace. Any
`project_dir` the model passes is resolved against it and must remain inside it.

## Errors Are Part of the Answer

`NOT FOUND`, `ambiguous`, `line 99 does not exist (file has 12 lines)` and (in the real server)
`the source line recorded in the trace differs from the file` tell the agent the file changed
since the crash. Those are more valuable than a silently wrong snippet.

## Run It

```
python main.py
```

The check builds a real temporary project, plants a `secret.txt` next to it, and a symlink to it
inside it, then throws traversal strings and absolute paths at `show()`.

## What You Learned

- Treat every path in untrusted text as data; look it up in an index of what exists.
- Suffix matching solves container and Windows paths.
- Symlinks need a `realpath` check at read time.

Next: [Module 07: MCP Wrapper and Testing](../07-mcp-wrapper-and-testing/)
