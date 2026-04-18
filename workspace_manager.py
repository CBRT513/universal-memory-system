#!/usr/bin/env python3
"""
Workspace Manager - Automatically detects and routes to correct workspace
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any

class WorkspaceManager:
    """Manages workspace detection and routing"""
    
    def __init__(self):
        self.home = Path.home()
        self.current_user = os.environ.get('USER', 'unknown')
        self.workspace = self.detect_workspace()
        
    def detect_workspace(self) -> str:
        """Detect which workspace to use based on various factors"""
        
        # 1. Check environment variable (highest priority)
        if 'UMS_WORKSPACE' in os.environ:
            return os.environ['UMS_WORKSPACE']
        
        # 2. Check current directory for .ums-workspace file
        cwd = Path.cwd()
        workspace_file = cwd / '.ums-workspace'
        if workspace_file.exists():
            return workspace_file.read_text().strip()
        
        # 3. Check parent directories for .ums-workspace
        for parent in cwd.parents:
            workspace_file = parent / '.ums-workspace'
            if workspace_file.exists():
                return workspace_file.read_text().strip()
        
        # 4. Check user account
        user_map = {
            'cerion': 'personal',
            'Cerion': 'personal',
            'equillabs': 'work',
            'Equillabs': 'work'
        }
        if self.current_user in user_map:
            return user_map[self.current_user]
        
        # 5. Check time of day (9-5 = work, else personal)
        from datetime import datetime
        hour = datetime.now().hour
        if 9 <= hour < 17 and datetime.now().weekday() < 5:  # Mon-Fri, 9-5
            return 'work'
        
        # 6. Default to personal
        return 'personal'
    
    def get_config(self) -> Dict[str, Any]:
        """Get configuration for current workspace"""
        workspace_dir = self.home / f'.ums-{self.workspace}'
        config_file = workspace_dir / 'config' / 'settings.json'
        
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        
        # Default config
        return {
            'profile': self.workspace,
            'api_port': 8091 if self.workspace == 'personal' else 8092,
            'database': str(workspace_dir / 'memories' / f'{self.workspace}_memories.db')
        }
    
    def set_environment(self):
        """Set environment variables for current workspace"""
        config = self.get_config()
        os.environ['UMS_WORKSPACE'] = self.workspace
        os.environ['UMS_PROFILE'] = config['profile']
        os.environ['MEMORY_API_PORT'] = str(config['api_port'])
        os.environ['MEMORY_DB_PATH'] = config['database']
        
    def switch_workspace(self, workspace: str):
        """Switch to a different workspace"""
        valid = ['personal', 'work']
        if workspace not in valid:
            print(f"Invalid workspace. Choose from: {valid}")
            return False
        
        # Create .ums-workspace file in current directory
        workspace_file = Path.cwd() / '.ums-workspace'
        workspace_file.write_text(workspace)
        print(f"Switched to {workspace} workspace for this directory")
        return True
    
    def status(self):
        """Show current workspace status"""
        config = self.get_config()
        print(f"Current Workspace: {self.workspace}")
        print(f"API Port: {config['api_port']}")
        print(f"Database: {config['database']}")
        
        # Check if API is running
        port = config['api_port']
        try:
            result = subprocess.run(
                f"lsof -i:{port}",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✓ API running on port {port}")
            else:
                print(f"✗ API not running (start with: ums-start)")
        except:
            print("Could not check API status")

# Global instance
manager = WorkspaceManager()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Workspace Manager")
    parser.add_argument('command', choices=['status', 'switch', 'detect'], 
                       help='Command to execute')
    parser.add_argument('workspace', nargs='?', choices=['personal', 'work'],
                       help='Workspace to switch to')
    
    args = parser.parse_args()
    
    if args.command == 'status':
        manager.status()
    elif args.command == 'detect':
        print(manager.workspace)
    elif args.command == 'switch':
        if args.workspace:
            manager.switch_workspace(args.workspace)
        else:
            print("Please specify workspace: personal or work")