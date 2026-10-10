// SPDX-License-Identifier: Apache-2.0
#include "../include/op6_power_policy.h"
#include <cassert>
#include <chrono>
#include <cstdio>
#include <thread>
#include <vector>

int main() {
  auto* h = op6_policy_create();
  assert(h != nullptr);
  std::vector<std::thread> threads;
  for (int i=0; i<6; ++i) {
    threads.emplace_back([h, i] {
      for (int j=0; j<2000; ++j) {
        const uint64_t t = static_cast<uint64_t>(j);
        assert(op6_policy_start(h, static_cast<uint32_t>(i % 4), t) == OP6_POLICY_OK);
        assert(op6_policy_set_mode(h, static_cast<uint32_t>(j % 4)) == OP6_POLICY_OK);
        op6_policy_result result{};
        assert(op6_policy_evaluate(h, t, &result) == OP6_POLICY_OK);
        assert(result.abi_version == OP6_POLICY_ABI_VERSION);
        assert(result.count <= OP6_POLICY_MAX_TARGETS);
        for (uint32_t k=0; k<result.count; ++k) assert(result.targets[k].value > 0);
      }
    });
  }
  for (auto& t : threads) t.join();
  assert(op6_policy_reset(h) == OP6_POLICY_OK);
  op6_policy_result final{};
  assert(op6_policy_evaluate(h, 100000, &final) == OP6_POLICY_OK);
  assert(final.count == 0);
  // Lifetime invariant: no API call overlaps destroy.
  op6_policy_destroy(h);
  std::puts("PASS: concurrent C ABI start/mode/evaluate/reset");
}
