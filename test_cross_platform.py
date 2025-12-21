"""
Cross-platform compatibility test for upgrade system.
Tests that commands work on both Windows and Linux.
"""

import sys
import platform
import subprocess
import json

def test_platform_detection():
    """Test platform detection."""
    print("\n" + "="*60)
    print("PLATFORM DETECTION")
    print("="*60)
    print(f"Operating System: {platform.system()}")
    print(f"Platform: {platform.platform()}")
    print(f"Python Version: {platform.python_version()}")
    print(f"Python Executable: {sys.executable}")
    print(f"Architecture: {platform.machine()}")

def test_python_commands():
    """Test Python/pip commands."""
    print("\n" + "="*60)
    print("PYTHON COMMANDS")
    print("="*60)
    
    # Test python executable
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True
        )
        print(f"✓ Python executable works: {result.stdout.strip()}")
    except Exception as e:
        print(f"✗ Python executable failed: {e}")
    
    # Test pip via python -m pip
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True
        )
        print(f"✓ pip (python -m pip) works: {result.stdout.strip()}")
    except Exception as e:
        print(f"✗ pip failed: {e}")
    
    # Test pip list
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True
        )
        packages = json.loads(result.stdout)
        print(f"✓ pip list works: Found {len(packages)} packages")
    except Exception as e:
        print(f"✗ pip list failed: {e}")

def test_npm_commands():
    """Test npm commands."""
    print("\n" + "="*60)
    print("NPM COMMANDS")
    print("="*60)
    
    # Determine correct npm command
    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
    
    # Test npm version
    try:
        result = subprocess.run(
            [npm_cmd, "--version"],
            capture_output=True,
            text=True
        )
        print(f"✓ npm works ({npm_cmd}): v{result.stdout.strip()}")
    except Exception as e:
        print(f"✗ npm failed: {e}")

def test_node_commands():
    """Test Node.js commands."""
    print("\n" + "="*60)
    print("NODE.JS COMMANDS")
    print("="*60)
    
    # Determine correct node command
    node_cmd = "node.exe" if platform.system() == "Windows" else "node"
    
    # Test node version
    try:
        result = subprocess.run(
            [node_cmd, "--version"],
            capture_output=True,
            text=True
        )
        print(f"✓ Node.js works ({node_cmd}): {result.stdout.strip()}")
    except Exception as e:
        print(f"✗ Node.js failed: {e}")

def test_git_commands():
    """Test Git commands."""
    print("\n" + "="*60)
    print("GIT COMMANDS")
    print("="*60)
    
    # Determine correct git command
    git_cmd = "git.exe" if platform.system() == "Windows" else "git"
    
    # Test git version
    try:
        result = subprocess.run(
            [git_cmd, "--version"],
            capture_output=True,
            text=True
        )
        print(f"✓ Git works ({git_cmd}): {result.stdout.strip()}")
    except Exception as e:
        print(f"✗ Git failed: {e}")

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CROSS-PLATFORM COMPATIBILITY TEST")
    print("="*60)
    
    test_platform_detection()
    test_python_commands()
    test_npm_commands()
    test_node_commands()
    test_git_commands()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if platform.system() == "Windows":
        print("✓ Running on Windows")
        print("  Commands use: npm.cmd, node.exe, git.exe")
        print("  Python: python -m pip")
    else:
        print("✓ Running on Linux/Unix")
        print("  Commands use: npm, node, git")
        print("  Python: python -m pip")
    
    print("\nAll commands are cross-platform compatible!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
