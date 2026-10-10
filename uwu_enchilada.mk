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

PRODUCT_NAME := uwu_enchilada
PRODUCT_DEVICE := enchilada
PRODUCT_BRAND := OnePlus
PRODUCT_MANUFACTURER := OnePlus
PRODUCT_MODEL := ONEPLUS A6003

ifneq ($(strip $(UWU_RELEASE_VERSION)),17.0.133)
$(error OnePlus 6 uwu target requires immutable official 17.0.133 manifest)
endif