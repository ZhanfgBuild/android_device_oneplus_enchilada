# Experimental, NOT OTA-flash-ready, OnePlus 6 uwuAOSP 17.0.133 target.
# Uses AOSP17 donor product, but the current donor common BoardConfig/fstab is
# legacy ext4; FIRST port the verified EROFS Retrofit Dynamic layout.
$(call inherit-product, device/oneplus/enchilada/aosp_enchilada.mk)

UWU_DEVICE_TYPE := phone
UWU_SUPPORTS_TELEPHONY := true
UWU_BUILDTYPE := UNOFFICIAL
$(call inherit-product, vendor/uwu/config/common.mk)

PRODUCT_NAME := uwu_enchilada
PRODUCT_DEVICE := enchilada
PRODUCT_BRAND := OnePlus
PRODUCT_MANUFACTURER := OnePlus
PRODUCT_MODEL := ONEPLUS A6003

# Reject a moving development branch or wrong build release.
ifneq ($(strip $(UWU_RELEASE_VERSION)),17.0.133)
$(error OnePlus 6 experimental uwu target requires immutable 17.0.133 manifest)
endif
