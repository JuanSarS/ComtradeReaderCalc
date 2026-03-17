#!/usr/bin/env python3
"""
Build executable for COMTRADE Pro using PyInstaller.

This script packages the PyQt6 desktop application into a standalone Windows .exe
without requiring Python installation on the target machine.

Usage:
    python build_executable.py

Output:
    ComtradeReaderCalc.exe (in the dist/ folder, then copied to root)
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess

def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")

def run_command(cmd, description):
    """Run a shell command and report results."""
    print(f"▶ {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=False)
    if result.returncode != 0:
        print(f"✗ {description} failed with code {result.returncode}")
        sys.exit(1)
    print(f"✓ {description} OK\n")

def main():
    print_header("COMTRADE Pro - Executable Builder")
    
    # Get project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print(f"Project root: {project_root}\n")
    
    # Step 1: Check PyInstaller is installed
    print_header("Step 1: Checking Dependencies")
    try:
        import PyInstaller
        print(f"✓ PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller not found. Install with:")
        print("  pip install -r requirements-dev.txt")
        sys.exit(1)
    
    # Step 2: Clean previous builds
    print_header("Step 2: Cleaning Previous Artifacts")
    for folder in ["build", "dist", "__pycache__"]:
        if Path(folder).exists():
            print(f"  Removing {folder}/...")
            shutil.rmtree(folder, ignore_errors=True)
    
    for file in ["ComtradeReaderCalc.spec"]:
        if Path(file).exists():
            print(f"  Removing {file}...")
            Path(file).unlink()
    print("✓ Cleanup complete\n")
    
    # Step 3: Build executable with PyInstaller
    print_header("Step 3: Building Executable")
    
    pyinstaller_cmd = (
        'pyinstaller '
        '--onefile '
        '--windowed '
        '--name ComtradeReaderCalc '
        '--icon=src/gui/assets/icon.ico '  # Add icon if available
        '--add-data "src:src" '
        '--add-data "data:data" '
        '--hidden-import=numpy '
        '--hidden-import=scipy '
        '--hidden-import=pandas '
        '--hidden-import=plotly '
        '--hidden-import=dash '
        'src/main.py'
    )
    
    print("Running PyInstaller...\n")
    result = subprocess.run(pyinstaller_cmd, shell=True)
    
    if result.returncode != 0:
        print("\n✗ PyInstaller build failed")
        print("\nWorkaround: Using alternative build without icon...")
        
        pyinstaller_cmd_fallback = (
            'pyinstaller '
            '--onefile '
            '--windowed '
            '--name ComtradeReaderCalc '
            '--add-data "src:src" '
            '--add-data "data:data" '
            '--hidden-import=numpy '
            '--hidden-import=scipy '
            '--hidden-import=pandas '
            '--hidden-import=plotly '
            '--hidden-import=dash '
            'src/main.py'
        )
        result = subprocess.run(pyinstaller_cmd_fallback, shell=True)
        
        if result.returncode != 0:
            print("\n✗ Build failed even with fallback")
            sys.exit(1)
    
    # Step 4: Copy executable to root
    print_header("Step 4: Copying Executable to Root")
    
    exe_src = project_root / "dist" / "ComtradeReaderCalc.exe"
    exe_dst = project_root / "ComtradeReaderCalc.exe"
    
    if exe_src.exists():
        print(f"  Copying: {exe_src.name}")
        shutil.copy(exe_src, exe_dst)
        print(f"  ✓ Executable ready: {exe_dst}\n")
    else:
        print(f"✗ Executable not found at {exe_src}")
        sys.exit(1)
    
    # Step 5: Generate summary
    print_header("Build Summary")
    
    exe_size_mb = exe_dst.stat().st_size / (1024 * 1024)
    
    print(f"✓ EXECUTABLE BUILT SUCCESSFULLY\n")
    print(f"Location: {exe_dst}")
    print(f"Size: {exe_size_mb:.1f} MB\n")
    print(f"You can now run the application with:")
    print(f"  ComtradeReaderCalc.exe\n")
    print(f"Or use the interactive menu:")
    print(f"  run_all_options.bat\n")
    
    # Optional: Clean build artifacts
    print_header("Cleanup")
    print("To save disk space, you can remove:")
    print("  - build/  (remove this folder)")
    print("  - dist/   (keep only if you want the uncompressed folder)")
    print("\nThe .exe in the root is ready to distribute.\n")

if __name__ == "__main__":
    main()
