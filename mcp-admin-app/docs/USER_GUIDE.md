# MCP Admin Application - User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Tool Management](#tool-management)
3. [LLM Provider Management](#llm-provider-management)
4. [Enhanced UI Features](#enhanced-ui-features)
5. [Workflow Creation and Tool Chaining](#workflow-creation-and-tool-chaining)
6. [Batch Operations](#batch-operations)
7. [Security and API Key Management](#security-and-api-key-management)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation and Setup

1. **Prerequisites**
   - Python 3.8 or higher
   - Tkinter (included with Python)
   - SQLite3 (included with Python)

2. **Installation**
   ```bash
   # Clone or download the application
   cd mcp-admin-app
   python main.py
   ```

3. **First Launch**
   - The application will automatically create configuration directories
   - Default configuration files will be initialized
   - The SQLite database will be created with the required schema

### Application Layout

The MCP Admin Application features a modern, tabbed interface with the following main sections:

- **Servers**: Manage MCP server instances
- **Tools**: Discover, configure, and execute MCP tools
- **Prompts**: Create and manage prompt templates
- **LLM Providers**: Configure language model providers
- **Security**: Monitor security events and access logs
- **Audit**: View comprehensive audit trails
- **Monitoring**: Real-time system monitoring and analytics

## Tool Management

### Tool Discovery

The application automatically discovers tools from connected MCP servers:

1. **Automatic Discovery**
   - Tools are discovered when servers are started
   - The system scans for new tools every 30 seconds
   - Tool metadata is extracted and stored in the registry

2. **Manual Tool Refresh**
   - Click "Refresh Tools" to manually scan for new tools
   - Use "Rescan Server" to refresh tools from a specific server

### Tool Registry

The tool registry provides a centralized view of all available tools:

1. **Tool Information**
   - Name and description
   - Server source
   - Category and tags
   - Parameter schema
   - Usage statistics

2. **Tool Categories**
   - File Operations
   - Web Search
   - Code Analysis
   - Data Processing
   - Communication
   - System Tools

### Tool Configuration

Configure tools for optimal performance and security:

1. **Default Parameters**
   - Set default values for frequently used parameters
   - Create parameter templates for common use cases
   - Configure validation rules

2. **Permissions and Access Control**
   - Set user-based permissions
   - Configure role-based access control
   - Set usage quotas and rate limits

3. **Tool Aliases**
   - Create custom shortcuts for tools
   - Set up command aliases for CLI-style access
   - Configure tool groups for batch operations

### Interactive Tool Testing

Test tools before deploying them in production workflows:

1. **Single Tool Testing**
   - Select a tool from the registry
   - Fill in required parameters
   - Execute and view results in real-time
   - Save test configurations for reuse

2. **Parameter Validation**
   - Real-time parameter validation
   - Schema-based input checking
   - Helpful error messages and suggestions

3. **Execution History**
   - View all previous tool executions
   - Compare results across different parameter sets
   - Export execution logs for analysis

## LLM Provider Management

### Supported Providers

The application supports multiple LLM providers:

**Cloud Providers:**
- OpenAI (GPT-3.5, GPT-4, GPT-4 Turbo)
- Anthropic (Claude 3 Haiku, Sonnet, Opus)
- Azure OpenAI Service
- Google AI (Gemini Pro, Gemini Ultra)

**Local Providers:**
- Ollama (Local model hosting)
- LM Studio (Local model management)
- Custom endpoints (Self-hosted models)

### Provider Configuration

1. **Adding a Cloud Provider**
   - Navigate to the LLM Providers tab
   - Click "Add Provider"
   - Select provider type (OpenAI, Anthropic, etc.)
   - Enter API credentials
   - Test connection and select available models

2. **Adding a Local Provider**
   - Select "Local Provider" type
   - Configure endpoint URL (e.g., http://localhost:11434 for Ollama)
   - Test connection and discover available models
   - Set resource limits and performance settings

3. **API Key Management**
   - All API keys are encrypted and stored securely
   - Keys are never displayed in plain text
   - Automatic key validation and expiration checking
   - Support for key rotation and updates

### Model Selection and Configuration

1. **Model Properties**
   - Context window size
   - Token limits
   - Pricing information
   - Performance characteristics

2. **Usage Tracking**
   - Token consumption monitoring
   - Cost tracking and budgeting
   - Performance metrics
   - Usage analytics and optimization suggestions

## Enhanced UI Features

### Multi-Selection Operations

The application supports advanced multi-selection for efficient bulk operations:

1. **Selection Modes**
   - **Single Selection**: Click to select one item
   - **Multiple Selection**: Ctrl+Click to select multiple items
   - **Range Selection**: Shift+Click to select a range
   - **Extended Selection**: Drag to select multiple items

2. **Selection Indicators**
   - Real-time selection count in status bar
   - Visual highlighting of selected items
   - Selection summary with item details

3. **Bulk Operations**
   - Delete multiple tools simultaneously
   - Apply configuration changes to multiple items
   - Export selected items
   - Batch permission updates

### Context Menus and Shortcuts

Right-click context menus provide quick access to common operations:

1. **Tool Context Menu**
   - Execute Tool
   - Edit Configuration
   - View Details
   - Delete Tool
   - Add to Workflow

2. **Keyboard Shortcuts**
   - `Delete`: Delete selected items
   - `Ctrl+A`: Select all items
   - `Ctrl+D`: Deselect all items
   - `F5`: Refresh view
   - `Ctrl+F`: Search/Filter

### Mouse Wheel Scrolling

Enhanced navigation with mouse wheel support:

1. **Batch Dialog Scrolling**
   - Smooth scrolling in large tool lists
   - Cross-platform compatibility
   - Configurable scroll sensitivity

2. **Canvas Navigation**
   - Zoom in/out with Ctrl+Wheel
   - Pan with middle mouse button
   - Smooth scrolling in workflow designer

### Tool Deletion Workflows

Safe and comprehensive tool deletion with multiple confirmation levels:

1. **Single Tool Deletion**
   - Right-click → Delete or press Delete key
   - Confirmation dialog with tool details
   - Impact analysis showing dependent workflows
   - Option to clean up execution history

2. **Bulk Tool Deletion**
   - Select multiple tools
   - Click "Delete Selected" or press Delete
   - Comprehensive confirmation with full impact analysis
   - Progress tracking for large deletions
   - Detailed completion report

3. **Safety Features**
   - Dependency checking before deletion
   - Automatic cleanup of related data
   - Rollback capability for accidental deletions
   - Detailed error handling and reporting

## Workflow Creation and Tool Chaining

### Workflow Designer

Create complex multi-step processes using the visual workflow designer:

1. **Creating a Workflow**
   - Navigate to the Workflows section
   - Click "New Workflow"
   - Drag tools from the palette to the canvas
   - Connect tools by dragging between output and input ports

2. **Tool Connections**
   - Output parameters automatically map to compatible inputs
   - Visual validation of parameter types
   - Support for data transformation between steps
   - Conditional branching based on results

3. **Workflow Configuration**
   - Set workflow name and description
   - Configure error handling strategies
   - Set timeout and retry policies
   - Add workflow metadata and tags

### Best Practices for Tool Chaining

1. **Design Principles**
   - Keep workflows focused on single objectives
   - Use descriptive names for workflow steps
   - Document complex logic with annotations
   - Test individual steps before chaining

2. **Error Handling**
   - Always configure error handling for each step
   - Use conditional branches for different outcomes
   - Implement retry logic for transient failures
   - Log intermediate results for debugging

3. **Performance Optimization**
   - Minimize data transfer between steps
   - Use parallel execution where possible
   - Cache expensive operations
   - Monitor resource usage

4. **Security Considerations**
   - Validate all inputs at workflow boundaries
   - Use least-privilege access for tools
   - Sanitize data between steps
   - Audit workflow executions

### Workflow Templates

Create reusable workflow patterns:

1. **Template Creation**
   - Save successful workflows as templates
   - Parameterize common variables
   - Add template documentation and examples
   - Version control for template updates

2. **Template Library**
   - Browse available templates by category
   - Search templates by functionality
   - Import/export templates between environments
   - Community template sharing

## Batch Operations

### Batch Tool Execution

Execute multiple tools simultaneously for efficient processing:

1. **Batch Configuration**
   - Select tools for batch execution
   - Configure common parameters
   - Set execution order and dependencies
   - Configure resource limits

2. **Execution Monitoring**
   - Real-time progress tracking
   - Individual tool status indicators
   - Resource usage monitoring
   - Cancellation and pause capabilities

3. **Result Analysis**
   - Aggregate result summaries
   - Individual execution details
   - Performance comparisons
   - Export results for further analysis

### Batch Testing and A/B Comparison

Compare different configurations and approaches:

1. **A/B Test Setup**
   - Define test variations
   - Set sample sizes and criteria
   - Configure statistical significance thresholds
   - Schedule test execution

2. **Statistical Analysis**
   - Automated statistical comparison
   - Confidence intervals and p-values
   - Performance metric comparisons
   - Recommendation generation

3. **Test Reporting**
   - Comprehensive test reports
   - Visual comparison charts
   - Statistical significance indicators
   - Actionable recommendations

## Security and API Key Management

### API Key Security

Secure management of sensitive credentials:

1. **Encryption**
   - All API keys encrypted at rest using AES-256
   - Secure key derivation from user credentials
   - No plain-text storage of sensitive data
   - Automatic encryption key rotation

2. **Access Control**
   - Role-based access to API keys
   - Audit logging for all key access
   - Time-limited access tokens
   - Multi-factor authentication support

3. **Key Management Best Practices**
   - Regular key rotation schedules
   - Separate keys for different environments
   - Principle of least privilege
   - Secure key backup and recovery

### Tool Security

Comprehensive security measures for tool execution:

1. **Sandboxing**
   - Isolated execution environments
   - Resource limit enforcement
   - Network access controls
   - File system restrictions

2. **Permission Management**
   - Fine-grained tool permissions
   - User and role-based access control
   - Usage quotas and rate limiting
   - Security policy enforcement

3. **Security Monitoring**
   - Real-time security event logging
   - Suspicious activity detection
   - Automated threat response
   - Security audit trails

### Security Best Practices

1. **Environment Setup**
   - Use dedicated service accounts
   - Implement network segmentation
   - Regular security updates
   - Backup and disaster recovery

2. **Operational Security**
   - Regular security audits
   - Penetration testing
   - Incident response procedures
   - Security awareness training

3. **Compliance**
   - Data protection regulations (GDPR, CCPA)
   - Industry standards (SOC 2, ISO 27001)
   - Audit trail requirements
   - Data retention policies

## Troubleshooting

### Common Issues

1. **Connection Problems**
   - Check network connectivity
   - Verify API credentials
   - Review firewall settings
   - Check service status

2. **Performance Issues**
   - Monitor resource usage
   - Check database performance
   - Review workflow complexity
   - Optimize tool configurations

3. **Tool Execution Failures**
   - Validate input parameters
   - Check tool permissions
   - Review error logs
   - Test tool isolation

### Diagnostic Tools

1. **Log Analysis**
   - Application logs in `~/.kiro/mcp-admin/logs/`
   - Error logs with stack traces
   - Performance metrics
   - Security event logs

2. **Health Checks**
   - Built-in system health monitoring
   - Provider connectivity tests
   - Database integrity checks
   - Resource usage monitoring

3. **Debug Mode**
   - Enable verbose logging
   - Step-by-step execution tracing
   - Parameter validation details
   - Network request/response logging

### Getting Help

1. **Documentation**
   - User guide (this document)
   - API documentation
   - Configuration reference
   - Best practices guide

2. **Support Channels**
   - GitHub issues for bug reports
   - Community forums for questions
   - Documentation wiki
   - Video tutorials and examples

3. **Self-Help Tools**
   - Built-in diagnostic utilities
   - Configuration validation
   - Automated troubleshooting
   - System health reports