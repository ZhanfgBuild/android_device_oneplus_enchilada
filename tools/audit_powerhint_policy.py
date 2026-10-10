#!/usr/bin/env python3
"""Static, read-only libperfmgr powerhint.json validator for OnePlus 6 AOSP 17.

Structural errors fail the build gate; policy risks are printed as warnings.
This DOES NOT prove hint execution, service health, frequency correctness, or boot.
"""
import argparse
import json
from pathlib import Path
import sys


def inspect(config):
    errors, warnings = [], []
    if not isinstance(config, dict):
        return ["top-level JSON must be an object"], warnings, {}
    nodes = config.get("Nodes")
    actions = config.get("Actions")
    if not isinstance(nodes, list) or not isinstance(actions, list):
        return ["Nodes and Actions must both be JSON arrays"], warnings, {}
    by_name = {}
    seen_paths = {}
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"Nodes[{i}] must be an object")
            continue
        name, path, values = node.get("Name"), node.get("Path"), node.get("Values")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"Nodes[{i}]: missing Name")
            continue
        if name in by_name:
            errors.append(f"duplicate Node name: {name}")
        by_name[name] = node
        if not isinstance(path, str) or not path.startswith(("/sys/", "/dev/", "/proc/")):
            if not isinstance(path, str) or not path.startswith(("vendor.", "persist.", "sys.")):
                warnings.append(f"Node {name}: nonstandard or missing Path {path!r}")
        if not isinstance(values, list) or not values or any(not isinstance(v, str) for v in values):
            errors.append(f"Node {name}: Values must be a nonempty list of strings")
        else:
            if len(values) != len(set(values)):
                warnings.append(f"Node {name}: duplicated Values entries")
            di = node.get("DefaultIndex", len(values)-1)
            if type(di) is not int or not (0 <= di < len(values)):
                errors.append(f"Node {name}: invalid DefaultIndex {di!r}")
        if isinstance(path, str):
            if path in seen_paths and seen_paths[path] != name:
                warnings.append(f"Node {name}: shares path with {seen_paths[path]}; coordinate policy writes")
            seen_paths[path] = name
        if path and path.endswith("scaling_governor"):
            warnings.append(f"Node {name}: direct governor writes require single-owner arbitration")
    seen_actions = set()
    hint_counter = {}
    for i, action in enumerate(actions):
        if not isinstance(action, dict):
            errors.append(f"Actions[{i}] must be an object")
            continue
        hint, node, val, duration = (action.get(k) for k in ("PowerHint", "Node", "Value", "Duration"))
        if not isinstance(hint, str) or not hint:
            errors.append(f"Actions[{i}]: missing PowerHint")
            continue
        if not isinstance(node, str) or node not in by_name:
            errors.append(f"Actions[{i}]: missing or unknown Node {node!r}")
            continue
        if not isinstance(val, str) or val not in by_name[node].get("Values", []):
            errors.append(f"Actions[{i}]: value {val!r} not permitted for Node {node!r}")
        if type(duration) is not int or duration < 0:
            errors.append(f"Actions[{i}]: Duration must be a nonnegative integer")
        key = hint, node
        if key in seen_actions:
            errors.append(f"duplicate Node action for PowerHint={hint}, Node={node}")
        seen_actions.add(key)
        hint_counter[hint] = hint_counter.get(hint, 0) + 1
        if duration == 0 and hint in ("INTERACTION", "LAUNCH", "AUDIO_LAUNCH"):
            warnings.append(f"{hint}/{node}: Duration=0 means no automatic timeout in libperfmgr; verify paired end/release path")
        p = by_name[node].get("Path", "")
        if duration == 0 and val == "1" and any(token in p for token in ("force_clk_on", "force_rail_on", "force_bus_on")):
            warnings.append(f"{hint}/{node}: indefinite rail/clock force ON; verify hint cancellation")
        if hint == "SUSTAINED_PERFORMANCE" and "GPUMax" in node:
            warnings.append(f"{hint}/{node}: sustained mode caps GPU; validate sustained FPS + power before changing")
    return errors, warnings, {"nodes": len(nodes), "actions": len(actions), "hints": hint_counter}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("policy", type=Path, help="powerhint.json policy to inspect; never modifies source")
    args = parser.parse_args(argv)
    try:
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL: unable to parse policy JSON: {exc}", file=sys.stderr)
        return 1
    errors, warnings, stats = inspect(policy)
    print("ONEPLUS 6 POWERHINT STATIC AUDIT (no modifications)")
    print("Nodes:", stats.get("nodes", "unknown"), "Actions:", stats.get("actions", "unknown"))
    print("Hints:", ", ".join(f"{h}={c}" for h, c in sorted(stats.get("hints", {}).items())))
    for w in warnings:
        print("WARN:", w)
    for e in errors:
        print("FAIL:", e)
    if errors:
        print(f"FAIL: {len(errors)} structural error(s), {len(warnings)} review warning(s).")
        return 1
    print(f"PASS: structural checks only; {len(warnings)} warning(s) require review.")
    print("NOT VERIFIED: Android 17 VINTF, HAL service, runtime hints or actual clocks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
