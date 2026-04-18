#!/usr/bin/env python3
"""
SubAgent Manager - Core library for managing Claude Code SubAgents
"""


# Workspace configuration - automatically detect personal vs work
import sys
from pathlib import Path
sys.path.insert(0, '/usr/local/share/universal-memory-system')
try:
    from workspace_config import config
    # This automatically sets up the right database and port
    import os
    os.environ['MEMORY_API_PORT'] = str(config.api_port)
    os.environ['MEMORY_DB_PATH'] = config.database_path
except ImportError:
    pass  # Fallback to defaults if workspace config not available

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import subprocess
import tempfile

# Add parent directory to path for memory system imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def parse_simple_yaml(content: str) -> Dict:
    """Simple YAML parser for basic key-value pairs"""
    result = {}
    for line in content.split('\n'):
        line = line.strip()
        if line and ':' in line and not line.startswith('#'):
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            result[key] = value
    return result

@dataclass
class SubAgent:
    """Represents a Claude Code SubAgent"""
    name: str
    description: str
    model: str
    instructions: str
    template_path: str
    
    def to_claude_code_format(self) -> str:
        """Convert to Claude Code subagent format"""
        return f"""---
name: {self.name}
description: {self.description}
model: {self.model}
---
{self.instructions}"""

class SubAgentManager:
    """Manages Claude Code SubAgents"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize SubAgent Manager"""
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.templates_dir = self.base_dir / "templates"
        self.configs_dir = self.base_dir / "configs"
        self.output_dir = self.base_dir / "output"
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)
        
        # Load configurations
        self.models_config = self._load_json_config("models.json")
        self.performance_config = self._load_json_config("performance.json")
        
    def _load_json_config(self, filename: str) -> Dict:
        """Load JSON configuration file"""
        config_path = self.configs_dir / filename
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _parse_yaml_template(self, template_path: Path) -> SubAgent:
        """Parse a YAML template file"""
        with open(template_path, 'r') as f:
            content = f.read()
            
        # Split on the YAML delimiter
        parts = content.split('---')
        
        # Parse YAML frontmatter
        yaml_content = parts[1].strip() if len(parts) > 1 else ""
        instructions = parts[2].strip() if len(parts) > 2 else ""
        
        # Parse YAML
        metadata = parse_simple_yaml(yaml_content) if yaml_content else {}
        
        return SubAgent(
            name=metadata.get('name', template_path.stem),
            description=metadata.get('description', ''),
            model=metadata.get('model', 'sonnet'),
            instructions=instructions,
            template_path=str(template_path)
        )
    
    def list_templates(self) -> List[SubAgent]:
        """List all available subagent templates"""
        templates = []
        for template_file in self.templates_dir.glob("*.yaml"):
            try:
                agent = self._parse_yaml_template(template_file)
                templates.append(agent)
            except Exception as e:
                print(f"Error loading template {template_file}: {e}")
        return templates
    
    def get_template(self, name: str) -> Optional[SubAgent]:
        """Get a specific template by name"""
        template_path = self.templates_dir / f"{name}.yaml"
        if template_path.exists():
            return self._parse_yaml_template(template_path)
        return None
    
    def create_subagent_file(self, name: str, output_path: Optional[Path] = None) -> Path:
        """Create a Claude Code subagent file"""
        agent = self.get_template(name)
        if not agent:
            raise ValueError(f"Template '{name}' not found")
        
        # Determine output path
        if not output_path:
            output_path = self.output_dir / f"{name}.md"
        
        # Write subagent file
        with open(output_path, 'w') as f:
            f.write(agent.to_claude_code_format())
        
        return output_path
    
    def create_all_subagents(self) -> List[Path]:
        """Create all subagent files from templates"""
        created_files = []
        for agent in self.list_templates():
            try:
                output_path = self.create_subagent_file(agent.name)
                created_files.append(output_path)
                print(f"Created: {output_path}")
            except Exception as e:
                print(f"Error creating {agent.name}: {e}")
        return created_files
    
    def recommend_model(self, task_type: str) -> str:
        """Recommend a model based on task type"""
        models = self.models_config.get('models', {})
        
        # Find recommended model for task
        for model_key, model_info in models.items():
            if task_type.lower() in [t.lower() for t in model_info.get('recommended_for', [])]:
                return model_key
        
        # Return default model
        return self.models_config.get('default_model', 'sonnet')
    
    def get_model_info(self, model_name: str) -> Dict:
        """Get information about a specific model"""
        models = self.models_config.get('models', {})
        return models.get(model_name, {})
    
    def optimize_for_performance(self, agent_name: str) -> Dict[str, Any]:
        """Get performance optimization settings for an agent"""
        perf = self.performance_config.get('performance', {})
        
        # Determine optimization based on agent type
        optimizations = {
            'parallel_execution': perf.get('parallel_execution', {}).get('enabled', True),
            'caching': perf.get('caching', {}).get('enabled', True),
            'stream_responses': perf.get('optimization', {}).get('stream_responses', True),
            'batch_processing': perf.get('optimization', {}).get('batch_processing', True)
        }
        
        return optimizations
    
    def integrate_with_memory_system(self, agent_name: str, task: str, result: str):
        """Integrate subagent results with the memory system"""
        try:
            from src.memory_cli import MemoryCLI
            
            cli = MemoryCLI()
            
            # Store the result in memory
            memory_content = f"""
SubAgent: {agent_name}
Task: {task}
Result: {result}
Timestamp: {datetime.now().isoformat()}
"""
            
            cli.store_memory(
                content=memory_content,
                category="subagent_result",
                tags=[f"subagent-{agent_name}", "automation", "claude-code"],
                importance=7
            )
            
            print(f"Result stored in memory system for {agent_name}")
            
        except ImportError:
            print("Memory system integration not available")
        except Exception as e:
            print(f"Error integrating with memory system: {e}")
    
    def execute_subagent(self, agent_name: str, task: str, integrate_memory: bool = True) -> str:
        """Execute a subagent with a specific task"""
        agent = self.get_template(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        # Create temporary file with subagent
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(agent.to_claude_code_format())
            temp_path = f.name
        
        try:
            # Prepare Claude Code command
            cmd = [
                "claude-code",
                "--subagent", temp_path,
                "--task", task
            ]
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            output = result.stdout
            
            # Store in memory if requested
            if integrate_memory:
                self.integrate_with_memory_system(agent_name, task, output)
            
            return output
            
        except subprocess.TimeoutExpired:
            return "Subagent execution timed out"
        except FileNotFoundError:
            return "Claude Code CLI not found. Please ensure it's installed and in PATH"
        except Exception as e:
            return f"Error executing subagent: {e}"
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def create_custom_subagent(self, name: str, description: str, 
                              instructions: str, model: str = "sonnet") -> Path:
        """Create a custom subagent template"""
        template_path = self.templates_dir / f"{name}.yaml"
        
        content = f"""---
name: {name}
description: {description}
model: {model}
---
{instructions}"""
        
        with open(template_path, 'w') as f:
            f.write(content)
        
        print(f"Created custom subagent template: {template_path}")
        return template_path

if __name__ == "__main__":
    # Test the manager
    manager = SubAgentManager()
    
    print("Available SubAgent Templates:")
    for agent in manager.list_templates():
        print(f"  - {agent.name}: {agent.description}")
    
    print("\nCreating all subagent files...")
    created = manager.create_all_subagents()
    print(f"Created {len(created)} subagent files in {manager.output_dir}")