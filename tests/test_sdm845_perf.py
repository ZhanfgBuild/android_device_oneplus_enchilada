"""Unit tests: read-only SDM845 performance audit utilities."""
import importlib.util
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(filename):
    spec = importlib.util.spec_from_file_location(filename.replace(".", "_"), ROOT / "tools" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kernel = load("audit_sdm845_kernel_config.py")
legacy = load("audit_legacy_postboot.py")


class KernelConfigTests(unittest.TestCase):
    def test_parse_enabled_and_disabled(self):
        data = kernel.parse_config("CONFIG_PSI=y\n# CONFIG_UCLAMP_TASK is not set\nCONFIG_EXTRA=42\n")
        self.assertEqual(data["CONFIG_PSI"], "y")
        self.assertEqual(data["CONFIG_UCLAMP_TASK"], "n")
        self.assertEqual(data["CONFIG_EXTRA"], "42")

    def test_reject_missing_psi(self):
        data = {name: "y" for name in kernel.REQUIRED}
        data["CONFIG_PSI"] = "n"
        errors, _ = kernel.evaluate(data)
        self.assertTrue(any("CONFIG_PSI=n" in item for item in errors))

    def test_optional_uclamp_not_required(self):
        data = {name: "y" for name in kernel.REQUIRED}
        errors, notes = kernel.evaluate(data)
        self.assertEqual(errors, [])
        self.assertTrue(any("CONFIG_UCLAMP_TASK=absent" in item for item in notes))


class LegacyAuditTests(unittest.TestCase):
    def test_classify_without_executing_input(self):
        source = """# echo performance > /sys/cpu/scaling_governor
echo schedutil > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
echo 0-3 > /dev/cpuset/background/cpus
echo 1 > /dev/stune/top-app/schedtune.prefer_idle
"""
        counts, samples = legacy.scan(source)
        self.assertEqual(counts["governor"], 1)
        self.assertEqual(counts["cpuset"], 1)
        self.assertEqual(counts["legacy_schedtune"], 1)
        self.assertEqual(samples["governor"], [2])


class ProbeSafetyTests(unittest.TestCase):
    def test_posix_shell_syntax(self):
        file = ROOT / "tools" / "op6_perf_probe.sh"
        result = subprocess.run(["sh", "-n", str(file)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_sysfs_write_and_no_private_probe(self):
        source = (ROOT / "tools" / "op6_perf_probe.sh").read_text(encoding="utf-8")
        for forbidden in ("fastboot", "flash ", "setprop ", "su -c", "dmesg",
                          "/proc/cmdline", "ro.serialno", "imei", "android_id",
                          "settings get secure", "resetprop"):
            self.assertNotIn(forbidden, source)
        self.assertNotRegex(source, r"(?m)^\s*(?:echo|printf)\b[^\n]*>\s*/(?:sys|proc|dev)/")


if __name__ == "__main__":
    unittest.main()
