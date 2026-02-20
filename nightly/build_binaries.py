import subprocess
import shutil
import os
import platform

# Configuration
APP_NAME = "ab_cli"
ENTRY_POINT = os.path.join("ab_cli", "cli", "main.py")

def build():
    print(f"🛠️ Starting build for {platform.system()}...")

    # 1. Clean workspace
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # 2. Build command
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--name", APP_NAME,
        "--collect-all",  "streamlit",
        "--collect-submodules", "rich._unicode_data",
        "--onedir",
        ENTRY_POINT
    ]

    # 3. Execute
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Build successful! Check the 'dist/{APP_NAME}' folder.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error: {e}")

if __name__ == "__main__":
    build()