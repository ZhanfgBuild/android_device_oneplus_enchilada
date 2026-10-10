# OnePlus 6 independent Android 17 Power AIDL event bridge

Status: Stage-3 small-module host tests and NDK ARM64 cross-compile only.
NOT a flashable ROM, AIDL service, system daemon or deployable root module.

## Architecture

1. `power/policy_engine.hpp` computes transient CPU/GPU resource requests.
   Boost events have a bounded TTL (180ms default interaction, 90ms display,
   600ms audio); explicit duration is capped to 5000ms. They do not persist
   after expiry. These durations are calibration hypotheses, not measured gains.
2. `power/aidl_event_adapter.hpp/.cpp` translates official Android 17
   Boost / Mode enums to the policy engine. It locks state to support
   concurrent future Binder callbacks. These are only *event semantics*,
   NOT an implementation of android.hardware.power.IPower.
3. `power/request_reconciler.hpp` computes desired resource Set / Release
   changes. A backend must explicitly acknowledge an *atomic* apply. Partial
   failures require a complete release/restore and recovery acknowledgement
   before further plans can be issued.
4. `power/policy_c_api.cpp` is now serialized with a per-instance mutex.
   A caller must never destroy a handle while other threads are using it.

## Verified AOSP 17 AIDL contract

Source: official hardware/interfaces **android-17.0.0_r1**, not main:
- Boost: https://android.googlesource.com/platform/hardware/interfaces/+/refs/tags/android-17.0.0_r1/power/aidl/android/hardware/power/Boost.aidl
- Mode: https://android.googlesource.com/platform/hardware/interfaces/+/refs/tags/android-17.0.0_r1/power/aidl/android/hardware/power/Mode.aidl
- IPower: https://android.googlesource.com/platform/hardware/interfaces/+/refs/tags/android-17.0.0_r1/power/aidl/android/hardware/power/IPower.aidl

Boost supported in the translator: INTERACTION (0),
DISPLAY_UPDATE_IMMINENT (1), AUDIO_LAUNCH (3).
Boost durationMs < 0 stops the matching boost, 0 maps to a bounded default,
and positive duration is capped to five seconds.

Mode supported in the translator: LOW_POWER (1),
SUSTAINED_PERFORMANCE (2), LAUNCH (5) and EXPENSIVE_RENDERING (6).
LOW_POWER outranks SUSTAINED while overlapping.
LAUNCH has a fallback 900ms TTL even if the disable callback is lost.
EXPENSIVE_RENDERING stays active until Mode=false or adapter Reset.

All unimplemented enum values MUST return false in the future
isBoostSupported()/isModeSupported() implementation. In particular:
- no claim of ADPF hint sessions, FMQ channel or CPU/GPU headroom;
- no double-tap wake support without device-specific input validation;
- no fixed-performance mode until 10-minute thermal calibration;
- no device idle, display suspend or camera/IMS boost implementation yet.

## Host validation and limits

CI uses an actual official AOSP17 tagged Boost/Mode AIDL download and checks
numeric ordinal mappings; also runs:
- C++ policy engine tests;
- C++ event adapter and multi-threaded tests;
- C ABI basic and multi-threaded tests;
- request reconciliation Set/Update/Release/failed-apply recovery tests;
- NDK AArch64 ELF + static library architecture inspection.

NDK compilation is not AOSP17 Soong compilation; live VINTF/SELinux and
AIDL binder/IPower API coverage still need a full source tree.

## Next work once large builder is available

- Compile against generated android.hardware.power-V*-ndk and implement
  full IPower methods, explicitly return EX_UNSUPPORTED_OPERATION for
  unsupported hint sessions/headroom/FMQ APIs.
- Confirm VINTF instance/default and sepolicy, SELinux enforcing, service
  startup, framework restarts and real hint calls from Android PowerManager.
- Design a node backend with *exclusive* hardware ownership and transaction
  rollback. Never ship parallel vendor perf daemons or force governors on boot.
- Test full 4.19 cgroup v2 support, camera/RIL/audio, display pipeline, boot,
  OTA rollback and frame-time thermal telemetry before merging for release.
