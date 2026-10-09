"""Regression tests for AOSP 17 SDM845 migration blockers."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("legacy_gate", BASE / "tools/check_aosp17_legacy.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class CompatibilityGateTests(unittest.TestCase):
    def test_checked_in_product_has_no_old_28_profiles(self):
        product = (BASE / "aosp_enchilada.mk").read_text(encoding="utf-8")
        device = (BASE / "device.mk").read_text(encoding="utf-8")
        self.assertEqual([], gate.product_errors(product, device))

    def test_old_vendor_cgroup_profile_fails(self):
        product = "PRODUCT_NAME := aosp_enchilada"
        device = "device/oneplus/sdm845-common/aosp-common.mk\n" + (
            "PRODUCT_COPY_FILES += system/core/libprocessgroup/profiles/"
            "cgroups_28.json:$(TARGET_COPY_OUT_VENDOR)/etc/cgroups.json"
        )
        self.assertTrue(gate.product_errors(product, device))

    def test_old_input_in_comment_not_a_failure(self):
        product = "PRODUCT_NAME := aosp_enchilada"
        device = "# system/core/libprocessgroup/profiles/cgroups_28.json\n" + (
            "device/oneplus/sdm845-common/aosp-common.mk"
        )
        self.assertEqual([], gate.product_errors(product, device))

    def test_legacy_hidl_manifest_warning(self):
        xml = """<manifest version="2.0" type="device" target-level="5">
        <hal format="hidl"><name>android.hardware.audio</name>
        <version>6.0</version></hal></manifest>"""
        errors, warnings = gate.manifest_findings(xml)
        self.assertEqual(errors, [])
        self.assertTrue(any("android.hardware.audio" in w for w in warnings))

    def test_bad_manifest_fails(self):
        errors, _ = gate.manifest_findings("<manifest><hal>")
        self.assertTrue(errors)

    def test_missing_workspace_fails(self):
        with tempfile.TemporaryDirectory() as path:
            self.assertTrue(gate.workspace_errors(Path(path)))


if __name__ == "__main__":
    unittest.main()
