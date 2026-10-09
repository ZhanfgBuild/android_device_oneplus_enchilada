# Independent AOSP 17 on OnePlus 6 (SDM845): porting gates

2026-10-10. Status: **Stage-1 static code / host tests**.
Android 17 upstream base: `android-17.0.0_r1` (official AOSP tag, June 16 2026).
This document is an evidence-based compatibility worklist, not a declaration that the device boots Android 17.

## P0. Build and boot sequence

1. **Device product and ownership.** Only `aosp_enchilada` inherits AOSP product
   configuration. The `common.mk` and proprietary trees are hardware donors.
   Eliminate build-time `vendor.lineage.*`, obsolete Qualcomm references and
   foreign runtime services one dependency at a time.
2. **Android 17 libprocessgroup.** The obsolete `cgroups_28.json` and
   `task_profiles_28.json` copy directives were removed from `device.mk`
   in Stage-1. Use platform defaults, then add a narrow *verified* vendor
   overlay when needed. Audit cgroup v1 cpusets/schedtune alongside cgroup v2 memory.
3. **Partition and recovery assumptions.** OnePlus 6 uses legacy A/B partition
   layout with recovery-as-boot. Do not blindly configure dynamic partitions,
   virtual A/B, recovery partition or generic modern fastbootd. Verify actual
   boot header, dtbo, fstab, encryption, AVB chain and OTA block devices.
4. **Vendor and FCM.** The stock Qualcomm/OxygenOS vendor stack is a legacy
   Android 11-era source. The common device manifest declares FCM target-level
   5 and HIDL HALs. Validate this *specific* AOSP 17 framework FCM matrix,
   not merely XML syntax. Do not raise target-level without implementing all
   newly required HALs. Run `checkvintf` and Treble VTS when a full source
   tree is available.
5. **Kernel base.** Compare the clean community SDM845 4.19 source and ABK
   4.19.325 with kernel modules, device tree, firmware interfaces, USB, WLAN,
   SELinux, binderfs, ION/DMA-buf, eBPF, scheduler and filesystem support.
   Linux 4.19 is out of upstream support; targeted security backports and a
   documented support policy are needed. A switch to kernel 5.15/GKI is
   experimental research, not a mandatory prerequisite for first boot.
6. **Init, Ueventd and SELinux.** Remove vendor-specific obsolete sysfs
   writes only after actual SDM845 execution paths are known. Verify labelling,
   neverallow, service context, property context and vendor init permissions
   with SELinux enforcing. No blanket permissive mode.

## P0. Audio, graphics and hardware compatibility

7. **Audio.** The donor common tree declares Audio HIDL 6.0, Audio Effect
   HIDL 6.0 and a Qualcomm legacy primary HAL. Modern Android uses AIDL
   audio interfaces for new features. Verify Android 17 framework support
   for the shipping FCM, then use a tested bridge/port where required.
   Calls, recording, Bluetooth offload and speaker protection are release gates.
8. **Display/GPU.** Verify Qualcomm HWC2, Gralloc/Mapper, ION/UBWC,
   SurfaceFlinger, Adreno 630 proprietary GLES/Vulkan and KGSL UAPI as a
   matched stack. The previous phone traces show 710 MHz GPU capability
   returning when a transient policy constraint clears. Never bake in a
   permanent forced GPU clock. Mesa Turnip remains an optional per-app
   experimental GPU userspace candidate.
9. **Modem/RIL/IMS.** Preserve vendor radio firmware; validate SIM, data,
   VoLTE/IMS, in-call audio, emergency calls and airplane mode.
   Do not flash unverified modem, DSP, TEE or bootloader firmware.
10. **Camera, fingerprint and trust.** Validate legacy camera provider/HIDL,
    both Sony camera sensors, codec encoder/decoder, fingerprint enrollment,
    Gatekeeper/Keymaster vs Keystore2, biometrics, DRM, attestation and
    hardware-backed data encryption. Never fake security patch levels.
