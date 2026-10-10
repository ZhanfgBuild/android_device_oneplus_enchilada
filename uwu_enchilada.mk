# Experimental, NOT OTA-flash-ready, OnePlus 6 uwuAOSP 17.0.133 target.
# Uses AOSP17 donor product; retrofit config is gated by verified per-device
# LP metadata. Includes all upstream uwu packages but is NOT yet a tested ROM.
$(call inherit-product, device/oneplus/enchilada/aosp_enchilada.mk)

UWU_DEVICE_TYPE := phone
UWU_SUPPORTS_TELEPHONY := true
UWU_BUILDTYPE := UNOFFICIAL
$(call inherit-product, vendor/uwu/config/common.mk)

PRODUCT_USE_DYNAMIC_PARTITIONS := true
PRODUCT_RETROFIT_DYNAMIC_PARTITIONS := true

# Replace the legacy physical ext4 fstab inherited from the common AOSP17
# donor. These destinations mirror the running 101 Boot's first-stage fstab
# layout (system/etc/fstab.qcom inside first_stage_ramdisk). This mapping is
# a SOURCE hypothesis until final 133 boot.img and target-files are inspected.
# Prevent two different sources from claiming vendor/etc/fstab.qcom.
PRODUCT_PACKAGES := $(filter-out fstab.qcom fstab.qcom.ramdisk,$(PRODUCT_PACKAGES))
OP6_UWU133_FSTAB := device/oneplus/sdm845-common/ota/uwu133/fstab.qcom
PRODUCT_COPY_FILES += \\
    $(OP6_UWU133_FSTAB):$(TARGET_COPY_OUT_VENDOR)/etc/fstab.qcom \\
    $(OP6_UWU133_FSTAB):$(TARGET_COPY_OUT_RAMDISK)/first_stage_ramdisk/system/etc/fstab.qcom


PRODUCT_NAME := uwu_enchilada
PRODUCT_DEVICE := enchilada
PRODUCT_BRAND := OnePlus
PRODUCT_MANUFACTURER := OnePlus
PRODUCT_MODEL := ONEPLUS A6003

ifneq ($(strip $(UWU_RELEASE_VERSION)),17.0.133)
$(error OnePlus 6 uwu target requires immutable official 17.0.133 manifest)
endif