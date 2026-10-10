// SPDX-License-Identifier: Apache-2.0
#include "include/op6_power_policy.h"
#include "policy_engine.hpp"
#include <chrono>
#include <cstdint>
#include <new>

struct op6_policy_handle {
  op6::power::Engine engine;
};
namespace {
constexpr uint64_t kMaxMs = 9223372036000ULL; // 292 years; avoid ns overflow.
bool ValidTime(uint64_t ms) { return ms <= kMaxMs; }
using op6::power::Time;
Time At(uint64_t ms) { return Time(std::chrono::milliseconds(static_cast<int64_t>(ms))); }
bool ValidHint(uint32_t hint) { return hint <= OP6_HINT_EXPENSIVE_RENDERING; }
bool ValidMode(uint32_t mode) { return mode <= OP6_MODE_BATTERY; }
} // namespace

extern "C" {
op6_policy_handle* op6_policy_create(void) {
  return new (std::nothrow) op6_policy_handle();
}
void op6_policy_destroy(op6_policy_handle* handle) { delete handle; }
op6_policy_status op6_policy_reset(op6_policy_handle* handle) {
  if (!handle) return OP6_POLICY_INVALID_ARGUMENT;
  handle->engine = op6::power::Engine{};
  return OP6_POLICY_OK;
}
op6_policy_status op6_policy_set_mode(op6_policy_handle* handle, uint32_t mode) {
  if (!handle || !ValidMode(mode)) return OP6_POLICY_INVALID_ARGUMENT;
  handle->engine.SetMode(static_cast<op6::power::Mode>(mode));
  return OP6_POLICY_OK;
}
op6_policy_status op6_policy_start(op6_policy_handle* handle, uint32_t hint,
                                    uint64_t monotonic_ms) {
  if (!handle || !ValidHint(hint) || !ValidTime(monotonic_ms))
    return OP6_POLICY_INVALID_ARGUMENT;
  try {
    handle->engine.Start(static_cast<op6::power::Hint>(hint), At(monotonic_ms));
  } catch (...) { return OP6_POLICY_INTERNAL_ERROR; }
  return OP6_POLICY_OK;
}
op6_policy_status op6_policy_stop(op6_policy_handle* handle, uint32_t hint) {
  if (!handle || !ValidHint(hint)) return OP6_POLICY_INVALID_ARGUMENT;
  handle->engine.Stop(static_cast<op6::power::Hint>(hint));
  return OP6_POLICY_OK;
}
op6_policy_status op6_policy_evaluate(op6_policy_handle* handle,
                                       uint64_t monotonic_ms,
                                       op6_policy_result* result) {
  if (!handle || !result || !ValidTime(monotonic_ms))
    return OP6_POLICY_INVALID_ARGUMENT;
  try {
    const auto targets = handle->engine.Evaluate(At(monotonic_ms));
    if (targets.size() > OP6_POLICY_MAX_TARGETS)
      return OP6_POLICY_INTERNAL_ERROR;
    op6_policy_result output{};
    output.abi_version = OP6_POLICY_ABI_VERSION;
    output.count = static_cast<uint32_t>(targets.size());
    size_t i = 0;
    for (const auto& [resource, value] : targets) {
      output.targets[i++] = {static_cast<uint32_t>(resource), 0u, value};
    }
    *result = output;
  } catch (...) { return OP6_POLICY_INTERNAL_ERROR; }
  return OP6_POLICY_OK;
}
} // extern "C"
