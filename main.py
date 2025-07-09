import os
import sys
import json
from kivy.logger import Logger
from kivy.app import App

# Helper: get file path whether .py or PyInstaller .exe or Kivy on Android
def resource_path(relative_path):
    """Get absolute path to resource, works for dev, PyInstaller .exe, and Kivy on Android."""
    if hasattr(sys, '_MEIPASS'): # PyInstaller
        base_path = sys._MEIPASS
    elif hasattr(sys, '_MEIPASS2'): # Buildozer on Android
        base_path = sys._MEIPASS2
    else: # Development environment
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Setup dependencies (if needed)
def setup_dependencies():
    # Ensure the 'bin' directory is in sys.path so its modules can be imported
    bin_path = resource_path("bin")
    if bin_path not in sys.path:
        sys.path.append(bin_path)
    Logger.info(f"Added bin path to sys.path: {bin_path}")

# Load or create config file
def load_or_generate_config():
    bin_path = resource_path("bin")
    config_file = os.path.join(bin_path, "config.json")
    default_config_file = os.path.join(bin_path, "defaultConfig.json")

    if not os.path.exists(config_file):
        Logger.warning(f"Config file not found: {config_file}. Attempting to generate from default.")
        if not os.path.exists(default_config_file):
            Logger.error(f"Default configuration file {default_config_file} not found. Please ensure it exists.")
            sys.exit(1)
        try:
            with open(default_config_file, 'r') as f:
                default_config = json.load(f)
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            Logger.info(f"Generated config.json from {default_config_file}")
        except json.JSONDecodeError as e:
            Logger.error(f"Failed to parse {default_config_file}: {e}")
            sys.exit(1)
        except Exception as e:
            Logger.error(f"Failed to generate {config_file}: {e}")
            sys.exit(1)

    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        Logger.error(f"Failed to parse {config_file}: {e}")
        sys.exit(1)
    except Exception as e:
        Logger.error(f"Failed to load {config_file}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_dependencies()

    try:
        from kivy_gui import BossExApp # Import the Kivy App class
    except ImportError as e:
        Logger.error(f"Kivy GUI module (kivy_gui.py) not found or has an import error: {e}. Please ensure it exists and try again.")
        sys.exit(1)

    # Load config and pass it to the Kivy App for initialization
    config = load_or_generate_config()
    BossExApp(config=config).run() # Pass config to the App constructor