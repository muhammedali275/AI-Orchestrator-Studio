"""
Upgrades API - Component version checking and upgrade management.

Provides endpoints for checking versions and managing upgrades for:
- Python packages (backend)
- npm packages (frontend)
- Ollama models
- System components

Cross-platform support for Windows and Linux.
"""

import logging
import asyncio
import subprocess
import json
import sys
import platform
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from ..config import get_settings, Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upgrades", tags=["upgrades"])


@router.get("/test-pip")
async def test_pip_directly():
    """Direct test of pip command to diagnose issues."""
    import sys
    import subprocess
    
    results = {
        "python_executable": sys.executable,
        "pip_command": get_pip_command(),
        "tests": []
    }
    
    # Test 1: Run pip command directly
    try:
        pip_cmd = get_pip_command()
        result = await run_command([*pip_cmd, "list", "--format=json"])
        
        if result["success"]:
            packages = json.loads(result["stdout"])
            results["tests"].append({
                "test": "pip list via run_command",
                "success": True,
                "packages_found": len(packages),
                "sample": [p["name"] for p in packages[:5]]
            })
        else:
            results["tests"].append({
                "test": "pip list via run_command",
                "success": False,
                "error": result["stderr"][:200]
            })
    except Exception as e:
        results["tests"].append({
            "test": "pip list via run_command",
            "success": False,
            "error": str(e)
        })
    
    # Test 2: Check what check_pip_packages returns
    try:
        backend_packages = await check_pip_packages()
        results["tests"].append({
            "test": "check_pip_packages()",
            "success": True,
            "packages_returned": len(backend_packages),
            "sample": [p.name for p in backend_packages[:5]] if backend_packages else []
        })
    except Exception as e:
        results["tests"].append({
            "test": "check_pip_packages()",
            "success": False,
            "error": str(e)
        })
    
    return results


def get_python_executable() -> str:
    """Get the correct Python executable for the current platform."""
    # Use the current Python interpreter
    return sys.executable


def get_pip_command() -> List[str]:
    """Get the correct pip command for the current platform."""
    # Use python -m pip for cross-platform compatibility
    return [get_python_executable(), "-m", "pip"]


@router.get("/test-connectivity")
async def test_connectivity():
    """Test internet connectivity to PyPI and npm registries."""
    results = {}
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test PyPI
            try:
                start = datetime.now()
                resp = await client.get("https://pypi.org/pypi/requests/json")
                elapsed = (datetime.now() - start).total_seconds() * 1000
                results["pypi"] = {
                    "status": "connected",
                    "status_code": resp.status_code,
                    "latency_ms": round(elapsed, 2),
                    "test_url": "https://pypi.org/pypi/requests/json"
                }
            except Exception as e:
                results["pypi"] = {
                    "status": "failed",
                    "error": str(e),
                    "test_url": "https://pypi.org/pypi/requests/json"
                }
            
            # Test npm registry
            try:
                start = datetime.now()
                resp = await client.get("https://registry.npmjs.org/react/latest")
                elapsed = (datetime.now() - start).total_seconds() * 1000
                results["npm"] = {
                    "status": "connected",
                    "status_code": resp.status_code,
                    "latency_ms": round(elapsed, 2),
                    "test_url": "https://registry.npmjs.org/react/latest"
                }
            except Exception as e:
                results["npm"] = {
                    "status": "failed",
                    "error": str(e),
                    "test_url": "https://registry.npmjs.org/react/latest"
                }
    except Exception as e:
        results["error"] = str(e)
    
    return results


# Models
class ComponentVersion(BaseModel):
    """Component version information."""
    name: str = Field(..., description="Component name")
    current_version: str = Field(..., description="Current version")
    latest_version: Optional[str] = Field(None, description="Latest available version")
    status: str = Field(..., description="up-to-date, update-available, major-update, unknown")
    type: str = Field(..., description="backend, frontend, ollama, system")
    update_command: Optional[str] = Field(None, description="Command to update")
    changelog_url: Optional[str] = Field(None, description="URL to changelog")


class UpgradeRequest(BaseModel):
    """Request to upgrade a component."""
    name: str = Field(..., description="Component name")
    type: str = Field(..., description="Component type")
    target_version: Optional[str] = Field(None, description="Target version (latest if not specified)")


class UpgradeStatus(BaseModel):
    """Upgrade operation status."""
    component: str
    status: str  # running, completed, failed
    progress: int  # 0-100
    message: str
    logs: List[str] = Field(default_factory=list)


# Global upgrade status tracker
upgrade_statuses: Dict[str, UpgradeStatus] = {}


