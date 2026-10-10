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

# Inherit from oneplus sdm845-common
include device/oneplus/sdm845-common/BoardConfigCommon.mk

DEVICE_PATH := device/oneplus/enchilada

# HIDL
DEVICE_MANIFEST_FILE += $(DEVICE_PATH)/manifest.xml

# Properties
TARGET_VENDOR_PROP += $(DEVICE_PATH)/vendor.prop

# inherit from the proprietary version
include vendor/oneplus/enchilada/BoardConfigVendor.mk

# Only the *uwu_enchilada* product opts into an EROFS Retrofit Dynamic
# profile. Other AOSP and Lineage targets keep their existing donor config.
# This profile INTENTIONALLY fails closed until lpdump sizes are validated.
ifeq ($(TARGET_PRODUCT),uwu_enchilada)
include device/oneplus/sdm845-common/ota/uwu133/BoardConfigRetrofit.mk
endif