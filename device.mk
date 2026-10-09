#
# Copyright (C) 2018 The LineageOS Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#
# This file sets variables that control the way modules are built
# throughout the system. It should not be used to conditionally
# disable makefiles (the proper mechanism to control what gets
# included in a build is to use PRODUCT_PACKAGES in a product
# definition file).
#

$(call inherit-product, $(SRC_TARGET_DIR)/product/product_launched_with_o_mr1.mk)

# AOSP/device overlays only. Lineage SDK overlays are intentionally excluded.
DEVICE_PACKAGE_OVERLAYS += \
    $(LOCAL_PATH)/overlay

PRODUCT_ENFORCE_RRO_EXCLUDED_OVERLAYS += \
    $(LOCAL_PATH)/overlay/frameworks/base/packages/overlays/NoCutoutOverlay

PRODUCT_PACKAGES += \
    NoCutoutOverlay

# Device uses high-density artwork where available
PRODUCT_AAPT_CONFIG := normal
PRODUCT_AAPT_PREF_CONFIG := xxhdpi

# Boot animation
TARGET_SCREEN_HEIGHT := 2280
TARGET_SCREEN_WIDTH := 1080

# Audio
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/audio/audio_policy_volumes.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio_policy_volumes.xml \
    $(LOCAL_PATH)/audio/default_volume_tables.xml:$(TARGET_COPY_OUT_VENDOR)/etc/default_volume_tables.xml

# NOTE: Lineage light service and OnePlusPocketMode are deliberately omitted
# during the AOSP 17 bring-up. They will be replaced with ROM-owned components
# after the base device boots cleanly without Lineage runtime namespaces.

# Power / process groups
# Android 17 AOSP owns its modern libprocessgroup defaults. Do not copy the
# removed Android-9 compatibility profiles (cgroups_28/task_profiles_28) into
# vendor. A device-specific vendor overlay will be added only after its schema,
# mount/controllers, and launch-FCM compatibility have been validated.
# See docs/AOSP17_SDM845_PORTING_GATES.md.


# Soong namespaces
PRODUCT_SOONG_NAMESPACES += \
    $(LOCAL_PATH)

# WiFi
PRODUCT_PACKAGES += \
    TargetWifiOverlay

# Inherit the AOSP-facing wrapper around the known-good OnePlus SDM845 stack.
$(call inherit-product, device/oneplus/sdm845-common/aosp-common.mk)

# Inherit from vendor blobs.
$(call inherit-product, vendor/oneplus/enchilada/enchilada-vendor.mk)