async def run_command(cmd: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
    """Run a shell command and capture output."""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        stdout, stderr = await process.communicate()
        
        return {
            "success": process.returncode == 0,
            "stdout": stdout.decode('utf-8', errors='ignore'),
            "stderr": stderr.decode('utf-8', errors='ignore'),
            "returncode": process.returncode
        }
    except Exception as e:
        logger.error(f"Command failed: {' '.join(cmd)}: {e}")
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


async def fetch_pypi_version(package_name: str) -> Optional[str]:
    """Fetch latest version from PyPI registry."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://pypi.org/pypi/{package_name}/json")
            if response.status_code == 200:
                data = response.json()
                version = data.get("info", {}).get("version")
                logger.info(f"✓ Fetched {package_name}: {version} from PyPI")
                return version
            else:
                logger.warning(f"PyPI returned {response.status_code} for {package_name}")
    except Exception as e:
        logger.warning(f"Could not fetch PyPI version for {package_name}: {e}")
    return None


async def check_pip_packages() -> List[ComponentVersion]:
    """Check ALL Python package versions with PyPI lookup."""
    components = []
    
    logger.info("="*60)
    logger.info("Starting check_pip_packages()")
    logger.info("="*60)
    
    try:
        # Get ALL installed packages using cross-platform pip command
        pip_cmd = get_pip_command()
        logger.info(f"🔍 Using pip command: {pip_cmd}")
        
        result = await run_command([*pip_cmd, "list", "--format=json"])
        
        logger.info(f"📊 Command result - Success: {result['success']}, Return code: {result.get('returncode', 'N/A')}")
        logger.info(f"📊 stdout length: {len(result['stdout'])}, stderr length: {len(result['stderr'])}")
        
        if not result["success"]:
            logger.error(f"❌ Failed to get pip list")
            logger.error(f"   stderr: {result['stderr'][:500]}")
            return components
        
        installed = json.loads(result["stdout"])
        logger.info(f"✅ Successfully parsed {len(installed)} Python packages")
        logger.info(f"🔍 Checking first few packages for updates...")
        logger.info(f"   Sample packages: {[p['name'] for p in installed[:5]]}")
        
        # Fetch latest versions from PyPI in parallel (limited concurrency)
        async def check_package(pkg):
            try:
                pkg_name = pkg["name"]
                current_version = pkg["version"]
                
                # Fetch from PyPI
                latest_version = await fetch_pypi_version(pkg_name)
                if not latest_version:
                    # If PyPI fetch fails, mark as unknown but still show the package
                    latest_version = "Unable to fetch"
                    status = "unknown"
                else:
                    status = "up-to-date"
                
                changelog_url = f"https://pypi.org/project/{pkg_name}/#history"
                
                if latest_version != current_version and latest_version != "Unable to fetch":
                    try:
                        # Compare versions
                        current_parts = [int(x) for x in current_version.split('.')[:3] if x.isdigit()]
                        latest_parts = [int(x) for x in latest_version.split('.')[:3] if x.isdigit()]
                        
                        if len(current_parts) > 0 and len(latest_parts) > 0:
                            if current_parts[0] < latest_parts[0]:
                                status = "major-update"
                            else:
                                status = "update-available"
                        else:
                            status = "update-available"
                    except:
                        status = "update-available"
                
                # Cross-platform upgrade command
                pip_upgrade_cmd = " ".join([*get_pip_command(), "install", "--upgrade", pkg_name])
                
                return ComponentVersion(
                    name=pkg_name,
                    current_version=current_version,
                    latest_version=latest_version,
                    status=status,
                    type="backend",
                    update_command=pip_upgrade_cmd,
                    changelog_url=changelog_url
                )
            except Exception as e:
                logger.error(f"Error checking package {pkg.get('name', 'unknown')}: {e}")
                return None
        
        # Process in batches to avoid overwhelming PyPI
        batch_size = 10
        for i in range(0, len(installed), batch_size):
            batch = installed[i:i + batch_size]
            results = await asyncio.gather(*[check_package(pkg) for pkg in batch])
            components.extend([r for r in results if r is not None])
            # Small delay between batches
            if i + batch_size < len(installed):
                await asyncio.sleep(0.5)
    
    except Exception as e:
        logger.error(f"❌❌❌ CRITICAL ERROR in check_pip_packages: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
    
    logger.info(f"✅ Returning {len(components)} backend components")
    return components


async def fetch_npm_version(package_name: str) -> Optional[str]:
    """Fetch latest version from npm registry."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://registry.npmjs.org/{package_name}/latest")
            if response.status_code == 200:
                data = response.json()
                version = data.get("version")
                logger.info(f"✓ Fetched {package_name}: {version} from npm registry")
                return version
            else:
                logger.warning(f"npm registry returned {response.status_code} for {package_name}")
    except Exception as e:
        logger.warning(f"Could not fetch npm version for {package_name}: {e}")
    return None


