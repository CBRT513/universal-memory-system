#!/usr/bin/env python3
"""
Apply workspace awareness to all existing tools
This adds workspace detection to the top of each tool
"""

import os
import sys
from pathlib import Path

# The import line to add to all tools
WORKSPACE_IMPORT = """
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
"""

def patch_file(filepath: Path):
    """Add workspace detection to a Python file"""
    
    content = filepath.read_text()
    
    # Skip if already patched
    if 'workspace_config import config' in content:
        print(f"  ✓ Already patched: {filepath.name}")
        return False
    
    # Find the right place to insert (after initial imports)
    lines = content.split('\n')
    
    # Find where to insert (after docstring and initial imports)
    insert_line = 0
    in_docstring = False
    for i, line in enumerate(lines):
        if i == 0 and line.startswith('#!'):
            continue
        if '"""' in line or "'''" in line:
            in_docstring = not in_docstring
            continue
        if not in_docstring and line.strip() and not line.startswith('#'):
            insert_line = i
            break
    
    # Insert our import
    lines.insert(insert_line, WORKSPACE_IMPORT)
    
    # Write back
    filepath.write_text('\n'.join(lines))
    print(f"  ✓ Patched: {filepath.name}")
    return True

def main():
    base = Path('/usr/local/share/universal-memory-system')
    
    # Files to patch
    files_to_patch = [
        base / 'src' / 'memory_cli.py',
        base / 'src' / 'api_service.py',
        base / 'src' / 'memory_service.py',
        base / 'src' / 'ai_context_generator.py',
        base / 'subagents' / 'cli' / 'subagent_cli.py',
        base / 'subagents' / 'lib' / 'subagent_manager.py',
    ]
    
    print("Applying workspace patches...")
    patched = 0
    
    for filepath in files_to_patch:
        if filepath.exists():
            if patch_file(filepath):
                patched += 1
        else:
            print(f"  ✗ Not found: {filepath.name}")
    
    print(f"\nPatched {patched} files")
    print("\nAll tools will now automatically use the correct workspace!")

if __name__ == "__main__":
    main()