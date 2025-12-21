"""
Test script to verify internet connectivity for upgrade system.
Tests PyPI and npm registry access.
"""

import asyncio
import httpx
from datetime import datetime

async def test_pypi():
    """Test PyPI connectivity."""
    print("\n" + "="*60)
    print("Testing PyPI (Python Package Index)...")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test with a well-known package
            start = datetime.now()
            response = await client.get("https://pypi.org/pypi/requests/json")
            elapsed = (datetime.now() - start).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                version = data.get("info", {}).get("version")
                print(f"✓ SUCCESS - PyPI is accessible")
                print(f"  Status Code: {response.status_code}")
                print(f"  Latency: {elapsed:.2f}ms")
                print(f"  Test Package: requests")
                print(f"  Latest Version: {version}")
                return True
            else:
                print(f"✗ FAILED - PyPI returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ FAILED - Error: {e}")
        return False

async def test_npm():
    """Test npm registry connectivity."""
    print("\n" + "="*60)
    print("Testing npm Registry...")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test with a well-known package
            start = datetime.now()
            response = await client.get("https://registry.npmjs.org/react/latest")
            elapsed = (datetime.now() - start).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                version = data.get("version")
                print(f"✓ SUCCESS - npm registry is accessible")
                print(f"  Status Code: {response.status_code}")
                print(f"  Latency: {elapsed:.2f}ms")
                print(f"  Test Package: react")
                print(f"  Latest Version: {version}")
                return True
            else:
                print(f"✗ FAILED - npm registry returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ FAILED - Error: {e}")
        return False

async def test_sample_packages():
    """Test fetching versions for some actual packages."""
    print("\n" + "="*60)
    print("Testing Sample Package Lookups...")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test Python packages
        python_packages = ["fastapi", "pydantic", "langchain"]
        print("\nPython Packages (PyPI):")
        for pkg in python_packages:
            try:
                response = await client.get(f"https://pypi.org/pypi/{pkg}/json")
                if response.status_code == 200:
                    version = response.json().get("info", {}).get("version")
                    print(f"  ✓ {pkg}: {version}")
                else:
                    print(f"  ✗ {pkg}: Failed (status {response.status_code})")
            except Exception as e:
                print(f"  ✗ {pkg}: Error - {e}")
        
        # Test npm packages
        npm_packages = ["react", "axios", "@mui/material"]
        print("\nnpm Packages:")
        for pkg in npm_packages:
            try:
                response = await client.get(f"https://registry.npmjs.org/{pkg}/latest")
                if response.status_code == 200:
                    version = response.json().get("version")
                    print(f"  ✓ {pkg}: {version}")
                else:
                    print(f"  ✗ {pkg}: Failed (status {response.status_code})")
            except Exception as e:
                print(f"  ✗ {pkg}: Error - {e}")

async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("UPGRADE SYSTEM CONNECTIVITY TEST")
    print("="*60)
    
    pypi_ok = await test_pypi()
    npm_ok = await test_npm()
    await test_sample_packages()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if pypi_ok and npm_ok:
        print("✓ ALL TESTS PASSED - Internet connectivity is working")
        print("  The upgrade system should be able to fetch versions from both registries.")
    elif pypi_ok or npm_ok:
        print("⚠ PARTIAL SUCCESS")
        if pypi_ok:
            print("  ✓ PyPI is accessible - Python package upgrades will work")
        if npm_ok:
            print("  ✓ npm registry is accessible - Frontend package upgrades will work")
    else:
        print("✗ ALL TESTS FAILED - Internet connectivity issues detected")
        print("  Please check:")
        print("  1. Internet connection is active")
        print("  2. Firewall/proxy settings allow HTTPS traffic")
        print("  3. DNS resolution is working")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
