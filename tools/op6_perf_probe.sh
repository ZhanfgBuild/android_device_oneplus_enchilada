#!/system/bin/sh
# OnePlus 6 read-only performance capability probe.
# No arguments, no root requirement, no property/sysfs writes, and no
# collection of identifiers, processes, app names, addresses or credentials.
# Run on the phone with: sh op6_perf_probe.sh
set -u
umask 077

if [ -d /sdcard/Download ] && [ -w /sdcard/Download ]; then
    outdir=/sdcard/Download
elif [ -d /storage/emulated/0/Download ] && [ -w /storage/emulated/0/Download ]; then
    outdir=/storage/emulated/0/Download
else
    outdir=.
fi
stamp=$(date '+%Y%m%d_%H%M%S' 2>/dev/null || echo unknown)
out="$outdir/OP6_PerfProbe_$stamp.txt"
tmp="$out.tmp.$$"
trap 'rm -f "$tmp"' 0
trap 'exit 1' 1 2 3 15

read_one() {
    file=$1
    label=$2
    if [ -r "$file" ]; then
        value=$(head -n 1 "$file" 2>/dev/null)
        printf '%s: %s\n' "$label" "$value"
    else
        printf '%s: unavailable\n' "$label"
    fi
}
read_file() {
    file=$1
    label=$2
    printf '[%s]\n' "$label"
    if [ -r "$file" ]; then
        head -n 10 "$file" 2>/dev/null
    else
        printf 'unavailable\n'
    fi
}
property() {
    value=$(getprop "$1" 2>/dev/null)
    printf '%s: %s\n' "$1" "${value:-unavailable}"
}
{
    echo 'OP6 PERFORMANCE / DRIVER CAPABILITY PROBE (read-only)'
    echo 'No serial number, Android ID, network address, app names or kernel logs.'
    property ro.product.device
    property ro.build.version.release
    property ro.build.version.sdk
    read_one /proc/uptime uptime_seconds
    read_one /sys/devices/system/cpu/present cpus_present
    read_one /sys/devices/system/cpu/online cpus_online

    echo
    echo '=== CPU frequency policies ==='
    for policy in /sys/devices/system/cpu/cpufreq/policy*; do
        [ -d "$policy" ] || continue
        printf '[%s]\n' "${policy##*/}"
        for name in related_cpus scaling_governor scaling_available_governors \
            scaling_min_freq scaling_max_freq cpuinfo_max_freq \
            scaling_cur_freq; do
            read_one "$policy/$name" "$name"
        done
    done

    echo
    echo '=== Scheduler and task groups ==='
    read_one /proc/sys/kernel/sched_util_clamp_min sysctl_uclamp_min
    read_one /proc/sys/kernel/sched_util_clamp_max sysctl_uclamp_max
    read_one /dev/cpuset/top-app/cpus top_app_cpus
    read_one /dev/cpuset/background/cpus background_cpus
    read_one /dev/cpuset/system-background/cpus system_background_cpus
    read_one /dev/stune/top-app/schedtune.boost legacy_top_app_stune_boost
    read_one /dev/stune/top-app/schedtune.prefer_idle legacy_top_app_prefer_idle
    read_one /sys/fs/cgroup/cgroup.controllers cgroup_v2_controllers
    read_one /sys/fs/cgroup/cgroup.subtree_control cgroup_v2_subtree_control

    echo
    echo '=== Memory PSI, swap, ZRAM ==='
    for metric in cpu memory io; do
        read_file "/proc/pressure/$metric" "$metric pressure"
    done
    if [ -r /proc/meminfo ]; then
        grep -E '^(MemTotal|MemAvailable|SwapTotal|SwapFree|Cached|SReclaimable):' /proc/meminfo
    fi
    if [ -r /proc/swaps ]; then
        read_file /proc/swaps swap_devices
    fi
    for ram in /sys/block/zram*; do
        [ -d "$ram" ] || continue
        printf '[%s]\n' "${ram##*/}"
        for name in disksize comp_algorithm mm_stat mem_limit writeback_limit; do
            read_one "$ram/$name" "$name"
        done
    done

    echo
    echo '=== GPU / KGSL and display ==='
    for gpu in /sys/class/kgsl/kgsl-3d0 /sys/class/devfreq/*kgsl*; do
        [ -d "$gpu" ] || continue
        printf '[%s]\n' "${gpu##*/}"
        for name in gpuclk max_gpuclk gpu_busy_percentage devfreq/governor \
            devfreq/cur_freq devfreq/max_freq devfreq/min_freq cur_freq \
            available_frequencies; do
            read_one "$gpu/$name" "$name"
        done
    done
    read_one /sys/class/graphics/fb0/modes frame_buffer_modes

    echo
    echo '=== Thermal zones (type and temperature only) ==='
    count=0
    for zone in /sys/class/thermal/thermal_zone*; do
        [ -d "$zone" ] || continue
        count=$((count + 1))
        [ "$count" -le 80 ] || break
        printf '[%s]\n' "${zone##*/}"
        read_one "$zone/type" type
        read_one "$zone/temp" millidegree_celsius
    done

    echo
    echo '=== Non-invasive capability checks ==='
    for path in /dev/kgsl-3d0 /dev/binderfs /sys/fs/cgroup \
        /proc/pressure/memory /sys/block/zram0; do
        if [ -e "$path" ]; then
            printf '%s: exists\n' "$path"
        else
            printf '%s: missing\n' "$path"
        fi
    done
    echo 'END. Measurements are a snapshot, NOT a benchmark or proof of stability.'
} > "$tmp" || {
    echo 'Unable to write performance report' >&2
    exit 1
}
mv "$tmp" "$out" || exit 1
trap - 0 1 2 3 15
printf 'Report: %s\n' "$out"
