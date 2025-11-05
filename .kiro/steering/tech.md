# Technology Stack & Build System

## Core Technologies

### Programming Language
- **Python 3.8+** - Primary language for all components
- Uses only Python standard library for core functionality (no external dependencies)

### UI Framework
- **Tkinter** - Cross-platform GUI framework (included with Python)
- **ttk** - Themed widgets for modern appearance

### Database
- **SQLite3** - Embedded database for logging, metrics, and configuration storage
- Database file stored in user's home directory: `~/.kiro/mcp-admin/data/admin.db`

### Configuration Management
- **JSON** - Configuration files stored in `~/.kiro/mcp-admin/config/`
- Automatic directory structure initialization

### Logging
- **Python logging module** - Comprehensive application and error logging
- Log rotation and file-based storage

## Architecture Patterns

### Layered Architecture
1. **Presentation Layer** (`ui/`) - Tkinter-based UI components
2. **Business Logic Layer** (`services/`) - Service classes handling operations
3. **Data Access Layer** (`data/`) - Database and file operations
4. **Core Layer** (`core/`) - Application framework and configuration
5. **Models Layer** (`models/`) - Data structures and enums

### Design Patterns
- **Service-oriented architecture** - Clear separation of concerns
- **Configuration management** - Centralized config handling
- **Context managers** - Proper resource management for database connections
- **Observer pattern** - UI updates and monitoring

## Common Commands

### Running the Application
```bash
# Main enhanced application
python main.py

# Demo with sample data
python demo.py

# Simple desktop prototype
python mcp-desktop-app/mcp_desktop.py
```

### Testing
```bash
# Run basic tests
python test_basic.py

# Run with verbose output
python -v test_basic.py
```

### Development
```bash
# Check Python version compatibility
python --version

# Validate imports and basic functionality
python -c "import main; print('All imports successful')"
```

## Future Dependencies
When advanced features are implemented, these dependencies may be added:
- `requests>=2.31.0` - HTTP API calls to LLM providers
- `cryptography>=41.0.0` - Encryption of sensitive data
- `schedule>=1.2.0` - Scheduled tasks and monitoring
- `psutil>=5.9.0` - System performance monitoring

## Platform Support
- **Windows** - Primary development platform
- **macOS** - Cross-platform compatibility via Tkinter
- **Linux** - Cross-platform compatibility via Tkinter

## Configuration Directories
- **Windows**: `%USERPROFILE%\.kiro\mcp-admin\`
- **macOS/Linux**: `~/.kiro/mcp-admin/`