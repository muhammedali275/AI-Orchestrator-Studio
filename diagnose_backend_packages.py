"""
Quick test to diagnose why backend packages aren't showing up.
"""

import asyncio
import sys
import subprocess
import json

async def test_pip_command():
    """Test the pip list command."""
    print("Testing pip list command...")
    print(f"Python executable: {sys.executable}")
    
    # Try different pip commands
    commands = [
        ["pip", "list", "--format=json"],
        [sys.executable, "-m", "pip", "list", "--format=json"],
        ["python", "-m", "pip", "list", "--format=json"],
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\nTest {i}: {' '.join(cmd)}")
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                packages = json.loads(stdout.decode('utf-8'))
                print(f"  ✓ SUCCESS: Found {len(packages)} packages")
                print(f"  First 3: {[p['name'] for p in packages[:3]]}")
                return True
            else:
                print(f"  ✗ FAILED: Return code {process.returncode}")
                print(f"  stderr: {stderr.decode('utf-8')[:200]}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
    
    return False

async def test_current_backend_endpoint():
    """Test what the current backend is returning."""
    print("\n" + "="*60)
    print("Testing current backend endpoint...")
    print("="*60)
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://localhost:8000/api/upgrades/check")
            data = response.json()
            
            backend_count = len(data.get("components", {}).get("backend", []))
            frontend_count = len(data.get("components", {}).get("frontend", []))
            
            print(f"Backend packages: {backend_count}")
            print(f"Frontend packages: {frontend_count}")
            
            if backend_count == 0:
                print("\n⚠ ISSUE: Backend packages array is empty!")
                print("This means the check_pip_packages() function is returning an empty list.")
                print("\nPossible causes:")
                print("1. The 'pip list' command is failing in the backend")
                print("2. The backend server is running old code (needs restart)")
                print("3. There's an exception being caught and logged")
            
            return data
    except Exception as e:
        print(f"✗ Failed to query backend: {e}")
        return None

async def main():
    print("\n" + "="*60)
    print("BACKEND PACKAGES DIAGNOSTIC")
    print("="*60)
    
    # Test pip command locally
    pip_works = await test_pip_command()
    
    # Test backend endpoint
    backend_data = await test_current_backend_endpoint()
    
    print("\n" + "="*60)
    print("DIAGNOSIS")
    print("="*60)
    
    if pip_works and backend_data and len(backend_data.get("components", {}).get("backend", [])) == 0:
        print("✓ pip list command works locally")
        print("✗ Backend endpoint returns empty array")
        print("\n🔧 SOLUTION:")
        print("   The backend server needs to be restarted to pick up the code changes.")
        print("   Run: .\\start-backend.bat (or restart the backend manually)")
    elif not pip_works:
        print("✗ pip list command is failing")
        print("\n🔧 SOLUTION:")
        print("   Check Python/pip installation")
    else:
        print("✓ Everything appears to be working")

if __name__ == "__main__":
    asyncio.run(main())
