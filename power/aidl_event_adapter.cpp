// SPDX-License-Identifier: Apache-2.0
#include "aidl_event_adapter.hpp"
#include <algorithm>
#include <chrono>

namespace op6::power {
namespace {
// AOSP android-17.0.0_r1:
// Boost.aidl: INTERACTION=0, DISPLAY_UPDATE_IMMINENT=1, ML_ACC=2,
// AUDIO_LAUNCH=3, CAMERA_LAUNCH=4, CAMERA_SHOT=5.
// Mode.aidl: DOUBLE_TAP_TO_WAKE=0, LOW_POWER=1, SUSTAINED_PERFORMANCE=2,
// FIXED_PERFORMANCE=3, VR=4, LAUNCH=5, EXPENSIVE_RENDERING=6.
// Never advertise capabilities whose hardware implementation is unverified.
constexpr int32_t kInteraction = 0;
constexpr int32_t kDisplayUpdate = 1;
constexpr int32_t kAudioLaunch = 3;
constexpr int32_t kLowPower = 1;
constexpr int32_t kSustained = 2;
constexpr int32_t kLaunch = 5;
constexpr int32_t kExpensiveRendering = 6;
constexpr int32_t kMaxBoostMs = 5000;

Hint ToHint(int32_t boost) {
  switch (boost) {
    case kInteraction: return Hint::Interaction;
    case kDisplayUpdate: return Hint::DisplayUpdate;
    default: return Hint::AudioLaunch;
  }
}
} // namespace

bool AidlEventAdapter::SupportsBoost(int32_t boost) noexcept {
  return boost == kInteraction || boost == kDisplayUpdate ||
         boost == kAudioLaunch;
}
bool AidlEventAdapter::SupportsMode(int32_t mode) noexcept {
  return mode == kLowPower || mode == kSustained ||
         mode == kLaunch || mode == kExpensiveRendering;
}

bool AidlEventAdapter::SetBoost(int32_t boost, int32_t duration_ms, Time now) {
  if (!SupportsBoost(boost)) return false;
  std::lock_guard<std::mutex> guard(mutex_);
  const Hint hint = ToHint(boost);
  if (duration_ms < 0) {
    engine_.Stop(hint);
  } else {
    const auto ttl = duration_ms == 0 ? Engine::Duration(hint)
      : std::chrono::milliseconds(std::min(duration_ms, kMaxBoostMs));
    engine_.StartFor(hint, now, ttl);
  }
  return true;
}

void AidlEventAdapter::UpdatePowerModeLocked() {
  // Low power outranks sustained when both are requested simultaneously.
  engine_.SetMode(low_power_ ? Mode::Battery :
                  sustained_ ? Mode::Sustained : Mode::Balanced);
}

bool AidlEventAdapter::SetMode(int32_t mode, bool enabled, Time now) {
  if (!SupportsMode(mode)) return false;
  std::lock_guard<std::mutex> guard(mutex_);
  switch (mode) {
    case kLowPower:
      low_power_ = enabled;
      UpdatePowerModeLocked();
      break;
    case kSustained:
      sustained_ = enabled;
      UpdatePowerModeLocked();
      break;
    case kLaunch:
      if (enabled) engine_.Start(Hint::Launch, now);
      else engine_.Stop(Hint::Launch);
      break;
    case kExpensiveRendering:
      expensive_rendering_ = enabled;
      break;
    default:
      return false;
  }
  return true;
}

Targets AidlEventAdapter::Snapshot(Time now) const {
  std::lock_guard<std::mutex> guard(mutex_);
  Targets out = engine_.Evaluate(now);
  if (expensive_rendering_) {
    auto [it, added] = out.emplace(Resource::GpuMin, 414000000);
    if (!added) it->second = std::max<int64_t>(it->second, 414000000);
    // A lower, thermally sustainable GPU ceiling takes precedence.
    const auto ceiling = out.find(Resource::GpuMax);
    if (ceiling != out.end() && it->second > ceiling->second)
      it->second = ceiling->second;
  }
  return out;
}

void AidlEventAdapter::Reset() {
  std::lock_guard<std::mutex> guard(mutex_);
  engine_ = Engine{};
  low_power_ = false;
  sustained_ = false;
  expensive_rendering_ = false;
}
} // namespace op6::power
