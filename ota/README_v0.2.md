# OP6: uwuAOSP 17.0.133 / A/B rollback integration checkpoint v0.2

Based on **running** 17.0.101, not on a guessed version number. The 17.0.133
`platform_vendor_uwu-versions/manifest/17.0.133.xml` is the immutable source
manifest. The source manifest differs in 43 pinned projects + 1 addition.

### WIP cross-repository wiring

- `ZhanfgBuild/android_device_oneplus_enchilada`: product `uwu_enchilada`
  and guarded inclusion of common `ota/uwu133/BoardConfigRetrofit.mk`.
- `ZhanfgBuild/android_device_oneplus_sdm845-common`: the actual 4.19 Boot
  source fstab, a read-only recovery fstab reference and verified-only Soong
  build inputs.
- The existing `init/fstab.qcom` module still installs a legacy ext4 donor
  fstab. Explicit override/Soong installation path resolution remains an
  **unmet gate**, not hidden by merely setting `TARGET_RECOVERY_FSTAB`.

`flash_ready=false` remains mandatory until device lpdump/block sizes,
OTA signing, 133 target-files, nonactive slot writing and complete rollback
(including shared userdata) are independently checked. A/B slots cannot
provide two independent userdata copies. v0.2 modifies source only, not the
phone. A **full** OTA is the first candidate; binary source-based incremental
OTA is blocked until matching 17.0.101 target-files are obtained.