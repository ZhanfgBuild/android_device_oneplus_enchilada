# SDM845/OnePlus 6 driver candidates and porting rules

2026-10-09 source inventory. **No newer driver is validated or shipped by this change.**
A source code update does not imply firmware/kernel ABI compatibility.

| Area | Candidate / pinned or reference source | Integration strategy | Release gate |
| --- | --- | --- | --- |
| Linux kernel | [community 4.19 donor](https://github.com/ZhanfgBuild/android_kernel_oneplus_sdm845/tree/lineage-23.2-4.19), [ABK 4.19 integration](https://github.com/ZhanfgBuild/kernel_oneplus_sdm845) and [Lineage 4.9 reference](https://github.com/ZhanfgBuild/android_kernel_oneplus_sdm845_los/tree/lineage-22.2) | compare sched/WALT, DT, ABI, firmware interfaces and security fixes; never force merge incompatible kernels | defconfig + full image + device boot/thermal tests |
| GPU kernel KGSL | `drivers/gpu/msm` in matched SDM845 4.19 tree | audit KGSL UAPI and Adreno GMU requirements against graphics stack; incremental cherry-picks only | HWC, Vulkan/OpenGL, gaming, suspend, thermal stability |
| GPU userspace | [Mesa Freedreno / Turnip](https://docs.mesa3d.org/drivers/freedreno.html) | experimental package in separate variant (not global system replacement); Adreno 6xx coverage exists, a630 runtime compatibility still must be tested | Vulkan conformance subset, compositor, 3D game suite, crash-free runs |
| Display/HWC/gralloc | Existing [OxygenOS blob/SDM845 vendor](https://github.com/ZhanfgBuild/proprietary_vendor_oneplus_sdm845-common) and OnePlus device hardware | maintain matching producer/consumer buffers, ION, UBWC, kernel KMS/KGSL interfaces | no blank screen, GPU hangs, flicker, blanking regressions |
| Power HAL | [OnePlus hardware (AOSP experimental branch)](https://github.com/ZhanfgBuild/android_hardware_oneplus/tree/bringup/aosp17) and [OPlus hardware](https://github.com/ZhanfgBuild/android_hardware_oplus/tree/lineage-24.0) | code donors only; implement ROM-owned AIDL HAL and task profiles after contract audit | no stale vendor hints, Power HAL + ADPF session correctness |
| Wi-Fi/BT | OnePlus WCN3990 driver + firmware/hostapd + vendor blobs; matched SDM845 kernel | transport/HAL/firmware set must match; don't insert firmware from different chip revisions | 2.4/5GHz, BT earbuds, airplane mode, roaming, standby |
| Modem/RIL/IMS | Existing proprietary Qualcomm/OOS 11 blobs, SDM845 HIDL contracts | keep last known-good DSP/modem stack; update userspace shims without flashing unverified baseband | calls, data, VoLTE, emergency calling, dual SIM and suspend |
| Audio/DSP | OnePlus WCD934x/audio HAL/Hexagon firmware | preserve A2DP offload, speaker and wired path while migrating AIDL; avoid default postprocessing | calls, playback, mic, recording, Bluetooth latency |
| Camera/ISP | Spectra 280 + vendor camera/HIDL + matched kernel/media buffers | preserve vendor ABI, shim carefully; don't transplant contemporary ISP blobs | both rear modules, front, photo/video, torch, camera privacy |
| Fingerprint/sensors | OnePlus HAL + Qualcomm sensors | validate VINTF/AIDL bridge and SELinux rules, keep vendor calibration | enrollment, unlock, rotation, proximity, idle power |
| UFS 2.1 | Existing SDM845 block/ufs kernel | inspect scheduler, filesystem, storage errors, discard and latency | fio-style safe test, sustained file I/O, data integrity |
| Battery & charge | Separate ABK `feature/op6-4500mah-battery` work | gauge real FCC/Qmax from detected IC, preserve protection, distinguish reporting from charging | true gauge capacity, charge cutoff, temperature and recovery |

## Porting protocol

1. Identify device hardware revision and full boot/vendor/firmware build identity without
   publishing serial numbers, IMEI, calibration data or keys.
2. Capture a reproducible source commit, license and the exact changed files.
3. Diff against compatible *same-family* donor, document UAPI/ABI implications,
   kernel configuration and VINTF requirements.
4. Build and test the narrowest subsystem. Driver updates are not valid simply
   because the repo branch name is newer.
5. Record boot and standby behavior; GPU hang rate, memory regressions,
   suspend, power, audio/calls and recovery.
6. Preserve a signed, identified fallback. No automatic modem/bootloader/TEE
   flashing and no undocumented thermals/voltages.

## Compatibility concerns to resolve before first AOSP 17 ROM

- Current `vendor/oneplus/*` is from older Lineage/stock donors; it is **not**
  automatically Android 17-compatible.
- Android 17 Memory Limiter and modern Power HAL may require cgroup v2,
  UClamp, thermal headroom and ADPF interfaces unavailable on the current kernel.
- Mesa Turnip provides a potential modern *graphics userspace* path but cannot
  automatically replace KGSL, Qualcomm DSP/firmware, or the stock HWC stack.
- Open-source Linux 4.19 KGSL changes should be backported along with required
  API and dependencies, never overwritten wholesale from newer Snapdragon SoCs.
- Hardware-independent AOSP 17 performance framework work can proceed
  separately from these vendor driver migrations.

**Result:** candidates identified, no binary driver download/flash, no stability claims.
