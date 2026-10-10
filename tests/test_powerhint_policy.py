import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("audit_powerhint_policy", Path(__file__).parents[1] / "tools/audit_powerhint_policy.py")
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)


def policy():
    return {
        "Nodes": [
            {"Name": "GPUMaxFreq", "Path": "/sys/class/kgsl/kgsl-3d0/devfreq/max_freq", "Values": ["710000000", "342000000"], "DefaultIndex": 0, "ResetOnInit": True},
            {"Name": "CPUBigClusterMinFreq", "Path": "/sys/devices/system/cpu/cpu4/cpufreq/scaling_min_freq", "Values": ["1209600", "825600"], "DefaultIndex": 1}
        ],
        "Actions": [
            {"PowerHint": "SUSTAINED_PERFORMANCE", "Node": "GPUMaxFreq", "Duration": 0, "Value": "342000000"},
            {"PowerHint": "INTERACTION", "Node": "CPUBigClusterMinFreq", "Duration": 0, "Value": "1209600"}
        ]
    }


class PowerHintValidatorTests(unittest.TestCase):
    def test_v5_shape_passes_with_warnings(self):
        errors, warnings, stats = auditor.inspect(policy())
        self.assertEqual(errors, [])
        self.assertEqual(stats["actions"], 2)
        self.assertTrue(any("no automatic timeout" in w for w in warnings))

    def test_rejects_duplicate_hint_node(self):
        p = policy()
        p["Actions"].append(dict(p["Actions"][0]))
        errors, _, _ = auditor.inspect(p)
        self.assertTrue(any("duplicate Node action" in e for e in errors))

    def test_rejects_unlisted_value(self):
        p = policy()
        p["Actions"][0]["Value"] = "596000000"
        errors, _, _ = auditor.inspect(p)
        self.assertTrue(any("not permitted" in e for e in errors))

    def test_rejects_index_out_of_range(self):
        p = policy()
        p["Nodes"][0]["DefaultIndex"] = 2
        errors, _, _ = auditor.inspect(p)
        self.assertTrue(any("DefaultIndex" in e for e in errors))

    def test_rejects_boolean_duration(self):
        p = policy()
        p["Actions"][0]["Duration"] = True
        errors, _, _ = auditor.inspect(p)
        self.assertTrue(any("Duration" in e for e in errors))

    def test_missing_arrays(self):
        errors, _, _ = auditor.inspect({"Nodes": []})
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
