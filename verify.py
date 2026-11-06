"""Run every module's main.py for real and require exit code 0 and an `ok:` line.

Each main.py checks its own results with assert, so a chapter whose code drifts out of sync
with what its README claims fails here. Module 07 starts a real MCP server subprocess and
talks to it over stdio.

Usage: python verify.py            # all modules
       python verify.py 03 05      # just these
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))


def modules(selected: list[str]) -> list[str]:
    names = sorted(d for d in os.listdir(ROOT) if d[:2].isdigit() and os.path.isfile(os.path.join(ROOT, d, "main.py")))
    if selected:
        names = [n for n in names if n[:2] in selected]
    if not names:
        sys.exit("no modules selected")
    return names


def main() -> int:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    failed: list[str] = []
    for name in modules(sys.argv[1:]):
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, name, "main.py")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=300,
            stdin=subprocess.DEVNULL,
        )
        ok_line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("ok:")), None)
        status = "PASS" if proc.returncode == 0 and ok_line else "FAIL"
        print(f"{status}  {name}  ({time.perf_counter() - t0:.1f}s)  {ok_line or ''}")
        if status == "FAIL":
            failed.append(name)
            print(proc.stdout[-2000:])
            print(proc.stderr[-2000:])
    if failed:
        print(f"\n{len(failed)} module(s) failed: {', '.join(failed)}")
        return 1
    print("\nall modules verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
