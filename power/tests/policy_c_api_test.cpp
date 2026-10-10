// SPDX-License-Identifier: Apache-2.0
#include "../include/op6_power_policy.h"
#include <cassert>
#include <climits>
#include <cstdio>

int64_t Find(op6_policy_result r, uint32_t key) {
  for (uint32_t i=0; i<r.count; ++i)
    if (r.targets[i].resource==key) return r.targets[i].value;
  return -1;
}
int main() {
  op6_policy_result result{};
  assert(op6_policy_start(nullptr, OP6_HINT_LAUNCH, 1000) == OP6_POLICY_INVALID_ARGUMENT);
  assert(op6_policy_evaluate(nullptr, 1000, &result) == OP6_POLICY_INVALID_ARGUMENT);
  op6_policy_handle* h=op6_policy_create();
  assert(h);
  assert(op6_policy_evaluate(h, 1000, &result) == OP6_POLICY_OK);
  assert(result.abi_version == OP6_POLICY_ABI_VERSION && result.count == 0);
  assert(op6_policy_set_mode(h, 999) == OP6_POLICY_INVALID_ARGUMENT);
  assert(op6_policy_start(h, 999, 1000) == OP6_POLICY_INVALID_ARGUMENT);
  assert(op6_policy_start(h, OP6_HINT_LAUNCH, ULLONG_MAX) == OP6_POLICY_INVALID_ARGUMENT);
  assert(op6_policy_start(h, OP6_HINT_LAUNCH, 1000) == OP6_POLICY_OK);
  assert(op6_policy_evaluate(h, 1500, &result) == OP6_POLICY_OK);
  assert(Find(result, OP6_RESOURCE_BIG_MIN) == 1459200);
  assert(op6_policy_evaluate(h, 1900, &result) == OP6_POLICY_OK);
  assert(result.count == 0); // ended by TTL even without Expire() mutating
  assert(op6_policy_set_mode(h, OP6_MODE_BATTERY) == OP6_POLICY_OK);
  assert(op6_policy_start(h, OP6_HINT_EXPENSIVE_RENDERING, 2000) == OP6_POLICY_OK);
  assert(op6_policy_evaluate(h, 2100, &result) == OP6_POLICY_OK);
  assert(Find(result, OP6_RESOURCE_GPU_MAX) == 520000000);
  assert(Find(result, OP6_RESOURCE_GPU_MIN) == 414000000);
  assert(op6_policy_stop(h, OP6_HINT_EXPENSIVE_RENDERING) == OP6_POLICY_OK);
  assert(op6_policy_evaluate(h, 2100, &result) == OP6_POLICY_OK);
  assert(Find(result, OP6_RESOURCE_GPU_MIN) == -1);
  assert(op6_policy_reset(h) == OP6_POLICY_OK);
  assert(op6_policy_evaluate(h, 2100, &result) == OP6_POLICY_OK && result.count == 0);
  op6_policy_destroy(h);
  op6_policy_destroy(nullptr);
  std::puts("PASS: C ABI, invalid args, TTL, modes, stop, reset, resource limits");
}
