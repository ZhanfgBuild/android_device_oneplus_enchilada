#!/usr/bin/env python3
"""AOSP17 SDM845 release gate, read-only and non-flashing."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

AOSP_PRODUCT = "PRODUCT_NAME := aosp_enchilada"
MIGRATION_BLOCKERS = (
    "system/core/libprocessgroup/profiles/cgroups_28.json",
    "system/core/libprocessgroup/profiles/task_profiles_28.json",
    "vendor/lineage/config/common_full_phone.mk",
    "vendor/lineage/config/common.mk",
)

# A hardware donor is not a release-grade Android 17 implementation.
RISK_HAL = {
    "android.hardware.audio", "android.hardware.audio.effect",
    "android.hardware.bluetooth", "android.hardware.camera.provider",
    "android.hardware.graphics.allocator",
    "android.hardware.graphics.composer",
    "android.hardware.graphics.mapper", "android.hardware.radio",
    "android.hardware.sensors", "android.hardware.gatekeeper",
    "android.hardware.keymaster", "android.hardware.power",
}
REQUIRED_WORKSPACE_INPUTS = (
    "build/envsetup.sh",
    "hardware/interfaces/power/aidl/Android.bp",
    "system/core/libprocessgroup/profiles/cgroups.json",
    "system/core/libprocessgroup/profiles/task_profiles.json",
    "device/oneplus/enchilada/aosp_enchilada.mk",
    "device/oneplus/sdm845-common/aosp-common.mk",
    "kernel/oneplus/sdm845/Makefile",
    "vendor/oneplus/enchilada/enchilada-vendor.mk",
    "vendor/oneplus/sdm845-common/sdm845-common-vendor.mk",
)


def product_errors(product: str, device: str) -> list[str]:
    failures = []
    if AOSP_PRODUCT not in product:
        failures.append("missing independent AOSP product name")
    if "device/oneplus/sdm845-common/aosp-common.mk" not in device:
        failures.append("not inheriting standalone AOSP hardware wrapper")
    # Ignore comments when checking accidental runtime inheritance.
    source_lines = [
        ln.split("#", 1)[0] for ln in (product + "\n" + device).splitlines()
    ]
    for old in MIGRATION_BLOCKERS:
        if any(old in ln for ln in source_lines):
            failures.append("obsolete or Lineage runtime input: " + old)
    return failures


def manifest_findings(raw_xml: str) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as exc:
        return [f"malformed device manifest XML: {exc}"], []
    if root.tag != "manifest" or root.attrib.get("type") != "device":
        errors.append("device manifest root/type invalid")
    if not root.attrib.get("target-level"):
        errors.append("device manifest missing shipping FCM target-level")
    hals = []
    for hal in root.findall("hal"):
        name = hal.findtext("name") or ""
        fmt = hal.attrib.get("format", "hidl")
        if not name:
            errors.append("unnamed HAL in VINTF manifest")
        hals.append((name, fmt))
        if name in RISK_HAL and fmt == "hidl":
            warnings.append(f"legacy HIDL interface: {name}; validate Android 17 FCM/runtime")
    if not hals:
        warnings.append("no HAL declarations in supplied manifest")
    return errors, sorted(set(warnings))


def workspace_errors(source_root: Path) -> list[str]:
    errors = []
    for path in REQUIRED_WORKSPACE_INPUTS:
        if not (source_root / path).is_file():
            errors.append("missing Android 17 workspace input: " + path)
    return errors


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    base = Path(__file__).resolve().parent.parent
    p.add_argument("--device-dir", type=Path, default=base)
    p.add_argument("--common-manifest", type=Path)
    p.add_argument("--workspace", type=Path)
    args = p.parse_args()

    errors, notes = [], []
    try:
        product = (args.device_dir / "aosp_enchilada.mk").read_text(encoding="utf-8")
        device = (args.device_dir / "device.mk").read_text(encoding="utf-8")
        errors.extend(product_errors(product, device))
    except OSError as exc:
        errors.append(f"cannot inspect independent product: {exc}")
    if args.common_manifest:
        try:
            manifest = args.common_manifest.read_text(encoding="utf-8")
            problems, warnings = manifest_findings(manifest)
            errors.extend(problems)
            notes.extend(warnings)
        except OSError as exc:
            errors.append(f"cannot inspect common VINTF manifest: {exc}")
    if args.workspace:
        errors.extend(workspace_errors(args.workspace))
    for line in notes:
        print("MIGRATION-RISK:", line)
    for line in errors:
        print("BLOCKER:", line, file=sys.stderr)
    if errors:
        print("FAIL: AOSP17 source/compatibility release gate", file=sys.stderr)
        return 1
    print("PASS: product independence and current Stage-1 static input checks.")
    print("UNVERIFIED: Soong, libvintf runtime, HAL services, modem, audio,")
    print("            display, encryption, kernel boot and on-device performance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
