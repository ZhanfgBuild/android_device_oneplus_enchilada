"""Unit tests for Android 17 Memory Limiter's specific kernel interfaces."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("memory_audit", ROOT / "tools/audit_android17_memory_limiter.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class MemoryLimiterKernelGateTests(unittest.TestCase):
    def test_legacy_kernel_high_only(self):
        legacy = ('int memory_high_write;\n'
                  'static struct cftype memory_files[] = {\n'
                  '  { .name = "high" },\n'
                  '  { .name = "max" },\n'
                  '};')
        status = audit.inspect_kernel_memory(legacy)
        self.assertTrue(status["memory.high"])
        self.assertFalse(status["memory.swap.max"])

    def test_kernel_with_swap_controller(self):
        modern = ('int memory_high_write;\n'
                  'static struct cftype memory_files[] = {\n'
                  '  { .name = "high" },\n'
                  '  { .name = "swap.max" },\n'
                  '};')
        self.assertTrue(all(audit.inspect_kernel_memory(modern).values()))

    def test_missing_table_is_hard_failure(self):
        with self.assertRaises(ValueError):
            audit.inspect_kernel_memory("CONFIG_MEMCG=y")


if __name__ == "__main__":
    unittest.main()
