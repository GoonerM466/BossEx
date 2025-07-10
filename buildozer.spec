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
# Use newer libffi version or exclude it to use system version
requirements = python3,kivy,plyer,android
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

# Android specific configurations
# (int) Android SDK target - using 33 for Android 13
android.api = 33
# (int) Minimum Android SDK API level
android.minapi = 21
# (str) Android NDK version - using 25.2.9519653 to match your path
android.ndk = 25.2.9519653
# (int) Android NDK API to use
android.ndk_api = 21
# (str) Android NDK path
android.ndk_path = /home/runner/work/BossEx/BossEx/android-sdk/ndk/25.2.9519653
# (str) Android SDK path
android.sdk_path = /home/runner/work/BossEx/BossEx/android-sdk
# (str) Android Build Tools version
android.build_tools = 33.0.2
# (list) Add directories to android project's src
android.add_src = bin
# (bool) Enable debug mode
android.debug = 1
# (list) Architecture specification
android.archs = arm64-v8a, armeabi-v7a
# (list) Gradle configuration for better compatibility
android.gradle_dependencies = 
# (list) Additional environment variables for libffi build
android.add_compile_options = -fPIC

# Python-for-android specific configurations
# (str) python-for-android branch to use - using develop for latest fixes
p4a.branch = develop
# (str) Python-for-android bootstrap
p4a.bootstrap = sdl2
# (bool) Setup.py handling for p4a
p4a.setup_py = False
# (str) Source directory for p4a
p4a.source_dir = 
# (str) Local recipes directory
p4a.local_recipes = 
# (str) Whitelist source extensions
p4a.whitelist_src = 
# (str) Blacklist source extensions
p4a.blacklist_src = 
# (list) Additional environment variables for build - Add autotools fixes
p4a.add_env = LIBTOOL_VERSION=2.4.6,AUTOTOOLS_BUILD=x86_64-linux-gnu,AUTOTOOLS_HOST=aarch64-linux-android
# (str) Additional build options for libffi compatibility
p4a.add_build_options = --libffi-dir=/usr/lib/x86_64-linux-gnu
# (str) Force specific libffi version or recipe
p4a.recipe_blacklist = 
# (str) Use specific python-for-android commit that has libffi fixes
p4a.commit = 

[buildozer]
# (int) Log level
log_level = 2
# (int) Display warning if buildozer is run as root
warn_on_root = 1
