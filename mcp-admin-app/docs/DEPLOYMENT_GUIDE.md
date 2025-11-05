# MCP Admin Application - Deployment Guide

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Configuration](#configuration)
4. [Security Setup](#security-setup)
5. [Performance Optimization](#performance-optimization)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Backup and Recovery](#backup-and-recovery)
8. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10, macOS 10.14, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **Memory**: 512 MB RAM
- **Storage**: 100 MB free disk space
- **Network**: Internet connection for cloud LLM providers

### Recommended Requirements

- **Operating System**: Windows 11, macOS 12+, or Linux (Ubuntu 20.04+)
- **Python**: 3.10 or higher
- **Memory**: 2 GB RAM
- **Storage**: 1 GB free disk space (for logs and data)
- **Network**: Stable broadband connection

### Hardware Considerations

- **CPU**: Multi-core processor recommended for batch operations
- **Memory**: Additional RAM needed for large tool registries
- **Storage**: SSD recommended for database performance
- **Network**: Low latency connection for real-time tool execution

## Installation Methods

### Method 1: Direct Python Installation

1. **Download the Application**
   ```bash
   git clone <repository-url>
   cd mcp-admin-app
   ```

2. **Verify Python Installation**
   ```bash
   python --version  # Should be 3.8+
   python -c "import tkinter; print('Tkinter available')"
   ```

3. **Run the Application**
   ```bash
   python main.py
   ```

### Method 2: Virtual Environment Installation

1. **Create Virtual Environment**
   ```bash
   python -m venv mcp-admin-env
   
   # Windows
   mcp-admin-env\Scripts\activate
   
   # macOS/Linux
   source mcp-admin-env/bin/activate
   ```

2. **Install Dependencies** (if any future dependencies are added)
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python main.py
   ```

### Method 3: Standalone Executable (Future)

When available, standalone executables will be provided for each platform:

- **Windows**: `mcp-admin-app.exe`
- **macOS**: `MCP Admin App.app`
- **Linux**: `mcp-admin-app` (AppImage)

## Configuration

### Initial Configuration

1. **First Launch Setup**
   - The application creates configuration directories automatically
   - Default settings are applied for immediate use
   - Database schema is initialized

2. **Configuration Directories**
   ```
   # Windows
   %USERPROFILE%\.kiro\mcp-admin\
   
   # macOS/Linux
   ~/.kiro/mcp-admin/
   ```

3. **Directory Structure**
   ```
   .kiro/mcp-admin/
   ├── config/
   │   ├── app-settings.json      # Application settings
   │   ├── servers.json           # MCP server configurations
   │   ├── llm-providers.json     # LLM provider settings
   │   └── notification-channels.json # Notification settings
   ├── data/
   │   ├── admin.db              # SQLite database
   │   └── backups/              # Automated backups
   ├── templates/
   │   └── prompts/              # Prompt templates
   └── logs/
       ├── application.log       # Application logs
       └── error.log            # Error logs
   ```

### Application Settings

Edit `config/app-settings.json` to customize application behavior:

```json
{
  "ui": {
    "theme": "default",
    "window_size": [1200, 800],
    "auto_refresh_interval": 30,
    "show_tooltips": true
  },
  "database": {
    "backup_interval": 3600,
    "max_log_entries": 10000,
    "vacuum_interval": 86400
  },
  "security": {
    "session_timeout": 3600,
    "max_failed_attempts": 5,
    "audit_retention_days": 90
  },
  "performance": {
    "max_concurrent_tools": 10,
    "tool_timeout": 300,
    "batch_size": 50
  }
}
```

### Server Configuration

Configure MCP servers in `config/servers.json`:

```json
{
  "servers": [
    {
      "id": "server-1",
      "name": "Development Server",
      "command": "python",
      "args": ["-m", "mcp_server"],
      "working_directory": "/path/to/server",
      "environment": {
        "MCP_PORT": "8080",
        "MCP_HOST": "localhost"
      },
      "auto_start": true,
      "restart_on_failure": true
    }
  ]
}
```

### LLM Provider Configuration

Configure LLM providers in `config/llm-providers.json`:

```json
{
  "providers": [
    {
      "id": "openai-1",
      "name": "OpenAI GPT-4",
      "type": "openai",
      "api_key_encrypted": "<encrypted-key>",
      "models": [
        {
          "id": "gpt-4",
          "name": "GPT-4",
          "max_tokens": 8192,
          "cost_per_input_token": 0.00003,
          "cost_per_output_token": 0.00006
        }
      ],
      "settings": {
        "temperature": 0.7,
        "max_tokens": 2048,
        "timeout": 30
      }
    }
  ]
}
```

## Security Setup

### API Key Management

1. **Secure Storage**
   - All API keys are encrypted using AES-256
   - Encryption keys derived from system-specific data
   - No plain-text storage of sensitive information

2. **Key Configuration**
   ```bash
   # Use the application UI to add API keys securely
   # Keys are automatically encrypted upon entry
   ```

3. **Key Rotation**
   - Regular key rotation recommended (monthly)
   - Update keys through the LLM Providers interface
   - Old keys are securely overwritten

### Access Control

1. **User Authentication** (if multi-user setup)
   - Configure user accounts and roles
   - Set up authentication providers
   - Enable multi-factor authentication

2. **Tool Permissions**
   - Configure role-based access control
   - Set tool-specific permissions
   - Implement usage quotas

3. **Network Security**
   - Use HTTPS for all external communications
   - Configure firewall rules
   - Implement network segmentation

### Audit and Compliance

1. **Audit Logging**
   - All actions are logged with timestamps
   - User attribution for all operations
   - Tamper-evident log storage

2. **Compliance Settings**
   ```json
   {
     "compliance": {
       "data_retention_days": 2555,  # 7 years
       "audit_log_encryption": true,
       "gdpr_compliance": true,
       "export_user_data": true
     }
   }
   ```

## Performance Optimization

### Database Optimization

1. **SQLite Configuration**
   - Enable WAL mode for better concurrency
   - Regular VACUUM operations
   - Index optimization for large datasets

2. **Database Maintenance**
   ```bash
   # Automatic maintenance is configured by default
   # Manual maintenance can be triggered through the UI
   ```

### Memory Management

1. **Tool Execution**
   - Configure memory limits per tool
   - Implement garbage collection for long-running processes
   - Monitor memory usage patterns

2. **Batch Operations**
   - Optimize batch sizes based on available memory
   - Implement streaming for large datasets
   - Use pagination for UI components

### Network Optimization

1. **Connection Pooling**
   - Reuse connections to LLM providers
   - Configure connection timeouts
   - Implement retry logic with exponential backoff

2. **Caching**
   - Cache tool metadata and schemas
   - Implement response caching for repeated queries
   - Use local caching for frequently accessed data

## Monitoring and Maintenance

### Health Monitoring

1. **System Health Checks**
   - Database connectivity
   - MCP server status
   - LLM provider availability
   - Resource usage monitoring

2. **Performance Metrics**
   - Response times for tool executions
   - Success/failure rates
   - Resource utilization
   - Cost tracking

### Log Management

1. **Log Configuration**
   ```json
   {
     "logging": {
       "level": "INFO",
       "max_file_size": "10MB",
       "backup_count": 5,
       "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
     }
   }
   ```

2. **Log Rotation**
   - Automatic log rotation based on size
   - Configurable retention periods
   - Compressed archive storage

### Maintenance Tasks

1. **Regular Maintenance**
   - Database optimization (weekly)
   - Log cleanup (daily)
   - Configuration backup (daily)
   - Security updates (as needed)

2. **Automated Maintenance**
   ```bash
   # Maintenance tasks are automated by default
   # Custom schedules can be configured in app-settings.json
   ```

## Backup and Recovery

### Backup Strategy

1. **Automated Backups**
   - Configuration files backed up hourly
   - Database backed up daily
   - Full system backup weekly

2. **Backup Locations**
   ```
   ~/.kiro/mcp-admin/data/backups/
   ├── config/           # Configuration backups
   ├── database/         # Database backups
   └── full/            # Full system backups
   ```

3. **Backup Configuration**
   ```json
   {
     "backup": {
       "enabled": true,
       "config_interval": 3600,
       "database_interval": 86400,
       "full_interval": 604800,
       "retention_days": 30,
       "compression": true
     }
   }
   ```

### Recovery Procedures

1. **Configuration Recovery**
   ```bash
   # Restore from backup through the UI
   # Or manually copy files from backup directory
   ```

2. **Database Recovery**
   ```bash
   # Stop the application
   # Replace admin.db with backup copy
   # Restart the application
   ```

3. **Full System Recovery**
   ```bash
   # Complete restoration from full backup
   # Includes all configurations, data, and templates
   ```

### Disaster Recovery

1. **Recovery Planning**
   - Document recovery procedures
   - Test recovery processes regularly
   - Maintain off-site backups

2. **Business Continuity**
   - Identify critical functions
   - Establish recovery time objectives
   - Plan for alternative systems

## Troubleshooting

### Common Deployment Issues

1. **Python Version Issues**
   ```bash
   # Check Python version
   python --version
   
   # Install correct version if needed
   # Use pyenv or conda for version management
   ```

2. **Permission Issues**
   ```bash
   # Ensure write permissions to config directory
   chmod -R 755 ~/.kiro/mcp-admin/
   ```

3. **Network Connectivity**
   ```bash
   # Test connectivity to LLM providers
   curl -I https://api.openai.com/v1/models
   ```

### Performance Issues

1. **Slow Database Operations**
   - Check database size and optimize
   - Rebuild indexes if necessary
   - Consider database migration for large datasets

2. **Memory Issues**
   - Monitor memory usage patterns
   - Adjust batch sizes and limits
   - Implement memory profiling

3. **Network Timeouts**
   - Adjust timeout settings
   - Check network stability
   - Implement retry mechanisms

### Error Diagnosis

1. **Log Analysis**
   ```bash
   # Check application logs
   tail -f ~/.kiro/mcp-admin/logs/application.log
   
   # Check error logs
   tail -f ~/.kiro/mcp-admin/logs/error.log
   ```

2. **Debug Mode**
   ```bash
   # Run with debug logging
   python main.py --debug
   ```

3. **System Information**
   - Collect system information for support
   - Include relevant log excerpts
   - Document reproduction steps

### Getting Support

1. **Self-Service Resources**
   - Check documentation and FAQ
   - Search existing issues
   - Use built-in diagnostic tools

2. **Community Support**
   - GitHub issues for bug reports
   - Community forums for questions
   - Stack Overflow for technical issues

3. **Enterprise Support**
   - Professional support options
   - Priority issue resolution
   - Custom deployment assistance