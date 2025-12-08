"""
Service Control - Knows how to restart safe services if allowed by config.

Provides service control operations for AIPanel.
"""

import logging
import subprocess
import platform
import os
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple

from ..core.config.config_service import ConfigService

logger = logging.getLogger(__name__)


class ServiceControl:
    """
    Service control for AIPanel.
    
    Knows how to restart safe services if allowed by config.
    """
    
    def __init__(self, config_service: ConfigService):
        """
        Initialize service control.
        
        Args:
            config_service: Configuration service
        """
        self.config_service = config_service
        self._is_windows = platform.system().lower() == "windows"
    
    async def restart_service(self, service_name: str) -> Dict[str, Any]:
        """
        Restart service.
        
        Args:
            service_name: Service name
            
        Returns:
            Restart result
        """
        try:
            # Check if service restart is allowed
            if not self.config_service.is_service_restart_allowed(service_name):
                return {
                    "success": False,
                    "message": f"Service restart not allowed: {service_name}"
                }
            
            # Get service configuration
            service_config = self.config_service.get_service_config(service_name)
            if not service_config:
                return {
                    "success": False,
                    "message": f"Service not found: {service_name}"
                }
            
            # Determine restart method
            restart_method = service_config.get("restart_method", "command")
            
            if restart_method == "command":
                # Restart using command
                return await self._restart_service_command(service_config)
            elif restart_method == "systemd":
                # Restart using systemd
                return await self._restart_service_systemd(service_config)
            elif restart_method == "docker":
                # Restart using Docker
                return await self._restart_service_docker(service_config)
            else:
                # Unknown restart method
                return {
                    "success": False,
                    "message": f"Unknown restart method: {restart_method}"
                }
            
        except Exception as e:
            logger.error(f"Error restarting service {service_name}: {str(e)}")
            return {
                "success": False,
                "message": f"Error restarting service: {str(e)}"
            }
    
    async def _restart_service_command(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Restart service using command.
        
        Args:
            service_config: Service configuration
            
        Returns:
            Restart result
        """
        try:
            # Get commands
            stop_command = service_config.get("stop_command")
            start_command = service_config.get("start_command")
            restart_command = service_config.get("restart_command")
            
            # Check if restart command is available
            if restart_command:
                # Execute restart command
                process = await asyncio.create_subprocess_shell(
                    restart_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                # Check result
                if process.returncode == 0:
                    return {
                        "success": True,
                        "message": f"Service restarted: {service_config.get('name')}",
                        "details": {
                            "stdout": stdout.decode() if stdout else "",
                            "stderr": stderr.decode() if stderr else ""
                        }
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Error restarting service: {stderr.decode() if stderr else 'Unknown error'}",
                        "details": {
                            "stdout": stdout.decode() if stdout else "",
                            "stderr": stderr.decode() if stderr else ""
                        }
                    }
            
            # Check if stop and start commands are available
            if stop_command and start_command:
                # Execute stop command
                stop_process = await asyncio.create_subprocess_shell(
                    stop_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stop_stdout, stop_stderr = await stop_process.communicate()
                
                # Check stop result
                if stop_process.returncode != 0:
                    return {
                        "success": False,
                        "message": f"Error stopping service: {stop_stderr.decode() if stop_stderr else 'Unknown error'}",
                        "details": {
                            "stdout": stop_stdout.decode() if stop_stdout else "",
                            "stderr": stop_stderr.decode() if stop_stderr else ""
                        }
                    }
                
                # Wait for service to stop
                await asyncio.sleep(2)
                
                # Execute start command
                start_process = await asyncio.create_subprocess_shell(
                    start_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                start_stdout, start_stderr = await start_process.communicate()
                
                # Check start result
                if start_process.returncode == 0:
                    return {
                        "success": True,
                        "message": f"Service restarted: {service_config.get('name')}",
                        "details": {
                            "stop_stdout": stop_stdout.decode() if stop_stdout else "",
                            "stop_stderr": stop_stderr.decode() if stop_stderr else "",
                            "start_stdout": start_stdout.decode() if start_stdout else "",
                            "start_stderr": start_stderr.decode() if start_stderr else ""
                        }
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Error starting service: {start_stderr.decode() if start_stderr else 'Unknown error'}",
                        "details": {
                            "stop_stdout": stop_stdout.decode() if stop_stdout else "",
                            "stop_stderr": stop_stderr.decode() if stop_stderr else "",
                            "start_stdout": start_stdout.decode() if start_stdout else "",
                            "start_stderr": start_stderr.decode() if start_stderr else ""
                        }
                    }
            
            # No valid commands available
            return {
                "success": False,
                "message": "No valid restart commands available"
            }
            
        except Exception as e:
            logger.error(f"Error restarting service using command: {str(e)}")
            return {
                "success": False,
                "message": f"Error restarting service: {str(e)}"
            }
    
    async def _restart_service_systemd(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Restart service using systemd.
        
        Args:
            service_config: Service configuration
            
        Returns:
            Restart result
        """
        try:
            # Check if running on Windows
            if self._is_windows:
                return {
                    "success": False,
                    "message": "Systemd not available on Windows"
                }
            
            # Get service name
            service_name = service_config.get("systemd_name", service_config.get("name"))
            
            # Execute systemctl command
            process = await asyncio.create_subprocess_shell(
                f"sudo systemctl restart {service_name}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            # Check result
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Service restarted: {service_name}",
                    "details": {
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else ""
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"Error restarting service: {stderr.decode() if stderr else 'Unknown error'}",
                    "details": {
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else ""
                    }
                }
            
        except Exception as e:
            logger.error(f"Error restarting service using systemd: {str(e)}")
            return {
                "success": False,
                "message": f"Error restarting service: {str(e)}"
            }
    
    async def _restart_service_docker(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Restart service using Docker.
        
        Args:
            service_config: Service configuration
            
        Returns:
            Restart result
        """
        try:
            # Get container name
            container_name = service_config.get("container_name", service_config.get("name"))
            
            # Execute Docker command
            process = await asyncio.create_subprocess_shell(
                f"docker restart {container_name}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            # Check result
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Container restarted: {container_name}",
                    "details": {
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else ""
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"Error restarting container: {stderr.decode() if stderr else 'Unknown error'}",
                    "details": {
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else ""
                    }
                }
            
        except Exception as e:
            logger.error(f"Error restarting service using Docker: {str(e)}")
            return {
                "success": False,
                "message": f"Error restarting service: {str(e)}"
            }
    
    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get service status.
        
        Args:
            service_name: Service name
            
        Returns:
            Service status
        """
        try:
            # Get service configuration
            service_config = self.config_service.get_service_config(service_name)
            if not service_config:
                return {
                    "status": "unknown",
                    "message": f"Service not found: {service_name}"
                }
            
            # Determine status method
            status_method = service_config.get("status_method", "command")
            
            if status_method == "command":
                # Get status using command
                return await self._get_service_status_command(service_config)
            elif status_method == "systemd":
                # Get status using systemd
                return await self._get_service_status_systemd(service_config)
            elif status_method == "docker":
                # Get status using Docker
                return await self._get_service_status_docker(service_config)
            elif status_method == "process":
                # Get status using process
                return await self._get_service_status_process(service_config)
            else:
                # Unknown status method
                return {
                    "status": "unknown",
                    "message": f"Unknown status method: {status_method}"
                }
            
        except Exception as e:
            logger.error(f"Error getting service status {service_name}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting service status: {str(e)}"
            }
    
    async def _get_service_status_command(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get service status using command.
        
        Args:
            service_config: Service configuration
            
        Returns:
            Service status
        """
        try:
            # Get status command
            status_command = service_config.get("status_command")
            if not status_command:
                return {
                    "status": "unknown",
                    "message": "No status command available"
                }
            
            # Execute status command
            process = await asyncio.create_subprocess_shell(
                status_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            # Check result
            if process.returncode == 0:
                return {
                    "status": "running",
                    "message": f"Service is running: {service_config.get('name')}",
                    "details": {
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else ""
                    }
                }
            else:
                return {
                    "status": "stopped",
                    "message": f"Service is not running: {service_config.get('name')}",
                    "details": {
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else ""
                    }
                }
            
        except Exception as e:
            logger.error(f"Error getting service status using command: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting service status: {str(e)}"
            }
    
    async def _get_service_status_systemd(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get service status using systemd.
        
        Args:
            service_config: Service configuration
            
        Returns:
            Service status
        """
        try:
            # Check if running on Windows
            if self._is_windows:
                return {
                    "status": "unknown",
                    "message": "Systemd not available on Windows"
                }
            
            # Get service name
            service_name = service_config.get("systemd_name", service_config.get("name"))
            
            # Execute systemctl command
            process = await asyncio.create_subprocess_shell(
                f"systemctl is-active {service_name}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            # Check result
            if process.returncode == 0:
                return {
                    "status": "running",
                    "message": f"Service is running: {service_name}",
                    "details": {
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else ""
                    }
                }
            else:
                return {
                    "status": "stopped",
                    "message": f"Service is not running: {service_name}",
                    "details": {
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else ""
                    }
                }
            
        except Exception as e:
            logger.error(f"Error getting service status using systemd: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting service status: {str(e)}"
            }
    
    async def _get_service_status_docker(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get service status using Docker.
        
        Args:
            service_config: Service configuration
            
        Returns:
            Service status
        """
        try:
            # Get container name
            container_name = service_config.get("container_name", service_config.get("name"))
            
            # Execute Docker command
            process = await asyncio.create_subprocess_shell(
                f"docker inspect --format='{{{{.State.Status}}}}' {container_name}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            # Check result
            if process.returncode == 0:
                status = stdout.decode().strip()
                
                if status == "running":
                    return {
                        "status": "running",
                        "message": f"Container is running: {container_name}",
                        "details": {
                            "docker_status": status
                        }
                    }
                else:
                    return {
                        "status": "stopped",
                        "message": f"Container is not running: {container_name}",
                        "details": {
                            "docker_status": status
                        }
                    }
            else:
                return {
                    "status": "unknown",
                    "message": f"Error getting container status: {stderr.decode() if stderr else 'Unknown error'}",
                    "details": {
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else ""
                    }
                }
            
        except Exception as e:
            logger.error(f"Error getting service status using Docker: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting service status: {str(e)}"
            }
    
    async def _get_service_status_process(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get service status using process.
        
        Args:
            service_config: Service configuration
            
        Returns:
            Service status
        """
        try:
            # Get process name
            process_name = service_config.get("process_name", service_config.get("name"))
            
            # Get process ID
            if self._is_windows:
                # Windows
                process = await asyncio.create_subprocess_shell(
                    f"tasklist /FI \"IMAGENAME eq {process_name}*\" /NH",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                # Check if process is running
                output = stdout.decode()
                if process_name in output:
                    return {
                        "status": "running",
                        "message": f"Process is running: {process_name}",
                        "details": {
                            "output": output
                        }
                    }
                else:
                    return {
                        "status": "stopped",
                        "message": f"Process is not running: {process_name}",
                        "details": {
                            "output": output
                        }
                    }
            else:
                # Unix-like
                process = await asyncio.create_subprocess_shell(
                    f"pgrep -f {process_name}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                # Check if process is running
                if process.returncode == 0:
                    return {
                        "status": "running",
                        "message": f"Process is running: {process_name}",
                        "details": {
                            "pid": stdout.decode().strip()
                        }
                    }
                else:
                    return {
                        "status": "stopped",
                        "message": f"Process is not running: {process_name}",
                        "details": {
                            "stderr": stderr.decode() if stderr else ""
                        }
                    }
            
        except Exception as e:
            logger.error(f"Error getting service status using process: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting service status: {str(e)}"
            }
