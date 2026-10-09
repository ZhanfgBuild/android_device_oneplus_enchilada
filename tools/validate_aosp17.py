#!/usr/bin/env python3
"""Offline AOSP 17 OnePlus 6 Stage-0 source and product preflight.

Checks source lockfile structure, device product independence, and (optionally)
a real synced workspace's critical inputs. Never flashes a device or builds a
ROM. Passing is NOT evidence of a bootable Android image.
"""
import argparse
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

EXPECTED_PATHS = {
    "device/oneplus/enchilada",
    "device/oneplus/sdm845-common",
    "hardware/oneplus",
    "hardware/oplus",
    "vendor/oneplus/enchilada",
    "vendor/oneplus/sdm845-common",
    "kernel/oneplus/sdm845",
    "hardware/qcom-caf/common",
    "device/qcom/sepolicy",
    "device/qcom/sepolicy_vndr",
}
SHA40 = re.compile(r"^[a-f0-9]{40}$")
NEEDED_FILES = (
    "device/oneplus/enchilada/AndroidProducts.mk",
    "device/oneplus/enchilada/aosp_enchilada.mk",
    "device/oneplus/enchilada/device.mk",
    "device/oneplus/sdm845-common/aosp-common.mk",
    "device/oneplus/sdm845-common/BoardConfigCommon.mk",
    "hardware/qcom-caf/common/common.mk",
    "device/qcom/sepolicy_vndr/SEPolicy.mk",
    "vendor/oneplus/enchilada/enchilada-vendor.mk",
    "vendor/oneplus/sdm845-common/sdm845-common-vendor.mk",
)


def validate_manifest(file: Path) -> list[str]:
    errors: list[str] = []
    try:
        root = ET.parse(file).getroot()
    except (ET.ParseError, OSError) as exc:
        return [f"Cannot read source manifest: {exc}"]
    if root.tag != "manifest":
        errors.append("Root element must be <manifest>")
    remotes = {r.get("name") for r in root.findall("remote")}
    paths: list[str] = []
    for p in root.findall("project"):
        name = p.get("name", "")
        path = p.get("path", "")
        sha = p.get("revision", "")
        remote = p.get("remote", "")
        if not name or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name):
            errors.append(f"Invalid repository name: {name!r}")
        if not path or path.startswith("/") or ".." in Path(path).parts:
            errors.append(f"Unsafe project path: {path!r}")
        if not SHA40.fullmatch(sha):
            errors.append(f"Unpinned revision for {name}: {sha!r}")
        if remote not in remotes:
            errors.append(f"Missing remote {remote!r} for {name}")
        paths.append(path)
    if len(paths) != len(set(paths)):
        errors.append("Duplicate project target paths")
    if set(paths) != EXPECTED_PATHS:
        errors.append(
            "Unexpected source layout: missing="
            + repr(sorted(EXPECTED_PATHS - set(paths)))
            + "; extra=" + repr(sorted(set(paths) - EXPECTED_PATHS))
        )
    return errors


def validate_device(device_dir: Path) -> list[str]:
    errors: list[str] = []
    required = {
        "AndroidProducts.mk": ("aosp_enchilada.mk",),
        "aosp_enchilada.mk": ("PRODUCT_NAME := aosp_enchilada",),
        "device.mk": ("sdm845-common/aosp-common.mk",),
        "BoardConfig.mk": ("sdm845-common/BoardConfigCommon.mk",),
    }
    for filename, must_contain in required.items():
        file = device_dir / filename
        try:
            content = file.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"Missing device file {filename}: {exc}")
            continue
        for needle in must_contain:
            if needle not in content:
                errors.append(f"Expected {needle!r} in {filename}")
        # The shipping product cannot inherit Lineage framework/services.
        if filename in ("aosp_enchilada.mk", "device.mk"):
            for line in content.splitlines():
                code = line.split("#", 1)[0]
                if "vendor/lineage/config" in code or "lineage_enchilada.mk" in code:
                    errors.append(f"Lineage runtime/product dependency in {filename}: {line.strip()}")
    return errors


def validate_workspace(root: Path) -> list[str]:
    errors: list[str] = []
    if not (root / "build/envsetup.sh").is_file():
        errors.append("Missing AOSP checkout: build/envsetup.sh")
    for path in sorted(EXPECTED_PATHS):
        if not (root / path).is_dir():
            errors.append(f"Source project missing: {path}")
    for filename in NEEDED_FILES:
        if not (root / filename).is_file():
            errors.append(f"Required source file missing: {filename}")

    board = root / "device/oneplus/sdm845-common/BoardConfigCommon.mk"
    if board.is_file():
        cfg = board.read_text(encoding="utf-8")
        if re.search(r"^\s*BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS\s*\+?=.*(?:set_hashtree_disabled_flag|set_verification_disabled_flag)", cfg, re.M):
            errors.append("AVB disabled-flags found in shipping BoardConfig")

    for vendor in ("vendor/oneplus/enchilada", "vendor/oneplus/sdm845-common"):
        directory = root / vendor
        if directory.is_dir():
            # A synced Git LFS project can still contain pointer files when
            # git-lfs smudge was unavailable. Check a bounded sample.
            count = 0
            for file in directory.rglob("*.so"):
                count += 1
                if count > 32:
                    break
                try:
                    with file.open("rb") as handle:
                        if handle.read(80).startswith(b"version https://git-lfs.github.com/spec/v1"):
                            errors.append(f"Unfetched Git LFS blob: {file.relative_to(root)}")
                            break
                except OSError:
                    pass
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path(__file__).resolve().parent.parent
    parser.add_argument("--manifest", type=Path, default=base / "manifests/enchilada-aosp17-stage0.xml")
    parser.add_argument("--device-dir", type=Path, default=base)
    parser.add_argument("--workspace", type=Path, help="Optional checked-out Android 17 source root")
    args = parser.parse_args()
    errors = validate_manifest(args.manifest) + validate_device(args.device_dir)
    if args.workspace:
        errors += validate_workspace(args.workspace)
    if errors:
        for item in errors:
            print("FAIL:", item, file=sys.stderr)
        print(f"FAIL: {len(errors)} preflight error(s). Not build verified.", file=sys.stderr)
        return 1
    print("PASS: source lockfile and AOSP product static checks.")
    if args.workspace:
        print("PASS: required workspace paths exist (not proof of compile compatibility).")
    print("STATUS: Stage-0 metadata only; Android 17 Soong, HAL, VINTF,")
    print("        SELinux, kernel, boot, and hardware runtime remain unverified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
