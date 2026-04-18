#!/usr/bin/env python3
"""
Universal AI Memory System - System Verification Script
Comprehensive test to ensure all components are working
"""
import os
import sys
import time
import json
import subprocess
import requests
from pathlib import Path

class SystemVerifier:
    """Verify all components of the Universal AI Memory System"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.src_dir = self.base_dir / "src"
        self.memory_api_url = "http://localhost:8091"
        self.gui_url = "http://localhost:8092"
        
    def print_status(self, message: str, status: str = "info"):
        """Print colored status messages"""
        colors = {
            "info": "\033[94m",
            "success": "\033[92m", 
            "warning": "\033[93m",
            "error": "\033[91m",
            "reset": "\033[0m"
        }
        
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        color = colors.get(status, colors["info"])
        icon = icons.get(status, "")
        reset = colors["reset"]
        
        print(f"{color}{icon} {message}{reset}")
    
    def run_command(self, command: str, capture: bool = False, timeout: int = 10):
        """Run command with timeout"""
        try:
            if capture:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=timeout
                )
                return result.returncode == 0, result.stdout.strip()
            else:
                result = subprocess.run(command, shell=True, timeout=timeout)
                return result.returncode == 0, ""
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def check_python_environment(self):
        """Check Python environment"""
        self.print_status("Checking Python environment...", "info")
        
        # Check Python version
        version = sys.version_info
        if version >= (3, 8):
            self.print_status(f"Python {version.major}.{version.minor}.{version.micro} - OK", "success")
        else:
            self.print_status(f"Python {version.major}.{version.minor} - Needs 3.8+", "error")
            return False
        
        # Check if virtual environment exists
        venv_dir = self.base_dir / "venv"
        if venv_dir.exists():
            self.print_status("Virtual environment - Found", "success")
        else:
            self.print_status("Virtual environment - Missing", "warning")
        
        return True
    
    def check_dependencies(self):
        """Check required dependencies"""
        self.print_status("Checking dependencies...", "info")
        
        required_modules = [
            "fastapi",
            "uvicorn", 
            "click",
            "rich",
            "numpy",
            "requests"
        ]
        
        missing = []
        for module in required_modules:
            try:
                __import__(module)
                self.print_status(f"{module} - Available", "success")
            except ImportError:
                missing.append(module)
                self.print_status(f"{module} - Missing", "error")
        
        if missing:
            self.print_status(f"Missing dependencies: {', '.join(missing)}", "error")
            return False
        
        return True
    
    def check_memory_service(self):
        """Check memory service functionality"""
        self.print_status("Checking memory service...", "info")
        
        try:
            # Import memory service
            sys.path.insert(0, str(self.src_dir))
            from memory_service import UniversalMemoryService
            
            # Create service instance
            service = UniversalMemoryService()
            
            # Test storing a memory
            result = service.store_memory(
                content="Test memory for system verification",
                tags=["test", "verification"],
                importance=5,
                source="verification_script"
            )
            
            if result["status"] in ["stored", "duplicate"]:
                self.print_status("Memory storage - OK", "success")
            else:
                self.print_status("Memory storage - Failed", "error")
                return False
            
            # Test searching
            results = service.search_memories(query="verification", limit=5)
            if results:
                self.print_status("Memory search - OK", "success")
            else:
                self.print_status("Memory search - No results", "warning")
            
            # Test context generation
            context = service.get_context(relevant_to="testing", max_tokens=500)
            if len(context) > 50:
                self.print_status("Context generation - OK", "success")
            else:
                self.print_status("Context generation - Minimal output", "warning")
            
            return True
            
        except Exception as e:
            self.print_status(f"Memory service error: {str(e)}", "error")
            return False
    
    def check_cli_interface(self):
        """Check CLI interface"""
        self.print_status("Checking CLI interface...", "info")
        
        try:
            # Test CLI help
            python_path = sys.executable
            cli_path = self.src_dir / "memory_cli.py"
            
            success, output = self.run_command(
                f"{python_path} {cli_path} --help",
                capture=True
            )
            
            if success and "Universal AI Memory System" in output:
                self.print_status("CLI help - OK", "success")
            else:
                self.print_status("CLI help - Failed", "error")
                return False
            
            # Test CLI store command
            success, output = self.run_command(
                f"{python_path} {cli_path} remember 'CLI test memory' --tags cli,test",
                capture=True
            )
            
            if success and ("stored" in output.lower() or "duplicate" in output.lower()):
                self.print_status("CLI store command - OK", "success")
            else:
                self.print_status("CLI store command - Failed", "error")
                return False
            
            return True
            
        except Exception as e:
            self.print_status(f"CLI interface error: {str(e)}", "error")
            return False
    
    def check_api_service(self):
        """Check if API service can start"""
        self.print_status("Checking API service...", "info")
        
        try:
            # Check if service is already running
            try:
                response = requests.get(f"{self.memory_api_url}/api/health", timeout=2)
                if response.status_code == 200:
                    self.print_status("API service - Already running", "success")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            # Try to import API service
            sys.path.insert(0, str(self.src_dir))
            from api_service import app
            
            self.print_status("API service import - OK", "success")
            return True
            
        except Exception as e:
            self.print_status(f"API service error: {str(e)}", "error")
            return False
    
    def check_gui_service(self):
        """Check GUI service"""
        self.print_status("Checking GUI service...", "info")
        
        try:
            # Check if GUI is already running
            try:
                response = requests.get(self.gui_url, timeout=2)
                if response.status_code == 200:
                    self.print_status("GUI service - Already running", "success")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            # Try to import GUI service
            sys.path.insert(0, str(self.src_dir))
            from librarian_gui import app
            
            self.print_status("GUI service import - OK", "success")
            return True
            
        except Exception as e:
            self.print_status(f"GUI service error: {str(e)}", "error")
            return False
    
    def check_storage_setup(self):
        """Check storage directory setup"""
        self.print_status("Checking storage setup...", "info")
        
        storage_dir = Path.home() / ".ai-memory"
        
        if storage_dir.exists():
            self.print_status(f"Storage directory - {storage_dir}", "success")
        else:
            self.print_status("Storage directory - Missing", "warning")
        
        # Check required subdirectories
        subdirs = ["vectors", "backups", "exports", "logs"]
        for subdir in subdirs:
            subdir_path = storage_dir / subdir
            if subdir_path.exists():
                self.print_status(f"  {subdir}/ - OK", "success")
            else:
                self.print_status(f"  {subdir}/ - Missing", "warning")
        
        return True
    
    def check_browser_integration(self):
        """Check browser integration files"""
        self.print_status("Checking browser integration...", "info")
        
        static_dir = self.base_dir / "static"
        required_files = [
            "browser_capture.js",
            "browser_integration.html"
        ]
        
        for file in required_files:
            file_path = static_dir / file
            if file_path.exists():
                self.print_status(f"{file} - Found", "success")
            else:
                self.print_status(f"{file} - Missing", "error")
                return False
        
        return True
    
    def run_full_verification(self):
        """Run complete system verification"""
        print("\n🧠 Universal AI Memory System - Verification")
        print("=" * 50)
        
        checks = [
            ("Python Environment", self.check_python_environment),
            ("Dependencies", self.check_dependencies),
            ("Storage Setup", self.check_storage_setup),
            ("Memory Service", self.check_memory_service),
            ("CLI Interface", self.check_cli_interface),
            ("API Service", self.check_api_service),
            ("GUI Service", self.check_gui_service),
            ("Browser Integration", self.check_browser_integration),
        ]
        
        passed = 0
        failed = 0
        
        for check_name, check_func in checks:
            print(f"\n--- {check_name} ---")
            
            try:
                if check_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.print_status(f"Check failed with exception: {str(e)}", "error")
                failed += 1
        
        # Summary
        print("\n" + "=" * 50)
        print(f"🧠 Verification Summary")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        
        if failed == 0:
            self.print_status("🎉 All checks passed! System is ready to use.", "success")
            print("\nNext steps:")
            print("1. Start services: ./scripts/start-services.sh")
            print("2. Try CLI: memory --help")
            print("3. Open GUI: http://localhost:8092")
            print("4. Browser integration: open static/browser_integration.html")
        else:
            self.print_status("⚠️ Some checks failed. Run setup.py to fix issues.", "warning")
        
        return failed == 0

if __name__ == "__main__":
    verifier = SystemVerifier()
    success = verifier.run_full_verification()
    sys.exit(0 if success else 1)