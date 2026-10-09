# OnePlus 6 / SDM845 performance architecture for independent AOSP 17

Status: **design + configuration inspection**, not a tuned or benchmarked ROM.
Device: OnePlus 6 (`enchilada`), Kryo 385 4+4, Adreno 630, UFS 2.1, LPDDR4x, 60 Hz 1080x2280 display.
Date: 2026-10-09.

## Performance objective

Optimize *perceived responsiveness* and *sustained performance per watt*.
No claim that SDM845 equals modern Snapdragon 8 chips in compute throughput.

Primary metrics, measured on real hardware under controlled battery, temperature and app conditions:
- SurfaceFlinger/FrameTimeline jank fraction, frame pacing and p95/p99 frame duration; nominal 60Hz vsync interval 16.67 ms.
- Touch-to-render latency and app launch/relaunch p50/p95, compared against an established baseline.
- First 2 minutes vs 15/30 minutes sustained performance, frame-time variance and thermal throttling.
- PSI memory/io/cpu stalls, ZRAM compression ratio, major fault and refault rate, lowmemorykiller events.
- Whole-device energy per representative task, screen-on drain, overnight idle drain, thermal headroom.
- Network, camera, audio and telephony regression tests after driver or scheduling changes.

No invented benchmark score or power percentage should be reported. Require at least five repeat runs per scenario,
consistent settings, and both 6GB/8GB device configurations when possible. Before claiming improvement,
compare p50/p95/p99 and energy, including adverse changes and the rollback point.

## Scheduling/control plane

1. Framework emits interaction, launch, camera, sustained workload and idle hints through a ROM-owned
   Power HAL / performance policy. Support Android Dynamic Performance Framework (ADPF) if the actual
   framework and AIDL Power HAL contracts pass compilation/runtime checks.
2. Android task profiles and cpusets own task grouping. If the audited kernel supports utilization clamps,
   use UClamp behind capability checks; otherwise retain the compatible WALT/schedtune path.
   Do **not** write the same knob from init scripts, Power HAL and an external tuning daemon.
3. Kernel owns CPU governor, devfreq, WALT/EAS implementations, GPU constraints and thermal safeguards.
   Start with supported schedutil/WALT combinations and measure; never force performance governor as the
   daily default or disable thermal throttling to improve benchmark scores.
4. Separate transient interaction hints from long-running sustained workload policy. Hint duration must
   expire. Thermal headroom takes precedence over performance requests.

### Performance modes (semantics only; NOT installed as a runtime tuning profile)

| Mode | Goal | CPU/GPU and memory behavior | Policy |
| --- | --- | --- | --- |
| Balanced | Default smoothness per watt | normal DVFS, PSI-lmkd, adaptive short hints | default after validation |
| Responsive | Touch, SystemUI, app switch | bounded transient boosts and prioritization, no permanent min freq | opt-in only after measurement |
| Sustained | Stable gaming/rendering | pacing + thermal-aware CPU/GPU budget; no aggressive peaks | opt-in only after long-run test |
| Battery | Idle/background efficiency | preserve alarms, BT, telephony, music and notification delivery | opt-in and functional regressions |

No hardware policy changes are applied by this document.

## Existing repository inspection

- `ZhanfgBuild/kernel_oneplus_sdm845:master` (Linux 4.19) `vendor/enchilada_defconfig` has
  `CONFIG_SCHED_WALT=y`, `CONFIG_PSI=y`, `CONFIG_MEMCG=y`,
  `CONFIG_ZRAM=y`, `CONFIG_CPU_FREQ_GOV_SCHEDUTIL=y`, `CONFIG_THERMAL=y`.
- `feature/a17-mmd-zram-4.19` additionally declares
  `CONFIG_UCLAMP_TASK=y`, `CONFIG_UCLAMP_TASK_GROUP=y`, and
  `CONFIG_ZRAM_DEFAULT_COMP_ALGORITHM="lz4kd"`. This does not prove the source builds or
  a device exposes usable UClamp controls.
- `device/oneplus/sdm845-common/init/init.qcom.post_boot.sh` has ~6095 lines
  shared with various Qualcomm platforms and contains writes for schedutil,
  interactive, ondemand, cpusets and legacy schedtune. Determine **which platform
  branches actually run** before removing anything; its mere presence does not mean
  every write executes on SDM845.
- Existing AOSP17 device config copies Android 9-era `cgroups_28.json` /
  `task_profiles_28.json`; that is a compatibility hazard, not an automatically
  suitable Android 17 performance policy. Audit against pinned Android 17 AOSP
  `libprocessgroup` before changing files or Cgroup controller layout.
- Android 17's `Memory Limiter` uses cgroup v2 memory controls such as `memory.high`
  and `memory.swap.max`. Do not claim support from `CONFIG_MEMCG=y` alone;
  check cgroup v2 mount, memory controller and runtime APIs.

## Memory and I/O

- Use PSI-enabled userspace `lmkd` with kernel support; profile thresholds after
  measuring stalls, refaults and foreground kills. Do not use hardcoded 4GB/ZRAM
  sizes or indiscriminately lower `minfree`.
- Compare lz4/lz4kd/zstd under the actual CPU load, page fault pattern, compression
  ratio and energy. Do not assume the fastest compression benchmark wins.
- Audit filesystem scheduler, UFS 2.1 queue behavior, F2FS/ext4 mounts, fsync,
  write amplification and I/O latency. Never disable durability/fsync broadly.

## Graphics and display

- First validate HWC, gralloc, SurfaceFlinger, KGSL, GPU devfreq and binary
  compatibility of the supplied Adreno stack.
- Mesa Freedreno GLES / Turnip Vulkan provide an important *experimental*
  Adreno 6xx path. Treat them as a separately profiled userspace-driver candidate,
  not a guaranteed system driver replacement. Compare Vulkan/GLES extensions,
  stability, memory usage, app compatibility and thermal behavior.
- GPU kernel driver (KGSL), proprietary userspace GL/Vulkan, firmware, allocator,
  gralloc and HWC belong to a compatibility matrix; do not swap just one binary.

## Safety gates

- No unconditional overclock, permanent boost, thermal disable, AVB disable,
  security patch spoofing or undocumented sysfs writes.
- Stage 0: Read-only `sh tools/op6_perf_probe.sh` snapshot (Android shell; no args).
- Stage 1: Compare `tools/audit_sdm845_kernel_config.py` with **generated** kernel
  `.config`, and independently verify source configs plus runtime interfaces.
- Stage 2: Implement compatible AIDL Power HAL / task profiles with feature flags;
  verify schedtune vs UClamp exclusivity and system boot.
- Stage 3: Profile performance against baseline; integrate only reproducible gains.
- Stage 4: Port drivers one subsystem at a time, with flashable rollback and
  fully verified kernel+HAL+firmware match.

## References

- Qualcomm SDM845: https://www.qualcomm.com/processors/application-processors/products/sdm845
- Android ADPF: https://source.android.com/docs/core/perf/performance-hint-api
- Android task profiles: https://source.android.com/docs/core/perf/cgroups
- Android lmkd/PSI: https://source.android.com/docs/core/perf/lmkd
- Android 17 Memory Limiter: https://source.android.com/docs/core/perf/memory-limiter
- Mesa Freedreno: https://docs.mesa3d.org/drivers/freedreno.html
- Android frame pacing: https://source.android.com/docs/core/graphics/frame-pacing
