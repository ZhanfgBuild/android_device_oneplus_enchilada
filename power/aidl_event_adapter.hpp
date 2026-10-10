// SPDX-License-Identifier: Apache-2.0
// Verified against hardware/interfaces android-17.0.0_r1 Power AIDL enums.
// This is a Binder-independent translator, NOT an IPower service.
#pragma once
#include "policy_engine.hpp"
#include <cstdint>
#include <mutex>

namespace op6::power {
class AidlEventAdapter final {
 public:
  // Numeric constants MUST match AOSP17 Boost.aidl / Mode.aidl.
  static bool SupportsBoost(int32_t boost) noexcept;
  static bool SupportsMode(int32_t mode) noexcept;

  // AIDL Boost: durationMs < 0 cancels, 0 uses bounded default, >0 is capped
  // at 5000ms. Returns false for unsupported boost kinds without mutation.
  bool SetBoost(int32_t boost, int32_t duration_ms, Time now);
  // AIDL Mode: explicit enable/disable with independent overlapping modes.
  // LAUNCH has a bounded lease even if its off callback is lost.
  bool SetMode(int32_t mode, bool enabled, Time now);
  Targets Snapshot(Time now) const;
  // Framework restart/shutdown: clears everything; adapter must also release
  // all previously applied kernel requests (which this module never writes).
  void Reset();

 private:
  mutable std::mutex mutex_;
  Engine engine_;
  bool low_power_ = false;
  bool sustained_ = false;
  bool expensive_rendering_ = false;
  void UpdatePowerModeLocked();
};
} // namespace op6::power