async def check_npm_packages() -> List[ComponentVersion]:
    """Check ALL npm package versions with registry lookup (cross-platform)."""
    components = []
    
    try:
        frontend_path = Path(__file__).parent.parent.parent.parent.parent / "frontend"
        
        # Check if package.json exists
        package_json = frontend_path / "package.json"
        if not package_json.exists():
            logger.warning(f"package.json not found at {package_json}")
            return components
        
        # Read package.json to get all dependencies
        with open(package_json, 'r') as f:
            pkg_data = json.load(f)
        
        all_deps = {}
        all_deps.update(pkg_data.get("dependencies", {}))
        all_deps.update(pkg_data.get("devDependencies", {}))
        
        logger.info(f"Checking {len(all_deps)} npm packages for updates...")
        
        # Get currently installed versions using cross-platform npm command
        npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
        result = await run_command([npm_cmd, "list", "--json", "--depth=0"], cwd=frontend_path)
        installed_versions = {}
        if result["success"] and result["stdout"]:
            try:
                npm_data = json.loads(result["stdout"])
                installed_versions = npm_data.get("dependencies", {})
            except:
                pass
        
        # Check each package against npm registry
        async def check_package(pkg_name: str, declared_version: str):
            try:
                # Get installed version
                current_version = "unknown"
                if pkg_name in installed_versions:
                    current_version = installed_versions[pkg_name].get("version", declared_version.lstrip("^~"))
                else:
                    current_version = declared_version.lstrip("^~")
                
                # Fetch latest from npm registry
                latest_version = await fetch_npm_version(pkg_name)
                if not latest_version:
                    latest_version = "Unable to fetch"
                    status = "unknown"
                else:
                    status = "up-to-date"
                
                changelog_url = f"https://www.npmjs.com/package/{pkg_name}?activeTab=versions"
                
                if latest_version != current_version and current_version != "unknown" and latest_version != "Unable to fetch":
                    try:
                        # Compare versions
                        current_parts = [int(x) for x in current_version.split('.')[:3] if x.isdigit()]
                        latest_parts = [int(x) for x in latest_version.split('.')[:3] if x.isdigit()]
                        
                        if len(current_parts) > 0 and len(latest_parts) > 0:
                            if current_parts[0] < latest_parts[0]:
                                status = "major-update"
                            elif current_parts < latest_parts:
                                status = "update-available"
                        else:
                            status = "update-available"
                    except:
                        status = "update-available"
                
                return ComponentVersion(
                    name=pkg_name,
                    current_version=current_version,
                    latest_version=latest_version,
                    status=status,
                    type="frontend",
                    update_command=f"npm install {pkg_name}@latest",
                    changelog_url=changelog_url
                )
            except Exception as e:
                logger.error(f"Error checking npm package {pkg_name}: {e}")
                return None
        
        # Process in batches
        batch_size = 10
        pkg_items = list(all_deps.items())
        for i in range(0, len(pkg_items), batch_size):
            batch = pkg_items[i:i + batch_size]
            results = await asyncio.gather(*[check_package(name, ver) for name, ver in batch])
            components.extend([r for r in results if r is not None])
            # Small delay between batches
            if i + batch_size < len(pkg_items):
                await asyncio.sleep(0.5)
    
    except Exception as e:
        logger.error(f"Error checking npm packages: {e}")
    
    return components


