#!/usr/bin/env python3
"""Inspect SDM845 kernel defconfig / generated .config for ROM performance gates.

Exit 1 only for basic missing capabilities, NOT because optional enhancements
are disabled. A successful result is NOT an Android 17 or kernel boot test.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

REQUIRED = {
    "CONFIG_CGROUPS": "Android task group foundation",
    "CONFIG_MEMCG": "memory cgroup for lmkd/memory accounting",
    "CONFIG_PSI": "pressure-stall signals for lmkd",
    "CONFIG_ZRAM": "compressed swap device",
    "CONFIG_CPU_FREQ": "CPU DVFS",
    "CONFIG_CPU_FREQ_GOV_SCHEDUTIL": "schedutil governor availability",
    "CONFIG_THERMAL": "thermal framework",
}
OPTIONAL = {
    "CONFIG_UCLAMP_TASK": "utilization clamps for latency-aware task profiles",
    "CONFIG_UCLAMP_TASK_GROUP": "task-group utilization clamps",
    "CONFIG_SCHED_WALT": "Qualcomm WALT scheduler; inspect interactions with EAS",
    "CONFIG_MEMCG_SWAP": "memory+swap cgroup accounting",
    "CONFIG_BPF_SYSCALL": "eBPF interfaces; verify Android 17 requirements separately",
    "CONFIG_ZRAM_WRITEBACK": "optional ZRAM writeback; not automatically desirable",
}


def parse_config(text: str) -> dict[str, str]:
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("CONFIG_") and "=" in line:
            key, value = line.split("=", 1)
            result[key] = value.strip()
        elif line.startswith("# CONFIG_") and line.endswith(" is not set"):
            key = line.split(" ", 2)[1]
            result[key] = "n"
    return result


def evaluate(options: dict[str, str]) -> tuple[list[str], list[str]]:
    errors = []
    notes = []
    for key, rationale in REQUIRED.items():
        value = options.get(key, "absent")
        if value != "y":
            errors.append(f"{key}={value} (required: {rationale})")
    for key, rationale in OPTIONAL.items():
        value = options.get(key, "absent")
        notes.append(f"{key}={value} ({rationale})")
    return errors, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Kernel defconfig or compiled .config")
    args = parser.parse_args()
    try:
        text = args.config.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"FAIL: cannot open kernel config: {exc}", file=sys.stderr)
        return 1
    errors, notes = evaluate(parse_config(text))
    for line in notes:
        print("OPTIONAL:", line)
    for line in errors:
        print("FAIL:", line)
    if errors:
        print("FAIL: required performance-related kernel config gates are missing.")
        return 1
    print("PASS: basic kernel configuration gates are present.")
    print("UNVERIFIED: Android 17 ABI/VINTF/SELinux/thermal policy, runtime and boot.")
    print("UClamp, cgroup v2 memory controller and ADPF require separate runtime tests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
