# MCP Admin Application - Enhanced Edition

A comprehensive desktop application for managing Model Context Protocol (MCP) servers, tools, and related infrastructure with advanced LLM integration, workflow automation, and comprehensive analytics.

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### 🔧 Core Features (Implemented)
- **Enhanced Server Management**: Complete lifecycle management of MCP servers
- **Advanced Tool Discovery**: Automatic discovery and registry of MCP tools
- **Interactive Tool Testing**: Real-time tool execution with parameter validation
- **Workflow Engine**: Visual workflow designer with tool chaining capabilities
- **Batch Operations**: Parallel execution and bulk management of tools
- **Enhanced UI**: Multi-selection, context menus, and mouse wheel scrolling
- **Tool Deletion**: Safe single and bulk deletion with comprehensive confirmations

### 🤖 LLM Integration Features
- **Multi-Provider Support**: OpenAI, Anthropic, Azure OpenAI, Google AI, Ollama, LM Studio
- **Real-time Testing**: Live prompt execution with token counting and cost analysis
- **Token Analytics**: Accurate token counting across different providers
- **Cost Tracking**: Real-time cost estimation and budget management
- **A/B Testing**: Statistical comparison of different configurations
- **Usage Analytics**: Comprehensive performance and cost insights

### 🔒 Security & Compliance
- **API Key Encryption**: AES-256 encryption for sensitive credentials
- **Tool Sandboxing**: Isolated execution environments with resource limits
- **Role-Based Access Control**: Fine-grained permissions and user management
- **Comprehensive Audit Trail**: Tamper-evident logging for compliance
- **Security Monitoring**: Real-time threat detection and alerting

### 📊 Analytics & Monitoring
- **Performance Dashboards**: Real-time metrics and trend analysis
- **Resource Monitoring**: CPU, memory, and network usage tracking
- **Quality Assessment**: Tool effectiveness and optimization recommendations
- **Business Intelligence**: ROI calculations and cost optimization insights

## 🚀 Installation

### Prerequisites
- **Python 3.8+** (Python 3.10+ recommended)
- **Tkinter** (included with Python)
- **SQLite3** (included with Python)

### Quick Installation
```bash
# Clone the repository
git clone <repository-url>
cd mcp-admin-app

# Run the application
python main.py

# Or run with demo data
python demo.py
```

### Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv mcp-admin-env

# Activate (Windows)
mcp-admin-env\Scripts\activate

# Activate (macOS/Linux)
source mcp-admin-env/bin/activate

# Run application
python main.py
```

## 🎯 Quick Start

### 1. First Launch
- Application automatically creates configuration directories
- Default settings are applied for immediate use
- SQLite database is initialized with required schema

### 2. Add Your First MCP Server
1. Navigate to the **Servers** tab
2. Click **"Add Server"**
3. Configure server details:
   - **Name**: `My Development Server`
   - **Command**: `python -m mcp_server`
   - **Arguments**: `--port 8080`
4. Click **"Save"** and **"Start"**

### 3. Configure LLM Provider
1. Go to **LLM Providers** tab
2. Click **"Add Provider"**
3. Select provider type (e.g., OpenAI)
4. Enter API credentials
5. Test connection and select models

### 4. Discover and Test Tools
1. Visit the **Tools** tab
2. Tools are automatically discovered from running servers
3. Select a tool and click **"Test"**
4. Configure parameters and execute

### 5. Create Your First Workflow
1. Navigate to **Workflows** tab
2. Click **"New Workflow"**
3. Drag tools from palette to canvas
4. Connect tools by dragging between ports
5. Save and execute workflow

## 📚 Documentation

### User Guides
- **[User Guide](docs/USER_GUIDE.md)** - Comprehensive user documentation
- **[Workflow Guide](docs/WORKFLOW_GUIDE.md)** - Workflow creation and best practices
- **[Batch Operations Guide](docs/BATCH_OPERATIONS_GUIDE.md)** - Advanced batch processing
- **[Security Guide](docs/SECURITY_GUIDE.md)** - Security setup and best practices

### Technical Documentation
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Configuration Reference](docs/CONFIGURATION_REFERENCE.md)** - Configuration options
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment

### Quick Reference
- **[Keyboard Shortcuts](#keyboard-shortcuts)** - Efficiency shortcuts
- **[Troubleshooting](#troubleshooting)** - Common issues and solutions

## 🏗️ Architecture

The application follows a modern layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Admin Application                    │
├─────────────────────────────────────────────────────────────┤
│  UI Layer (Enhanced)                                        │
│  ├── Tools Page (Multi-selection, Context Menus)          │
│  ├── Workflows Page (Visual Designer)                      │
│  ├── LLM Providers Page (Multi-provider Management)        │
│  ├── Analytics Dashboard (Real-time Metrics)               │
│  └── Security & Audit Pages                                │
├─────────────────────────────────────────────────────────────┤
│  Services Layer (Extended)                                  │
│  ├── Tool Manager (Discovery, Execution, Analytics)        │
│  ├── Workflow Engine (Orchestration, Monitoring)           │
│  ├── LLM Manager (Multi-provider Integration)              │
│  ├── Security Service (Authentication, Authorization)       │
│  └── Analytics Service (Metrics, Insights)                 │
├─────────────────────────────────────────────────────────────┤
│  Data Layer (Expanded)                                      │
│  ├── Tool Registry (Metadata, Configurations)              │
│  ├── Execution History (Results, Performance)              │
│  ├── LLM Analytics (Usage, Costs, Performance)             │
│  └── Security Logs (Audit Trail, Events)                   │
└─────────────────────────────────────────────────────────────┘
```

