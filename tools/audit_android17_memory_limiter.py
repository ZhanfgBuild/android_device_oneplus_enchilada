#!/usr/bin/env python3
"""Verify two kernel-source prerequisites for Android 17 Memory Limiter.

Read-only. Source-level evidence is NOT the same as checking generated kernel
config, runtime cgroup hierarchy or SELinux permissions.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

MEMORY_FILES_START = "static struct cftype memory_files[] = {"


def inspect_kernel_memory(source: str) -> dict[str, bool]:
    if MEMORY_FILES_START not in source:
        raise ValueError("cgroup v2 memory_files[] table not found")
    block = source.split(MEMORY_FILES_START, 1)[1].split("\n};", 1)[0]
    names = set(re.findall(r'\.name\s*=\s*"([^"]+)"', block))
    return {
        "memory.high": "high" in names and "memory_high_write" in source,
        "memory.swap.max": "swap.max" in names or "swap" in names and
                           bool(re.search(r"swap.*max.*write", block)),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("memcontrol", type=Path)
    p.add_argument("--require-complete", action="store_true",
                   help="Fail if either Android 17 Memory Limiter interface is missing")
    a = p.parse_args()
    try:
        source = a.memcontrol.read_text(encoding="utf-8")
        features = inspect_kernel_memory(source)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    for name, present in features.items():
        print(f'{"PRESENT" if present else "MISSING"}: cgroup v2 {name}')
    if a.require_complete and not all(features.values()):
        print("FAIL: kernel source is not ready for Android 17 Memory Limiter", file=sys.stderr)
        return 1
    print("SOURCE AUDIT ONLY: generated .config, kernel boot and userspace runtime unverified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