async def check_ollama_models(settings: Settings) -> List[ComponentVersion]:
    """Check Ollama model versions."""
    components = []
    
    try:
        import httpx
        
        # Use configured Ollama URL or default
        ollama_url = "http://localhost:11434"
        for conn_id, conn in (getattr(settings, 'llm_connections', {}) or {}).items():
            base = getattr(conn, 'base_url', '')
            if 'ollama' in base.lower() or '11434' in base:
                ollama_url = base
                break
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Get installed models
            resp = await client.get(f"{ollama_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("models", [])
                
                for model in models:
                    name = model.get("name", "")
                    modified = model.get("modified_at", "")
                    size = model.get("size", 0)
                    
                    components.append(ComponentVersion(
                        name=name,
                        current_version=modified[:10] if modified else "installed",
                        latest_version="Check ollama.com",
                        status="unknown",  # Ollama doesn't expose version checking API
                        type="ollama",
                        update_command=f"ollama pull {name}",
                        changelog_url="https://ollama.com/library"
                    ))
    
    except Exception as e:
        logger.error(f"Error checking Ollama models: {e}")
    
    return components


async def check_system_components() -> List[ComponentVersion]:
    """Check system component versions (cross-platform)."""
    components = []
    
    try:
        # Python version - use the current interpreter
        try:
            python_version = platform.python_version()
            components.append(ComponentVersion(
                name="Python",
                current_version=python_version,
                latest_version="Check python.org",
                status="unknown",
                type="system",
                changelog_url="https://www.python.org/downloads/"
            ))
        except Exception as e:
            logger.error(f"Could not get Python version: {e}")
        
        # Node.js version
        node_cmd = "node.exe" if platform.system() == "Windows" else "node"
        node_result = await run_command([node_cmd, "--version"])
        if node_result["success"]:
            version = node_result["stdout"].strip().replace('v', '')
            components.append(ComponentVersion(
                name="Node.js",
                current_version=version,
                latest_version="Check nodejs.org",
                status="unknown",
                type="system",
                changelog_url="https://nodejs.org/"
            ))
        
        # Git version
        git_cmd = "git.exe" if platform.system() == "Windows" else "git"
        git_result = await run_command([git_cmd, "--version"])
        if git_result["success"]:
            version = git_result["stdout"].strip().split()[-1]
            components.append(ComponentVersion(
                name="Git",
                current_version=version,
                latest_version="Check git-scm.com",
                status="unknown",
                type="system",
                changelog_url="https://git-scm.com/"
            ))
        
        # npm version
        npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
        npm_result = await run_command([npm_cmd, "--version"])
        if npm_result["success"]:
            version = npm_result["stdout"].strip()
            components.append(ComponentVersion(
                name="npm",
                current_version=version,
                latest_version="Check npmjs.com",
                status="unknown",
                type="system",
                changelog_url="https://www.npmjs.com/"
            ))
    
    except Exception as e:
        logger.error(f"Error checking system components: {e}")
    
    return components


@router.get("/check", response_model=Dict[str, Any])
async def check_updates(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Check for available updates across all components.
    
    Returns:
        Dictionary with components grouped by type
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting upgrade check - fetching from internet registries...")
        logger.info("=" * 60)
        
        # Run checks in parallel
        backend_task = check_pip_packages()
        frontend_task = check_npm_packages()
        ollama_task = check_ollama_models(settings)
        system_task = check_system_components()
        
        backend, frontend, ollama, system = await asyncio.gather(
            backend_task, frontend_task, ollama_task, system_task
        )
        
        logger.info(f"✓ Backend packages checked: {len(backend)}")
        logger.info(f"✓ Frontend packages checked: {len(frontend)}")
        logger.info(f"✓ Ollama models checked: {len(ollama)}")
        logger.info(f"✓ System components checked: {len(system)}")
        
        all_components = backend + frontend + ollama + system
        
        # Calculate summary
        summary = {
            "total": len(all_components),
            "up_to_date": len([c for c in all_components if c.status == "up-to-date"]),
            "updates_available": len([c for c in all_components if c.status in ["update-available", "major-update"]]),
            "unknown": len([c for c in all_components if c.status == "unknown"])
        }
        
        return {
            "success": True,
            "checked_at": datetime.utcnow().isoformat(),
            "summary": summary,
            "components": {
                "backend": [c.dict() for c in backend],
                "frontend": [c.dict() for c in frontend],
                "ollama": [c.dict() for c in ollama],
                "system": [c.dict() for c in system]
            }
        }
    
    except Exception as e:
        logger.error(f"Error checking updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def perform_upgrade(component_name: str, component_type: str, target_version: Optional[str] = None):
    """Perform upgrade in background (cross-platform)."""
    status_key = f"{component_type}:{component_name}"
    
    upgrade_statuses[status_key] = UpgradeStatus(
        component=component_name,
        status="running",
        progress=10,
        message="Starting upgrade...",
        logs=[]
    )
    
    try:
        if component_type == "backend":
            # Upgrade pip package using cross-platform command
            pip_cmd = get_pip_command()
            cmd = [*pip_cmd, "install", "--upgrade", component_name]
            if target_version:
                cmd[-1] = f"{component_name}=={target_version}"
            
            upgrade_statuses[status_key].progress = 30
            upgrade_statuses[status_key].message = f"Installing {component_name}..."
            upgrade_statuses[status_key].logs.append(f"Executing: {' '.join(cmd)}")
            
            result = await run_command(cmd)
            
            upgrade_statuses[status_key].logs.append(result["stdout"])
            if result["stderr"]:
                upgrade_statuses[status_key].logs.append(result["stderr"])
            
            if result["success"]:
                upgrade_statuses[status_key].status = "completed"
                upgrade_statuses[status_key].progress = 100
                upgrade_statuses[status_key].message = f"Successfully upgraded {component_name}"
            else:
                upgrade_statuses[status_key].status = "failed"
                upgrade_statuses[status_key].message = f"Failed to upgrade {component_name}"
        
        elif component_type == "frontend":
            # Upgrade npm package using cross-platform command
            frontend_path = Path(__file__).parent.parent.parent.parent.parent / "frontend"
            
            npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
            pkg_spec = f"{component_name}@{target_version}" if target_version else f"{component_name}@latest"
            cmd = [npm_cmd, "install", pkg_spec]
            
            upgrade_statuses[status_key].progress = 30
            upgrade_statuses[status_key].message = f"Installing {component_name}..."
            upgrade_statuses[status_key].logs.append(f"Executing: {' '.join(cmd)}")
            
            result = await run_command(cmd, cwd=frontend_path)
            
            upgrade_statuses[status_key].logs.append(result["stdout"])
            if result["stderr"]:
                upgrade_statuses[status_key].logs.append(result["stderr"])
            
            if result["success"]:
                upgrade_statuses[status_key].status = "completed"
                upgrade_statuses[status_key].progress = 100
                upgrade_statuses[status_key].message = f"Successfully upgraded {component_name}"
            else:
                upgrade_statuses[status_key].status = "failed"
                upgrade_statuses[status_key].message = f"Failed to upgrade {component_name}"
        
        elif component_type == "ollama":
            # Pull Ollama model
            cmd = ["ollama", "pull", component_name]
            
            upgrade_statuses[status_key].progress = 30
            upgrade_statuses[status_key].message = f"Pulling {component_name}..."
            
            result = await run_command(cmd)
            
            upgrade_statuses[status_key].logs.append(result["stdout"])
            if result["stderr"]:
                upgrade_statuses[status_key].logs.append(result["stderr"])
            
            if result["success"]:
                upgrade_statuses[status_key].status = "completed"
                upgrade_statuses[status_key].progress = 100
                upgrade_statuses[status_key].message = f"Successfully pulled {component_name}"
            else:
                upgrade_statuses[status_key].status = "failed"
                upgrade_statuses[status_key].message = f"Failed to pull {component_name}"
        
        else:
            upgrade_statuses[status_key].status = "failed"
            upgrade_statuses[status_key].message = f"Unsupported component type: {component_type}"
    
    except Exception as e:
        logger.error(f"Upgrade failed for {component_name}: {e}")
        upgrade_statuses[status_key].status = "failed"
        upgrade_statuses[status_key].message = str(e)
        upgrade_statuses[status_key].logs.append(f"Error: {str(e)}")


@router.post("/upgrade")
async def upgrade_component(
    request: UpgradeRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Upgrade a specific component.
    
    Args:
        request: Upgrade request with component details
        background_tasks: FastAPI background tasks
        
    Returns:
        Status of upgrade initiation
    """
    try:
        status_key = f"{request.type}:{request.name}"
        
        # Check if already upgrading
        if status_key in upgrade_statuses and upgrade_statuses[status_key].status == "running":
            raise HTTPException(status_code=409, detail="Upgrade already in progress")
        
        # Start background upgrade
        background_tasks.add_task(
            perform_upgrade,
            request.name,
            request.type,
            request.target_version
        )
        
        return {
            "success": True,
            "message": f"Upgrade started for {request.name}",
            "status_key": status_key
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting upgrade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{status_key}")
async def get_upgrade_status(status_key: str) -> UpgradeStatus:
    """Get status of an ongoing or completed upgrade."""
    if status_key not in upgrade_statuses:
        raise HTTPException(status_code=404, detail="Upgrade status not found")
    
    return upgrade_statuses[status_key]


@router.get("/status")
async def list_upgrade_statuses() -> Dict[str, UpgradeStatus]:
    """List all upgrade statuses."""
    return upgrade_statuses


@router.delete("/status/{status_key}")
async def clear_upgrade_status(status_key: str) -> Dict[str, Any]:
    """Clear upgrade status for a component."""
    if status_key in upgrade_statuses:
        del upgrade_statuses[status_key]
        return {"success": True, "message": "Status cleared"}
    
    raise HTTPException(status_code=404, detail="Status not found")
