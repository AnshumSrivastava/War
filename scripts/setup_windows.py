import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil

# ======================================================================
# Wargame Engine - Windows Setup & Dependency Manager
# ======================================================================
# This script will:
# 1. Create a Python Virtual Environment if one doesn't exist.
# 2. Check and install required Python packages (PyQt5, redis, numpy).
# 3. Check if Redis is accessible locally.
# 4. If Redis is missing on Windows, optionally download the Memurai 
#    developer edition (a native Windows Redis port) or instruct the user.
# ======================================================================

REQUIRED_PACKAGES = ["PyQt5", "numpy"]

def print_step(msg):
    print(f"\n[{'='*40}]\n>>> {msg}\n[{'='*40}]")

def check_python_version():
    if sys.version_info < (3, 10):
        print("[ERROR] Python 3.10+ is required. Please upgrade your Python installation.")
        sys.exit(1)

def setup_virtual_env():
    venv_dir = "venv"
    if not os.path.exists(venv_dir):
        print_step("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
    
    # Path to pip inside the virtual env
    if sys.platform == "win32":
        pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(venv_dir, "bin", "pip")
    
    return pip_exe

def install_dependencies(pip_exe):
    print_step("Checking missing python dependencies...")
    subprocess.check_call([pip_exe, "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL)
    
    for pkg in REQUIRED_PACKAGES:
        print(f"Installing {pkg}...")
        subprocess.check_call([pip_exe, "install", pkg], stdout=subprocess.DEVNULL)
    print("All python dependencies installed successfully.")



if __name__ == "__main__":
    check_python_version()
    
    pip_exe = setup_virtual_env()
    install_dependencies(pip_exe)
    

    print_step("Setup Complete!")
    print("""
To launch the Wargame Engine:
1. Activate the environment: .\\venv\\Scripts\\activate
2. Run the engine: python main.py
""")
