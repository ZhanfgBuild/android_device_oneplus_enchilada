"""Unit tests for the independent AOSP 17 Stage-0 preflight."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_aosp17", ROOT / "tools" / "validate_aosp17.py")
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


class PreflightTests(unittest.TestCase):
    def test_checked_in_manifest(self):
        self.assertEqual([], preflight.validate_manifest(ROOT / "manifests/enchilada-aosp17-stage0.xml"))

    def test_checked_in_product(self):
        self.assertEqual([], preflight.validate_device(ROOT))

    def test_mutated_manifest_cannot_use_branch_name(self):
        tree = ET.parse(ROOT / "manifests/enchilada-aosp17-stage0.xml")
        tree.getroot().find("project").set("revision", "main")
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "broken.xml"
            tree.write(dest, encoding="utf-8")
            self.assertTrue(any("Unpinned revision" in e for e in preflight.validate_manifest(dest)))

    def test_missing_workspace_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            errors = preflight.validate_workspace(Path(temp))
            self.assertTrue(any("Missing AOSP checkout" in e for e in errors))
            self.assertTrue(any("Source project missing" in e for e in errors))

    def test_reject_disabled_avb(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            board = root / "device/oneplus/sdm845-common/BoardConfigCommon.mk"
            board.parent.mkdir(parents=True)
            board.write_text(
                "BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --set_verification_disabled_flag\n",
                encoding="utf-8",
            )
            self.assertTrue(any("AVB disabled-flags" in e for e in preflight.validate_workspace(root)))


if __name__ == "__main__":
    unittest.main()
