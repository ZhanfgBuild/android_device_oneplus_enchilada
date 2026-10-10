// SPDX-License-Identifier: Apache-2.0
// C ABI facade for a policy calculator. Not a Power HAL or a sysfs writer.
#ifndef OP6_POWER_POLICY_H_
#define OP6_POWER_POLICY_H_
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

#if defined(_WIN32)
#define OP6_POWER_API __declspec(dllexport)
#else
#define OP6_POWER_API __attribute__((visibility("default")))
#endif

#define OP6_POLICY_ABI_VERSION 1u
#define OP6_POLICY_MAX_TARGETS 6u

typedef struct op6_policy_handle op6_policy_handle;
typedef enum op6_policy_status {
  OP6_POLICY_OK = 0,
  OP6_POLICY_INVALID_ARGUMENT = 1,
  OP6_POLICY_INTERNAL_ERROR = 2
} op6_policy_status;
typedef enum op6_policy_hint {
  OP6_HINT_INTERACTION = 0,
  OP6_HINT_LAUNCH = 1,
  OP6_HINT_AUDIO_LAUNCH = 2,
  OP6_HINT_EXPENSIVE_RENDERING = 3
} op6_policy_hint;
typedef enum op6_policy_mode {
  OP6_MODE_BALANCED = 0,
  OP6_MODE_RESPONSIVE = 1,
  OP6_MODE_SUSTAINED = 2,
  OP6_MODE_BATTERY = 3
} op6_policy_mode;
typedef enum op6_policy_resource {
  OP6_RESOURCE_LITTLE_MIN = 0,
  OP6_RESOURCE_BIG_MIN = 1,
  OP6_RESOURCE_GPU_MIN = 2,
  OP6_RESOURCE_LITTLE_MAX = 3,
  OP6_RESOURCE_BIG_MAX = 4,
  OP6_RESOURCE_GPU_MAX = 5
} op6_policy_resource;

typedef struct op6_policy_target {
  uint32_t resource;
  uint32_t reserved;
  int64_t value;
} op6_policy_target;
typedef struct op6_policy_result {
  uint32_t abi_version;
  uint32_t count;
  op6_policy_target targets[OP6_POLICY_MAX_TARGETS];
} op6_policy_result;

// Monotonic time in milliseconds. The host must pass a consistent clock origin.
// All targets are desired limits only; actual writes are forbidden in this module.
OP6_POWER_API op6_policy_handle* op6_policy_create(void);
OP6_POWER_API void op6_policy_destroy(op6_policy_handle* handle);
OP6_POWER_API op6_policy_status op6_policy_reset(op6_policy_handle* handle);
OP6_POWER_API op6_policy_status op6_policy_set_mode(op6_policy_handle* handle,
                                                     uint32_t mode);
OP6_POWER_API op6_policy_status op6_policy_start(op6_policy_handle* handle,
                                                  uint32_t hint, uint64_t monotonic_ms);
OP6_POWER_API op6_policy_status op6_policy_stop(op6_policy_handle* handle,
                                                 uint32_t hint);
OP6_POWER_API op6_policy_status op6_policy_evaluate(op6_policy_handle* handle,
                                                     uint64_t monotonic_ms,
                                                     op6_policy_result* result);
#ifdef __cplusplus
}
#endif
#endif
