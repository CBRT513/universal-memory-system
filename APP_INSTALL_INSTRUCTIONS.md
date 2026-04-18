# Universal Memory System - macOS App Installation

## Quick Start

Run the installer to set up the Universal Memory System as a macOS app:

```bash
./install_memory_app.sh
```

This will:
1. Install the app to `/Applications/Universal Memory System.app`
2. Set up a Python virtual environment with all dependencies
3. Create the `memory-cli` command for terminal access
4. Start the Memory System automatically

## Using the App

### Launch from Applications
- Open **Applications** folder
- Double-click **Universal Memory System**
- The app will start the memory service and open the dashboard

### Dashboard Access
Once running, access the dashboard at:
- http://localhost:8091/dashboard

### Command Line Interface
Use the memory CLI from any terminal:
```bash
memory-cli store "Important note about the project"
memory-cli search "project notes"
memory-cli stats
```

### Managing the Service

#### From Terminal:
```bash
# Start the service
open -a "Universal Memory System"

# Or use the app directly
"/Applications/Universal Memory System.app/Contents/MacOS/UniversalMemorySystem" start

# Stop the service
"/Applications/Universal Memory System.app/Contents/MacOS/UniversalMemorySystem" stop

# Check status
"/Applications/Universal Memory System.app/Contents/MacOS/UniversalMemorySystem" status
```

## Features

- **Automatic Startup**: Double-click the app to start the memory service
- **Dashboard**: Web-based interface for managing memories
- **API Access**: RESTful API on port 8091
- **CLI Access**: `memory-cli` command available system-wide
- **Notifications**: System notifications for service status

## File Locations

- **App**: `/Applications/Universal Memory System.app`
- **Data & Config**: `~/Library/Application Support/UniversalMemorySystem/`
- **Logs**: `~/Library/Logs/UniversalMemorySystem/`
- **Database**: `~/Library/Application Support/UniversalMemorySystem/data/memories.db`

## Troubleshooting

### Service Won't Start
1. Check logs: `~/Library/Logs/UniversalMemorySystem/memory_service.log`
2. Ensure port 8091 is not in use: `lsof -i :8091`
3. Verify Python installation: `python3 --version`

### Permission Issues
If you get permission errors:
```bash
# Fix permissions
chmod +x "/Applications/Universal Memory System.app/Contents/MacOS/UniversalMemorySystem"
```

### Reinstalling
To reinstall or update:
```bash
# Run the installer again - it will backup existing installation
./install_memory_app.sh
```

## Uninstalling

To completely remove the Universal Memory System:
```bash
# Stop the service
"/Applications/Universal Memory System.app/Contents/MacOS/UniversalMemorySystem" stop

# Remove the app
rm -rf "/Applications/Universal Memory System.app"

# Remove data and configs (optional - this deletes all memories!)
rm -rf ~/Library/Application\ Support/UniversalMemorySystem
rm -rf ~/Library/Logs/UniversalMemorySystem

# Remove CLI symlink
sudo rm /usr/local/bin/memory-cli
```

## Development Mode

To run in development mode without installing:
```bash
# From the project directory
python3 src/api_service.py --port 8091
```

## Support

For issues or questions, check:
- Logs: `~/Library/Logs/UniversalMemorySystem/`
- Documentation: See CLAUDE.md and README.md
- API Docs: http://localhost:8091/docs (when running)