# Independent AOSP 17 / SDM845 Power HAL policy contract

Status: **non-shipping design gate only**. This does not change boot, clocks, thermal limits or firmware.

## Decision

The ROM has exactly one Android-side owner for interactive CPU/GPU requests: a ROM-maintained
AIDL Power HAL backed by a validated libperfmgr-like hint engine. Kernel scheduler and thermal
governors retain authority over DVFS, voltage, LMH and device safety. AOSP independence means
we maintain the product, interface and runtime integration ourselves; it does NOT require
discarding suitable, legally reusable HAL code.

Do not add a parallel root daemon, persistent `performance` governor or proprietary
frequency writer to make the device look faster.

## Contract

1. **CPU:** default to scheduler-driven DVFS after checking the actual kernel and hardware
   (`schedutil` is the initial reference candidate); `performance` is reserved for
   explicit controlled experiments, never the installed default.
2. **GPU:** preserve KGSL + `msm-adreno-tz` DVFS on the initial donor stack. Differentiate
   a GPU *frequency ceiling* from the actual clock. Also track `max_pwrlevel` as an
   independent user-defined KGSL power-level ceiling (smaller number permits faster states).
3. **Thermal:** preserve hardware LMH and thermal safeguards. Do not overwrite cooling
   devices or reset constraints merely because an app requests more performance.
4. **Hints:** short events (interaction, launch, audio launch, expensive rendering) must be
   explicitly timed out or paired with a reliable end/release path. In libperfmgr,
   an Action with `Duration=0` has no automatic timeout; it is not an instantaneous pulse.
   Some named modes are intentionally indefinite while enabled (e.g. sustained mode);
   review their stop transitions.
5. **Limits:** a configured default maximum frequency is an *allowed ceiling*, not a
   forced clock. Never report it as GPU utilization or as a benchmark.
6. **Task groups:** coexistence of Android `/system/etc/task_profiles.json` and vendor
   `/vendor/etc/task_profiles.json` requires explicit controller compatibility review.
   Old schedtune profiles cannot be assumed to support modern Android 17 UClamp/ADPF.
7. **Validation:** refuse a release build on invalid `powerhint.json` structure, including
   unknown Node names, missing Values, invalid DefaultIndex, nonnumeric/negative duration,
   undefined Value, or duplicate (PowerHint, Node) Actions. Emit review warnings, not silent
   modifications, for indefinite interactive hints and GPU rail/clock forcing.
8. **Performance modes:** Balanced, Responsive, Sustained and Battery modes are candidate
   operating points, not arbitrary static frequency tables. No new profile ships before
   real-device trace, power/thermal evaluation and a reliable rollback.
9. **Driver compatibility:** HAL, kernel KGSL, firmware, gralloc/HWC and GPU userspace
   belong to a tested interface matrix. Do not insert Turnip or newer Qualcomm blobs
   into the primary image before subsystem-specific tests pass.
10. **Privacy:** raw single-user hardware reports belong in the user's private working
    records, not this public repository.

## Verification gates

- Policy JSON unit tests and static validator run against the exact candidate source.
- Source+vendor HAL interface resolved and AOSP 17 Soong product compiles.
- AIDL HAL starts, registers, handles hint start/stop, and survives framework restarts.
- CPU/GPU idle frequencies reduce as expected; an interrupted interaction does not
  leave a permanent min-frequency or force-clock constraint.
- Sustained performance mode exits cleanly; thermal limits always supersede boosts.
- Only then profile FrameTimeline p95/p99, launch p50/p95, idle drain and thermal stability.

Reference implementation semantics:
https://android.googlesource.com/platform/hardware/google/pixel/+/refs/heads/main/power-libperfmgr/libperfmgr/HintManager.cc

No system or frequency changes are made by this file.
