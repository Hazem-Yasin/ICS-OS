#!/usr/bin/env python3
"""Rebuild the writing map whenever a file in writing/ changes (stdlib polling).

    python writing-map/watch.py [--interval 2] [--settle 3]

Waits until edits stop for --settle seconds, then runs build_map.py --quiet.
Tick "auto-reload" in the viewer and it refreshes itself after each rebuild.
Stop with Ctrl+C.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
import os
WRITING = Path(os.environ.get("ICS_WRITING") or HERE.parent.parent / "ICS-Writing")


def snapshot():
    snap = {}
    for p in WRITING.rglob("*"):
        if ".obsidian" in p.parts or not p.is_file():
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        snap[str(p)] = (st.st_mtime_ns, st.st_size)
    return snap


def build():
    r = subprocess.run([sys.executable, str(HERE / "build_map.py"), "--quiet"])
    print(time.strftime("%H:%M:%S"), "rebuilt" if r.returncode == 0 else f"build failed ({r.returncode})", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--settle", type=float, default=3.0)
    a = ap.parse_args()
    print(f"Watching {WRITING} (Ctrl+C to stop)")
    last = snapshot()
    build()
    dirty_since = None
    try:
        while True:
            time.sleep(a.interval)
            cur = snapshot()
            if cur != last:
                last = cur
                dirty_since = time.time()
            elif dirty_since and time.time() - dirty_since >= a.settle:
                dirty_since = None
                build()
                last = snapshot()
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
