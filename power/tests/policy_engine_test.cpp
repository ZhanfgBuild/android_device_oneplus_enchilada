// SPDX-License-Identifier: Apache-2.0
#include "../policy_engine.hpp"
#include <cassert>
#include <chrono>
#include <iostream>
using namespace op6::power;
using namespace std::chrono_literals;

int main() {
  const Time base{};
  Engine e;
  assert(e.Evaluate(base).empty());
  assert(e.ActiveCount() == 0);

  e.Start(Hint::Interaction, base);
  assert(e.Evaluate(base).at(Resource::BigMin) == 1209600);
  assert(e.Evaluate(base + 180ms).empty()); // no infinite interaction hint
  e.Expire(base + 181ms);
  assert(e.ActiveCount() == 0);

  e.Start(Hint::Interaction, base);
  e.Start(Hint::Launch, base + 10ms);
  auto mix = e.Evaluate(base + 20ms);
  assert(mix.at(Resource::LittleMin) == 979200);
  assert(mix.at(Resource::BigMin) == 1459200);
  assert(e.Evaluate(base + 181ms).at(Resource::BigMin) == 1459200);
  assert(e.Evaluate(base + 911ms).empty());

  // Previous interaction remains independent of the launch hint.
  e.Start(Hint::Launch, base);
  e.Stop(Hint::Launch);
  assert(e.Evaluate(base).count(Resource::BigMin) == 1);
  e.Stop(Hint::Interaction);
  assert(e.Evaluate(base).empty());

  e.Start(Hint::ExpensiveRendering, base);
  assert(e.Evaluate(base).at(Resource::GpuMin) == 414000000);
  e.SetMode(Mode::Battery);
  auto battery = e.Evaluate(base);
  assert(battery.at(Resource::GpuMin) == 414000000);
  assert(battery.at(Resource::GpuMax) == 520000000);
  assert(battery.at(Resource::BigMax) == 1996800);
  assert(e.Evaluate(base + 300ms).count(Resource::GpuMin) == 0);
  e.SetMode(Mode::Balanced);
  assert(e.Evaluate(base + 300ms).empty());

  e.Start(Hint::AudioLaunch, base);
  assert(e.Evaluate(base).at(Resource::BigMin) == 1056000);
  assert(e.Evaluate(base + 600ms).empty());
  e.Stop(Hint::AudioLaunch);
  e.SetMode(Mode::Sustained);
  assert(e.Evaluate(base).at(Resource::GpuMax) == 596000000);
  assert(e.Evaluate(base).at(Resource::BigMax) == 2246400);
  e.SetMode(Mode::Responsive);
  // The earlier rendering hint is no longer effective after its TTL.
  assert(e.Evaluate(base + 300ms).empty());
  e.Expire(base + 300ms);
  assert(e.ActiveCount() == 0);

  // Never writes to /sys: this tests policy arithmetic, not an Android HAL.
  std::cout << "PASS: policy TTL, overlap, stop, modes, release and limits\n";
  return 0;
}
