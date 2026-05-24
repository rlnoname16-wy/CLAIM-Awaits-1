[app]

title = CLAIM Awaits
package.name = claimawaits
package.domain = com.claim

source.dir = .
source.include_exts = py,png,jpg,kv,json

# Kivy + Python
# Pinned for reproducible builds / CI
requirements = python3==3.11.9,kivy==2.3.0

version = 0.1

# Android
fullscreen = 0
orientation = portrait
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

# (Optional) If you add an icon later, put it in this folder and set:
# icon.filename = %(source.dir)s/icon.png

[buildozer]

log_level = 2
warn_on_root = 0
