# Module 04: Application Frames vs Library Frames

## The Concept

A typical Django, Spring or Express trace has 40 to 80 frames and one or two of them are yours.
A report that lists all of them buries the answer; a report that hides the wrong ones lies. So:
classify every frame, show the application frames, **collapse** runs of the rest into one line
("4 library frames hidden: requests, urllib3"), and expose the **innermost application frame**
as a first-class field.

```
Frames (innermost first; * = application code):
    library   .../site-packages/requests/adapters.py:700 in send
    library   .../site-packages/requests/sessions.py:602 in get
  * app       /app/client.py:31 in fetch                  <- start here
```

## The Rules Are Conventions, Not Magic

| Language | Library | Standard library / runtime | Framework |
|---|---|---|---|
| Python | `/site-packages/`, `/dist-packages/` | `lib/python3.x/`, `<frozen ...>` | known names in site-packages (flask, django) |
| Node | `/node_modules/` | `node:internal/...`, `internal/...` | express, react-dom in node_modules |
| Java | `com.google.`, `org.apache.` | `java.`, `javax.`, `jdk.`, `sun.`, `kotlin.` | `org.springframework.`, `io.netty.` |
| Go | `/pkg/mod/`, `/vendor/` | import path with **no dot** in its first element (`net/http`) | |
| Rust | `.cargo/registry/src/` | `/rustc/<hash>/library/`, `std::`, `core::` | |
| .NET | `Newtonsoft.`, `Dapper.` | `System.`, `Microsoft.` | `Microsoft.AspNetCore.` |

Windows needs care: a Python install lives at `...\Python312\Lib\json\decoder.py`, no
`lib/python3.12/` in sight. Normalise backslashes first and match `python\d*/lib/`.

## Fail Safe

Heuristics are wrong sometimes. The question is which way. If an unrecognised path is classified
as a **library**, a real bug in your code disappears from the report. If it is classified as
**app**, you see one extra frame. So everything unrecognised is `app`. A vendored library in your
tree looks like your code; that is acceptable. Hiding your code is not.

## Run It

```
python main.py
```

## What You Learned

- Classification is per language and convention-based; keep each rule small and testable.
- The innermost application frame is the single most useful field in a trace report.
- Choose the failure direction deliberately: unknown means "show it".

Next: [Module 05: Fingerprinting](../05-fingerprinting/)
