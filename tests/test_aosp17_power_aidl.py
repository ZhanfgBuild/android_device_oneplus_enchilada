"""Offline tests for the AOSP17 Boost/Mode ordinal drift gate."""
import importlib.util
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / "tools/check_aosp17_power_aidl.py"
spec = importlib.util.spec_from_file_location("aosp_power_aidl", p)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

BOOST = """
enum Boost {
  INTERACTION,
  DISPLAY_UPDATE_IMMINENT,
  ML_ACC,
  AUDIO_LAUNCH,
  CAMERA_LAUNCH,
  CAMERA_SHOT,
}
"""
MODE = """
enum Mode {
  DOUBLE_TAP_TO_WAKE,
  LOW_POWER,
  SUSTAINED_PERFORMANCE,
  FIXED_PERFORMANCE,
  VR,
  LAUNCH,
  EXPENSIVE_RENDERING,
}
"""
CPP = """
constexpr int32_t kInteraction = 0;
constexpr int32_t kDisplayUpdate = 1;
constexpr int32_t kAudioLaunch = 3;
constexpr int32_t kLowPower = 1;
constexpr int32_t kSustained = 2;
constexpr int32_t kLaunch = 5;
constexpr int32_t kExpensiveRendering = 6;
"""


class AidlContractTests(unittest.TestCase):
    def test_expected_enums(self):
        self.assertEqual([], api.validate(BOOST, MODE, CPP))

    def test_ordinals_explicit(self):
        example = "enum Boost { INTERACTION=0, DISPLAY_UPDATE_IMMINENT=7, AUDIO_LAUNCH=8, }"
        self.assertEqual(7, api.enum_ordinals(example, "Boost")["DISPLAY_UPDATE_IMMINENT"])

    def test_changed_aidl_fails(self):
        self.assertTrue(api.validate(BOOST.replace("ML_ACC,", "ML_ACC, EXTRA,"), MODE, CPP))

    def test_changed_adapter_fails(self):
        self.assertTrue(api.validate(BOOST, MODE, CPP.replace("kLowPower = 1", "kLowPower = 9")))

    def test_unparsable_fails(self):
        self.assertTrue(api.validate("invalid", MODE, CPP))


if __name__ == "__main__":
    unittest.main()
