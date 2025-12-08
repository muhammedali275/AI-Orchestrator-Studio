"""
Configuration File Writer Service.

Handles writing configuration changes from GUI to persistent files.
"""

import json
import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigWriter:
    """Service for writing configuration to files."""
    
    def __init__(self, base_path: str = "."):
        """
        Initialize config writer.
        
        Args:
            base_path: Base directory for configuration files
        """
        self.base_path = Path(base_path)
        self.config_dir = self.base_path / "backend" / "orchestrator" / "config"
        self.env_file = self.base_path / "backend" / "orchestrator" / ".env"
        
    def write_env_file(self, config: Dict[str, Any]) -> bool:
        """
        Write configuration to .env file.
        
        Args:
            config: Dictionary of environment variables
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read existing .env file if it exists
            existing_config = {}
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            existing_config[key.strip()] = value.strip()
            
            # Update with new config
            existing_config.update(config)
            
            # Write back to file
            with open(self.env_file, 'w') as f:
                f.write("# AI Orchestrator Studio Configuration\n")
                f.write("# Auto-generated from GUI\n\n")
                
                for key, value in sorted(existing_config.items()):
                    # Handle values with spaces or special characters
                    if isinstance(value, str) and (' ' in value or any(c in value for c in ['#', '$', '&'])):
                        value = f'"{value}"'
                    f.write(f"{key}={value}\n")
            
            logger.info(f"Successfully wrote {len(config)} variables to .env file")
            return True
            
        except Exception as e:
            logger.error(f"Error writing .env file: {str(e)}")
            return False
    
    def write_json_config(self, filename: str, config: Dict[str, Any]) -> bool:
        """
        Write configuration to JSON file.
        
        Args:
            filename: Name of the JSON file (e.g., 'agents.json')
            config: Configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = self.config_dir / filename
            
            # Write JSON with pretty formatting
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Successfully wrote configuration to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing {filename}: {str(e)}")
            return False
    
    def write_agents_config(self, agents: list) -> bool:
        """
        Write agents configuration.
        
        Args:
            agents: List of agent configurations
            
        Returns:
            True if successful
        """
        config = {"agents": agents}
        return self.write_json_config("agents.json", config)
    
    def write_datasources_config(self, datasources: list) -> bool:
        """
        Write datasources configuration.
        
        Args:
            datasources: List of datasource configurations
            
        Returns:
            True if successful
        """
        config = {"datasources": datasources}
        return self.write_json_config("datasources.json", config)
    
    def write_tools_config(self, tools: list) -> bool:
        """
        Write tools configuration.
        
        Args:
            tools: List of tool configurations
            
        Returns:
            True if successful
        """
        config = {"tools": tools}
        return self.write_json_config("tools.json", config)
    
    def read_json_config(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Read configuration from JSON file.
        
        Args:
            filename: Name of the JSON file
            
        Returns:
            Configuration dictionary or None if error
        """
        try:
            filepath = self.config_dir / filename
            
            if not filepath.exists():
                logger.warning(f"Config file {filename} does not exist")
                return None
            
            with open(filepath, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error reading {filename}: {str(e)}")
            return None
    
    def backup_config(self, filename: str) -> bool:
        """
        Create a backup of a configuration file.
        
        Args:
            filename: Name of the file to backup
            
        Returns:
            True if successful
        """
        try:
            filepath = self.config_dir / filename
            
            if not filepath.exists():
                return False
            
            backup_path = filepath.with_suffix(filepath.suffix + '.backup')
            
            import shutil
            shutil.copy2(filepath, backup_path)
            
            logger.info(f"Created backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup of {filename}: {str(e)}")
            return False
