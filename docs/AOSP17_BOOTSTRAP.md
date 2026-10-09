# OnePlus 6 independent AOSP 17: Stage-0 source bootstrap

Status: **SOURCE INVENTORY / STATIC PREFLIGHT ONLY** (2026-10-09).
No Android 17 image, Soong build, boot, hardware functionality, OTA or AVB/relock result is claimed here.

## Architecture and source policy

- ROM userspace: Google's AOSP `android-17.0.0_r1`.
- Product: `aosp_enchilada`; Android device codename `enchilada` (OnePlus 6).
- No Lineage product inheritance, SDK, system framework packages, or shipping runtime identity.
- Known-good community device descriptions and legacy OnePlus/OxygenOS 11 blobs are *hardware donors*, not a basis for renaming a Lineage ROM.
- Current experimental bridge kernel: community Linux 4.19, clean fork pinned in the manifest. Separately preserve the LineageOS 22.2/Linux 4.9 compatibility reference.
- Root, ReSukiSU, SuSFS, dynamic partition conversion, kernel 5.15/GKI migration and relocking the bootloader are **NOT** Stage-0 prerequisites or asserted achievements.

## Reproducible source layout

The file `manifests/enchilada-aosp17-stage0.xml` pins 10 source repositories to full commit IDs. It is a **repo local manifest**, not a replacement for the official AOSP `platform/manifest`.

On a dedicated Linux machine with Android build prerequisites, sufficient disk/RAM, `repo` and `git-lfs` installed:

```sh
# The extra bootstrap checkout holds our unmerged build tools.
git clone --depth=1 -b work/aosp17-source-preflight-20261009 \
    https://github.com/ZhanfgBuild/android_device_oneplus_enchilada.git ../op6-aosp17-bootstrap

mkdir -p op6-aosp17
cd op6-aosp17
repo init -u https://android.googlesource.com/platform/manifest -b android-17.0.0_r1
mkdir -p .repo/local_manifests
cp ../../op6-aosp17-bootstrap/manifests/enchilada-aosp17-stage0.xml \
    .repo/local_manifests/enchilada.xml
repo sync -c -j8 --fail-fast

# Git LFS objects must be materialized, not left as pointer files.
repo forall vendor/oneplus/enchilada vendor/oneplus/sdm845-common -c 'git lfs pull'

python3 ../../op6-aosp17-bootstrap/tools/validate_aosp17.py \
    --device-dir device/oneplus/enchilada --workspace .
```

The commands are examples for a configured build host, **not a claim that the full AOSP checkout or a compilation has been run**. Do not run them from the phone; they do not flash or modify a device.

## Known integration blockers before Soong

1. Vendor blobs use `lineage-22.2`; the AOSP Android 17 HAL/framework interface contract has not been verified.
2. `sdm845-common/common.mk` is still a compatibility donor. Package removal via the AOSP wrapper does **not** prove that inherited product modules and Soong namespaces are independent of LineageOS. Audit and replace framework-specific references at source.
3. The device uses Qualcomm CAF build makefiles and vendor sepolicy donors. Even when their source trees are present, transitive Soong module dependencies, QSSI sepolicy and HIDL/VINTF versions may be incompatible with AOSP 17.
4. `BOARD_VENDOR_SEPOLICY_DIRS`, VINTF matrices and the Qualcomm legacy vendor policy must be compiled and evaluated together; SELinux enforcing is required for release.
5. Existing BoardConfig embeds the historical vendor security patch date `2021-11-01`. Do **not** present a patched fingerprint or a modern framework security date as proof that proprietary firmware has received fixes.
6. The 4.19 build and `enchilada_defconfig` must be checked against this exact ROM boot/vendor baseline. A standalone ABK ZIP, even if CI passes, is not a verified replacement boot image.
7. AOSP manifest sync plus this preflight does **not** prove `lunch`, Soong bootstrap, kernel build, init, adb, or recovery will work.
8. Older OnePlus 6 A/B and recovery-in-boot layout must be handled as-is until a safe signed OTA/recovery design is tested. Never assume virtual A/B/dynamic partitions exist.

## Advancement gates

| Gate | Evidence | Current |
| --- | --- | --- |
| S0 | Pinned source layout + offline tests | Submitted for CI |
| S1 | AOSP product parsed; Soong/bootstrap completes | Not verified |
| S2 | All required images and dependency manifest compile | Not verified |
| S3 | OnePlus 6 boot + init + adb + recovery rollback | Not verified |
| S4 | Display, touch, cellular/IMS, camera, fingerprint, Wi-Fi, audio, sensors, suspend, charging | Not verified |
| S5 | OTA, signing, security policy, repeated recovery tests | Not verified |

**Safety:** All work remains in an isolated branch. Do not merge to a shipping build or flash experimental boot/system/vbmeta artifacts without a tested recovery path. Do not relock an experimental bootloader.
