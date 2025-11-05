# MCP Admin Application - Configuration Reference

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Application Settings](#application-settings)
3. [Server Configuration](#server-configuration)
4. [LLM Provider Configuration](#llm-provider-configuration)
5. [Tool Configuration](#tool-configuration)
6. [Security Configuration](#security-configuration)
7. [Performance Configuration](#performance-configuration)
8. [Logging Configuration](#logging-configuration)
9. [Database Configuration](#database-configuration)
10. [Environment Variables](#environment-variables)

## Configuration Overview

The MCP Admin Application uses a hierarchical configuration system with multiple configuration files stored in the user's configuration directory. Configuration files are in JSON format and support environment variable substitution.

### Configuration Directory Structure

```
~/.kiro/mcp-admin/
├── config/
│   ├── app-settings.json          # Main application settings
│   ├── servers.json               # MCP server configurations
│   ├── llm-providers.json         # LLM provider settings
│   ├── tools.json                 # Tool-specific configurations
│   ├── security.json              # Security policies and settings
│   ├── performance.json           # Performance tuning parameters
│   ├── logging.json               # Logging configuration
│   └── notification-channels.json # Notification settings
├── data/
│   └── admin.db                   # SQLite database
├── templates/
│   └── prompts/                   # Prompt templates
└── logs/
    ├── application.log            # Application logs
    └── error.log                  # Error logs
```

### Configuration Loading Order

1. Default configuration (built-in)
2. System-wide configuration (if exists)
3. User configuration files
4. Environment variables (override)
5. Command-line arguments (highest priority)

### Environment Variable Substitution

Configuration files support environment variable substitution using the `${VAR_NAME}` syntax:

```json
{
  "database": {
    "connection_string": "${DATABASE_URL:sqlite:///~/.kiro/mcp-admin/data/admin.db}"
  }
}
```

## Application Settings

### app-settings.json

Main application configuration file containing UI, database, security, and performance settings.

```json
{
  "application": {
    "name": "MCP Admin Application",
    "version": "1.0.0",
    "environment": "production",
    "debug_mode": false,
    "auto_update": true
  },
  "ui": {
    "theme": "default",
    "window_size": [1200, 800],
    "window_position": [100, 100],
    "auto_refresh_interval": 30,
    "show_tooltips": true,
    "enable_animations": true,
    "font_size": 12,
    "color_scheme": {
      "primary": "#1a73e8",
      "secondary": "#34a853",
      "error": "#d93025",
      "warning": "#fbbc04",
      "background": "#ffffff",
      "text": "#202124"
    }
  },
  "database": {
    "type": "sqlite",
    "connection_string": "sqlite:///~/.kiro/mcp-admin/data/admin.db",
    "backup_interval": 3600,
    "max_log_entries": 10000,
    "vacuum_interval": 86400,
    "connection_pool_size": 10,
    "query_timeout": 30
  },
  "security": {
    "session_timeout": 3600,
    "max_failed_attempts": 5,
    "lockout_duration": 900,
    "password_policy": {
      "min_length": 8,
      "require_uppercase": true,
      "require_lowercase": true,
      "require_numbers": true,
      "require_special_chars": true
    },
    "audit_retention_days": 90,
    "encryption_algorithm": "AES-256-GCM",
    "key_derivation_iterations": 100000
  },
  "performance": {
    "max_concurrent_tools": 10,
    "tool_timeout": 300,
    "batch_size": 50,
    "cache_size_mb": 256,
    "gc_interval": 300,
    "thread_pool_size": 20
  },
  "features": {
    "tool_discovery": true,
    "workflow_engine": true,
    "batch_operations": true,
    "llm_integration": true,
    "analytics": true,
    "audit_logging": true,
    "backup_restore": true
  },
  "limits": {
    "max_tools_per_server": 1000,
    "max_workflow_steps": 100,
    "max_batch_items": 1000,
    "max_file_size_mb": 100,
    "max_execution_time": 3600
  }
}
```

### Configuration Field Descriptions

#### Application Section
- `name`: Application display name
- `version`: Current application version
- `environment`: Deployment environment (development, staging, production)
- `debug_mode`: Enable debug logging and features
- `auto_update`: Enable automatic updates

#### UI Section
- `theme`: UI theme name (default, dark, light)
- `window_size`: Default window dimensions [width, height]
- `window_position`: Default window position [x, y]
- `auto_refresh_interval`: Automatic refresh interval in seconds
- `show_tooltips`: Enable UI tooltips
- `enable_animations`: Enable UI animations
- `font_size`: Default font size
- `color_scheme`: UI color configuration

#### Database Section
- `type`: Database type (sqlite, postgresql, mysql)
- `connection_string`: Database connection string
- `backup_interval`: Automatic backup interval in seconds
- `max_log_entries`: Maximum log entries before cleanup
- `vacuum_interval`: Database vacuum interval in seconds
- `connection_pool_size`: Database connection pool size
- `query_timeout`: Query timeout in seconds

#### Security Section
- `session_timeout`: User session timeout in seconds
- `max_failed_attempts`: Maximum failed login attempts
- `lockout_duration`: Account lockout duration in seconds
- `password_policy`: Password complexity requirements
- `audit_retention_days`: Audit log retention period
- `encryption_algorithm`: Encryption algorithm for sensitive data
- `key_derivation_iterations`: PBKDF2 iteration count

#### Performance Section
- `max_concurrent_tools`: Maximum concurrent tool executions
- `tool_timeout`: Default tool execution timeout
- `batch_size`: Default batch operation size
- `cache_size_mb`: Memory cache size in MB
- `gc_interval`: Garbage collection interval in seconds
- `thread_pool_size`: Thread pool size for concurrent operations

## Server Configuration

### servers.json

Configuration for MCP servers managed by the application.

```json
{
  "servers": [
    {
      "id": "server-1",
      "name": "Development Server",
      "description": "Local development MCP server",
      "command": "python",
      "args": ["-m", "mcp_server", "--port", "8080"],
      "working_directory": "/path/to/server",
      "environment": {
        "MCP_PORT": "8080",
        "MCP_HOST": "localhost",
        "DEBUG": "true"
      },
      "auto_start": true,
      "restart_on_failure": true,
      "max_restart_attempts": 3,
      "restart_delay": 5,
      "health_check": {
        "enabled": true,
        "interval": 30,
        "timeout": 10,
        "endpoint": "http://localhost:8080/health"
      },
      "logging": {
        "level": "INFO",
        "file": "~/.kiro/mcp-admin/logs/server-1.log",
        "max_size_mb": 10,
        "backup_count": 5
      },
      "security": {
        "authentication": {
          "type": "api_key",
          "api_key": "${SERVER_1_API_KEY}"
        },
        "tls": {
          "enabled": false,
          "cert_file": "",
          "key_file": ""
        }
      },
      "resource_limits": {
        "memory_mb": 512,
        "cpu_percent": 50,
        "disk_mb": 1024
      }
    }
  ],
  "global_settings": {
    "discovery_interval": 60,
    "connection_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 5
  }
}
```

### Server Configuration Fields

#### Basic Settings
- `id`: Unique server identifier
- `name`: Human-readable server name
- `description`: Server description
- `command`: Executable command to start the server
- `args`: Command-line arguments array
- `working_directory`: Server working directory
- `environment`: Environment variables for the server

#### Lifecycle Management
- `auto_start`: Start server automatically on application startup
- `restart_on_failure`: Restart server if it fails
- `max_restart_attempts`: Maximum restart attempts
- `restart_delay`: Delay between restart attempts in seconds

#### Health Monitoring
- `health_check.enabled`: Enable health checking
- `health_check.interval`: Health check interval in seconds
- `health_check.timeout`: Health check timeout in seconds
- `health_check.endpoint`: Health check endpoint URL

#### Logging
- `logging.level`: Log level (DEBUG, INFO, WARN, ERROR)
- `logging.file`: Log file path
- `logging.max_size_mb`: Maximum log file size in MB
- `logging.backup_count`: Number of backup log files

#### Security
- `security.authentication.type`: Authentication type (none, api_key, oauth)
- `security.authentication.api_key`: API key for authentication
- `security.tls.enabled`: Enable TLS encryption
- `security.tls.cert_file`: TLS certificate file path
- `security.tls.key_file`: TLS private key file path

#### Resource Limits
- `resource_limits.memory_mb`: Memory limit in MB
- `resource_limits.cpu_percent`: CPU usage limit percentage
- `resource_limits.disk_mb`: Disk usage limit in MB

## LLM Provider Configuration

### llm-providers.json

Configuration for LLM providers and models.

```json
{
  "providers": [
    {
      "id": "openai-1",
      "name": "OpenAI GPT-4",
      "type": "openai",
      "enabled": true,
      "api_key_encrypted": "<encrypted-api-key>",
      "endpoint_url": "https://api.openai.com/v1",
      "organization_id": "${OPENAI_ORG_ID}",
      "models": [
        {
          "id": "gpt-4",
          "name": "GPT-4",
          "display_name": "GPT-4 (8K context)",
          "max_tokens": 8192,
          "context_window": 8192,
          "input_cost_per_token": 0.00003,
          "output_cost_per_token": 0.00006,
          "supports_streaming": true,
          "supports_functions": true,
          "tokenizer_type": "cl100k_base"
        },
        {
          "id": "gpt-3.5-turbo",
          "name": "GPT-3.5 Turbo",
          "display_name": "GPT-3.5 Turbo (4K context)",
          "max_tokens": 4096,
          "context_window": 4096,
          "input_cost_per_token": 0.0000015,
          "output_cost_per_token": 0.000002,
          "supports_streaming": true,
          "supports_functions": true,
          "tokenizer_type": "cl100k_base"
        }
      ],
      "default_settings": {
        "temperature": 0.7,
        "max_tokens": 2048,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
      },
      "rate_limits": {
        "requests_per_minute": 3500,
        "tokens_per_minute": 90000,
        "requests_per_day": 10000
      },
      "retry_policy": {
        "max_attempts": 3,
        "initial_delay": 1,
        "max_delay": 60,
        "exponential_base": 2
      },
      "timeout": 30,
      "connection_pool_size": 10
    },
    {
      "id": "anthropic-1",
      "name": "Anthropic Claude",
      "type": "anthropic",
      "enabled": true,
      "api_key_encrypted": "<encrypted-api-key>",
      "endpoint_url": "https://api.anthropic.com/v1",
      "models": [
        {
          "id": "claude-3-opus-20240229",
          "name": "Claude 3 Opus",
          "display_name": "Claude 3 Opus",
          "max_tokens": 4096,
          "context_window": 200000,
          "input_cost_per_token": 0.000015,
          "output_cost_per_token": 0.000075,
          "supports_streaming": true,
          "supports_functions": false,
          "tokenizer_type": "claude"
        }
      ],
      "default_settings": {
        "temperature": 0.7,
        "max_tokens": 2048,
        "top_p": 1.0
      }
    },
    {
      "id": "ollama-1",
      "name": "Local Ollama",
      "type": "ollama",
      "enabled": true,
      "endpoint_url": "http://localhost:11434",
      "models": [
        {
          "id": "llama2:7b",
          "name": "Llama 2 7B",
          "display_name": "Llama 2 7B (Local)",
          "max_tokens": 4096,
          "context_window": 4096,
          "input_cost_per_token": 0.0,
          "output_cost_per_token": 0.0,
          "supports_streaming": true,
          "supports_functions": false,
          "tokenizer_type": "llama"
        }
      ],
      "connection_timeout": 60,
      "read_timeout": 300
    }
  ],
  "global_settings": {
    "default_provider": "openai-1",
    "token_counting_cache_size": 1000,
    "cost_tracking_enabled": true,
    "usage_analytics_enabled": true,
    "budget_alerts": {
      "enabled": true,
      "daily_limit": 100.0,
      "monthly_limit": 1000.0,
      "alert_thresholds": [0.8, 0.9, 0.95]
    }
  }
}
```

### LLM Provider Configuration Fields

#### Provider Settings
- `id`: Unique provider identifier
- `name`: Provider display name
- `type`: Provider type (openai, anthropic, azure, google, ollama, custom)
- `enabled`: Enable/disable the provider
- `api_key_encrypted`: Encrypted API key
- `endpoint_url`: API endpoint URL
- `organization_id`: Organization ID (if applicable)

#### Model Configuration
- `models`: Array of available models
- `id`: Model identifier
- `name`: Model name
- `display_name`: Human-readable model name
- `max_tokens`: Maximum tokens per request
- `context_window`: Model context window size
- `input_cost_per_token`: Cost per input token
- `output_cost_per_token`: Cost per output token
- `supports_streaming`: Streaming support flag
- `supports_functions`: Function calling support flag
- `tokenizer_type`: Tokenizer type for accurate counting

#### Default Settings
- `temperature`: Default temperature setting
- `max_tokens`: Default maximum tokens
- `top_p`: Default top-p setting
- `frequency_penalty`: Default frequency penalty
- `presence_penalty`: Default presence penalty

#### Rate Limits and Policies
- `rate_limits`: Provider-specific rate limits
- `retry_policy`: Retry configuration for failed requests
- `timeout`: Request timeout in seconds
- `connection_pool_size`: HTTP connection pool size

## Tool Configuration

### tools.json

Tool-specific configuration and overrides.

```json
{
  "tool_defaults": {
    "timeout": 300,
    "retry_count": 3,
    "memory_limit_mb": 256,
    "cpu_limit_percent": 25,
    "sandbox_enabled": true,
    "logging_enabled": true,
    "cache_results": false
  },
  "tool_overrides": {
    "file_reader": {
      "timeout": 60,
      "memory_limit_mb": 128,
      "allowed_extensions": [".txt", ".json", ".csv", ".xml"],
      "max_file_size_mb": 10,
      "default_parameters": {
        "encoding": "utf-8"
      }
    },
    "web_scraper": {
      "timeout": 120,
      "memory_limit_mb": 512,
      "rate_limit_requests_per_minute": 60,
      "allowed_domains": ["example.com", "api.example.com"],
      "user_agent": "MCP-Admin/1.0",
      "default_parameters": {
        "follow_redirects": true,
        "max_redirects": 5
      }
    },
    "data_processor": {
      "timeout": 600,
      "memory_limit_mb": 1024,
      "cpu_limit_percent": 50,
      "cache_results": true,
      "cache_ttl": 3600
    }
  },
  "categories": {
    "file_operations": {
      "display_name": "File Operations",
      "description": "Tools for file system operations",
      "icon": "file",
      "color": "#4285f4"
    },
    "web_search": {
      "display_name": "Web Search",
      "description": "Tools for web searching and scraping",
      "icon": "search",
      "color": "#34a853"
    },
    "data_processing": {
      "display_name": "Data Processing",
      "description": "Tools for data transformation and analysis",
      "icon": "analytics",
      "color": "#fbbc04"
    },
    "communication": {
      "display_name": "Communication",
      "description": "Tools for messaging and notifications",
      "icon": "message",
      "color": "#ea4335"
    }
  },
  "permissions": {
    "default_policy": "restricted",
    "roles": {
      "admin": {
        "can_execute_all": true,
        "can_configure": true,
        "can_delete": true,
        "can_view_logs": true
      },
      "user": {
        "can_execute_all": false,
        "can_configure": false,
        "can_delete": false,
        "can_view_logs": false,
        "allowed_categories": ["file_operations", "data_processing"]
      },
      "viewer": {
        "can_execute_all": false,
        "can_configure": false,
        "can_delete": false,
        "can_view_logs": false,
        "allowed_tools": ["file_reader", "data_viewer"]
      }
    }
  }
}
```

## Security Configuration

### security.json

Security policies and authentication settings.

```json
{
  "authentication": {
    "methods": ["local", "ldap", "oauth2"],
    "default_method": "local",
    "session_timeout": 3600,
    "remember_me_duration": 2592000,
    "max_concurrent_sessions": 5,
    "local": {
      "password_policy": {
        "min_length": 8,
        "max_length": 128,
        "require_uppercase": true,
        "require_lowercase": true,
        "require_numbers": true,
        "require_special_chars": true,
        "forbidden_passwords": ["password", "123456", "admin"]
      },
      "lockout_policy": {
        "max_failed_attempts": 5,
        "lockout_duration": 900,
        "reset_failed_attempts_after": 3600
      }
    },
    "ldap": {
      "server_url": "ldap://ldap.example.com:389",
      "bind_dn": "cn=admin,dc=example,dc=com",
      "bind_password": "${LDAP_BIND_PASSWORD}",
      "user_search_base": "ou=users,dc=example,dc=com",
      "user_search_filter": "(uid={username})",
      "group_search_base": "ou=groups,dc=example,dc=com",
      "group_search_filter": "(member={user_dn})"
    },
    "oauth2": {
      "providers": [
        {
          "name": "google",
          "client_id": "${GOOGLE_CLIENT_ID}",
          "client_secret": "${GOOGLE_CLIENT_SECRET}",
          "authorization_url": "https://accounts.google.com/o/oauth2/auth",
          "token_url": "https://oauth2.googleapis.com/token",
          "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
          "scopes": ["openid", "email", "profile"]
        }
      ]
    }
  },
  "authorization": {
    "rbac_enabled": true,
    "default_role": "viewer",
    "role_hierarchy": {
      "admin": ["user", "viewer"],
      "user": ["viewer"]
    }
  },
  "encryption": {
    "algorithm": "AES-256-GCM",
    "key_derivation": {
      "algorithm": "PBKDF2",
      "iterations": 100000,
      "salt_length": 32
    },
    "at_rest": {
      "enabled": true,
      "key_rotation_days": 90
    },
    "in_transit": {
      "tls_version": "1.3",
      "cipher_suites": [
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "TLS_AES_128_GCM_SHA256"
      ]
    }
  },
  "audit": {
    "enabled": true,
    "log_all_requests": true,
    "log_sensitive_data": false,
    "retention_days": 90,
    "export_format": "json",
    "events": {
      "authentication": true,
      "authorization": true,
      "tool_execution": true,
      "configuration_changes": true,
      "data_access": true
    }
  },
  "security_policies": {
    "tool_execution": {
      "sandbox_required": true,
      "resource_limits_enforced": true,
      "network_access_restricted": true,
      "file_system_access_restricted": true
    },
    "data_handling": {
      "encrypt_sensitive_data": true,
      "mask_sensitive_logs": true,
      "data_retention_days": 365,
      "secure_deletion": true
    },
    "api_security": {
      "rate_limiting_enabled": true,
      "cors_enabled": true,
      "allowed_origins": ["https://admin.example.com"],
      "api_key_required": true
    }
  }
}
```

## Performance Configuration

### performance.json

Performance tuning and optimization settings.

```json
{
  "execution": {
    "max_concurrent_tools": 20,
    "max_concurrent_workflows": 5,
    "max_concurrent_batches": 3,
    "thread_pool_size": 50,
    "queue_size": 1000,
    "timeout_default": 300,
    "timeout_max": 3600
  },
  "memory": {
    "heap_size_mb": 2048,
    "cache_size_mb": 512,
    "gc_threshold_mb": 1024,
    "gc_interval_seconds": 300,
    "memory_limit_per_tool_mb": 256,
    "memory_monitoring_enabled": true
  },
  "database": {
    "connection_pool_size": 20,
    "connection_timeout": 30,
    "query_timeout": 60,
    "batch_size": 1000,
    "vacuum_interval_hours": 24,
    "analyze_interval_hours": 6,
    "wal_mode": true,
    "synchronous": "NORMAL"
  },
  "caching": {
    "enabled": true,
    "tool_metadata_ttl": 3600,
    "execution_results_ttl": 1800,
    "provider_info_ttl": 7200,
    "max_cache_entries": 10000,
    "cache_cleanup_interval": 300
  },
  "network": {
    "connection_pool_size": 100,
    "connection_timeout": 30,
    "read_timeout": 60,
    "max_retries": 3,
    "retry_delay": 1,
    "keep_alive": true,
    "compression_enabled": true
  },
  "monitoring": {
    "metrics_collection_interval": 60,
    "performance_logging_enabled": true,
    "slow_query_threshold": 5,
    "resource_monitoring_enabled": true,
    "alert_thresholds": {
      "cpu_percent": 80,
      "memory_percent": 85,
      "disk_percent": 90,
      "response_time_ms": 5000
    }
  }
}
```

## Logging Configuration

### logging.json

Logging configuration for different components.

```json
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "standard": {
      "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
      "datefmt": "%Y-%m-%d %H:%M:%S"
    },
    "detailed": {
      "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(funcName)s(): %(message)s",
      "datefmt": "%Y-%m-%d %H:%M:%S"
    },
    "json": {
      "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
      "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
    }
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "level": "INFO",
      "formatter": "standard",
      "stream": "ext://sys.stdout"
    },
    "file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "DEBUG",
      "formatter": "detailed",
      "filename": "~/.kiro/mcp-admin/logs/application.log",
      "maxBytes": 10485760,
      "backupCount": 5
    },
    "error_file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "ERROR",
      "formatter": "detailed",
      "filename": "~/.kiro/mcp-admin/logs/error.log",
      "maxBytes": 10485760,
      "backupCount": 5
    },
    "security_file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "INFO",
      "formatter": "json",
      "filename": "~/.kiro/mcp-admin/logs/security.log",
      "maxBytes": 10485760,
      "backupCount": 10
    }
  },
  "loggers": {
    "mcp_admin": {
      "level": "DEBUG",
      "handlers": ["console", "file"],
      "propagate": false
    },
    "mcp_admin.security": {
      "level": "INFO",
      "handlers": ["security_file"],
      "propagate": false
    },
    "mcp_admin.tools": {
      "level": "INFO",
      "handlers": ["file"],
      "propagate": false
    },
    "mcp_admin.llm": {
      "level": "INFO",
      "handlers": ["file"],
      "propagate": false
    },
    "mcp_admin.workflow": {
      "level": "INFO",
      "handlers": ["file"],
      "propagate": false
    }
  },
  "root": {
    "level": "WARNING",
    "handlers": ["console", "error_file"]
  }
}
```

## Database Configuration

### Database Connection Settings

The application supports multiple database backends with specific configuration options:

#### SQLite Configuration
```json
{
  "database": {
    "type": "sqlite",
    "connection_string": "sqlite:///~/.kiro/mcp-admin/data/admin.db",
    "sqlite_options": {
      "journal_mode": "WAL",
      "synchronous": "NORMAL",
      "cache_size": 10000,
      "temp_store": "MEMORY",
      "mmap_size": 268435456
    }
  }
}
```

#### PostgreSQL Configuration
```json
{
  "database": {
    "type": "postgresql",
    "connection_string": "postgresql://user:password@localhost:5432/mcp_admin",
    "postgresql_options": {
      "pool_size": 20,
      "max_overflow": 30,
      "pool_timeout": 30,
      "pool_recycle": 3600,
      "echo": false
    }
  }
}
```

#### MySQL Configuration
```json
{
  "database": {
    "type": "mysql",
    "connection_string": "mysql://user:password@localhost:3306/mcp_admin",
    "mysql_options": {
      "charset": "utf8mb4",
      "pool_size": 20,
      "max_overflow": 30,
      "pool_timeout": 30,
      "pool_recycle": 3600
    }
  }
}
```

## Environment Variables

### Core Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_ADMIN_CONFIG_DIR` | Configuration directory path | `~/.kiro/mcp-admin` |
| `MCP_ADMIN_LOG_LEVEL` | Global log level | `INFO` |
| `MCP_ADMIN_DEBUG` | Enable debug mode | `false` |
| `MCP_ADMIN_PORT` | Application port | `8080` |
| `MCP_ADMIN_HOST` | Application host | `localhost` |

### Database Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | SQLite default |
| `DATABASE_POOL_SIZE` | Connection pool size | `10` |
| `DATABASE_TIMEOUT` | Query timeout in seconds | `30` |

### Security Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret key | Auto-generated |
| `JWT_SECRET` | JWT signing secret | Auto-generated |
| `ENCRYPTION_KEY` | Data encryption key | Auto-generated |
| `SESSION_TIMEOUT` | Session timeout in seconds | `3600` |

### LLM Provider Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | None |
| `ANTHROPIC_API_KEY` | Anthropic API key | None |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | None |
| `GOOGLE_API_KEY` | Google AI API key | None |
| `OLLAMA_HOST` | Ollama server host | `localhost:11434` |

### Performance Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_CONCURRENT_TOOLS` | Maximum concurrent tool executions | `10` |
| `TOOL_TIMEOUT` | Default tool timeout in seconds | `300` |
| `BATCH_SIZE` | Default batch operation size | `50` |
| `CACHE_SIZE_MB` | Memory cache size in MB | `256` |
| `THREAD_POOL_SIZE` | Thread pool size | `20` |

### Example Environment File (.env)

```bash
# Application Settings
MCP_ADMIN_DEBUG=false
MCP_ADMIN_LOG_LEVEL=INFO
MCP_ADMIN_PORT=8080

# Database Configuration
DATABASE_URL=sqlite:///~/.kiro/mcp-admin/data/admin.db

# Security Settings
SECRET_KEY=your-secret-key-here
SESSION_TIMEOUT=3600

# LLM Provider API Keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here

# Performance Settings
MAX_CONCURRENT_TOOLS=20
TOOL_TIMEOUT=300
CACHE_SIZE_MB=512

# Feature Flags
ENABLE_ANALYTICS=true
ENABLE_AUDIT_LOGGING=true
ENABLE_BACKUP_RESTORE=true
```

### Configuration Validation

The application validates all configuration files on startup and provides detailed error messages for invalid configurations:

```json
{
  "validation_errors": [
    {
      "file": "app-settings.json",
      "field": "performance.max_concurrent_tools",
      "error": "Value must be between 1 and 100",
      "current_value": 150
    },
    {
      "file": "llm-providers.json",
      "field": "providers[0].api_key_encrypted",
      "error": "API key is required for enabled providers",
      "current_value": null
    }
  ]
}
```

### Configuration Migration

When upgrading the application, configuration files are automatically migrated to new formats:

```json
{
  "migration_log": {
    "from_version": "1.0.0",
    "to_version": "1.1.0",
    "migrations_applied": [
      {
        "file": "app-settings.json",
        "changes": [
          "Added new field: features.workflow_engine",
          "Renamed field: ui.refresh_interval -> ui.auto_refresh_interval"
        ]
      }
    ],
    "backup_created": "~/.kiro/mcp-admin/config/backup-2024-01-15-10-30-00/"
  }
}
```