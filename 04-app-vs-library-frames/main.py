"""Module 04: application frames vs library frames.

A 60-frame trace is mostly framework plumbing. What you want is "the innermost frame that is
MY code". Classification is per language and uses only path / package conventions:

  Python  site-packages / dist-packages        -> library
          lib/python3.12/ (not site-packages)  -> stdlib
          <frozen ...>                         -> stdlib
  Node    node_modules/                        -> library
          node:internal/...                    -> runtime
  Java    java. javax. jdk. sun. kotlin.       -> stdlib
          org.springframework. etc.            -> framework
  Go      /pkg/mod/ or /vendor/                -> library
          GOROOT/src/ (no dot in import path)  -> stdlib / runtime

These are heuristics, and they fail in the safe direction: unknown code counts as YOUR code,
so nothing is hidden from you.

Run:  python main.py
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from loader import load  # noqa: E402

m1 = load("01-anatomy-of-a-python-traceback")
m3 = load("03-other-languages")


def norm(p: str) -> str:
    return p.replace("\\", "/")


def python_kind(path: str) -> str:
    p = norm(path)
    if p.startswith("<frozen"):
        return "stdlib"
    if "/site-packages/" in p or "/dist-packages/" in p:
        return "library"
    if re.search(r"/lib(64)?/python3?(\.\d+)?/", p.lower()) or re.search(r"/python\d*/lib/", p.lower()):
        return "stdlib"  # Windows: ...\Python312\Lib\json\decoder.py
    return "app"


def node_kind(path: str) -> str:
    p = norm(path)
    if p.startswith(("node:", "internal/")):
        return "runtime"
    if "/node_modules/" in p:
        return "library"
    return "app"


JAVA_STD = ("java.", "javax.", "jdk.", "sun.", "kotlin.")
JAVA_FRAMEWORK = ("org.springframework.", "org.hibernate.", "org.apache.catalina.", "io.netty.")


def java_kind(function: str) -> str:
    if function.startswith(JAVA_STD):
        return "stdlib"
    if function.startswith(JAVA_FRAMEWORK):
        return "framework"
    return "app"


def go_kind(function: str, path: str) -> str:
    p = norm(path)
    if "/pkg/mod/" in p or "/vendor/" in p:
        return "library"
    first = function.split("/", 1)[0].split(".", 1)[0]
    if function.startswith("runtime.") or function == "panic":
        return "runtime"
    if first != "main" and "." not in function.split("/", 1)[0]:
        return "stdlib"  # import paths without a dot in the first element are the standard library
    return "app"


def classify(language: str, exc: m1.Exc) -> m1.Exc:
    for f in exc.frames:
        if language == "python":
            f.kind = python_kind(f.file)
        elif language == "node":
            f.kind = node_kind(f.file)
        elif language == "java":
            f.kind = java_kind(f.function)
        elif language == "go":
            f.kind = go_kind(f.function, f.file)
    return exc


def innermost_app_frame(exc: m1.Exc) -> m1.Frame | None:
    """Frames are innermost-first, so the first app frame is the innermost one."""
    return next((f for f in exc.frames if f.kind == "app"), None)


PY = """\
Traceback (most recent call last):
  File "/app/client.py", line 31, in fetch
    resp = session.get(url, timeout=5)
  File "/usr/local/lib/python3.12/site-packages/requests/sessions.py", line 602, in get
    return self.request("GET", url, **kwargs)
  File "/usr/local/lib/python3.12/site-packages/requests/adapters.py", line 700, in send
    raise ConnectionError(e, request=request)
requests.exceptions.ConnectionError: Max retries exceeded
"""


def main() -> None:
    exc = classify("python", m1.parse_traceback(PY))
    assert [f.kind for f in exc.frames] == ["library", "library", "app"]
    inner = innermost_app_frame(exc)
    assert inner is not None and inner.function == "fetch" and inner.line == 31

    assert python_kind(r"C:\Users\me\AppData\Local\Programs\Python\Python312\Lib\json\decoder.py") == "stdlib"
    assert python_kind("<frozen runpy>") == "stdlib"

    chain = m3.parse_java(m3.JAVA_TEXT)
    root = classify("java", chain[-1])
    assert innermost_app_frame(root).function == "com.acme.Db.connect"  # type: ignore[union-attr]
    assert java_kind("org.springframework.web.servlet.FrameworkServlet.service") == "framework"
    assert java_kind("java.base/java.lang.Thread.run".rsplit("/", 1)[-1]) == "stdlib"

    assert node_kind("node:internal/modules/cjs/loader") == "runtime"
    assert node_kind("/srv/app/node_modules/express/lib/router/index.js") == "library"

    assert go_kind("net/http.(*conn).serve", "/usr/local/go/src/net/http/server.go") == "stdlib"
    assert go_kind("github.com/gin-gonic/gin.(*Context).Next", "/go/pkg/mod/github.com/gin-gonic/gin@v1.9.1/context.go") == "library"
    assert go_kind("main.main", "/app/main.go") == "app"

    # the safe direction: something unrecognised is treated as your code, never hidden
    assert python_kind("/somewhere/odd/place/util.py") == "app"
    print("ok: innermost application frame found through library frames in 4 languages")


if __name__ == "__main__":
    main()
