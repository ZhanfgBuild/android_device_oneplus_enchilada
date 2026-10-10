#!/system/bin/sh
# OnePlus 6 | uwuAOSP 17.0.101 -> 17.0.133 | A/B / Retrofit Dynamic read-only gate
# No arguments. Never modifies bootctl state, images, mounts, packages or properties.
set -u
umask 077
STAMP="$(date -u '+%Y%m%d_%H%M%S' 2>/dev/null || echo unknown)"
DEST='/sdcard/Download'
if [ ! -d "$DEST" ] || [ ! -w "$DEST" ]; then
    DEST='/data/local/tmp'
fi
if [ ! -d "$DEST" ] || [ ! -w "$DEST" ]; then
    printf '%s\n' 'Cannot create output in /sdcard/Download or /data/local/tmp' >&2
    exit 1
fi
REPORT="$DEST/OP6_uwu133_AB_Rollback_Preflight_${STAMP}.txt"
log() { printf '%s\n' "$*" >> "$REPORT"; }
prop() { getprop "$1" 2>/dev/null; }
readcheck() {
    label="$1"; shift
    log "===== $label ====="
    if command -v "$1" >/dev/null 2>&1; then
        "$@" >> "$REPORT" 2>&1 || log "NOTICE: command returned nonzero (non-fatal read-only operation)"
    else
        log "UNAVAILABLE: $1"
    fi
}
log 'OnePlus 6 uwuAOSP 101->133 dual-slot upgrade/rollback preflight (READ ONLY)'
log "UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null)"
log "uid=$(id -u 2>/dev/null)"
log 'No partitions, boot slots, ROM properties, mount state, or OTA state are modified.'
log '===== DEVICE PROPERTIES ====='
for key in \
  ro.product.device ro.product.model ro.build.version.release ro.build.version.sdk \
  ro.uwu.release ro.uwu.version ro.uwu.device ro.uwu.maintainer \
  ro.boot.slot_suffix ro.build.ab_update ro.boot.dynamic_partitions \
  ro.boot.dynamic_partitions_retrofit ro.virtual_ab.enabled ro.boot.super_partition \
  ro.boot.verifiedbootstate ro.boot.vbmeta.device_state \
  ro.crypto.state ro.crypto.type ro.build.version.security_patch \
  ro.system.build.fingerprint ro.bootimage.build.fingerprint \
  init.svc.update_engine; do
    log "$key=$(prop "$key")"
done
log '===== READ-ONLY OTA GATES ====='
[ "$(prop ro.product.device)" = OnePlus6 ] && log 'DEVICE=OK' || log 'DEVICE=STOP_UNEXPECTED'
[ "$(prop ro.build.ab_update)" = true ] && log 'AB=OK' || log 'AB=STOP_UNEXPECTED'
[ "$(prop ro.boot.dynamic_partitions_retrofit)" = true ] && log 'RETROFIT_DYNAMIC=OK' || log 'RETROFIT_DYNAMIC=STOP_UNEXPECTED'
case "$(prop ro.boot.slot_suffix)" in _a|_b) log 'CURRENT_SLOT=OK';; *) log 'CURRENT_SLOT=STOP_UNKNOWN';; esac
[ "$(prop ro.uwu.release)" = '17.0.101' ] && log 'SOURCE_RELEASE=101_EXPECTED' || log 'SOURCE_RELEASE=STOP_REVIEW_BUILD'
log '===== BOOTCTL A/B STATE (READS ONLY) ====='
if command -v bootctl >/dev/null 2>&1; then
  for key in get-number-slots get-current-slot; do
    log "> bootctl $key"
    bootctl "$key" >> "$REPORT" 2>&1 || log 'NOTICE: bootctl query failed'
  done
  for slot in 0 1; do
    for key in get-suffix is-slot-bootable is-slot-marked-successful; do
      log "> bootctl $key $slot"
      bootctl "$key" "$slot" >> "$REPORT" 2>&1 || log 'NOTICE: bootctl query failed'
    done
  done
else
  log 'UNAVAILABLE: bootctl'
fi
log '===== PHYSICAL AB PARTITION SIZES (READS ONLY) ====='
for name in boot_a boot_b dtbo_a dtbo_b vbmeta_a vbmeta_b system_a system_b vendor_a vendor_b odm_a odm_b misc logdump; do
  dev="/dev/block/by-name/$name"
  if [ -e "$dev" ]; then
    size='unknown'
    if command -v blockdev >/dev/null 2>&1; then
      size="$(blockdev --getsize64 "$dev" 2>/dev/null || echo unknown)"
    fi
    link="$(readlink -f "$dev" 2>/dev/null || echo unknown)"
    log "$name | bytes=$size | target=$link"
  else
    log "$name | ABSENT"
  fi
done
log '===== MOUNT POINTS AND FILESYSTEM ====='
if command -v mount >/dev/null 2>&1; then
  mount 2>/dev/null | grep -E ' on (/[[:space:]]|/vendor[[:space:]]|/odm[[:space:]]|/metadata[[:space:]]|/data[[:space:]])' >> "$REPORT" || :
fi
log '===== LIVE FSTAB (ONLY RELEVANT LINES, IF ACCESSIBLE) ====='
for f in /vendor/etc/fstab.qcom /odm/etc/fstab.qcom /system/etc/recovery.fstab /first_stage_ramdisk/system/etc/fstab.qcom; do
  if [ -r "$f" ]; then
    log "FILE: $f"
    grep -E '^[^#[:space:]].*[[:space:]](/system|/vendor|/odm|/metadata|/data|/misc)[[:space:]]' "$f" >> "$REPORT" 2>/dev/null || :
  fi
done
log '===== LOGICAL PARTITION METADATA (READ ONLY, IF LP DUMP EXISTS) ====='
if command -v lpdump >/dev/null 2>&1; then
  for slot in 0 1; do
    src='/dev/block/by-name/system_a'
    [ "$slot" -eq 1 ] && src='/dev/block/by-name/system_b'
    if [ -r "$src" ]; then
      log "> lpdump --slot $slot $src"
      lpdump --slot "$slot" "$src" 2>&1 | sed -n '1,180p' >> "$REPORT" || log 'NOTICE: lpdump query failed'
    else
      log "UNAVAILABLE: $src"
    fi
  done
else
  log 'UNAVAILABLE: lpdump (not proof that logical partition metadata is missing)'
fi
log '===== OTA TRUST ANCHOR DIGESTS (PUBLIC CERTIFICATES ONLY) ====='
for f in /system/etc/security/otacerts.zip /system/etc/security/avb /res/keys; do
  if [ -r "$f" ] && [ -f "$f" ] && command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$f" >> "$REPORT" 2>/dev/null || :
  fi
done
log '===== NOTES ====='
log 'A/B preserves the *old OS slot*, NOT a separate copy of /data.'
log 'Do not set-active, erase, flash, wipe, or install any OTA from this probe.'
log 'The ROM author platform/recovery/OTA signing keys are not inferred from release-keys strings.'
log 'An A/B target-files build for uwu 133 must be verified against these layout facts before any device test.'
log "DONE: $REPORT"
printf 'DONE: %s\n' "$REPORT"