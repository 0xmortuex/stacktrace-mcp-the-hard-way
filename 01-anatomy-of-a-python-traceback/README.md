# Module 01: Anatomy of a Python Traceback

## The Concept

A traceback is text meant for a human reading top to bottom. An agent needs data. The first
decision of the whole project is the **data model**, because every later module (chains,
other languages, fingerprints, mapping) hangs off it:

```
Exc    type, message, frames, via
Frame  file, line, function, source, kind
```

One decision inside it matters more than the rest: **frames are stored innermost-first.**

```
Traceback (most recent call last):          <- Python prints the OUTERMOST call first
  File "/app/main.py", line 14, in <module>
    print(compute(0))
          ^^^^^^^^^^
  File "/app/main.py", line 10, in compute  <- ...and the line that raised, LAST
    return 100 / x
           ~~~~^~~
ZeroDivisionError: division by zero
```

Java, Node, .NET and Go (goroutine stacks) print the other way round. If every parser
normalises to "innermost first", everything downstream ("the first application frame", "the top
three frames for a fingerprint") is written once instead of six times.

## What the Parser Does

1. Find the `Traceback (most recent call last):` header.
2. Read frames: a `File "...", line N, in func` line, then indented source and, on Python 3.11+,
   a **caret line** (`^^^^`, `~~~~^~~`) that underlines the failing expression. The caret line
   is not source code, so it is recognised (only `~`, `^` and spaces) and skipped.
3. The first non-indented line after the frames is the exception line: `Type: message`, or just
   `Type` for things like `KeyboardInterrupt`.
4. **Truncated input is an error, not a guess.** A traceback with frames but no exception line
   raises `ValueError("...truncated input?")`. The real server turns that into a result flagged
   PARTIAL with a reason; it never invents a type.

## Why These Regexes Look Boring

```python
FRAME_RE = re.compile(r'^\s*File "(.*)", line (\d+)(?:, in (.*))?$')
```

Anchored at both ends, one greedy `.*` per group, no nested quantifiers like `(a+)+`. Input is
untrusted, so the rule is: **a regex may not backtrack catastrophically**. Module 07 tests this
with hostile inputs.

## Run It

```
python main.py
```

## What You Learned

- Normalise direction once, in the model.
- Caret lines exist and must not be mistaken for source.
- Boring, anchored regexes are a security property.

Next: [Module 02: Chained Exceptions](../02-chained-exceptions/)
