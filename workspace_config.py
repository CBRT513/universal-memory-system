#!/usr/bin/env python3
"""
Workspace Configuration - Automatically detects and configures workspace
This module is imported by all UMS tools to ensure they use the right data
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class WorkspaceConfig:
    """Single source of truth for workspace configuration"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.home = Path.home()
        self._detect_workspace()
        self._load_config()
        self._apply_config()
    
    def _detect_workspace(self):
        """Detect current workspace from multiple sources"""
        
        # 1. Environment variable (highest priority - set by 'switch' command)
        if 'UMS_WORKSPACE' in os.environ:
            self.workspace = os.environ['UMS_WORKSPACE']
            return
        
        # 2. Saved preference file
        current_file = self.home / '.ums-current-workspace'
        if current_file.exists():
            self.workspace = current_file.read_text().strip()
            return
        
        # 3. User account detection
        user = os.environ.get('USER', '')
        if user.lower() in ['equillabs', 'equi']:
            self.workspace = 'work'
        else:
            self.workspace = 'personal'
    
    def _load_config(self):
        """Load configuration for current workspace"""
        workspace_dir = self.home / f'.ums-{self.workspace}'
        config_file = workspace_dir / 'config' / 'settings.json'
        
        if config_file.exists():
            with open(config_file) as f:
                self.config = json.load(f)
        else:
            # Default configuration
            self.config = {
                'profile': self.workspace,
                'api_port': 8091 if self.workspace == 'personal' else 8092,
                'database': str(workspace_dir / 'memories' / f'{self.workspace}_memories.db'),
                'log_dir': str(workspace_dir / 'logs'),
                'subagent_output': str(workspace_dir / 'subagent-outputs')
            }
    
    def _apply_config(self):
        """Apply configuration to environment"""
        os.environ['UMS_WORKSPACE'] = self.workspace
        os.environ['UMS_PROFILE'] = self.config['profile']
        os.environ['MEMORY_API_PORT'] = str(self.config['api_port'])
        os.environ['MEMORY_DB_PATH'] = self.config['database']
        
        # Create directories if they don't exist
        for key in ['log_dir', 'subagent_output']:
            if key in self.config:
                Path(self.config[key]).mkdir(parents=True, exist_ok=True)
    
    @property
    def api_port(self) -> int:
        return self.config['api_port']
    
    @property
    def database_path(self) -> str:
        return self.config['database']
    
    @property
    def is_work(self) -> bool:
        return self.workspace == 'work'
    
    @property
    def is_personal(self) -> bool:
        return self.workspace == 'personal'
    
    def get_api_url(self) -> str:
        return f"http://localhost:{self.api_port}"
    
    def switch_to(self, workspace: str):
        """Switch to a different workspace"""
        if workspace not in ['personal', 'work']:
            raise ValueError(f"Invalid workspace: {workspace}")
        
        # Save preference
        current_file = self.home / '.ums-current-workspace'
        current_file.write_text(workspace)
        
        # Update environment
        os.environ['UMS_WORKSPACE'] = workspace
        
        # Reinitialize
        self._initialized = False
        self.__init__()

# Global config instance - import this everywhere
config = WorkspaceConfig()

# Convenience functions
def get_workspace() -> str:
    """Get current workspace name"""
    return config.workspace

def get_api_port() -> int:
    """Get API port for current workspace"""
    return config.api_port

def get_database_path() -> str:
    """Get database path for current workspace"""
    return config.database_path

def switch_workspace(workspace: str):
    """Switch to different workspace"""
    config.switch_to(workspace)
    print(f"Switched to {workspace} workspace")
    print(f"  API Port: {config.api_port}")
    print(f"  Database: {config.database_path}")

if __name__ == "__main__":
    # Test/debug
    print(f"Current workspace: {config.workspace}")
    print(f"API Port: {config.api_port}")
    print(f"Database: {config.database_path}")