#!/usr/bin/env python3
"""Home Assistant Configuration Reload Tool.

Calls the Home Assistant API to reload core configuration after config files
have been pushed to the instance.
"""

import os
import sys
from pathlib import Path

import requests


def load_env_file():
    """Load environment variables from .env file."""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")


def reload_config():
    """Reload Home Assistant core configuration via API."""
    # Load environment variables
    load_env_file()

    # Get configuration
    ha_url = os.getenv("HA_URL", "http://homeassistant.local:8123")
    token = os.getenv("HA_TOKEN", "")

    if not token:
        print("❌ Error: HA_TOKEN not found in environment or .env file")
        print("   Create a .env file with: HA_TOKEN=your_long_lived_access_token")
        print("   Get your token from Home Assistant Profile page")
        return False

    # Prepare API request
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    reload_endpoints = [
        ("core configuration", "homeassistant/reload_core_config"),
        ("automations", "automation/reload"),
        ("scripts", "script/reload"),
        ("scenes", "scene/reload"),
    ]

    try:
        all_ok = True
        for name, service in reload_endpoints:
            url = f"{ha_url}/api/services/{service}"
            print(f"🔄 Reloading {name}...")
            response = requests.post(url, headers=headers, timeout=30)

            if response.status_code == 200:
                print(f"✅ {name.capitalize()} reloaded successfully!")
            else:
                print(f"❌ Failed to reload {name}: {response.status_code}")
                if response.text:
                    print(f"   Response: {response.text}")
                all_ok = False

        return all_ok

    except requests.exceptions.Timeout:
        print("❌ Timeout: Home Assistant took too long to respond")
        print("   This may indicate a configuration error preventing reload")
        return False

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Cannot reach Home Assistant at {ha_url}")
        print("   Check that Home Assistant is running and accessible")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    SUCCESS = reload_config()
    sys.exit(0 if SUCCESS else 1)
