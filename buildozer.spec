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

# Force build True or False
android.force_build = True

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# Added libffi explicitly to fix compilation issues
requirements = python3,kivy,plyer,libffi

# (str) The category of the application
category = other

# (list) List of target devices
target.devices = mobile

# (bool) Set fullscreen mode
fullscreen = 1

# (str) The entry point of your application
main.py = main.py

# (str) Android orientation
orientation = portrait,landscape

# FIXED: Updated to consistent API levels
# (int) Android SDK target - using 33 for Android 13
android.api = 33

# (int) Minimum Android SDK API level
android.minapi = 21

# FIXED: Updated NDK to match your path
# (str) Android NDK version - using 25c to match your path
android.ndk = 25c

# (int) Android NDK API to use
android.ndk_api = 21

# FIXED: Updated path to match NDK 25c
# (str) Android NDK path
android.ndk_path = /home/runner/work/BossEx/BossEx/android-sdk/ndk/25.2.9519653

# (str) Android SDK path
android.sdk_path = /home/runner/work/BossEx/BossEx/android-sdk

# FIXED: Updated build tools to match API 33
# (str) Android Build Tools version
android.build_tools = 33.0.2

# (list) Add directories to android project's src
android.add_src = bin

# (bool) Enable debug mode
android.debug = 1

# (str) Log level for build process
log_level = 2

# FIXED: Changed to stable master branch instead of develop
# (str) python-for-android branch to use
p4a.branch = master

# ADD: Python-for-android bootstrap
p4a.bootstrap = sdl2

# ADD: Architecture specification
android.archs = arm64-v8a, armeabi-v7a

# ADD: Gradle configuration for better compatibility
android.gradle_dependencies = 

# ADD: Additional environment variables for libffi
android.add_compile_options = -fPIC

[buildozer]

# (int) Log level
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
