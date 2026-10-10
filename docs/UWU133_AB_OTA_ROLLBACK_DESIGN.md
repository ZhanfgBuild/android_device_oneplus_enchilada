# uwuAOSP 17.0.101 → 17.0.133: OnePlus 6 A/B Rollback OTA (SOURCE-ONLY)

```text
OnePlus 6 / uwuAOSP 17.0.101 -> 17.0.133
Experimental dual-slot A/B + Retrofit Dynamic Partition OTA design
2026-10-10
STATUS: ARCHITECTURE + READ-ONLY PREFLIGHT + SOURCE PRODUCT STUB READY
STATUS: FULL ROM IMAGE / SIGNED OTA / REAL DEVICE A/B TEST NOT YET BUILT OR VALIDATED

1. DECISION
Recommend uwuAOSP 17.0.133 as the new DEVELOPMENT and future RELEASE baseline.
The user's running OS is verified as 17.0.101, Android 17 SDK 37, a 2026-09-29 unofficial
awa-xaga build. Freeze 101 as rollback reference; do NOT overwrite the current slot.

2. SOURCE PINNING AND CHANGE SCOPE
The immutable official 17.0.101 manifest lists 1,159 project paths.
The official 17.0.133 manifest lists 1,160 project paths.
Between them 43 existing project revisions changed; 1 project was added.
Changed components include frameworks/base, Settings, Launcher3, uwuSettingsExt,
uwuAICore, uwuPrism, build/make, Soong, Recovery, vendor/uwu and some SELinux
policies. This is an actual userspace platform upgrade, NOT simply a version change.
Use the frozen 133 release manifest (NEVER moving uwu-17.0 branch for production).
Official references:
https://github.com/uwuAOSP/platform_vendor_uwu-versions/blob/main/manifest/17.0.101.xml
https://github.com/uwuAOSP/platform_vendor_uwu-versions/blob/main/manifest/17.0.133.xml

3. ACTUAL USER PHONE FACTS
OnePlus 6 (ONEPLUS A6003), installed slot A (_a), Android 17 / API 37.
ro.boot.dynamic_partitions=true
ro.boot.dynamic_partitions_retrofit=true
ro.boot.super_partition=system
ro.virtual_ab.enabled is unset (do not label it a Virtual A/B device).
Working kernel: Linux 4.19.325 with integrated BakaSU.
Working ROM boot.img: Android Boot header v1, partition 64 MiB.
The actual boot.img Ramdisk fstab declares:
  system /system erofs logical slotselect avb=vbmeta
  vendor /vendor erofs logical slotselect avb
  odm /odm erofs logical slotselect avb
  /metadata ext4 on /dev/block/by-name/logdump
  /data ext4 encrypted with aes-256-xts:aes-256-cts:v2, fsverity, quota
Older ext4 / fileencryption=ice fstab belongs to a stale 4.9 baseline: DO NOT REUSE.
Current Google Drive ROM has a matching 64MiB stock boot.img, but its full OTA ZIP
has not been read (the connector has a 256MiB per-file download ceiling).

4. MAJOR SOURCE GAP: DEVICE TREE NOT FLASH READY
Repository ZhanfgBuild/android_device_oneplus_enchilada bringup/aosp17 presently has
product aosp_enchilada, NOT an uwu_enchilada 133 product.
Repository ZhanfgBuild/android_device_oneplus_sdm845-common bringup/aosp17 declares
legacy ext4 fstab, not logical EROFS. AB_OTA_PARTITIONS include boot/dtbo/system/
vbmeta/vendor without proven coverage of logical odm, metadata, or physical groups.
It is a separate AOSP17 bring-up stage, not the known working awa-xaga 101 tree.
DO NOT change its BoardConfig to guessed group sizes or call the current product
an OTA-compatible ROM. First obtain actual lpdump extents and block capacities.
The provided uwu_enchilada.mk is ONLY a preliminary product entrance.

5. OTA LAYOUT / SAFETY PROTOCOL
State 0: Current system A is known bootable, BakaSU + recovery + dtbo_A/vbmeta_A
         intact. A is the source and MUST NOT be rewritten by update package.
State 1: Device probe checks bootctl slot A/B bootable/successful, current fingerprint,
         exact group layout (lpdump), 64 MiB Boot, fstab and OTA trust anchors.
State 2: Prepare uwu133 target-files.zip using frozen 17.0.133 manifest and a validated
         OnePlus6 ROM device/vendor/kernel/proprietary set. Build EROFS dm-linear
         logical partitions and coherent new metadata for the inactive B slot.
State 3: Prepare B's 133 boot.img with a new compatible recovery ramdisk and the
         verified 4.19 BakaSU kernel + exact device DTBs. Do not carry a stale 101
         recovery ramdisk without 133 init/SELinux/boot validation. Match dtbo_B,
         vbmeta_B and AVB signing chain. Do not blindly omit boot from OTA.
State 4: Generate a FULL A/B OTA from target-files; a reliable binary delta
         requires a matching signed 101 target-files.zip (not available).
State 5: Verify OTA package signature versus device-accepted OTA public keys;
         verify AVB chain, partition table, dynamic metadata, group sizes,
         payload manifest, expected modified partitions and both Boot images.
State 6: Apply via supported update_engine with explicit approval after preflight;
         write ONLY the inactive B slot (system, vendor, odm, boot, dtbo, vbmeta
         as needed), then stage slot B boot.
State 7: First B boot run known-good checks (adb, display/touch, telephony,
         decrypt /data, SELinux, Wi-Fi, recovery, BakaSU manager/modules) before
         considering the new build release-ready. Keep old A slot untouched.
State 8: If new slot B fails, return to old A via bootloader/fastboot slot
         selection when allowed. Automatic fallback also depends on the actual
         boot-control HAL/bootloader state and must be tested on device.
State 9: DO NOT install a second OTA until user decides to retire A as fallback.

6. ROLLBACK LIMITS
A/B slot rollback preserves the old SYSTEM partition images, not /data.
Both 101 and 133 operate on the same /data and /metadata; database migrations,
APEX state, userspace or FBE changes can break a downgrade even when A boots.
Before any real rollout, make a separate off-device backup of important data
and prove restore on a non-critical test case. Never promise zero-data-loss
rollback based on dual slots alone. For best safety, do not enroll users in
new encryption format or force /data schema migration during first trial.

7. OTA SIGNATURE/AVB
The device reports release-keys, green verifiedboot and locked vbmeta state;
those properties alone do not establish the actual bootloader lock state or
private signing key possession. Previous custom BakaSU fastboot Boot succeeded.
Using a self-generated platform/OTA key does not make it automatically accepted
by the current 101 Recovery/update_engine. Do not disable AVB/verification to
claim an OTA works. Inspect public trust anchors, choose a supported signing
transition / authorized recovery route, and perform a signed packaging dry-run.
Never commit private keys or raw user/vendor ROM images to a public repository.

8. IMPLEMENTATION STAGES (NO USER DECISION NEEDED FOR SOURCE PREP)
A. Freeze 101/133 source manifests and generate source-commit diff. [DONE]
B. Define uwu_enchilada.mk 133-only product and fail-closed tests. [DONE]
C. Capture bootctl + lpdump + partition sizes with provided no-arg SH. [NEEDS DEVICE LOG]
D. Port actual retrofit EROFS metadata + FBEv2 fstab into device-common tree.
E. Align vendor trees, SELinux, 133 Recovery, 4.19 BakaSU Boot and dtbo/AVB.
F. Build target-files and 133 candidate image on appropriate CI/cloud host.
G. Create A/B OTA payload and verify all signatures/manifest/partition operations.
H. Conduct first controlled device install to inactive slot and rollback tests.

9. CURRENT OUTPUTS
  uwu_enchilada.mk - source product stub only (not yet ready to compile bootable OTA)
  OP6_uwu133_AB_Rollback_Preflight_ReadOnly.sh - no-argument read-only shell
  REVIEW_ONLY_OTA_GATE.json - known facts + explicit NOT_FLASH_READY status
  check_ota_gate.py - fail-closed validator
  test_ota_gate.py - negative tests
No flashable image is included. No automatic slot switching, bootctl writes,
formatting, repartitioning or SELinux changes are performed.

10. PUBLIC AOSP REFERENCE DOCUMENTS
https://source.android.com/docs/core/ota/ab
https://source.android.com/docs/core/ota/dynamic_partitions/ab_legacy
https://source.android.com/docs/core/ota/sign_builds
https://source.android.com/docs/core/ota/dynamic_partitions/implement
```
