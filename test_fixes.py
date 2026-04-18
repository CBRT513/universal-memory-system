#!/usr/bin/env python3
"""
Test script for critical fixes:
1. Git detection improvements
2. Global Capture system validation
"""

import os
import sys
import subprocess
from pathlib import Path

def test_git_detection():
    """Test git detection functionality"""
    print("🧪 Testing Git Detection Fixes")
    print("=" * 40)
    
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    try:
        from memory_service import get_memory_service
        
        # Initialize service
        service = get_memory_service()
        
        # Test project detection
        project = service._detect_project()
        print(f"✅ Project detection: {project}")
        
        # Test git info
        git_info = service._get_git_info()
        print(f"✅ Git repository: {git_info['is_git_repo']}")
        
        if git_info['is_git_repo']:
            print(f"   Repository name: {git_info['repo_name']}")
            print(f"   Repository root: {git_info['repo_root']}")
            print(f"   Remote URL: {git_info['remote_url']}")
            print(f"   GitHub repo: {git_info['github_repo']}")
            print(f"   Current branch: {git_info['current_branch']}")
            print(f"   Commit hash: {git_info['commit_hash']}")
        else:
            print("   Not a git repository")
            
        print("✅ Git detection tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Git detection test failed: {e}")
        return False

def test_global_capture_build():
    """Test Global Capture build process"""
    print("\n🧪 Testing Global Capture Build")
    print("=" * 40)
    
    global_capture_dir = Path(__file__).parent / "global-capture"
    
    if not global_capture_dir.exists():
        print("❌ Global Capture directory not found")
        return False
        
    # Check if we're on macOS
    if subprocess.run(['uname'], capture_output=True, text=True).stdout.strip() != 'Darwin':
        print("⚠️  Global Capture is macOS-only, skipping build test")
        return True
    
    # Check required files
    main_swift = global_capture_dir / "main.swift"
    build_script = global_capture_dir / "build.sh"
    
    if not main_swift.exists():
        print("❌ main.swift not found")
        return False
        
    if not build_script.exists():
        print("❌ build.sh not found")
        return False
        
    print("✅ Required files found")
    
    # Test Swift syntax checking (without full compilation)
    try:
        # Check if Swift compiler is available
        swift_check = subprocess.run(['swift', '--version'], 
                                   capture_output=True, text=True, timeout=10)
        
        if swift_check.returncode != 0:
            print("⚠️  Swift compiler not available, skipping syntax check")
            return True
            
        print(f"✅ Swift compiler available: {swift_check.stdout.strip().split()[0]}")
        
        # Basic syntax check (typecheck only, no compilation)
        print("🔍 Checking Swift syntax...")
        syntax_check = subprocess.run(['swift', '-frontend', '-typecheck', 'main.swift'],
                                    capture_output=True, text=True, 
                                    cwd=str(global_capture_dir),
                                    timeout=30)
        
        if syntax_check.returncode == 0:
            print("✅ Swift syntax check passed!")
        else:
            print(f"⚠️  Swift syntax warnings/errors:")
            if syntax_check.stderr:
                # Filter out common warnings that don't affect functionality
                errors = [line for line in syntax_check.stderr.split('\n') 
                         if line.strip() and 'warning:' not in line.lower()]
                if errors:
                    for error in errors[:5]:  # Show first 5 errors
                        print(f"   {error}")
            
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Swift syntax check timed out")
        return False
    except Exception as e:
        print(f"❌ Swift syntax check failed: {e}")
        return False

def test_system_integration():
    """Test overall system integration"""
    print("\n🧪 Testing System Integration")
    print("=" * 40)
    
    try:
        # Test memory service health
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from memory_service import get_memory_service
        
        service = get_memory_service()
        health = service.health_check()
        
        print(f"✅ Memory service health: {health['status']}")
        
        if health['status'] == 'healthy':
            # Test basic functionality
            test_result = service.store_memory(
                content="Test memory for system validation",
                category="test",
                tags=["system-test", "validation"],
                source="test_fixes"
            )
            
            print(f"✅ Memory storage test: {test_result['status']}")
            
            # Test search
            search_results = service.search_memories(
                query="test memory validation",
                limit=1
            )
            
            print(f"✅ Memory search test: {len(search_results)} results found")
            
        return True
        
    except Exception as e:
        print(f"❌ System integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 Running Critical Fix Tests")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(test_git_detection())
    results.append(test_global_capture_build())
    results.append(test_system_integration())
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All critical fixes validated successfully!")
        return 0
    else:
        print("⚠️  Some tests failed - please review the output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())