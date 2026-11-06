# Break It: Module 04

1. **A monorepo that vendors a library under `vendor/` inside the project.** Python rule: is it
   `app` or `library`? Argue both directions, then pick the fail-safe one.
2. **Windows Python with a venv inside the project:** `C:\proj\.venv\Lib\site-packages\...`.
   `python_kind` sees `/site-packages/` after normalisation. Is a *project-local* stdlib path like
   `C:\proj\lib\python3.12\x.py` classified wrongly? Construct it and see.
3. **Go function with a dotted first element but standard-library origin?** There is none, but
   there is a `testing` package that is stdlib yet mostly noise. Add a `framework` kind for it.
