# Module 02: Chained Exceptions and the Root Cause

## The Concept

Real failures are wrapped. A config value fails to parse, the loader wraps it in a
`RuntimeError`, the web framework wraps *that* in a 500. The exception that reaches the log is
the last wrapper. The one you need to fix is the first.

Python prints the **cause first**, separated by one of two sentences:

```
ValueError: invalid literal ...                                  <- root cause

The above exception was the direct cause of the following exception:     (raise X from e)

RuntimeError: config load failed                                 <- what escaped
```

```
During handling of the above exception, another exception occurred:     (raised inside an except block)
```

The two sentences mean different things. "Direct cause" is deliberate (`from e`); "during
handling" is a bug or a retry path. They are recorded in `via`.

## The Algorithm

Split the text on the two separator lines, parse every block with module 01, then **reverse**
the list: `chain[0]` is what was finally raised and `chain[-1]` is the **root cause**. The same
convention is used for Java's `Caused by:` and .NET's `---> inner`, so a report can say
"root cause: `chain[-1]`" for every language.

## ExceptionGroup

Python 3.11 added `ExceptionGroup` (and `asyncio.TaskGroup` raises one). Its output is drawn in a
box:

```
  + Exception Group Traceback (most recent call last):
  |   File "/app/t.py", line 12, in <module>
  | ExceptionGroup: unhandled errors in a TaskGroup (2 sub-exceptions)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "/app/t.py", line 4, in boom
    | ValueError: a
    +---------------- 2 ----------------
    | KeyError: 'b'
    +------------------------------------
```

The grammar is recursive and **column-based**: a layer's text lives on `|` lines at one column;
`+-+---- 1 ----` starts the children, which live two columns deeper; `+---- 2 ----` separates
them and an unnumbered `+------` closes the list. A child can itself be a group, so `peel()`
recurses with `col + 2`. Note the second child above has *no* traceback, only `KeyError: 'b'`:
a sub-exception that was never raised has no frames.

A group has **several** root causes, one per leaf. Code that assumes "one root cause" is wrong
for TaskGroups; the real server reports all leaves.

## Run It

```
python main.py
```

## What You Learned

- Cause-first printing must be reversed so every language agrees on "root cause is last".
- Cause vs context are different facts; keep both.
- Box-drawn output is a small recursive grammar, not a regex.

Next: [Module 03: Other Languages](../03-other-languages/)
