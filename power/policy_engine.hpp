// SPDX-License-Identifier: Apache-2.0
// Policy computation only: never opens or writes a sysfs node.
#pragma once
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <map>
#include <optional>
#include <stdexcept>
#include <vector>

namespace op6::power {
enum class Resource { LittleMin, BigMin, GpuMin, LittleMax, BigMax, GpuMax };
enum class Hint { Interaction, Launch, AudioLaunch, ExpensiveRendering, DisplayUpdate };
enum class Mode { Balanced, Responsive, Sustained, Battery };
using Time = std::chrono::steady_clock::time_point;
using Targets = std::map<Resource, int64_t>;

// A policy request is deliberately NOT a sysfs writer. An AIDL HAL adapter
// must validate target paths, permission, controller and thermal headroom.
class Engine final {
 public:
  void SetMode(Mode mode) noexcept { mode_ = mode; }
  Mode GetMode() const noexcept { return mode_; }

  // Restart coalesces repeated events. Every transient hint expires.
  void Start(Hint hint, Time now) { StartFor(hint, now, Duration(hint)); }
  // AIDL Boost accepts caller-provided durationMs; enforce a hard upper bound.
  void StartFor(Hint hint, Time now, std::chrono::milliseconds ttl) {
    if (ttl.count() <= 0 || ttl > std::chrono::milliseconds(5000))
      throw std::invalid_argument("invalid boost duration");
    const auto expiry = now + ttl;
    for (auto& active : active_) {
      if (active.hint == hint) {
        active.expires = std::max(expiry, active.expires);
        return;
      }
    }
    active_.push_back({hint, expiry});
  }
  void Stop(Hint hint) {
    active_.erase(std::remove_if(active_.begin(), active_.end(),
                  [hint](const Active& a) { return a.hint == hint; }),
                  active_.end());
  }
  void Expire(Time now) {
    active_.erase(std::remove_if(active_.begin(), active_.end(),
                  [now](const Active& a) { return a.expires <= now; }),
                  active_.end());
  }
  size_t ActiveCount() const noexcept { return active_.size(); }

  // Only return active resource requests; omission means "release the hint".
  // The adapter must clear any previously written request on omission.
  Targets Evaluate(Time now) const {
    Targets out;
    switch (mode_) {
      case Mode::Balanced:
      case Mode::Responsive: break;
      case Mode::Sustained:
        Add(out, Resource::BigMax, 2246400);
        Add(out, Resource::GpuMax, 596000000);
        break;
      case Mode::Battery:
        Add(out, Resource::BigMax, 1996800);
        Add(out, Resource::GpuMax, 520000000);
        break;
    }
    for (const auto& active : active_) {
      if (active.expires <= now) continue;
      switch (active.hint) {
        case Hint::Interaction:
          Add(out, Resource::LittleMin, 748800);
          Add(out, Resource::BigMin, 1209600);
          break;
        case Hint::DisplayUpdate:
          Add(out, Resource::LittleMin, 748800);
          Add(out, Resource::BigMin, 1209600);
          break;
        case Hint::Launch:
          Add(out, Resource::LittleMin, 979200);
          Add(out, Resource::BigMin, 1459200);
          break;
        case Hint::AudioLaunch:
          Add(out, Resource::BigMin, 1056000);
          break;
        case Hint::ExpensiveRendering:
          Add(out, Resource::GpuMin, 414000000);
          break;
      }
    }
    // Fail closed on contradictory floor/ceiling requests. The lower-frequency
    // ceiling has precedence over short-lived performance hints.
    Clamp(out, Resource::LittleMin, Resource::LittleMax);
    Clamp(out, Resource::BigMin, Resource::BigMax);
    Clamp(out, Resource::GpuMin, Resource::GpuMax);
    return out;
  }

  static std::chrono::milliseconds Duration(Hint hint) {
    switch (hint) {
      case Hint::Interaction: return std::chrono::milliseconds(180);
      case Hint::Launch: return std::chrono::milliseconds(900);
      case Hint::AudioLaunch: return std::chrono::milliseconds(600);
      case Hint::ExpensiveRendering: return std::chrono::milliseconds(250);
      case Hint::DisplayUpdate: return std::chrono::milliseconds(90);
    }
    throw std::invalid_argument("unknown performance hint");
  }

 private:
  struct Active { Hint hint; Time expires; };
  std::vector<Active> active_;
  Mode mode_ = Mode::Balanced;
  static bool Ceiling(Resource key) {
    return key == Resource::LittleMax || key == Resource::BigMax ||
           key == Resource::GpuMax;
  }
  static void Add(Targets& out, Resource key, int64_t value) {
    auto [it, inserted] = out.emplace(key, value);
    if (!inserted) {
      it->second = Ceiling(key) ? std::min(value, it->second)
                                : std::max(value, it->second);
    }
  }
  static void Clamp(Targets& out, Resource min_key, Resource max_key) {
    auto low = out.find(min_key);
    auto high = out.find(max_key);
    if (low != out.end() && high != out.end() && low->second > high->second)
      low->second = high->second;
  }
};
} // namespace op6::power