11. **Connectivity and peripherals.** Validate Wi-Fi/BT coexistence, BT music,
    NFC, GNSS, USB/MTP/ADB, sensors, vibration, alarm, double-tap, proximity,
    charging, suspend/resume and wake-up sources. Check old Qualcomm
    proprietary system_ext packages for removed framework APIs.

## P0. Android 17 memory and runtime contract

12. **Memory Limiter.** Official Android 17 implementation uses cgroup v2
    `memory.high` and `memory.swap.max`. Existing OnePlus 6 logs expose
    cgroup v2 `memory` controller, and ABK 4.19 `mm/memcontrol.c`
    defines `memory_high_write` and the `high` cftype, but its cgroup v2
    `memory_files[]` list does **not** expose a `swap.max` cftype.
    That is a *specific confirmed source-level missing feature*, subject
    to proving the exact generated kernel binary/branch on-device.
    Assess upstream swap accounting backport, all mm/swap prerequisites and
    Kconfig before claiming Android 17 Memory Limiter works.
13. **LMKD/PSI and ZRAM.** Keep PSI and memory cgroups. Measure stalls,
    compress ratio, background kills and UI latency, not only maximum
    compression speed. No indiscriminate swap allocation or LMK thresholds.
14. **ART, binder and BPF.** Verify platform bionic/APEX/ART, Binder IPC,
    BPF program load and verifier, netd/tethering and seccomp compatibility;
    kernel .config flags are not runtime proof.

## P1. Performance and UX modernization

15. **Power HAL control plane.** Stage-1 policy engine in
    `power/policy_engine.hpp` implements bounded hints, timer expiry and
    resource arbitration. It emits requests *without writing sysfs*. A
    vendor-stable AIDL Power HAL adapter must be compiled against the exact
    Android 17 NDK interface, then pass VINTF/service registration/SELinux
    and lifetime tests before inclusion in `PRODUCT_PACKAGES`.
16. **Scheduler.** Default initial reference is schedutil + WALT with one
    policy owner. UClamp on a tested ABK branch can be explored, but old
    schedtune cannot be swapped blindly for cgroup v2 CPU controller.
17. **Frame pipeline.** Benchmark FrameTimeline p95/p99, touch latency,
    SurfaceFlinger, HWUI, HWC, ART app launch and thermal steady state.
    Improve visual smoothness through pacing, prefetch and resource hints
    without disabling power safeguards.
18. **User-facing ROM.** Once basic telephony, Wi-Fi, camera, suspend and
    security pass, provide own Settings/launcher/theming, updater, integrated
    performance profiles and rollback, maintaining AOSP as the base rather
    than inheriting a third-party ROM framework.

## Release evidence gates

- S0: source manifest pinned, integrity and static compatibility checks PASS.
- S1: clean AOSP17 `lunch aosp_enchilada-userdebug` and Soong *parse* PASS.
- S2: kernel + boot, dtbo, vbmeta, vendor, system images build together;
  libvintf/sepolicy contract PASS.
- S3: real OnePlus 6 boots to ADB with verified recovery rollback.
- S4: real radio/IMS, screen, touch, Wi-Fi, audio, camera, encryption, fingerprint,
  storage, charging and standby smoke tests PASS.
- S5: performance, thermal, power and repeated OTA/rollback matrix PASS.
- Release signing / bootloader lock requires its own independent security audit;
  DO NOT RELOCK experimental firmware.

There is currently no verified S1/S2/S3/OTA result and no flashable ROM release.

## Official references

- AOSP 17 release: https://android.googlesource.com/platform/manifest/+/refs/tags/android-17.0.0_r1
- Android 17 Memory Limiter: https://source.android.com/docs/core/perf/memory-limiter
- VINTF architecture: https://source.android.com/docs/core/architecture/vintf
- Stable AIDL HAL: https://source.android.com/docs/core/architecture/aidl/aidl-hals
- Android Power: https://source.android.com/docs/core/power
