# Project Structure & Organization

## Repository Layout

```
mcp-admin-app/                 # Main enhanced application
├── core/                      # Application framework and configuration
│   ├── app.py                # Main application class
│   ├── config.py             # Configuration management
│   └── logging_config.py     # Logging setup
├── models/                    # Data structures and business objects
│   ├── base.py               # Base classes and enums
│   ├── server.py             # MCP server models
│   ├── prompt.py             # Prompt template models
│   ├── security.py           # Security event models
│   └── llm.py                # LLM provider models
├── services/                  # Business logic and operations
│   ├── server_manager.py     # Server lifecycle management
│   ├── tool_manager.py       # Tool discovery and management
│   ├── prompt_manager.py     # Prompt template management
│   ├── security_service.py   # Security monitoring
│   ├── audit_service.py      # Audit trail management
│   ├── llm_manager.py        # LLM provider integration
│   └── monitoring_service.py # Real-time monitoring
├── data/                      # Database and storage management
│   └── database.py           # SQLite database operations
├── ui/                        # User interface components
│   ├── servers_page.py       # Server management UI
│   ├── tools_page.py         # Tool management UI
│   ├── prompts_page.py       # Prompt templates UI
│   ├── security_page.py      # Security monitoring UI
│   ├── audit_page.py         # Audit trail UI
│   ├── llm_page.py           # LLM provider UI
│   └── monitoring_page.py    # Monitoring dashboard UI
├── main.py                    # Application entry point
├── demo.py                    # Demo with sample data
├── test_basic.py             # Basic test suite
├── requirements.txt          # Dependencies (future use)
├── README.md                 # Project documentation
└── IMPLEMENTATION_SUMMARY.md # Development status

mcp-desktop-app/              # Simple prototype application
└── mcp_desktop.py           # Prototype implementation
```

## Naming Conventions

### Files and Directories
- **Snake_case** for Python files: `server_manager.py`, `audit_service.py`
- **Lowercase** for directories: `core/`, `services/`, `ui/`
- **PascalCase** for class names: `MCPServer`, `ServerManager`, `ServersPage`
- **UPPERCASE** for constants: `SERVER_STATUS`, `DEFAULT_CONFIG`

### Code Organization
- **One class per file** in most cases
- **Related functionality grouped** in service modules
- **UI components** follow `{feature}_page.py` pattern
- **Models** represent data structures with validation methods

## Module Dependencies

### Import Hierarchy
1. **Standard library imports** first
2. **Third-party imports** second (when added)
3. **Local application imports** last

### Dependency Flow
```
UI Layer (ui/) 
    ↓ depends on
Services Layer (services/)
    ↓ depends on  
Models Layer (models/) + Data Layer (data/)
    ↓ depends on
Core Layer (core/)
```

## Configuration Structure

### Runtime Configuration Directory
```
~/.kiro/mcp-admin/
├── config/
│   ├── app-settings.json      # Application settings
│   ├── servers.json           # Server configurations
│   ├── llm-providers.json     # LLM provider settings
│   └── notification-channels.json # Notification settings
├── data/
│   ├── admin.db              # SQLite database
│   └── backups/              # Configuration backups
├── templates/
│   └── prompts/              # Prompt templates
└── logs/
    ├── application.log       # Application logs
    └── error.log            # Error logs
```

## Extension Points

### Adding New Features
1. **Define models** in `models/` for data structures
2. **Implement services** in `services/` for business logic
3. **Create UI components** in `ui/` for user interface
4. **Update main app** in `core/app.py` to integrate components
5. **Add database schema** in `data/database.py` if needed

### Service Integration Pattern
- Services receive `config_manager` and `db_manager` in constructor
- Services expose public methods for operations
- Services handle their own error logging and exception handling
- UI components call service methods and handle user feedback

## Code Style Guidelines

### Python Conventions
- **PEP 8** compliance for code formatting
- **Type hints** for function parameters and return values
- **Docstrings** for all classes and public methods
- **Comprehensive error handling** with logging
- **Context managers** for resource management (database connections)

### UI Conventions
- **Consistent color scheme**: Primary blue (#1a73e8), success green (#34a853), error red (#d93025)
- **Responsive layouts** using pack() and grid() managers
- **Modal dialogs** for data entry and confirmation
- **Status indicators** and user feedback for all operations