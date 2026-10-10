// SPDX-License-Identifier: Apache-2.0
#include "../aidl_event_adapter.hpp"
#include <cassert>
#include <chrono>
#include <cstdio>
#include <thread>
#include <vector>
using namespace op6::power;
using namespace std::chrono_literals;

int64_t Get(const Targets& t, Resource r) {
  const auto it = t.find(r);
  return it == t.end() ? -1 : it->second;
}
int main() {
  const Time origin{};
  AidlEventAdapter adapter;
  assert(adapter.Snapshot(origin).empty());
  assert(AidlEventAdapter::SupportsBoost(0));
  assert(AidlEventAdapter::SupportsBoost(1));
  assert(AidlEventAdapter::SupportsBoost(3));
  assert(!AidlEventAdapter::SupportsBoost(2)); // ML_ACC unsupported
  assert(!AidlEventAdapter::SupportsBoost(4)); // camera unsupported
  assert(!AidlEventAdapter::SupportsMode(0)); // double tap requires hardware
  assert(!AidlEventAdapter::SupportsMode(3)); // FIXED needs thermal profiling
  assert(!adapter.SetBoost(2, 100, origin));
  assert(!adapter.SetMode(99, true, origin));

  // Explicit 40ms duration, cancellation and independent display boost.
  assert(adapter.SetBoost(0, 40, origin));
  assert(Get(adapter.Snapshot(origin + 39ms), Resource::BigMin) == 1209600);
  assert(adapter.Snapshot(origin + 40ms).empty());
  assert(adapter.SetBoost(0, 1000, origin));
  assert(adapter.SetBoost(1, 0, origin));
  assert(adapter.SetBoost(0, -1, origin));
  assert(Get(adapter.Snapshot(origin + 20ms), Resource::BigMin) == 1209600);
  assert(adapter.Snapshot(origin + 91ms).empty());

  // Unknown AIDL duration zero remains bounded, maximum 5000ms.
  assert(adapter.SetBoost(3, 0, origin));
  assert(adapter.Snapshot(origin + 599ms).count(Resource::BigMin) == 1);
  assert(adapter.Snapshot(origin + 600ms).empty());
  assert(adapter.SetBoost(3, 100000, origin));
  assert(Get(adapter.Snapshot(origin + 4999ms), Resource::BigMin) == 1056000);
  assert(adapter.Snapshot(origin + 5000ms).empty());
  assert(adapter.SetBoost(3, -1, origin));

  // Independent overlapping AIDL modes: low power overrides sustained.
  assert(adapter.SetMode(2, true, origin));
  assert(Get(adapter.Snapshot(origin), Resource::BigMax) == 2246400);
  assert(adapter.SetMode(1, true, origin));
  assert(Get(adapter.Snapshot(origin), Resource::BigMax) == 1996800);
  assert(adapter.SetMode(1, false, origin));
  assert(Get(adapter.Snapshot(origin), Resource::BigMax) == 2246400);
  assert(adapter.SetMode(2, false, origin));
  assert(adapter.Snapshot(origin).empty());

  // LAUNCH is a Mode, not a Boost; bounded fallback prevents stuck limits.
  assert(adapter.SetMode(5, true, origin));
  assert(Get(adapter.Snapshot(origin + 899ms), Resource::BigMin) == 1459200);
  assert(adapter.Snapshot(origin + 900ms).empty());
  assert(adapter.SetMode(5, true, origin));
  assert(adapter.SetMode(5, false, origin));
  assert(adapter.Snapshot(origin).empty());

  // Expensive rendering stays on until its Mode is explicitly disabled.
  assert(adapter.SetMode(6, true, origin));
  assert(Get(adapter.Snapshot(origin + 30000ms), Resource::GpuMin) == 414000000);
  assert(adapter.SetMode(1, true, origin));
  auto both = adapter.Snapshot(origin);
  assert(Get(both, Resource::GpuMin) == 414000000);
  assert(Get(both, Resource::GpuMax) == 520000000);
  assert(adapter.SetMode(6, false, origin));
  assert(Get(adapter.Snapshot(origin), Resource::GpuMin) == -1);
  adapter.Reset();
  assert(adapter.Snapshot(origin).empty());

  // Binder callbacks can overlap. Lock the entire state transition/snapshot.
  std::vector<std::thread> workers;
  for (int i = 0; i < 4; ++i) {
    workers.emplace_back([&adapter, i, origin]() {
      for (int j = 0; j < 1000; ++j) {
        assert(adapter.SetBoost(i % 2, 1, origin + std::chrono::milliseconds(j)));
        auto out = adapter.Snapshot(origin + std::chrono::milliseconds(j));
        for (auto [r, v] : out) {
          (void)r;
          assert(v > 0);
        }
        if (j % 3 == 0) adapter.SetBoost(i % 2, -1, origin);
      }
    });
  }
  for (auto& w : workers) w.join();
  adapter.Reset();
  assert(adapter.Snapshot(origin).empty());
  std::puts("PASS: AOSP17 Boost/Mode routing, bounded lifetime, precedence, concurrency");
  return 0;
}
