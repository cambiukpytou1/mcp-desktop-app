# MCP Admin Application - API Reference

## Table of Contents

1. [API Overview](#api-overview)
2. [Tool Management API](#tool-management-api)
3. [LLM Provider API](#llm-provider-api)
4. [Workflow API](#workflow-api)
5. [Batch Operations API](#batch-operations-api)
6. [Security API](#security-api)
7. [Analytics API](#analytics-api)
8. [Configuration API](#configuration-api)
9. [Error Handling](#error-handling)
10. [Authentication](#authentication)

## API Overview

The MCP Admin Application provides a comprehensive REST API for programmatic access to all application features. The API follows RESTful principles and uses JSON for data exchange.

### Base URL
```
http://localhost:8080/api/v1
```

### Authentication
All API requests require authentication using API keys or JWT tokens.

### Response Format
All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123"
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "TOOL_NOT_FOUND",
    "message": "Tool with ID 'tool_123' not found",
    "details": {...}
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123"
}
```

## Tool Management API

### List Tools
Retrieve a list of all available tools with optional filtering.

```http
GET /tools
```

**Query Parameters:**
- `category` (string): Filter by tool category
- `server_id` (string): Filter by MCP server
- `status` (string): Filter by tool status (active, inactive, error)
- `search` (string): Search in tool names and descriptions
- `limit` (integer): Maximum number of results (default: 50)
- `offset` (integer): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "tools": [
      {
        "id": "tool_123",
        "name": "File Reader",
        "description": "Reads files from the file system",
        "category": "file_operations",
        "server_id": "server_1",
        "status": "active",
        "schema": {...},
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 247,
    "limit": 50,
    "offset": 0
  }
}
```

### Get Tool Details
Retrieve detailed information about a specific tool.

```http
GET /tools/{tool_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "tool_123",
    "name": "File Reader",
    "description": "Reads files from the file system",
    "category": "file_operations",
    "server_id": "server_1",
    "status": "active",
    "schema": {
      "parameters": [
        {
          "name": "file_path",
          "type": "string",
          "required": true,
          "description": "Path to the file to read"
        }
      ]
    },
    "permissions": {...},
    "analytics": {
      "total_executions": 1247,
      "success_rate": 0.945,
      "average_execution_time": 2.3
    }
  }
}
```

### Execute Tool
Execute a tool with specified parameters.

```http
POST /tools/{tool_id}/execute
```

**Request Body:**
```json
{
  "parameters": {
    "file_path": "/path/to/file.txt"
  },
  "options": {
    "timeout": 300,
    "retry_count": 3
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_456",
    "status": "completed",
    "result": {
      "content": "File content here...",
      "size": 1024
    },
    "execution_time": 1.23,
    "resource_usage": {
      "memory_mb": 45,
      "cpu_percent": 12
    }
  }
}
```

### Update Tool Configuration
Update tool configuration and parameters.

```http
PUT /tools/{tool_id}/config
```

**Request Body:**
```json
{
  "default_parameters": {
    "timeout": 300
  },
  "permissions": {
    "allowed_roles": ["admin", "user"],
    "rate_limit": 100
  }
}
```

### Delete Tool
Remove a tool from the registry.

```http
DELETE /tools/{tool_id}
```

**Query Parameters:**
- `cleanup_history` (boolean): Whether to clean up execution history (default: true)

### Batch Tool Operations
Perform operations on multiple tools simultaneously.

```http
POST /tools/batch
```

**Request Body:**
```json
{
  "operation": "execute",
  "tool_ids": ["tool_123", "tool_456", "tool_789"],
  "parameters": {
    "common_params": {...},
    "tool_specific": {
      "tool_123": {...}
    }
  },
  "options": {
    "execution_strategy": "parallel",
    "max_concurrent": 10
  }
}
```

## LLM Provider API

### List Providers
Retrieve all configured LLM providers.

```http
GET /llm/providers
```

**Response:**
```json
{
  "success": true,
  "data": {
    "providers": [
      {
        "id": "openai_1",
        "name": "OpenAI GPT-4",
        "type": "openai",
        "status": "active",
        "models": [
          {
            "id": "gpt-4",
            "name": "GPT-4",
            "max_tokens": 8192,
            "cost_per_input_token": 0.00003,
            "cost_per_output_token": 0.00006
          }
        ]
      }
    ]
  }
}
```

### Add Provider
Configure a new LLM provider.

```http
POST /llm/providers
```

**Request Body:**
```json
{
  "name": "OpenAI GPT-4",
  "type": "openai",
  "api_key": "sk-...",
  "endpoint_url": "https://api.openai.com/v1",
  "models": ["gpt-4", "gpt-3.5-turbo"],
  "settings": {
    "temperature": 0.7,
    "max_tokens": 2048
  }
}
```

### Test Provider Connection
Test connectivity to an LLM provider.

```http
POST /llm/providers/{provider_id}/test
```

**Response:**
```json
{
  "success": true,
  "data": {
    "connection_status": "success",
    "response_time": 234,
    "available_models": ["gpt-4", "gpt-3.5-turbo"],
    "rate_limits": {
      "requests_per_minute": 3500,
      "tokens_per_minute": 90000
    }
  }
}
```

### Execute Prompt
Execute a prompt against an LLM provider.

```http
POST /llm/providers/{provider_id}/execute
```

**Request Body:**
```json
{
  "model": "gpt-4",
  "prompt": "Explain the concept of machine learning",
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "execution_id": "llm_exec_789",
    "response": "Machine learning is...",
    "usage": {
      "input_tokens": 12,
      "output_tokens": 156,
      "total_tokens": 168
    },
    "cost": {
      "input_cost": 0.00036,
      "output_cost": 0.00936,
      "total_cost": 0.00972
    },
    "execution_time": 2.45
  }
}
```

## Workflow API

### List Workflows
Retrieve all workflows.

```http
GET /workflows
```

**Response:**
```json
{
  "success": true,
  "data": {
    "workflows": [
      {
        "id": "workflow_123",
        "name": "Data Processing Pipeline",
        "description": "Processes incoming data files",
        "status": "active",
        "steps": 5,
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

### Create Workflow
Create a new workflow.

```http
POST /workflows
```

**Request Body:**
```json
{
  "name": "Data Processing Pipeline",
  "description": "Processes incoming data files",
  "steps": [
    {
      "id": "step_1",
      "tool_id": "file_reader",
      "parameters": {...},
      "position": {"x": 100, "y": 100}
    }
  ],
  "connections": [
    {
      "from_step": "step_1",
      "from_output": "content",
      "to_step": "step_2",
      "to_input": "data"
    }
  ]
}
```

### Execute Workflow
Execute a workflow with specified inputs.

```http
POST /workflows/{workflow_id}/execute
```

**Request Body:**
```json
{
  "inputs": {
    "file_path": "/path/to/input.txt"
  },
  "options": {
    "timeout": 1800,
    "parallel_execution": true
  }
}
```

## Batch Operations API

### Create Batch Operation
Create a new batch operation.

```http
POST /batch
```

**Request Body:**
```json
{
  "type": "tool_execution",
  "name": "Daily Data Processing",
  "items": [
    {
      "tool_id": "tool_123",
      "parameters": {...}
    }
  ],
  "options": {
    "execution_strategy": "parallel",
    "max_concurrent": 10,
    "timeout": 3600
  }
}
```

### Get Batch Status
Retrieve the status of a batch operation.

```http
GET /batch/{batch_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "batch_456",
    "status": "running",
    "progress": {
      "total": 100,
      "completed": 75,
      "failed": 2,
      "remaining": 23
    },
    "started_at": "2024-01-15T10:30:00Z",
    "estimated_completion": "2024-01-15T11:15:00Z"
  }
}
```

### Cancel Batch Operation
Cancel a running batch operation.

```http
POST /batch/{batch_id}/cancel
```

## Security API

### List Security Events
Retrieve security events with filtering.

```http
GET /security/events
```

**Query Parameters:**
- `event_type` (string): Filter by event type
- `user_id` (string): Filter by user
- `start_date` (string): Start date for filtering
- `end_date` (string): End date for filtering
- `risk_level` (string): Filter by risk level

**Response:**
```json
{
  "success": true,
  "data": {
    "events": [
      {
        "id": "sec_event_123",
        "event_type": "unauthorized_access",
        "user_id": "user_456",
        "resource": "tool_789",
        "risk_level": "high",
        "timestamp": "2024-01-15T10:30:00Z",
        "details": {...}
      }
    ]
  }
}
```

### Get Audit Trail
Retrieve audit trail entries.

```http
GET /security/audit
```

**Response:**
```json
{
  "success": true,
  "data": {
    "entries": [
      {
        "id": "audit_123",
        "action": "tool_execution",
        "user_id": "user_456",
        "resource": "tool_789",
        "timestamp": "2024-01-15T10:30:00Z",
        "details": {...}
      }
    ]
  }
}
```

## Analytics API

### Get Usage Analytics
Retrieve usage analytics data.

```http
GET /analytics/usage
```

**Query Parameters:**
- `time_range` (string): Time range for analytics (1h, 24h, 7d, 30d)
- `group_by` (string): Grouping dimension (tool, user, category)
- `metric` (string): Specific metric to retrieve

**Response:**
```json
{
  "success": true,
  "data": {
    "metrics": {
      "total_executions": 12470,
      "success_rate": 0.945,
      "average_execution_time": 2.3,
      "total_cost": 145.67
    },
    "trends": [
      {
        "timestamp": "2024-01-15T10:00:00Z",
        "executions": 156,
        "success_rate": 0.94
      }
    ]
  }
}
```

### Get Performance Metrics
Retrieve performance metrics.

```http
GET /analytics/performance
```

**Response:**
```json
{
  "success": true,
  "data": {
    "system_metrics": {
      "cpu_usage": 65.2,
      "memory_usage": 78.5,
      "disk_usage": 45.3,
      "network_throughput": 125.6
    },
    "application_metrics": {
      "active_executions": 23,
      "queue_length": 5,
      "error_rate": 0.055
    }
  }
}
```

## Configuration API

### Get Configuration
Retrieve application configuration.

```http
GET /config
```

**Response:**
```json
{
  "success": true,
  "data": {
    "application": {
      "version": "1.0.0",
      "environment": "production"
    },
    "features": {
      "batch_operations": true,
      "workflow_engine": true,
      "analytics": true
    },
    "limits": {
      "max_concurrent_tools": 50,
      "max_batch_size": 1000,
      "max_workflow_steps": 100
    }
  }
}
```

### Update Configuration
Update application configuration.

```http
PUT /config
```

**Request Body:**
```json
{
  "limits": {
    "max_concurrent_tools": 75
  },
  "features": {
    "new_feature": true
  }
}
```

## Error Handling

### Error Codes

| Code | Description |
|------|-------------|
| `TOOL_NOT_FOUND` | Requested tool does not exist |
| `INVALID_PARAMETERS` | Tool parameters are invalid |
| `EXECUTION_FAILED` | Tool execution failed |
| `PERMISSION_DENIED` | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| `PROVIDER_UNAVAILABLE` | LLM provider is unavailable |
| `WORKFLOW_INVALID` | Workflow configuration is invalid |
| `BATCH_FAILED` | Batch operation failed |
| `AUTHENTICATION_FAILED` | Authentication failed |
| `INTERNAL_ERROR` | Internal server error |

### Error Response Details

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETERS",
    "message": "Parameter 'file_path' is required",
    "details": {
      "parameter": "file_path",
      "expected_type": "string",
      "provided_value": null
    },
    "suggestions": [
      "Provide a valid file path",
      "Check parameter documentation"
    ]
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123"
}
```

## Authentication

### API Key Authentication
Include the API key in the request header:

```http
Authorization: Bearer your_api_key_here
```

### JWT Token Authentication
Include the JWT token in the request header:

```http
Authorization: Bearer your_jwt_token_here
```

### OAuth 2.0 Authentication
For OAuth 2.0 flows, follow the standard OAuth 2.0 specification:

1. **Authorization Code Flow**
   ```http
   GET /oauth/authorize?client_id=your_client_id&response_type=code&redirect_uri=your_redirect_uri
   ```

2. **Token Exchange**
   ```http
   POST /oauth/token
   Content-Type: application/x-www-form-urlencoded
   
   grant_type=authorization_code&code=auth_code&client_id=your_client_id&client_secret=your_client_secret
   ```

### Rate Limiting
API requests are subject to rate limiting:

- **Default Limit**: 1000 requests per hour per API key
- **Burst Limit**: 100 requests per minute
- **Headers**: Rate limit information is included in response headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

### Webhooks
Configure webhooks to receive real-time notifications:

```http
POST /webhooks
```

**Request Body:**
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["tool.executed", "batch.completed", "workflow.failed"],
  "secret": "your_webhook_secret"
}
```

**Webhook Payload:**
```json
{
  "event": "tool.executed",
  "data": {
    "tool_id": "tool_123",
    "execution_id": "exec_456",
    "status": "completed",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "webhook_id": "webhook_789"
}
```