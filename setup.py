#!/usr/bin/env python3
"""
Universal AI Memory System - Automated Setup Script
Production-ready setup for Mac mini deployment with zero-configuration
"""
import os
import sys
import json
import shutil
import subprocess
import platform
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import tarfile
import zipfile

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class UniversalMemorySetup:
    """Complete automated setup for Universal AI Memory System"""
    
    def __init__(self):
        self.setup_dir = Path(__file__).parent
        self.home_dir = Path.home()
        self.memory_dir = self.home_dir / ".ai-memory"
        self.venv_dir = self.setup_dir / "venv"
        self.system_type = platform.system()
        self.architecture = platform.machine()
        
        # Configuration
        self.config = {
            "memory_api_port": 8091,
            "librarian_gui_port": 8092,
            "embedding_provider": "sentence-transformers",  # Default to local
            "auto_start_services": True,
            "shell_completion": True,
            "desktop_integration": True,
            "browser_integration": True,
            "service_management": True
        }
        
        # Track installation progress
        self.progress = {
            "system_check": False,
            "dependencies": False,
            "python_env": False,
            "memory_service": False,
            "cli_integration": False,
            "gui_service": False,
            "browser_setup": False,
            "service_management": False,
            "verification": False
        }
    
    def print_status(self, message: str, status: str = "info", prefix: str = ""):
        """Print colored status messages"""
        colors = {
            "info": Colors.BLUE,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED,
            "header": Colors.HEADER + Colors.BOLD
        }
        
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "header": "🧠"
        }
        
        color = colors.get(status, Colors.BLUE)
        icon = icons.get(status, "")
        
        print(f"{prefix}{color}{icon} {message}{Colors.END}")
    
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
        print(f"🧠 {text}")
        print(f"{'='*60}{Colors.END}\n")
    
    def run_command(self, command: str, check: bool = True, capture: bool = False) -> Tuple[bool, str]:
        """Run shell command with error handling"""
        try:
            if capture:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    check=check
                )
                return result.returncode == 0, result.stdout.strip()
            else:
                result = subprocess.run(command, shell=True, check=check)
                return result.returncode == 0, ""
        except subprocess.CalledProcessError as e:
            if capture:
                return False, str(e)
            return False, ""
    
    def check_system_requirements(self) -> bool:
        """Check system requirements and compatibility"""
        self.print_header("System Requirements Check")
        
        all_good = True
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            self.print_status(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} - Compatible", "success")
        else:
            self.print_status(f"Python {python_version.major}.{python_version.minor} - Requires 3.8+", "error")
            all_good = False
        
        # Check macOS version (if on macOS)
        if self.system_type == "Darwin":
            success, version = self.run_command("sw_vers -productVersion", capture=True)
            if success:
                self.print_status(f"macOS {version} detected", "success")
            else:
                self.print_status("Could not detect macOS version", "warning")
        
        # Check available disk space
        disk_usage = shutil.disk_usage(self.home_dir)
        free_gb = disk_usage.free / (1024**3)
        
        if free_gb >= 2:
            self.print_status(f"Available disk space: {free_gb:.1f} GB - Sufficient", "success")
        else:
            self.print_status(f"Available disk space: {free_gb:.1f} GB - May be insufficient", "warning")
        
        # Check internet connectivity
        try:
            urllib.request.urlopen('https://pypi.org', timeout=5)
            self.print_status("Internet connectivity - Available", "success")
        except:
            self.print_status("Internet connectivity - Limited (may affect setup)", "warning")
        
        # Check required system tools
        required_tools = ['pip3', 'git'] if self.system_type == "Darwin" else ['pip3']
        
        for tool in required_tools:
            if shutil.which(tool):
                self.print_status(f"{tool} - Available", "success")
            else:
                self.print_status(f"{tool} - Missing (will attempt to install)", "warning")
        
        # Check ports availability
        ports_to_check = [self.config["memory_api_port"], self.config["librarian_gui_port"]]
        for port in ports_to_check:
            success, _ = self.run_command(f"lsof -i :{port}", check=False)
            if not success:
                self.print_status(f"Port {port} - Available", "success")
            else:
                self.print_status(f"Port {port} - In use (may cause conflicts)", "warning")
        
        self.progress["system_check"] = all_good
        return all_good
    
    def setup_python_environment(self) -> bool:
        """Setup Python virtual environment and dependencies"""
        self.print_header("Python Environment Setup")
        
        try:
            # Create virtual environment
            if self.venv_dir.exists():
                self.print_status("Removing existing virtual environment", "info")
                shutil.rmtree(self.venv_dir)
            
            self.print_status("Creating Python virtual environment...", "info")
            success, _ = self.run_command(f"{sys.executable} -m venv {self.venv_dir}")
            
            if not success:
                self.print_status("Failed to create virtual environment", "error")
                return False
            
            self.print_status("Virtual environment created", "success")
            
            # Determine pip path
            pip_path = self.venv_dir / "bin" / "pip" if self.system_type != "Windows" else self.venv_dir / "Scripts" / "pip"
            
            # Upgrade pip
            self.print_status("Upgrading pip...", "info")
            success, _ = self.run_command(f"{pip_path} install --upgrade pip")
            
            if success:
                self.print_status("pip upgraded successfully", "success")
            else:
                self.print_status("pip upgrade failed (continuing anyway)", "warning")
            
            # Install core dependencies
            dependencies = [
                "fastapi>=0.100.0",
                "uvicorn[standard]>=0.20.0",
                "click>=8.1.0",
                "rich>=13.0.0",
                "jinja2>=3.1.0",
                "python-multipart>=0.0.6",
                "numpy>=1.24.0",
                "requests>=2.31.0",
                "sqlite-fts4",  # Better SQLite FTS support
            ]
            
            # Add optional dependencies with fallbacks
            optional_deps = [
                "sentence-transformers>=2.2.0",  # For local embeddings
                "hnswlib>=0.8.0",  # For vector search
                "pyperclip>=1.8.0",  # For clipboard integration
                "python-dotenv>=1.0.0",  # For environment variables
            ]
            
            # Install core dependencies
            self.print_status("Installing core dependencies...", "info")
            deps_cmd = f"{pip_path} install " + " ".join(f'"{dep}"' for dep in dependencies)
            success, output = self.run_command(deps_cmd, check=False, capture=True)
            
            if success:
                self.print_status("Core dependencies installed successfully", "success")
            else:
                self.print_status("Some core dependencies failed to install", "warning")
                self.print_status(f"Error: {output}", "error")
            
            # Install optional dependencies (continue on failure)
            self.print_status("Installing optional dependencies...", "info")
            failed_optional = []
            
            for dep in optional_deps:
                success, _ = self.run_command(f"{pip_path} install \"{dep}\"", check=False)
                if success:
                    self.print_status(f"✓ {dep.split('>=')[0]}", "success", "  ")
                else:
                    failed_optional.append(dep.split('>=')[0])
                    self.print_status(f"✗ {dep.split('>=')[0]} (optional)", "warning", "  ")
            
            if failed_optional:
                self.print_status(f"Optional dependencies not installed: {', '.join(failed_optional)}", "warning")
                self.print_status("System will work with reduced functionality", "info")
            
            self.progress["python_env"] = True
            return True
            
        except Exception as e:
            self.print_status(f"Python environment setup failed: {str(e)}", "error")
            return False
    
    def setup_memory_service(self) -> bool:
        """Setup and configure the memory service"""
        self.print_header("Memory Service Configuration")
        
        try:
            # Create memory directory structure
            self.print_status("Creating memory storage directories...", "info")
            
            directories = [
                self.memory_dir,
                self.memory_dir / "vectors",
                self.memory_dir / "backups",
                self.memory_dir / "exports",
                self.memory_dir / "logs"
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
            
            self.print_status(f"Storage directory created: {self.memory_dir}", "success")
            
            # Create default configuration
            config = {
                "storage_path": str(self.memory_dir),
                "api_port": self.config["memory_api_port"],
                "gui_port": self.config["librarian_gui_port"],
                "embedding_provider": self.config["embedding_provider"],
                "embedding_model": "all-MiniLM-L6-v2",  # Default sentence-transformers model
                "vector_search_enabled": True,
                "auto_backup": True,
                "backup_interval_hours": 24,
                "max_storage_size_gb": 10,
                "log_level": "INFO",
                "cors_origins": ["http://localhost:3000", "http://127.0.0.1:3000"],  # For development
                "rate_limiting": False  # Disable for local use
            }
            
            config_file = self.memory_dir / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.print_status("Configuration file created", "success")
            
            # Test memory service import
            python_path = self.venv_dir / "bin" / "python" if self.system_type != "Windows" else self.venv_dir / "Scripts" / "python"
            test_cmd = f'cd "{self.setup_dir}/src" && {python_path} -c "from memory_service import get_memory_service; print(\\"Memory service OK\\")"'
            
            success, output = self.run_command(test_cmd, check=False, capture=True)
            
            if success and "Memory service OK" in output:
                self.print_status("Memory service import test passed", "success")
            else:
                self.print_status("Memory service import test failed", "warning")
                self.print_status(f"Output: {output}", "info")
            
            self.progress["memory_service"] = True
            return True
            
        except Exception as e:
            self.print_status(f"Memory service setup failed: {str(e)}", "error")
            return False
    
    def setup_cli_integration(self) -> bool:
        """Setup CLI integration with global memory command"""
        self.print_header("CLI Integration Setup")
        
        try:
            # Make CLI script executable
            cli_script = self.setup_dir / "src" / "memory_cli.py"
            os.chmod(cli_script, 0o755)
            
            # Create shell integration
            python_path = self.venv_dir / "bin" / "python" if self.system_type != "Windows" else self.venv_dir / "Scripts" / "python"
            
            # Create global memory command script
            memory_script = self.home_dir / ".local" / "bin" / "memory"
            memory_script.parent.mkdir(parents=True, exist_ok=True)
            
            script_content = f"""#!/bin/bash
# Universal AI Memory CLI wrapper
cd "{self.setup_dir}/src"
exec "{python_path}" memory_cli.py "$@"
"""
            
            with open(memory_script, 'w') as f:
                f.write(script_content)
            
            os.chmod(memory_script, 0o755)
            self.print_status("Global memory command created", "success")
            
            # Add to shell configuration
            shell_configs = {
                "bash": self.home_dir / ".bashrc",
                "zsh": self.home_dir / ".zshrc",
                "fish": self.home_dir / ".config" / "fish" / "config.fish"
            }
            
            # Detect current shell
            shell = os.environ.get("SHELL", "").split("/")[-1]
            
            if shell in shell_configs and self.config.get("shell_completion", True):
                config_file = shell_configs[shell]
                
                shell_addition = f"""
# Universal AI Memory CLI
export PATH="$HOME/.local/bin:$PATH"
export MEMORY_HOME="{self.setup_dir}"

# Completion (uncomment after first run)
# eval "$(_MEMORY_COMPLETE={shell}_source memory)"
"""
                
                # Check if already added
                config_exists = config_file.exists()
                already_configured = False
                
                if config_exists:
                    with open(config_file, 'r') as f:
                        content = f.read()
                        already_configured = "Universal AI Memory CLI" in content
                
                if not already_configured:
                    config_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(config_file, 'a') as f:
                        f.write(shell_addition)
                    self.print_status(f"Added memory command to {config_file.name}", "success")
                else:
                    self.print_status(f"CLI already configured in {config_file.name}", "info")
            
            # Test CLI command
            test_cmd = f'PATH="$HOME/.local/bin:$PATH" memory --help'
            success, output = self.run_command(test_cmd, check=False, capture=True)
            
            if success and "Universal AI Memory System" in output:
                self.print_status("CLI command test passed", "success")
            else:
                self.print_status("CLI command test failed (may work after shell restart)", "warning")
            
            self.progress["cli_integration"] = True
            return True
            
        except Exception as e:
            self.print_status(f"CLI integration failed: {str(e)}", "error")
            return False
    
    def setup_gui_service(self) -> bool:
        """Setup librarian GUI service"""
        self.print_header("Librarian GUI Setup")
        
        try:
            # Test GUI service import
            python_path = self.venv_dir / "bin" / "python" if self.system_type != "Windows" else self.venv_dir / "Scripts" / "python"
            test_cmd = f'cd "{self.setup_dir}/src" && {python_path} -c "from librarian_gui import app; print(\\"GUI service OK\\")"'
            
            success, output = self.run_command(test_cmd, check=False, capture=True)
            
            if success and "GUI service OK" in output:
                self.print_status("GUI service import test passed", "success")
            else:
                self.print_status("GUI service import test failed", "warning")
                self.print_status(f"Output: {output}", "info")
            
            # Create desktop shortcut for GUI (macOS)
            if self.system_type == "Darwin" and self.config.get("desktop_integration", True):
                self.create_macos_app()
            
            self.progress["gui_service"] = True
            return True
            
        except Exception as e:
            self.print_status(f"GUI service setup failed: {str(e)}", "error")
            return False
    
    def create_macos_app(self):
        """Create macOS application bundle for easy access"""
        try:
            app_dir = Path("/Applications/Universal AI Memory.app")
            contents_dir = app_dir / "Contents"
            macos_dir = contents_dir / "MacOS"
            resources_dir = contents_dir / "Resources"
            
            # Remove existing app
            if app_dir.exists():
                shutil.rmtree(app_dir)
            
            # Create directory structure
            macos_dir.mkdir(parents=True, exist_ok=True)
            resources_dir.mkdir(parents=True, exist_ok=True)
            
            # Create Info.plist
            info_plist = contents_dir / "Info.plist"
            plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>memory-gui</string>
    <key>CFBundleIdentifier</key>
    <string>com.universalai.memory</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Universal AI Memory</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>'''
            
            with open(info_plist, 'w') as f:
                f.write(plist_content)
            
            # Create launcher script
            launcher = macos_dir / "memory-gui"
            python_path = self.venv_dir / "bin" / "python"
            
            launcher_content = f'''#!/bin/bash
cd "{self.setup_dir}/src"
"{python_path}" librarian_gui.py --host 127.0.0.1 --port {self.config["librarian_gui_port"]} &
sleep 2
open "http://127.0.0.1:{self.config["librarian_gui_port"]}"
'''
            
            with open(launcher, 'w') as f:
                f.write(launcher_content)
            
            os.chmod(launcher, 0o755)
            
            self.print_status("macOS application created", "success")
            
        except Exception as e:
            self.print_status(f"macOS app creation failed: {str(e)}", "warning")
    
    def setup_browser_integration(self) -> bool:
        """Setup browser integration and bookmarklet"""
        self.print_header("Browser Integration Setup")
        
        try:
            # Copy browser integration files to user accessible location
            browser_dir = self.memory_dir / "browser"
            browser_dir.mkdir(exist_ok=True)
            
            static_dir = self.setup_dir / "static"
            if static_dir.exists():
                for file in static_dir.glob("*"):
                    if file.is_file():
                        shutil.copy2(file, browser_dir / file.name)
            
            self.print_status("Browser integration files copied", "success")
            
            # Create easy access HTML file
            integration_file = browser_dir / "integration.html"
            if not integration_file.exists():
                # Copy from static directory or create basic one
                static_integration = static_dir / "browser_integration.html"
                if static_integration.exists():
                    shutil.copy2(static_integration, integration_file)
                else:
                    # Create minimal integration file
                    minimal_html = '''<!DOCTYPE html>
<html><head><title>AI Memory Browser Integration</title></head>
<body>
<h1>Universal AI Memory - Browser Integration</h1>
<p>Drag this bookmarklet to your bookmark bar:</p>
<a href="javascript:(function(){document.body.appendChild(document.createElement('script')).src='http://localhost:8091/static/browser_capture.js';})();">🧠 Capture AI Memory</a>
<p>Then click it on any AI website to capture insights!</p>
</body></html>'''
                    with open(integration_file, 'w') as f:
                        f.write(minimal_html)
            
            self.print_status(f"Browser integration available: {integration_file}", "success")
            
            self.progress["browser_setup"] = True
            return True
            
        except Exception as e:
            self.print_status(f"Browser integration setup failed: {str(e)}", "error")
            return False
    
    def setup_service_management(self) -> bool:
        """Setup service management and auto-start"""
        self.print_header("Service Management Setup")
        
        try:
            scripts_dir = self.setup_dir / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            
            python_path = self.venv_dir / "bin" / "python" if self.system_type != "Windows" else self.venv_dir / "Scripts" / "python"
            
            # Create service startup script
            start_script = scripts_dir / "start-services.sh"
            start_script_content = f"""#!/bin/bash
# Universal AI Memory System - Service Starter

echo "🧠 Starting Universal AI Memory System..."

# Check if already running
if curl -s http://localhost:{self.config["memory_api_port"]}/api/health > /dev/null 2>&1; then
    echo "⚠️  Memory service already running on port {self.config["memory_api_port"]}"
else
    echo "🚀 Starting Memory Service..."
    cd "{self.setup_dir}/src"
    "{python_path}" -m uvicorn memory_service:app --host 127.0.0.1 --port {self.config["memory_api_port"]} > "{self.memory_dir}/logs/memory_service.log" 2>&1 &
    echo $! > "{self.memory_dir}/memory_service.pid"
    sleep 2
fi

if curl -s http://localhost:{self.config["librarian_gui_port"]}/ > /dev/null 2>&1; then
    echo "⚠️  GUI service already running on port {self.config["librarian_gui_port"]}"
else
    echo "🎨 Starting Librarian GUI..."
    cd "{self.setup_dir}/src"
    "{python_path}" librarian_gui.py --host 127.0.0.1 --port {self.config["librarian_gui_port"]} > "{self.memory_dir}/logs/gui_service.log" 2>&1 &
    echo $! > "{self.memory_dir}/gui_service.pid"
    sleep 2
fi

echo "✅ Services started!"
echo "📊 Memory API: http://localhost:{self.config["memory_api_port"]}/docs"
echo "🎨 Librarian GUI: http://localhost:{self.config["librarian_gui_port"]}/"
echo "🌐 Browser Integration: file://{self.memory_dir}/browser/integration.html"
"""
            
            with open(start_script, 'w') as f:
                f.write(start_script_content)
            
            os.chmod(start_script, 0o755)
            
            # Create stop script
            stop_script = scripts_dir / "stop-services.sh"
            stop_script_content = f"""#!/bin/bash
# Universal AI Memory System - Service Stopper

echo "🛑 Stopping Universal AI Memory System..."

# Stop services using PID files
for service in memory_service gui_service; do
    pid_file="{self.memory_dir}/${{service}}.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $service (PID: $pid)..."
            kill "$pid"
            rm "$pid_file"
        else
            echo "$service not running"
            rm -f "$pid_file"
        fi
    fi
done

# Fallback: kill by port
pkill -f "memory_service"
pkill -f "librarian_gui"

echo "✅ Services stopped"
"""
            
            with open(stop_script, 'w') as f:
                f.write(stop_script_content)
            
            os.chmod(stop_script, 0o755)
            
            # Create status script
            status_script = scripts_dir / "status.sh"
            status_script_content = f"""#!/bin/bash
# Universal AI Memory System - Status Check

echo "🔍 Universal AI Memory System Status"
echo "=================================="

# Check Memory Service
if curl -s http://localhost:{self.config["memory_api_port"]}/api/health > /dev/null 2>&1; then
    echo "✅ Memory Service: Running (http://localhost:{self.config["memory_api_port"]})"
else
    echo "❌ Memory Service: Not running"
fi

# Check GUI Service
if curl -s http://localhost:{self.config["librarian_gui_port"]}/ > /dev/null 2>&1; then
    echo "✅ Librarian GUI: Running (http://localhost:{self.config["librarian_gui_port"]})"
else
    echo "❌ Librarian GUI: Not running"
fi

# Check CLI
if command -v memory > /dev/null 2>&1; then
    echo "✅ CLI Command: Available"
else
    echo "❌ CLI Command: Not found (restart shell or source config)"
fi

# Check storage
if [ -d "{self.memory_dir}" ]; then
    echo "✅ Storage Directory: {self.memory_dir}"
    echo "   $(du -sh "{self.memory_dir}" | cut -f1) used"
else
    echo "❌ Storage Directory: Not found"
fi
"""
            
            with open(status_script, 'w') as f:
                f.write(status_script_content)
            
            os.chmod(status_script, 0o755)
            
            # Create launchd service for macOS auto-start
            if self.system_type == "Darwin" and self.config.get("auto_start_services", True):
                self.create_launchd_service(start_script)
            
            self.print_status("Service management scripts created", "success")
            
            self.progress["service_management"] = True
            return True
            
        except Exception as e:
            self.print_status(f"Service management setup failed: {str(e)}", "error")
            return False
    
    def create_launchd_service(self, start_script_path: Path):
        """Create macOS launchd service for auto-start"""
        try:
            launch_agents_dir = self.home_dir / "Library" / "LaunchAgents"
            launch_agents_dir.mkdir(parents=True, exist_ok=True)
            
            plist_file = launch_agents_dir / "com.universalai.memory.plist"
            
            plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.universalai.memory</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{start_script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>WorkingDirectory</key>
    <string>{self.setup_dir}</string>
    <key>StandardOutPath</key>
    <string>{self.memory_dir}/logs/launchd.out</string>
    <key>StandardErrorPath</key>
    <string>{self.memory_dir}/logs/launchd.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
        <key>MEMORY_HOME</key>
        <string>{self.setup_dir}</string>
    </dict>
</dict>
</plist>'''
            
            with open(plist_file, 'w') as f:
                f.write(plist_content)
            
            # Load the service
            success, _ = self.run_command(f"launchctl load {plist_file}", check=False)
            
            if success:
                self.print_status("Auto-start service configured (launchd)", "success")
            else:
                self.print_status("Auto-start service created (manual load required)", "warning")
                self.print_status(f"Load with: launchctl load {plist_file}", "info")
            
        except Exception as e:
            self.print_status(f"Auto-start service creation failed: {str(e)}", "warning")
    
    def verify_installation(self) -> bool:
        """Verify that everything is working correctly"""
        self.print_header("Installation Verification")
        
        all_tests_passed = True
        
        # Test 1: Python environment
        try:
            python_path = self.venv_dir / "bin" / "python" if self.system_type != "Windows" else self.venv_dir / "Scripts" / "python"
            success, output = self.run_command(f"{python_path} --version", capture=True)
            
            if success:
                self.print_status(f"Python environment: {output}", "success")
            else:
                self.print_status("Python environment test failed", "error")
                all_tests_passed = False
                
        except Exception as e:
            self.print_status(f"Python environment test error: {str(e)}", "error")
            all_tests_passed = False
        
        # Test 2: Memory service import
        try:
            python_path = self.venv_dir / "bin" / "python" if self.system_type != "Windows" else self.venv_dir / "Scripts" / "python"
            test_cmd = f'cd "{self.setup_dir}/src" && {python_path} -c "from memory_service import UniversalMemoryService; print(\\"Import OK\\")"'
            success, output = self.run_command(test_cmd, check=False, capture=True)
            
            if success and "Import OK" in output:
                self.print_status("Memory service import: OK", "success")
            else:
                self.print_status("Memory service import: Failed", "error")
                all_tests_passed = False
                
        except Exception as e:
            self.print_status(f"Memory service test error: {str(e)}", "error")
            all_tests_passed = False
        
        # Test 3: Storage directory
        if self.memory_dir.exists() and os.access(self.memory_dir, os.R_OK | os.W_OK):
            self.print_status(f"Storage directory: {self.memory_dir}", "success")
        else:
            self.print_status("Storage directory: Not accessible", "error")
            all_tests_passed = False
        
        # Test 4: Configuration file
        config_file = self.memory_dir / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                self.print_status("Configuration file: Valid JSON", "success")
            except:
                self.print_status("Configuration file: Invalid JSON", "error")
                all_tests_passed = False
        else:
            self.print_status("Configuration file: Missing", "error")
            all_tests_passed = False
        
        # Test 5: CLI availability
        success, _ = self.run_command("command -v memory", check=False)
        if success:
            self.print_status("CLI command: Available", "success")
        else:
            self.print_status("CLI command: Not in PATH (restart shell)", "warning")
        
        self.progress["verification"] = all_tests_passed
        return all_tests_passed
    
    def print_completion_summary(self):
        """Print installation completion summary"""
        self.print_header("Installation Complete!")
        
        print(f"{Colors.GREEN}🎉 Universal AI Memory System has been successfully installed!{Colors.END}\n")
        
        # Service URLs
        memory_url = f"http://localhost:{self.config['memory_api_port']}"
        gui_url = f"http://localhost:{self.config['librarian_gui_port']}"
        browser_file = self.memory_dir / "browser" / "integration.html"
        
        print(f"{Colors.BOLD}Quick Start:{Colors.END}")
        print(f"1. Start services: {Colors.CYAN}./scripts/start-services.sh{Colors.END}")
        print(f"2. Open GUI: {Colors.CYAN}{gui_url}{Colors.END}")
        print(f"3. Try CLI: {Colors.CYAN}memory --help{Colors.END}")
        print(f"4. Browser integration: {Colors.CYAN}file://{browser_file}{Colors.END}")
        print()
        
        print(f"{Colors.BOLD}Service Management:{Colors.END}")
        print(f"• Start: {Colors.CYAN}./scripts/start-services.sh{Colors.END}")
        print(f"• Stop: {Colors.CYAN}./scripts/stop-services.sh{Colors.END}")
        print(f"• Status: {Colors.CYAN}./scripts/status.sh{Colors.END}")
        print()
        
        print(f"{Colors.BOLD}Key Locations:{Colors.END}")
        print(f"• Storage: {Colors.CYAN}{self.memory_dir}{Colors.END}")
        print(f"• Logs: {Colors.CYAN}{self.memory_dir}/logs{Colors.END}")
        print(f"• Scripts: {Colors.CYAN}{self.setup_dir}/scripts{Colors.END}")
        print()
        
        if self.system_type == "Darwin":
            print(f"{Colors.BOLD}macOS Integration:{Colors.END}")
            print(f"• App: {Colors.CYAN}Universal AI Memory.app{Colors.END} in Applications")
            print(f"• Auto-start: {Colors.CYAN}Configured via launchd{Colors.END}")
            print()
        
        print(f"{Colors.BOLD}Example Usage:{Colors.END}")
        print(f"• Store memory: {Colors.CYAN}memory remember \"Solution for React performance\"{Colors.END}")
        print(f"• Search: {Colors.CYAN}memory search \"database optimization\"{Colors.END}")
        print(f"• Get context: {Colors.CYAN}memory context --relevant-to \"authentication\" --copy{Colors.END}")
        print()
        
        # Show any warnings
        failed_components = [k for k, v in self.progress.items() if not v]
        if failed_components:
            print(f"{Colors.YELLOW}⚠️  Some components had issues:{Colors.END}")
            for component in failed_components:
                print(f"  • {component.replace('_', ' ').title()}")
            print("The system should still work with reduced functionality.")
            print()
        
        print(f"{Colors.GREEN}🧠 Your AI conversations will never lose context again!{Colors.END}")
    
    def run_setup(self) -> bool:
        """Run the complete setup process"""
        self.print_header("Universal AI Memory System Setup")
        
        print(f"{Colors.CYAN}Welcome to the Universal AI Memory System installer!")
        print(f"This will set up everything you need for persistent AI memory.{Colors.END}\n")
        
        # Confirmation
        try:
            response = input(f"{Colors.BOLD}Continue with installation? (y/N): {Colors.END}")
            if response.lower() not in ['y', 'yes']:
                print("Installation cancelled.")
                return False
        except KeyboardInterrupt:
            print("\nInstallation cancelled.")
            return False
        
        print()
        
        # Setup steps
        steps = [
            ("Checking system requirements", self.check_system_requirements),
            ("Setting up Python environment", self.setup_python_environment),
            ("Configuring memory service", self.setup_memory_service),
            ("Setting up CLI integration", self.setup_cli_integration),
            ("Setting up GUI service", self.setup_gui_service),
            ("Configuring browser integration", self.setup_browser_integration),
            ("Setting up service management", self.setup_service_management),
            ("Verifying installation", self.verify_installation),
        ]
        
        overall_success = True
        
        for step_name, step_func in steps:
            self.print_status(f"Starting: {step_name}", "info")
            
            try:
                success = step_func()
                if success:
                    self.print_status(f"Completed: {step_name}", "success")
                else:
                    self.print_status(f"Failed: {step_name}", "error")
                    overall_success = False
            except KeyboardInterrupt:
                self.print_status("Setup interrupted by user", "error")
                return False
            except Exception as e:
                self.print_status(f"Error in {step_name}: {str(e)}", "error")
                overall_success = False
        
        # Show completion summary
        self.print_completion_summary()
        
        return overall_success

def main():
    """Main setup function"""
    setup = UniversalMemorySetup()
    
    try:
        success = setup.run_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Setup failed with error: {str(e)}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()