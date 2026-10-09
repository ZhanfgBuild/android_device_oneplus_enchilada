#!/usr/bin/env python3
"""Read-only inventory of legacy Qualcomm post-boot performance writes.

Does not claim that every branch of the input shell script runs on SDM845.
"""
from __future__ import annotations
import argparse
from collections import Counter
from pathlib import Path
import re
import sys

PATTERNS = {
    "governor": re.compile(r"/scaling_governor\b"),
    "cpufreq_limits": re.compile(r"/scaling_(?:min|max)_freq\b"),
    "cpuset": re.compile(r"/(?:dev/cpuset|cpuset/)[^\s;]+"),
    "legacy_schedtune": re.compile(r"(?:/dev/stune/|schedtune\.)"),
    "thermal": re.compile(r"(?:/sys/class/thermal/|/thermal_message/|thermal-engine)"),
    "gpu": re.compile(r"(?:/kgsl-|/devfreq/|/gpuclk\b)"),
}


def scan(content: str) -> tuple[Counter, dict[str, list[int]]]:
    counts: Counter = Counter()
    samples: dict[str, list[int]] = {key: [] for key in PATTERNS}
    for idx, line in enumerate(content.splitlines(), 1):
        # Skip standalone comments and blank lines. These results are only
        # textual risk flags, not proof the platform executes this block.
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for key, expression in PATTERNS.items():
            if expression.search(line):
                counts[key] += 1
                if len(samples[key]) < 8:
                    samples[key].append(idx)
    return counts, samples


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    try:
        content = args.source.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    counts, samples = scan(content)
    print(f"Inspected {len(content.splitlines())} source lines.")
    for name in PATTERNS:
        print(f"{name}: {counts[name]} active-looking textual matches, examples at lines {samples[name]}")
    print("IMPORTANT: platform branches and runtime execution remain unverified.")
    print("Do not delete/rewrite this legacy script without inspecting SDM845 execution paths.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
