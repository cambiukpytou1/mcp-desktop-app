# MCP Admin Application - Installation Guide

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Initial Setup](#initial-setup)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Upgrading](#upgrading)
8. [Uninstallation](#uninstallation)

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **Operating System** | Windows 10, macOS 10.14, or Linux (Ubuntu 18.04+) |
| **Python** | 3.8 or higher |
| **Memory** | 512 MB RAM |
| **Storage** | 100 MB free disk space |
| **Network** | Internet connection for LLM providers |

### Recommended Requirements

| Component | Requirement |
|-----------|-------------|
| **Operating System** | Windows 11, macOS 12+, or Linux (Ubuntu 20.04+) |
| **Python** | 3.10 or higher |
| **Memory** | 2 GB RAM |
| **Storage** | 1 GB free disk space |
| **Network** | Stable broadband connection |

### Hardware Considerations

- **CPU**: Multi-core processor recommended for batch operations
- **Memory**: Additional RAM needed for large tool registries and concurrent operations
- **Storage**: SSD recommended for better database performance
- **Network**: Low latency connection for real-time tool execution

## Installation Methods

### Method 1: Direct Python Installation (Recommended)

This is the simplest method for most users.

#### Step 1: Verify Python Installation

```bash
# Check Python version
python --version
# or
python3 --version

# Should output Python 3.8.0 or higher
```

If Python is not installed or the version is too old:

**Windows:**
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer and check "Add Python to PATH"
3. Verify installation: `python --version`

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python

# Or download from python.org
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install python3 python3-pip tkinter
```

#### Step 2: Verify Tkinter

```bash
python -c "import tkinter; print('Tkinter is available')"
```

If Tkinter is not available:

**Windows/macOS:** Tkinter is included with Python
**Linux:** Install the tkinter package:
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# CentOS/RHEL
sudo yum install tkinter
```

#### Step 3: Download and Run

```bash
# Download the application (replace with actual download method)
git clone <repository-url>
cd mcp-admin-app

# Run the application
python main.py
```

### Method 2: Virtual Environment Installation

Recommended for development or when you want to isolate dependencies.

#### Step 1: Create Virtual Environment

```bash
# Create virtual environment
python -m venv mcp-admin-env

# Activate virtual environment
# Windows:
mcp-admin-env\Scripts\activate

# macOS/Linux:
source mcp-admin-env/bin/activate
```

#### Step 2: Install Application

```bash
# Download application
git clone <repository-url>
cd mcp-admin-app

# Install any future dependencies
pip install -r requirements.txt  # (if requirements.txt exists)

# Run application
python main.py
```

#### Step 3: Create Launch Script

**Windows (run.bat):**
```batch
@echo off
cd /d "%~dp0"
mcp-admin-env\Scripts\activate
python main.py
pause
```

**macOS/Linux (run.sh):**
```bash
#!/bin/bash
cd "$(dirname "$0")"
source mcp-admin-env/bin/activate
python main.py
```

Make executable: `chmod +x run.sh`

### Method 3: System-Wide Installation

For system administrators who want to install for all users.

#### Step 1: Install to System Location

```bash
# Create system directory
sudo mkdir -p /opt/mcp-admin-app

# Copy application files
sudo cp -r mcp-admin-app/* /opt/mcp-admin-app/

# Set permissions
sudo chown -R root:root /opt/mcp-admin-app
sudo chmod -R 755 /opt/mcp-admin-app
```

#### Step 2: Create System Launcher

**Linux Desktop Entry (/usr/share/applications/mcp-admin.desktop):**
```ini
[Desktop Entry]
Name=MCP Admin Application
Comment=Manage MCP servers and tools
Exec=python3 /opt/mcp-admin-app/main.py
Icon=/opt/mcp-admin-app/icon.png
Terminal=false
Type=Application
Categories=Development;System;
```

**Windows System Shortcut:**
Create shortcut with target: `python "C:\Program Files\MCP Admin App\main.py"`

### Method 4: Portable Installation

For users who want a portable installation on USB drives or shared systems.

#### Step 1: Create Portable Directory Structure

```
mcp-admin-portable/
├── app/                    # Application files
├── python/                 # Portable Python (optional)
├── config/                 # Configuration override
├── data/                   # Portable data directory
└── run.bat / run.sh        # Launch script
```

#### Step 2: Configure Portable Mode

Set environment variable in launch script:
```bash
export MCP_ADMIN_CONFIG_DIR="$(dirname "$0")/data"
export MCP_ADMIN_PORTABLE=true
```

## Initial Setup

### First Launch

1. **Run the Application**
   ```bash
   python main.py
   ```

2. **Initial Configuration**
   - Application creates configuration directories automatically
   - Default settings are applied
   - SQLite database is initialized

3. **Configuration Directory**
   The application creates the following structure:
   ```
   ~/.kiro/mcp-admin/
   ├── config/
   ├── data/
   ├── templates/
   └── logs/
   ```

### Setup Wizard (Future Feature)

When available, the setup wizard will guide you through:
1. Basic application settings
2. Database configuration
3. Security settings
4. Initial server configuration
5. LLM provider setup

## Configuration

### Basic Configuration

#### Application Settings

Edit `~/.kiro/mcp-admin/config/app-settings.json`:

```json
{
  "ui": {
    "theme": "default",
    "window_size": [1200, 800],
    "auto_refresh_interval": 30
  },
  "performance": {
    "max_concurrent_tools": 10,
    "tool_timeout": 300
  }
}
```

#### Server Configuration

Add your first MCP server in `~/.kiro/mcp-admin/config/servers.json`:

```json
{
  "servers": [
    {
      "id": "server-1",
      "name": "My Development Server",
      "command": "python",
      "args": ["-m", "mcp_server", "--port", "8080"],
      "auto_start": true
    }
  ]
}
```

### Advanced Configuration

#### Environment Variables

Create `.env` file in application directory:

```bash
# Application Settings
MCP_ADMIN_DEBUG=false
MCP_ADMIN_LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///~/.kiro/mcp-admin/data/admin.db

# LLM Providers
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here

# Performance
MAX_CONCURRENT_TOOLS=20
TOOL_TIMEOUT=300
```

#### Security Configuration

Configure security settings in `~/.kiro/mcp-admin/config/security.json`:

```json
{
  "authentication": {
    "session_timeout": 3600,
    "max_failed_attempts": 5
  },
  "encryption": {
    "algorithm": "AES-256-GCM"
  }
}
```

## Verification

### Installation Verification

#### Step 1: Basic Functionality Test

```bash
# Test application startup
python main.py --version

# Test database initialization
python -c "
from data.database import DatabaseManager
db = DatabaseManager()
print('Database connection successful')
"

# Test UI components
python -c "
import tkinter as tk
root = tk.Tk()
root.withdraw()
print('Tkinter GUI available')
root.destroy()
"
```

#### Step 2: Feature Verification

1. **Launch Application**
   ```bash
   python main.py
   ```

2. **Check Core Features**
   - ✅ Application window opens
   - ✅ Navigation sidebar is visible
   - ✅ Database connection established
   - ✅ Configuration files created

3. **Test Server Management**
   - Add a test server configuration
   - Verify server appears in list
   - Test start/stop functionality (if server available)

4. **Test Tool Discovery**
   - Connect to an MCP server
   - Verify tools are discovered and listed
   - Test tool execution (if tools available)

#### Step 3: Performance Verification

```bash
# Test with demo data
python demo.py

# Monitor resource usage
# Windows: Task Manager
# macOS: Activity Monitor
# Linux: htop or top
```

### Health Check Script

Create a health check script (`health_check.py`):

```python
#!/usr/bin/env python3
"""Health check script for MCP Admin Application"""

import sys
import os
import sqlite3
import tkinter as tk
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)")
        return False

def check_tkinter():
    """Check Tkinter availability"""
    try:
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        print("✅ Tkinter available")
        return True
    except Exception as e:
        print(f"❌ Tkinter not available: {e}")
        return False

def check_sqlite():
    """Check SQLite availability"""
    try:
        conn = sqlite3.connect(":memory:")
        conn.close()
        print("✅ SQLite available")
        return True
    except Exception as e:
        print(f"❌ SQLite not available: {e}")
        return False

def check_config_directory():
    """Check configuration directory"""
    config_dir = Path.home() / ".kiro" / "mcp-admin"
    if config_dir.exists():
        print(f"✅ Configuration directory: {config_dir}")
        return True
    else:
        print(f"⚠️  Configuration directory not found: {config_dir}")
        return False

def check_application_files():
    """Check application files"""
    required_files = [
        "main.py",
        "core/app.py",
        "data/database.py",
        "ui/servers_page.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if not missing_files:
        print("✅ All required application files present")
        return True
    else:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False

def main():
    """Run all health checks"""
    print("MCP Admin Application - Health Check")
    print("=" * 40)
    
    checks = [
        check_python_version,
        check_tkinter,
        check_sqlite,
        check_application_files,
        check_config_directory
    ]
    
    results = []
    for check in checks:
        results.append(check())
        print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"Health Check Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All checks passed! Application should work correctly.")
        return 0
    else:
        print("⚠️  Some checks failed. Please address the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

Run health check:
```bash
python health_check.py
```

## Troubleshooting

### Common Installation Issues

#### Issue: Python Not Found

**Symptoms:**
```
'python' is not recognized as an internal or external command
```

**Solutions:**
1. **Windows:** Add Python to PATH during installation
2. **macOS/Linux:** Use `python3` instead of `python`
3. **All platforms:** Reinstall Python with PATH option enabled

#### Issue: Tkinter Not Available

**Symptoms:**
```
ModuleNotFoundError: No module named 'tkinter'
```

**Solutions:**
1. **Linux:** Install tkinter package
   ```bash
   sudo apt install python3-tk  # Ubuntu/Debian
   sudo yum install tkinter      # CentOS/RHEL
   ```
2. **Windows/macOS:** Reinstall Python (Tkinter should be included)

#### Issue: Permission Denied

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/home/user/.kiro'
```

**Solutions:**
1. Check directory permissions:
   ```bash
   ls -la ~/.kiro/
   ```
2. Fix permissions:
   ```bash
   chmod -R 755 ~/.kiro/mcp-admin/
   ```
3. Run as different user if necessary

#### Issue: Database Lock Error

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**
1. Close all application instances
2. Remove lock file:
   ```bash
   rm ~/.kiro/mcp-admin/data/admin.db-wal
   rm ~/.kiro/mcp-admin/data/admin.db-shm
   ```
3. Restart application

#### Issue: Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'core'
```

**Solutions:**
1. Ensure you're running from the application directory:
   ```bash
   cd mcp-admin-app
   python main.py
   ```
2. Check PYTHONPATH:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

### Performance Issues

#### Issue: Slow Startup

**Causes:**
- Large configuration files
- Slow database initialization
- Network connectivity issues

**Solutions:**
1. Check configuration file sizes
2. Optimize database (run VACUUM)
3. Check network connectivity
4. Enable debug mode to identify bottlenecks

#### Issue: High Memory Usage

**Causes:**
- Large tool registries
- Memory leaks in tool execution
- Inefficient caching

**Solutions:**
1. Reduce concurrent tool limits
2. Clear tool execution history
3. Restart application periodically
4. Monitor memory usage patterns

### Network Issues

#### Issue: LLM Provider Connection Failures

**Symptoms:**
```
ConnectionError: Failed to connect to api.openai.com
```

**Solutions:**
1. Check internet connectivity
2. Verify API keys
3. Check firewall settings
4. Test with curl:
   ```bash
   curl -I https://api.openai.com/v1/models
   ```

#### Issue: MCP Server Connection Failures

**Solutions:**
1. Verify server is running
2. Check server configuration
3. Test server connectivity
4. Review server logs

## Upgrading

### Backup Before Upgrading

```bash
# Backup configuration and data
cp -r ~/.kiro/mcp-admin ~/.kiro/mcp-admin-backup-$(date +%Y%m%d)

# Or use built-in backup (when available)
python main.py --backup
```

### Upgrade Process

#### Method 1: In-Place Upgrade

```bash
# Stop application
# Download new version
git pull origin main  # or download new files

# Run upgrade script (when available)
python upgrade.py

# Start application
python main.py
```

#### Method 2: Clean Installation

```bash
# Backup data
cp -r ~/.kiro/mcp-admin/data ~/mcp-admin-data-backup

# Remove old installation
rm -rf mcp-admin-app

# Install new version
git clone <repository-url>
cd mcp-admin-app

# Restore data
cp -r ~/mcp-admin-data-backup ~/.kiro/mcp-admin/data

# Run application
python main.py
```

### Configuration Migration

The application automatically migrates configuration files when needed. Manual migration may be required for major version changes.

## Uninstallation

### Complete Removal

```bash
# Remove application files
rm -rf mcp-admin-app

# Remove configuration and data (optional)
rm -rf ~/.kiro/mcp-admin

# Remove virtual environment (if used)
rm -rf mcp-admin-env

# Remove system shortcuts/launchers (if created)
rm /usr/share/applications/mcp-admin.desktop  # Linux
```

### Partial Removal (Keep Data)

```bash
# Remove only application files
rm -rf mcp-admin-app

# Keep configuration and data in ~/.kiro/mcp-admin/
```

### Data Export Before Removal

```bash
# Export configurations
python main.py --export-config config-backup.json

# Export data (when available)
python main.py --export-data data-backup.json

# Manual backup
tar -czf mcp-admin-backup.tar.gz ~/.kiro/mcp-admin/
```

## Getting Help

### Self-Help Resources

1. **Documentation**: Check the comprehensive documentation in `docs/`
2. **Health Check**: Run the health check script
3. **Debug Mode**: Enable debug logging for detailed information
4. **Log Files**: Check application logs in `~/.kiro/mcp-admin/logs/`

### Community Support

1. **GitHub Issues**: Report bugs and request features
2. **Discussions**: Ask questions and share experiences
3. **Wiki**: Community-maintained documentation and tips

### Professional Support

For enterprise deployments and professional support:
1. **Consulting Services**: Custom deployment and configuration
2. **Priority Support**: Faster issue resolution
3. **Training**: User and administrator training programs

---

**Installation complete!** You're ready to start managing your MCP infrastructure with the enhanced MCP Admin Application.