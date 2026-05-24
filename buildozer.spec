[app]

title = CLAIM Awaits
package.name = claimawaits
package.domain = com.claim

source.dir = .
source.include_exts = py,png,jpg,kv,json

# Kivy + Python
requirements = python3==3.11.9,kivy==2.3.0

version = 0.1

# Android
fullscreen = 0
orientation = portrait
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

# Force Buildozer/p4a to use the GitHub Actions Android SDK/NDK (fixes AIDL)
android.sdk_path = $ANDROID_SDK_ROOT
android.ndk_path = $ANDROID_SDK_ROOT/ndk/25.2.9519653

# (Optional) If you add an icon later, put it in this folder and set:
# icon.filename = %(source.dir)s/icon.png

[buildozer]

log_level = 2
warn_on_root = 0
