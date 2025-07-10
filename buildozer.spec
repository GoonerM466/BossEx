[app]
# (str) Title of your application
title = BossEx AED Regex Builder
# (str) Package name
package.name = bossexregex
# (str) Package domain
package.domain = org.goonerb.aed
# (str) Source code where the main.py lives
source.dir = .
# (list) Source files to include
source.include_exts = py,kv,png,jpg,gif,json
# (str) Application versioning
version = 1.0.0
# (list) Application requirements
requirements = python3,kivy,plyer,android
# (str) The entry point of your application
main.py = main.py
# (str) Android orientation
orientation = portrait,landscape

# Android specific configurations
# (int) Android SDK target
android.api = 33
# (int) Minimum Android SDK API level
android.minapi = 21
# (str) Android NDK version
android.ndk = 25c
# (int) Android NDK API to use
android.ndk_api = 21
# (list) Architecture specification
android.archs = arm64-v8a, armeabi-v7a
# (bool) Enable debug mode
android.debug = 1
# (bool) Set fullscreen mode
fullscreen = 1

# Python-for-android specific configurations
# (str) python-for-android bootstrap
p4a.bootstrap = sdl2

[buildozer]
# (int) Log level
log_level = 2
# (int) Display warning if buildozer is run as root
warn_on_root = 1
