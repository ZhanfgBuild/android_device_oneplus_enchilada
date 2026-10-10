#!/usr/bin/env python3
"""Check AOSP17 frozen Power AIDL enum ordinals against our event adapter.

Accepts exact source files downloaded from Google's pinned android-17.0.0_r1
tag; never substitutes Android master silently.
"""
import argparse
from pathlib import Path
import re
import sys

EXPECTED_BOOST = {
    "kInteraction": "INTERACTION",
    "kDisplayUpdate": "DISPLAY_UPDATE_IMMINENT",
    "kAudioLaunch": "AUDIO_LAUNCH",
}
EXPECTED_MODE = {
    "kLowPower": "LOW_POWER",
    "kSustained": "SUSTAINED_PERFORMANCE",
    "kLaunch": "LAUNCH",
    "kExpensiveRendering": "EXPENSIVE_RENDERING",
}


def enum_ordinals(source: str, name: str) -> dict[str, int]:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r"//[^\n]*", "", source)
    match = re.search(r"\benum\s+" + re.escape(name) + r"\s*\{(.*?)\}", source, re.DOTALL)
    if not match:
        raise ValueError(f"AIDL enum {name} not found")
    ordinal = 0
    out = {}
    for part in match.group(1).split(","):
        part = part.strip()
        if not part:
            continue
        item = re.fullmatch(r"([A-Z][A-Z0-9_]*)\s*(?:=\s*(\d+))?", part)
        if not item:
            raise ValueError(f"unexpected AIDL enumerator in {name}: {part!r}")
        if item.group(2):
            ordinal = int(item.group(2))
        out[item.group(1)] = ordinal
        ordinal += 1
    return out


def validate(boost: str, mode: str, adapter: str) -> list[str]:
    errors = []
    try:
        enums = {"Boost": enum_ordinals(boost, "Boost"),
                 "Mode": enum_ordinals(mode, "Mode")}
    except ValueError as err:
        return [str(err)]
    pairs = (("Boost", EXPECTED_BOOST), ("Mode", EXPECTED_MODE))
    for ename, bindings in pairs:
        for constant, aidl_name in bindings.items():
            expected = enums[ename].get(aidl_name)
            c = re.search(r"constexpr\s+int32_t\s+" + re.escape(constant) +
                          r"\s*=\s*(\d+)\s*;", adapter)
            if expected is None or not c or int(c.group(1)) != expected:
                errors.append(f"{ename} mapping mismatch: {constant}/{aidl_name} "
                              f"(AIDL={expected}, adapter={c.group(1) if c else 'missing'})")
    return errors


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("boost_aidl", type=Path)
    p.add_argument("mode_aidl", type=Path)
    p.add_argument("adapter_cpp", type=Path)
    a = p.parse_args()
    try:
        errors = validate(*(f.read_text(encoding="utf-8") for f in
                            (a.boost_aidl, a.mode_aidl, a.adapter_cpp)))
    except OSError as exc:
        print(f"FAIL: cannot load pinned API input: {exc}", file=sys.stderr)
        return 1
    for problem in errors:
        print("FAIL:", problem, file=sys.stderr)
    if errors:
        return 1
    print("PASS: AOSP17 Power AIDL Boost/Mode ordinals match the adapter constants.")
    print("SCOPE: enum constants only, NOT binder service implementation or Soong.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
