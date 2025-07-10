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

# (str) python-for-android branch to use
p4a.branch = master

# (str) python-for-android git url
p4a.url = https://github.com/kivy/python-for-android.git

# (str) The directory in which python-for-android should look for your own build recipes
p4a.local_recipes = ./p4a-recipes

# (str) Filename to the hook for p4a
p4a.hook = ./p4a-hook.py

# (str) Bootstrap to use for new builds
p4a.bootstrap = sdl2

# (str) The Android arch to build for
android.arch = arm64-v8a

# (bool) Whether to use the gradle wrapper
android.gradle_wrapper = 1

# (str) java file encoding
android.java_encoding = utf-8

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
