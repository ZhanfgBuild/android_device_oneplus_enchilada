# OnePlus 6 AOSP 17: small modules, 2026-10-10

## Built

- Native CPU/GPU power policy: power/policy_engine.hpp, power/policy_c_api.cpp
  and power/include/op6_power_policy.h. Seven versioned C ABI functions.
- Real Android ARM64 ELF shared library, NDK API 29 target, C++ runtime
  statically linked. NDK cross-compile and ELF AArch64 check passed in CI.
- Powerhint JSON static auditor: tools/audit_powerhint_policy.py with six tests.
- Host native engine and ABI lifecycle tests and AOSP17 compatibility gates.

CI workflow: .github/workflows/aosp17-small-modules.yml.
These are standalone components only. Full AOSP17 Soong builds have NOT run.

## Integration constraints

- This module is a request calculator, not a real AIDL Power HAL service.
  It never writes to sysfs and cannot guarantee a thermal limit or CPU clock.
  Only a future tested AIDL adapter can apply and fully release a request.
- The C ABI expects a single serialized caller. Start/evaluate timestamps
  must share the same monotonic origin; wall clock is invalid.
- Battery and Sustained modes persist until explicit mode exit or reset;
  short-lived hints have bounded TTL or an explicit Stop.
- NDK Android ABI build != vendor VINTF registration, SELinux compatibility,
  ROM boot, device test, APK, Magisk module or flashable ZIP.
- The Android 17 kernel memory.swap.max gap is tracked in kernel Issue #28.
- Never manually copy the .so to the vendor partition of a running phone.

## Validated locally and in CI

Host engine test PASS.
Host C ABI test PASS.
Host audit policy 6 tests PASS.
NDK ARM64 compile + ELF architecture + exported symbol checks PASS.
SHA256 checks on downloaded GitHub build artifact PASS.

## Next

1. Integrate ROM-owned Power HAL AIDL adapter against exact Android17 headers.
2. Audit and replace old task profiles after complete Soong configuration.
3. Port missing cgroup v2 swap.max into validated kernel build.
4. Graphic/audio/IMS HAL compatibility and recovery/rollback gates.

No production ROM build or device flashing has been attempted by this work.
