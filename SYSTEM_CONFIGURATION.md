# System Configuration Guide for Development

## Sudo Timeout Configuration

### Overview
The default sudo timeout on macOS and Linux is 5 minutes. For development environments where frequent sudo commands are needed (installing packages, modifying system files, running services), this can become tedious. You can extend this timeout to reduce authentication prompts.

### Configuration Steps

#### 1. Single User Configuration
```bash
# Extend timeout to 60 minutes for current user
echo "Defaults:$(whoami) timestamp_timeout=60" | sudo tee /etc/sudoers.d/$(whoami)-timeout
sudo chmod 440 /etc/sudoers.d/$(whoami)-timeout
```

#### 2. Multiple Users Configuration
```bash
# For specific users (example: cerion and Equillabs)
echo "Defaults:cerion timestamp_timeout=60" | sudo tee /etc/sudoers.d/cerion-timeout
echo "Defaults:Equillabs timestamp_timeout=60" | sudo tee /etc/sudoers.d/equillabs-timeout

# Set proper permissions
sudo chmod 440 /etc/sudoers.d/*-timeout
```

#### 3. Verification
```bash
# Check sudoers syntax for errors
sudo visudo -c

# Expected output:
# /etc/sudoers: parsed OK
# /private/etc/sudoers.d/username-timeout: parsed OK
```

### Use Cases in Development

#### Universal Memory System
- Installing Python packages with pip
- Starting/stopping services on privileged ports
- Modifying system configuration files
- Installing global capture components

#### AgentForge
- Running tests that require elevated privileges
- Installing system dependencies
- Managing service daemons
- Port binding for development servers

#### CBRT UI
- Installing npm packages globally
- Running build scripts that modify system directories
- Managing Firebase emulators
- Deploying to local test environments

### Security Considerations

⚠️ **Important Security Notes:**

1. **Development Only**: This configuration should ONLY be used in development environments
2. **Production Systems**: Never apply this to production servers
3. **Shared Systems**: Be cautious on shared development machines
4. **Default Timeout**: The default 5-minute timeout exists for security reasons
5. **Review Regularly**: Periodically review and audit sudoers configurations

### Timeout Options

```bash
# Common timeout values
timestamp_timeout=0     # Always require password
timestamp_timeout=5     # Default (5 minutes)
timestamp_timeout=15    # Moderate extension
timestamp_timeout=60    # Development convenience
timestamp_timeout=-1    # Never timeout (NOT RECOMMENDED)
```

### Removing Configuration

If you need to remove the extended timeout:

```bash
# Remove specific user configuration
sudo rm /etc/sudoers.d/username-timeout

# Or reset to default
echo "Defaults:username timestamp_timeout=5" | sudo tee /etc/sudoers.d/username-timeout
sudo chmod 440 /etc/sudoers.d/username-timeout
```

### Troubleshooting

#### Common Issues

1. **"bad permissions" error**
   ```bash
   # Fix permissions
   sudo chmod 440 /etc/sudoers.d/your-file
   ```

2. **Syntax errors in sudoers**
   ```bash
   # Always validate before applying
   sudo visudo -c
   ```

3. **Configuration not taking effect**
   ```bash
   # Start a new terminal session or run
   sudo -k  # Clear sudo timestamp
   ```

### Best Practices

1. **Use separate files**: Store custom configurations in `/etc/sudoers.d/` instead of editing main sudoers file
2. **Always validate**: Run `sudo visudo -c` after any changes
3. **Document changes**: Keep track of custom configurations
4. **Use descriptive names**: Name files clearly (e.g., `developer-timeout` instead of `custom`)
5. **Regular audits**: Review sudoers configurations periodically

### Integration with Development Tools

#### Claude Code / Cursor / AI Assistants
When using AI coding assistants that may need to run sudo commands:
- Reduces interruptions during automated tasks
- Allows smoother execution of system-level operations
- Prevents timeout during long-running operations

#### Docker/Container Development
- Installing Docker components
- Managing container networks
- Accessing privileged container features

#### System Service Development
- Starting/stopping daemons
- Modifying system service configurations
- Testing service installations

---

*Last Updated: 2025-08-15*
*Configuration tested on: macOS 14.x, Ubuntu 22.04, Debian 12*