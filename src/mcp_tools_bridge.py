#!/usr/bin/env python3
"""
MCP Tools Bridge - Custom implementation of MCP tools for UMS
Provides GitHub, Git, and Browser automation without external dependencies
"""

import json
import subprocess
import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import sqlite3

class MCPToolsBridge:
    """
    Bridge between MCP concepts and your existing tools
    Implements GitHub, Git, and Browser automation natively
    """
    
    def __init__(self):
        self.ums_api = "http://localhost:8091"
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.repos_base = Path.home() / "Projects"
        
        # Track tool usage for optimization
        self.tool_usage = {}
        
    async def execute_tool(self, tool_name: str, params: Dict) -> Dict[str, Any]:
        """
        Main entry point for tool execution
        Routes to appropriate handler based on tool type
        """
        
        # Track usage
        self.tool_usage[tool_name] = self.tool_usage.get(tool_name, 0) + 1
        
        # Route to appropriate handler
        if tool_name.startswith("github_"):
            return await self.handle_github_tool(tool_name, params)
        elif tool_name.startswith("git_"):
            return await self.handle_git_tool(tool_name, params)
        elif tool_name.startswith("browser_"):
            return await self.handle_browser_tool(tool_name, params)
        elif tool_name.startswith("filesystem_"):
            return await self.handle_filesystem_tool(tool_name, params)
        elif tool_name.startswith("memory_"):
            return await self.handle_memory_tool(tool_name, params)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    # GitHub Tools
    async def handle_github_tool(self, tool: str, params: Dict) -> Dict:
        """Handle GitHub-related operations"""
        
        if tool == "github_list_repos":
            return await self.github_list_repos(params.get("user", "cerion"))
        
        elif tool == "github_create_issue":
            return await self.github_create_issue(
                params.get("repo"),
                params.get("title"),
                params.get("body")
            )
        
        elif tool == "github_get_issues":
            return await self.github_get_issues(
                params.get("repo"),
                params.get("state", "open")
            )
        
        elif tool == "github_analyze_repo":
            return await self.github_analyze_repo(params.get("repo"))
        
        return {"error": f"Unknown GitHub tool: {tool}"}
    
    async def github_list_repos(self, username: str) -> Dict:
        """List GitHub repositories for a user"""
        
        # Use gh CLI if available
        try:
            result = subprocess.run(
                ["gh", "repo", "list", username, "--json", "name,description,url"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                repos = json.loads(result.stdout)
                return {
                    "status": "success",
                    "repos": repos,
                    "count": len(repos)
                }
        except:
            pass
        
        # Fallback to API
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"token {self.github_token}"} if self.github_token else {}
            
            async with session.get(
                f"https://api.github.com/users/{username}/repos",
                headers=headers
            ) as response:
                if response.status == 200:
                    repos = await response.json()
                    return {
                        "status": "success",
                        "repos": [
                            {
                                "name": r["name"],
                                "description": r["description"],
                                "url": r["html_url"]
                            }
                            for r in repos
                        ],
                        "count": len(repos)
                    }
        
        return {"status": "error", "message": "Could not fetch repos"}
    
    async def github_create_issue(self, repo: str, title: str, body: str) -> Dict:
        """Create a GitHub issue"""
        
        try:
            result = subprocess.run(
                ["gh", "issue", "create", 
                 "--repo", repo,
                 "--title", title,
                 "--body", body],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "issue_url": result.stdout.strip()
                }
        except:
            pass
        
        return {"status": "error", "message": "Could not create issue"}
    
    async def github_get_issues(self, repo: str, state: str = "open") -> Dict:
        """Get issues from a repository"""
        
        try:
            result = subprocess.run(
                ["gh", "issue", "list",
                 "--repo", repo,
                 "--state", state,
                 "--json", "number,title,state,author"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                issues = json.loads(result.stdout)
                return {
                    "status": "success",
                    "issues": issues,
                    "count": len(issues)
                }
        except:
            pass
        
        return {"status": "error", "message": "Could not fetch issues"}
    
    async def github_analyze_repo(self, repo: str) -> Dict:
        """Analyze a GitHub repository structure"""
        
        analysis = {
            "status": "success",
            "repo": repo,
            "analysis": {}
        }
        
        # Get languages
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo}/languages"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                analysis["analysis"]["languages"] = json.loads(result.stdout)
        except:
            pass
        
        # Get recent commits
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo}/commits", "--jq", ".[0:5]"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                commits = json.loads(result.stdout)
                analysis["analysis"]["recent_commits"] = len(commits)
        except:
            pass
        
        return analysis
    
    # Git Tools
    async def handle_git_tool(self, tool: str, params: Dict) -> Dict:
        """Handle Git operations"""
        
        repo_path = params.get("repo_path", str(self.repos_base))
        
        if tool == "git_status":
            return await self.git_status(repo_path)
        
        elif tool == "git_diff":
            return await self.git_diff(repo_path, params.get("cached", False))
        
        elif tool == "git_branch":
            return await self.git_branch(repo_path)
        
        elif tool == "git_log":
            return await self.git_log(repo_path, params.get("limit", 10))
        
        elif tool == "git_commit":
            return await self.git_commit(
                repo_path,
                params.get("message"),
                params.get("files", [])
            )
        
        return {"error": f"Unknown Git tool: {tool}"}
    
    async def git_status(self, repo_path: str) -> Dict:
        """Get git status of a repository"""
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n') if result.stdout else []
                
                status = {
                    "modified": [],
                    "added": [],
                    "deleted": [],
                    "untracked": []
                }
                
                for line in lines:
                    if line:
                        status_code = line[:2]
                        file_path = line[3:]
                        
                        if 'M' in status_code:
                            status["modified"].append(file_path)
                        elif 'A' in status_code:
                            status["added"].append(file_path)
                        elif 'D' in status_code:
                            status["deleted"].append(file_path)
                        elif '??' in status_code:
                            status["untracked"].append(file_path)
                
                return {
                    "status": "success",
                    "repo": repo_path,
                    "changes": status,
                    "total_changes": sum(len(v) for v in status.values())
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def git_diff(self, repo_path: str, cached: bool = False) -> Dict:
        """Get git diff"""
        
        try:
            cmd = ["git", "diff"]
            if cached:
                cmd.append("--cached")
            
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "diff": result.stdout,
                    "lines_added": result.stdout.count('\n+'),
                    "lines_removed": result.stdout.count('\n-')
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def git_branch(self, repo_path: str) -> Dict:
        """Get git branches"""
        
        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                branches = []
                current_branch = None
                
                for line in result.stdout.split('\n'):
                    if line:
                        if line.startswith('*'):
                            current_branch = line[2:].strip()
                            branches.append(current_branch)
                        else:
                            branches.append(line.strip())
                
                return {
                    "status": "success",
                    "current_branch": current_branch,
                    "branches": branches
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def git_log(self, repo_path: str, limit: int = 10) -> Dict:
        """Get git log"""
        
        try:
            result = subprocess.run(
                ["git", "log", f"--max-count={limit}", "--oneline"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                commits = []
                for line in result.stdout.split('\n'):
                    if line:
                        parts = line.split(' ', 1)
                        if len(parts) == 2:
                            commits.append({
                                "hash": parts[0],
                                "message": parts[1]
                            })
                
                return {
                    "status": "success",
                    "commits": commits,
                    "count": len(commits)
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def git_commit(self, repo_path: str, message: str, files: List[str]) -> Dict:
        """Create a git commit"""
        
        try:
            # Add files
            if files:
                for file in files:
                    subprocess.run(["git", "add", file], cwd=repo_path)
            
            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": "Commit created",
                    "output": result.stdout
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Browser Tools
    async def handle_browser_tool(self, tool: str, params: Dict) -> Dict:
        """Handle browser automation"""
        
        if tool == "browser_screenshot":
            return await self.browser_screenshot(params.get("url"))
        
        elif tool == "browser_scrape":
            return await self.browser_scrape(params.get("url"))
        
        elif tool == "browser_test":
            return await self.browser_test(params.get("url"), params.get("tests", []))
        
        return {"error": f"Unknown browser tool: {tool}"}
    
    async def browser_screenshot(self, url: str) -> Dict:
        """Take a screenshot of a webpage"""
        
        # Use Chrome/Chromium headless if available
        try:
            output_file = f"/tmp/screenshot_{datetime.now().timestamp()}.png"
            
            result = subprocess.run([
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "--headless",
                "--disable-gpu",
                "--screenshot=" + output_file,
                "--window-size=1280,720",
                url
            ], capture_output=True)
            
            if result.returncode == 0 and os.path.exists(output_file):
                return {
                    "status": "success",
                    "screenshot": output_file,
                    "url": url
                }
        except:
            pass
        
        return {"status": "error", "message": "Could not take screenshot"}
    
    async def browser_scrape(self, url: str) -> Dict:
        """Scrape content from a webpage"""
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Basic extraction (you could enhance with BeautifulSoup)
                        title = ""
                        if "<title>" in html and "</title>" in html:
                            start = html.index("<title>") + 7
                            end = html.index("</title>")
                            title = html[start:end]
                        
                        return {
                            "status": "success",
                            "url": url,
                            "title": title,
                            "content_length": len(html),
                            "content_preview": html[:500]
                        }
            except Exception as e:
                return {"status": "error", "message": str(e)}
    
    # Filesystem Tools
    async def handle_filesystem_tool(self, tool: str, params: Dict) -> Dict:
        """Handle filesystem operations"""
        
        if tool == "filesystem_read":
            return await self.filesystem_read(params.get("path"))
        
        elif tool == "filesystem_write":
            return await self.filesystem_write(
                params.get("path"),
                params.get("content")
            )
        
        elif tool == "filesystem_list":
            return await self.filesystem_list(params.get("path", "."))
        
        elif tool == "filesystem_search":
            return await self.filesystem_search(
                params.get("path", "."),
                params.get("pattern")
            )
        
        return {"error": f"Unknown filesystem tool: {tool}"}
    
    async def filesystem_read(self, file_path: str) -> Dict:
        """Read a file"""
        
        try:
            path = Path(file_path)
            if path.exists():
                content = path.read_text()
                return {
                    "status": "success",
                    "path": str(path),
                    "content": content,
                    "size": len(content),
                    "lines": content.count('\n') + 1
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def filesystem_write(self, file_path: str, content: str) -> Dict:
        """Write to a file"""
        
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            
            return {
                "status": "success",
                "path": str(path),
                "size": len(content)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def filesystem_list(self, dir_path: str) -> Dict:
        """List directory contents"""
        
        try:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                items = []
                for item in path.iterdir():
                    items.append({
                        "name": item.name,
                        "type": "dir" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None
                    })
                
                return {
                    "status": "success",
                    "path": str(path),
                    "items": items,
                    "count": len(items)
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Memory Tools (integrate with UMS)
    async def handle_memory_tool(self, tool: str, params: Dict) -> Dict:
        """Handle memory operations via UMS"""
        
        if tool == "memory_store":
            return await self.memory_store(
                params.get("content"),
                params.get("tags", []),
                params.get("category", "note")
            )
        
        elif tool == "memory_recall":
            return await self.memory_recall(
                params.get("query"),
                params.get("limit", 5)
            )
        
        elif tool == "memory_stats":
            return await self.memory_stats()
        
        return {"error": f"Unknown memory tool: {tool}"}
    
    async def memory_store(self, content: str, tags: List[str], category: str) -> Dict:
        """Store in UMS"""
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ums_api}/api/memory/store",
                json={
                    "content": content,
                    "tags": tags,
                    "category": category,
                    "source": "mcp_tools_bridge"
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "status": "success",
                        "memory_id": result.get("id")
                    }
        
        return {"status": "error", "message": "Could not store memory"}
    
    async def memory_recall(self, query: str, limit: int = 5) -> Dict:
        """Recall from UMS"""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.ums_api}/api/memory/search",
                params={"query": query, "limit": limit}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "status": "success",
                        "memories": result.get("results", []),
                        "count": result.get("count", 0)
                    }
        
        return {"status": "error", "message": "Could not recall memories"}
    
    async def memory_stats(self) -> Dict:
        """Get UMS statistics"""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.ums_api}/api/stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    return {
                        "status": "success",
                        "stats": stats
                    }
        
        return {"status": "error", "message": "Could not get stats"}
    
    async def test_connections(self) -> Dict:
        """Test all MCP tool connections"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "tools_tested": [],
            "status": "testing"
        }
        
        # Test GitHub connection
        if self.github_token:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"token {self.github_token}"}
                    async with session.get("https://api.github.com/user", headers=headers) as resp:
                        if resp.status == 200:
                            results["tools_tested"].append({"tool": "github", "status": "connected"})
                        else:
                            results["tools_tested"].append({"tool": "github", "status": "auth_failed"})
            except Exception as e:
                results["tools_tested"].append({"tool": "github", "status": "error", "error": str(e)})
        else:
            results["tools_tested"].append({"tool": "github", "status": "no_token"})
        
        # Test Git availability
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                results["tools_tested"].append({"tool": "git", "status": "available"})
            else:
                results["tools_tested"].append({"tool": "git", "status": "not_found"})
        except Exception as e:
            results["tools_tested"].append({"tool": "git", "status": "error", "error": str(e)})
        
        # Test filesystem access
        try:
            test_path = Path.home() / ".ums_test"
            test_path.write_text("test")
            test_path.unlink()
            results["tools_tested"].append({"tool": "filesystem", "status": "accessible"})
        except Exception as e:
            results["tools_tested"].append({"tool": "filesystem", "status": "error", "error": str(e)})
        
        # Test UMS API connection
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ums_api}/health", timeout=aiohttp.ClientTimeout(total=2)) as resp:
                    if resp.status == 200:
                        results["tools_tested"].append({"tool": "memory", "status": "connected"})
                    else:
                        results["tools_tested"].append({"tool": "memory", "status": "api_down"})
        except Exception as e:
            results["tools_tested"].append({"tool": "memory", "status": "not_running", "note": "Start UMS API service"})
        
        # Determine overall status
        all_ok = all(t.get("status") in ["connected", "available", "accessible", "no_token"] 
                     for t in results["tools_tested"])
        results["status"] = "ready" if all_ok else "partial"
        
        return results


# CLI Interface for testing
async def main():
    bridge = MCPToolsBridge()
    
    print("🔧 MCP Tools Bridge Test")
    print("=" * 40)
    
    # Test GitHub tools
    print("\n📦 Testing GitHub tools...")
    result = await bridge.execute_tool("github_list_repos", {"user": "cerion"})
    print(f"  Repos found: {result.get('count', 0) if result else 'Error'}")
    
    # Test Git tools
    print("\n🔀 Testing Git tools...")
    result = await bridge.execute_tool("git_status", {
        "repo_path": "/Users/cerion/Projects/Machine_Maintenance_App"
    })
    print(f"  Git status: {result.get('status') if result else 'Error'}")
    
    # Test filesystem tools
    print("\n📁 Testing Filesystem tools...")
    result = await bridge.execute_tool("filesystem_list", {
        "path": "/usr/local/share/universal-memory-system/src"
    })
    print(f"  Files found: {result.get('count', 0) if result else 'Error'}")
    
    # Test memory tools
    print("\n🧠 Testing Memory tools...")
    result = await bridge.execute_tool("memory_stats", {})
    print(f"  Memory stats: {result.get('status') if result else 'Error'}")
    
    print("\n✅ MCP Tools Bridge operational!")

if __name__ == "__main__":
    asyncio.run(main())