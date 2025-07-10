[app]

# (str) Title of your application
title = BossEx AED Regex Builder

# (str) Package name
# Ensure this is unique, usually lowercase with no spaces
package.name = bossexregex

# (str) Package domain (usually your website reverse, e.g., 'org.mycompany')
package.domain = org.goonerb.aed

# (str) Source code where the main.py lives.
# This should be the directory where this buildozer.spec file is located.
source.dir = .

# (list) Source files to include (let empty to include all the files)
# Buildozer includes .py, .kv, .png, .jpg, .gif by default.
# We explicitly add .json for your config files.
source.include_exts = py,kv,png,jpg,gif,json

# (list) List of inclusions using pattern matching
# Example: source.include_patterns = assets/*,images/*.png
# Since your logo.png is in the root, 'source.include_exts' covers it.

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
#source.exclude_dirs =

# (list) List of exclusions using pattern matching
# Do not prefix with './'
#source.exclude_patterns = license,images/*/*.jpg

# Force build True or False
android.force_build = True

# (str) Application versioning (method 1)
version = 1.0.0

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
# python3 and kivy are essential. plyer is needed for clipboard functionality.
# Your 'bin' folder modules are included via 'android.add_src'.
requirements = python3,kivy,plyer

# (str) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.kivy = ../../kivy

# (str) Presplash of the application (appears briefly on app launch)
# If you have a presplash image, uncomment and provide the path.
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) The category of the application:
#        'game' or 'other'
category = other

# (list) List of target devices
#        'samsung', 'motorola', 'htc', 'lg'
#        'tablet', 'mobile'
target.devices = mobile

# (list) Plugins to install.
#        This should be empty for most Kivy apps.
# plugins =

# (bool) Set fullscreen mode
fullscreen = 1

# (str) The entry point of your application relative to the src_dir.
main.py = main.py

# (str) Android orientation: 'landscape', 'portrait', 'sensor', 'user'
# 'portrait' locks it to vertical. 'sensor' allows rotation.
orientation = portrait,landscape

# (int) Android SDK target (e.g. 27 for Android 8.1, 28 for Android 9, 31 for Android 12)
# It's recommended to use a recent stable SDK version. Let's aim for 33.
android.api = 21

# (int) Minimum Android SDK API level (the oldest Android version your app will support)
# Generally 21 (Android 5.0 Lollipop) or 23 (Android 6.0 Marshmallow) for broad compatibility.
android.minapi = 21

# (int) Android NDK version. Default is usually fine.
# We are providing a specific NDK path below, so this line can remain commented or removed.
android.ndk = 23b

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
android.ndk_api = 21

# (str) Android NDK path (if not using default)
# IMPORTANT: This path must match where your GitHub Actions workflow installs the NDK.
android.ndk_path = /home/runner/work/BossEx/BossEx/android-sdk/ndk/25.2.9519653

# (str) Android SDK path (if not using default)
# IMPORTANT: This path must match where your GitHub Actions workflow installs the SDK.
android.sdk_path = /home/runner/work/BossEx/BossEx/android-sdk

# (str) Android Build Tools version (e.g., '33.0.2')
# Explicitly set to match the version we install and android.api.
android.build_tools = 33.0.2

# (list) Add directories or files to the android project's src directory.
# This is CRITICAL for including your 'bin' folder modules.
android.add_src = bin

# (list) Add directories to the android project's res directory.
# If you had other static assets (e.g., fonts, sound files) in a separate folder (e.g., 'data'),
# you would list them here. For logo.png, 'source.include_exts' handles it.
# android.add_resource_dir = data

# (bool) Use the Android NDK for all Python modules (can help with complex dependencies)
# android.build_all_python_modules = 1

# (bool) Enable Android debug bridge (adb) logging (useful for seeing logs on device)
# android.enable_remote_logger = 1

# (list) Add Java extensions to the project
# android.extra_java_classes = your/java/code/MyClass.java

# (bool) Set true to allow the app to be debuggable (useful for adb logcat, defaults to 0 for release)
android.debug = 1

# (str) Log level for the build process (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# Use 'debug' for more verbose output if you hit issues.
log_level = 2

# --- Signing and Release (for app stores) ---
# For development (using `buildozer android debug`), Buildozer automatically
# creates a debug keystore. You don't need to configure these for debugging.
# If you plan to release to an app store, you'll need to create your own keystore
# and uncomment/fill in these values for `buildozer android release`.

# (str) The name of the signing key.
# p4a.release_keystore = ~/path/to/your.keystore

# (str) The alias of the signing key.
# p4a.release_keyalias = your_key_alias

# (str) The password for the release keystore.
# p4a.release_keystore_passphrase = your_password

# (str) The password for the release key alias.
# p4a.release_keyalias_passphrase = your_password

# (str) python-for-android branch to use, defaults to master
p4a.branch = develop


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2 # This controls Buildozer's own output, not the Android build logs

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
# bin_dir = ./bin # This refers to the Buildozer's output 'bin' folder, not your source 'bin' folder

#    -----------------------------------------------------------------------------
#    List as sections
#
#    You can define all the "list" as [section:key].
#    Each line will be considered as a option to the list.
#    Let's take [app] / source.exclude_patterns.
#    Instead of doing:
#
#[app]
#source.exclude_patterns = license,data/audio/*.wav,data/images/original/*
#
#    This can be translated into:
#
#[app:source.exclude_patterns]
#license
#data/audio/*.wav
#data/images/original/*
#
#
#
#    -----------------------------------------------------------------------------
#    Profiles
#
#    You can extend section / key with a profile
#    For example, you want to deploy a demo version of your application without
#    HD content. You could first change the title to add "(demo)" in the name
#    and extend the excluded directories to remove the HD content.
#
#[app@demo]
#title = My Application...