### Key Components
- **Tool Discovery Engine**: Automatic tool detection and classification
- **Workflow Engine**: Visual workflow designer and execution engine
- **LLM Integration Layer**: Multi-provider support with unified interface
- **Security Framework**: Comprehensive security and compliance features
- **Analytics Engine**: Real-time metrics and business intelligence

## ⚙️ Configuration

### Configuration Directory
```
~/.kiro/mcp-admin/
├── config/
│   ├── app-settings.json          # Main application settings
│   ├── servers.json               # MCP server configurations
│   ├── llm-providers.json         # LLM provider settings
│   ├── tools.json                 # Tool-specific configurations
│   ├── security.json              # Security policies
│   └── performance.json           # Performance tuning
├── data/
│   ├── admin.db                   # SQLite database
│   └── backups/                   # Automated backups
├── templates/
│   └── prompts/                   # Prompt templates
└── logs/
    ├── application.log            # Application logs
    ├── security.log               # Security events
    └── error.log                  # Error logs
```

### Environment Variables
```bash
# Core Settings
MCP_ADMIN_DEBUG=false
MCP_ADMIN_LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///~/.kiro/mcp-admin/data/admin.db

# LLM Providers
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Performance
MAX_CONCURRENT_TOOLS=20
TOOL_TIMEOUT=300
```

## 🔒 Security

### Security Features
- **🔐 API Key Encryption**: AES-256-GCM encryption for all credentials
- **🏰 Tool Sandboxing**: Isolated execution with resource limits
- **👥 RBAC**: Role-based access control with fine-grained permissions
- **📋 Audit Logging**: Comprehensive tamper-evident audit trails
- **🛡️ Threat Detection**: Real-time security monitoring and alerting

### Security Best Practices
1. **Use strong API keys** with appropriate provider-level restrictions
2. **Enable audit logging** for compliance requirements
3. **Configure resource limits** to prevent abuse
4. **Regular security updates** and key rotation
5. **Monitor security events** and respond to alerts

### Compliance Support
- **SOX**: Financial data protection and audit trails
- **GDPR**: Data protection and privacy controls
- **HIPAA**: Healthcare data security (when applicable)
- **SOC 2**: Security controls and monitoring

## 🎮 Keyboard Shortcuts

### Global Shortcuts
- `Ctrl+N`: New item (context-dependent)
- `Ctrl+S`: Save current configuration
- `Ctrl+R`: Refresh current view
- `F5`: Refresh all data
- `Ctrl+F`: Search/Filter
- `Esc`: Cancel current operation

### Tool Management
- `Delete`: Delete selected tools
- `Ctrl+A`: Select all tools
- `Ctrl+E`: Execute selected tools
- `Ctrl+T`: Test selected tools
- `Ctrl+D`: Duplicate tool configuration

### Workflow Designer
- `Ctrl+Z`: Undo last action
- `Ctrl+Y`: Redo last action
- `Ctrl+C`: Copy selected elements
- `Ctrl+V`: Paste elements
- `Space`: Pan canvas (hold and drag)

## 🔧 Troubleshooting

### Common Issues

#### Connection Problems
```bash
# Check Python version
python --version  # Should be 3.8+

# Test basic imports
python -c "import tkinter; print('Tkinter OK')"

# Check configuration directory
ls -la ~/.kiro/mcp-admin/
```

#### Performance Issues
- **Slow tool execution**: Check resource limits in configuration
- **High memory usage**: Reduce concurrent tool limits
- **Database locks**: Ensure proper connection cleanup

#### LLM Provider Issues
- **API key errors**: Verify key encryption and provider settings
- **Rate limiting**: Check provider rate limits and implement backoff
- **Token counting**: Verify tokenizer configuration for accuracy

### Getting Help
1. **Check logs**: `~/.kiro/mcp-admin/logs/`
2. **Enable debug mode**: Set `MCP_ADMIN_DEBUG=true`
3. **Review documentation**: Comprehensive guides available
4. **Community support**: GitHub issues and discussions

## 🤝 Contributing

We welcome contributions! The application is designed to be extensible:

### Adding New Features
1. **Define models** in `models/` for data structures
2. **Implement services** in `services/` for business logic
3. **Create UI components** in `ui/` for user interface
4. **Update main app** to integrate new components
5. **Add tests** to ensure reliability

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd mcp-admin-app

# Install development dependencies (when available)
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run with debug mode
MCP_ADMIN_DEBUG=true python main.py
```

### Code Style
- **PEP 8** compliance for Python code
- **Type hints** for all function parameters
- **Comprehensive docstrings** for classes and methods
- **Error handling** with proper logging

## 📄 License

This project is part of the MCP ecosystem and follows the same licensing terms. See [LICENSE](LICENSE) for details.

---

## 🚀 What's New in Enhanced Edition

### Recent Updates
- ✅ **Advanced Tool Management**: Multi-selection, batch operations, safe deletion
- ✅ **LLM Integration**: Multi-provider support with real-time testing
- ✅ **Enhanced UI**: Mouse wheel scrolling, context menus, keyboard shortcuts
- ✅ **Workflow Engine**: Visual designer with tool chaining capabilities
- ✅ **Security Framework**: Comprehensive security and compliance features
- ✅ **Analytics Dashboard**: Real-time metrics and business intelligence

### Coming Soon
- 🔄 **Advanced Workflow Features**: Conditional logic, loops, error handling
- 🔄 **Machine Learning Integration**: Intelligent tool recommendations
- 🔄 **Enterprise Features**: SSO, advanced RBAC, multi-tenancy
- 🔄 **Cloud Deployment**: Docker containers, Kubernetes support

---

**Ready to get started?** Run `python main.py` and explore the comprehensive MCP administration capabilities!