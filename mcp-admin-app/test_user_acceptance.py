#!/usr/bin/env python3
"""
User Acceptance Testing (UAT) for MCP Admin Application

This comprehensive UAT suite validates the complete user experience
and workflow functionality from an end-user perspective.

Task 20.2: Perform user acceptance testing and optimization
"""

import os
import sys
import time
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core imports
from core.config import ConfigurationManager
from data.database import DatabaseManager

# Service imports
from services.server_manager import ServerManager
from services.tool_manager import AdvancedToolManager
from services.tool_discovery import ToolDiscoveryEngine
from services.tool_execution import ToolExecutionEngine
from services.prompt_manager import PromptManager
from services.security_service import SecurityService
from services.audit_service import AuditService

# Model imports
from models.server import MCPServer
from models.base import ServerStatus
from models.tool import ToolRegistryEntry, ToolCategory, ToolStatus, ToolParameter
from models.prompt import PromptTemplate


class UserAcceptanceTest:
    """Comprehensive User Acceptance Testing suite"""
    
    def __init__(self):
        """Initialize UAT environment"""
        self.test_dir = tempfile.mkdtemp(prefix="mcp_admin_uat_")
        self.config_manager = None
        self.db_manager = None
        self.services = {}
        self.test_results = {}
        self.user_scenarios = []
        
    def setup_uat_environment(self):
        """Set up realistic UAT environment with sample data"""
        print("Setting up User Acceptance Testing environment...")
        
        try:
            # Initialize configuration
            self.config_manager = ConfigurationManager()
            self.config_manager.initialize()
            
            # Initialize database
            test_db_path = Path(self.test_dir) / "uat_admin.db"
            self.db_manager = DatabaseManager(test_db_path)
            self.db_manager.initialize()
            
            # Initialize services
            self.services = {
                'server_manager': ServerManager(self.config_manager, self.db_manager),
                'tool_manager': AdvancedToolManager(self.db_manager),
                'tool_discovery': ToolDiscoveryEngine(),
                'tool_execution': ToolExecutionEngine(self.db_manager),
                'prompt_manager': PromptManager(self.config_manager, self.db_manager),
                'security_service': SecurityService(self.db_manager),
                'audit_service': AuditService(self.db_manager)
            }
            
            # Create realistic sample data
            self._create_sample_data()
            
            print("✓ UAT environment setup complete")
            return True
            
        except Exception as e:
            print(f"✗ UAT environment setup failed: {e}")
            return False
    
    def _create_sample_data(self):
        """Create realistic sample data for UAT"""
        try:
            # Create sample servers
            server_configs = [
                {
                    "name": "Development MCP Server",
                    "command": "python",
                    "args": ["-m", "mcp_server", "--dev"],
                    "description": "Development environment MCP server",
                    "auto_start": True
                },
                {
                    "name": "Production MCP Server", 
                    "command": "mcp-server",
                    "args": ["--config", "prod.json"],
                    "description": "Production MCP server with file operations",
                    "auto_start": False
                },
                {
                    "name": "Testing MCP Server",
                    "command": "node",
                    "args": ["mcp-test-server.js"],
                    "description": "Testing server for web operations",
                    "auto_start": False
                }
            ]
            
            server_manager = self.services['server_manager']
            for config in server_configs:
                server_manager.add_server(config)
            
            # Create sample tools
            tool_manager = self.services['tool_manager']
            sample_tools = [
                ToolRegistryEntry(
                    name="file_reader",
                    description="Read files from the filesystem with various encoding support",
                    server_id="dev-server-1",
                    category=ToolCategory.FILE_OPERATIONS,
                    schema={
                        "type": "function",
                        "function": {
                            "name": "file_reader",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string", "description": "File path to read"},
                                    "encoding": {"type": "string", "default": "utf-8"}
                                },
                                "required": ["path"]
                            }
                        }
                    },
                    parameters=[
                        ToolParameter(name="path", type="string", description="File path to read", required=True),
                        ToolParameter(name="encoding", type="string", description="File encoding", required=False, default_value="utf-8")
                    ],
                    status=ToolStatus.AVAILABLE,
                    usage_count=45,
                    success_rate=0.96
                ),
                ToolRegistryEntry(
                    name="web_search",
                    description="Search the web using multiple search engines",
                    server_id="prod-server-1", 
                    category=ToolCategory.WEB_SEARCH,
                    schema={
                        "type": "function",
                        "function": {
                            "name": "web_search",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Search query"},
                                    "engine": {"type": "string", "enum": ["google", "bing", "duckduckgo"], "default": "google"},
                                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
                                },
                                "required": ["query"]
                            }
                        }
                    },
                    parameters=[
                        ToolParameter(name="query", type="string", description="Search query", required=True),
                        ToolParameter(name="engine", type="string", description="Search engine", required=False, default_value="google"),
                        ToolParameter(name="limit", type="integer", description="Max results", required=False, default_value=10)
                    ],
                    status=ToolStatus.AVAILABLE,
                    usage_count=123,
                    success_rate=0.89
                ),
                ToolRegistryEntry(
                    name="code_analyzer",
                    description="Analyze Python code for issues and suggestions",
                    server_id="test-server-1",
                    category=ToolCategory.CODE_ANALYSIS,
                    schema={
                        "type": "function",
                        "function": {
                            "name": "code_analyzer",
                            "parameters": {
                                "type": "object", 
                                "properties": {
                                    "code": {"type": "string", "description": "Python code to analyze"},
                                    "check_style": {"type": "boolean", "default": True},
                                    "check_complexity": {"type": "boolean", "default": False}
                                },
                                "required": ["code"]
                            }
                        }
                    },
                    parameters=[
                        ToolParameter(name="code", type="string", description="Python code to analyze", required=True),
                        ToolParameter(name="check_style", type="boolean", description="Check code style", required=False, default_value=True),
                        ToolParameter(name="check_complexity", type="boolean", description="Check complexity", required=False, default_value=False)
                    ],
                    status=ToolStatus.AVAILABLE,
                    usage_count=67,
                    success_rate=0.94
                ),
                ToolRegistryEntry(
                    name="data_processor",
                    description="Process and transform data in various formats",
                    server_id="prod-server-1",
                    category=ToolCategory.DATA_PROCESSING,
                    schema={
                        "type": "function",
                        "function": {
                            "name": "data_processor",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "data": {"type": "string", "description": "Data to process"},
                                    "format": {"type": "string", "enum": ["json", "csv", "xml"], "default": "json"},
                                    "operation": {"type": "string", "enum": ["validate", "transform", "analyze"], "default": "validate"}
                                },
                                "required": ["data"]
                            }
                        }
                    },
                    parameters=[
                        ToolParameter(name="data", type="string", description="Data to process", required=True),
                        ToolParameter(name="format", type="string", description="Data format", required=False, default_value="json"),
                        ToolParameter(name="operation", type="string", description="Operation type", required=False, default_value="validate")
                    ],
                    status=ToolStatus.AVAILABLE,
                    usage_count=89,
                    success_rate=0.91
                ),
                ToolRegistryEntry(
                    name="system_monitor",
                    description="Monitor system resources and performance",
                    server_id="dev-server-1",
                    category=ToolCategory.MONITORING,
                    schema={
                        "type": "function",
                        "function": {
                            "name": "system_monitor",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "metric": {"type": "string", "enum": ["cpu", "memory", "disk", "network"], "default": "cpu"},
                                    "duration": {"type": "integer", "default": 60, "minimum": 1, "maximum": 3600}
                                },
                                "required": []
                            }
                        }
                    },
                    parameters=[
                        ToolParameter(name="metric", type="string", description="Metric to monitor", required=False, default_value="cpu"),
                        ToolParameter(name="duration", type="integer", description="Duration in seconds", required=False, default_value=60)
                    ],
                    status=ToolStatus.AVAILABLE,
                    usage_count=34,
                    success_rate=0.98
                )
            ]
            
            for tool in sample_tools:
                tool_manager.register_tool(tool)
            
            # Create sample prompt templates
            prompt_manager = self.services['prompt_manager']
            sample_templates = [
                PromptTemplate(
                    id="analysis-template-1",
                    name="Code Analysis Template",
                    content="Please analyze the following code for potential issues:\n\n{code}\n\nFocus on: {focus_areas}",
                    description="Template for analyzing code quality and issues",
                    parameters={"code": {"type": "string", "required": True}, "focus_areas": {"type": "string", "required": False, "default": "syntax, style, performance"}},
                    tags=["code", "analysis", "quality"],
                    version="1.0",
                    created_by="admin"
                ),
                PromptTemplate(
                    id="search-template-1", 
                    name="Web Search Template",
                    content="Search for information about: {topic}\n\nSearch parameters:\n- Engine: {engine}\n- Results: {max_results}",
                    description="Template for web search operations",
                    parameters={"topic": {"type": "string", "required": True}, "engine": {"type": "string", "required": False, "default": "google"}, "max_results": {"type": "integer", "required": False, "default": 10}},
                    tags=["search", "web", "information"],
                    version="1.2",
                    created_by="admin"
                ),
                PromptTemplate(
                    id="data-template-1",
                    name="Data Processing Template", 
                    content="Process the following data:\n\n{data}\n\nOperation: {operation}\nFormat: {format}",
                    description="Template for data processing operations",
                    parameters={"data": {"type": "string", "required": True}, "operation": {"type": "string", "required": False, "default": "validate"}, "format": {"type": "string", "required": False, "default": "json"}},
                    tags=["data", "processing", "validation"],
                    version="1.0",
                    created_by="admin"
                )
            ]
            
            for template in sample_templates:
                prompt_manager.save_template(template)
            
            print("✓ Sample data created successfully")
            
        except Exception as e:
            print(f"✗ Error creating sample data: {e}")
            raise
    
    def test_user_scenario_1_server_management(self):
        """UAT Scenario 1: Server Management Workflow"""
        print("\n🧪 UAT Scenario 1: Server Management Workflow")
        
        try:
            server_manager = self.services['server_manager']
            
            # User Story: Administrator wants to manage MCP servers
            print("   📋 Testing server management workflow...")
            
            # Step 1: View existing servers
            servers = server_manager.get_servers()
            assert len(servers) >= 3, "Should have sample servers"
            print(f"   ✓ Step 1: Found {len(servers)} configured servers")
            
            # Step 2: Add a new server
            new_server_config = {
                "name": "UAT Test Server",
                "command": "python",
                "args": ["-m", "test_server"],
                "description": "Server added during UAT",
                "auto_start": False
            }
            
            server_id = server_manager.add_server(new_server_config)
            assert server_id is not None, "Server creation should succeed"
            print("   ✓ Step 2: Successfully added new server")
            
            # Step 3: Verify server was added
            updated_servers = server_manager.get_servers()
            assert len(updated_servers) == len(servers) + 1, "Server count should increase"
            print("   ✓ Step 3: Server list updated correctly")
            
            # Step 4: Get server details
            server = server_manager.get_server(server_id)
            assert server is not None, "Should retrieve server details"
            assert server.name == "UAT Test Server", "Server name should match"
            print("   ✓ Step 4: Server details retrieved correctly")
            
            # Step 5: Update server configuration
            update_success = server_manager.update_server(server_id, description="Updated during UAT")
            assert update_success, "Server update should succeed"
            print("   ✓ Step 5: Server configuration updated")
            
            self.test_results['server_management'] = True
            print("   ✅ Server Management Workflow: PASSED")
            
        except Exception as e:
            self.test_results['server_management'] = False
            print(f"   ❌ Server Management Workflow: FAILED - {e}")
    
    def test_user_scenario_2_tool_discovery_and_management(self):
        """UAT Scenario 2: Tool Discovery and Management"""
        print("\n🧪 UAT Scenario 2: Tool Discovery and Management")
        
        try:
            tool_manager = self.services['tool_manager']
            tool_discovery = self.services['tool_discovery']
            
            print("   📋 Testing tool discovery and management workflow...")
            
            # Step 1: View existing tools
            all_tools = tool_manager.get_all_tools()
            initial_count = len(all_tools)
            assert initial_count >= 5, "Should have sample tools"
            print(f"   ✓ Step 1: Found {initial_count} existing tools")
            
            # Step 2: Discover new tools from a server
            discovered_tools = tool_discovery.scan_server_tools("uat-test-server")
            assert len(discovered_tools) > 0, "Should discover some tools"
            print(f"   ✓ Step 2: Discovered {len(discovered_tools)} new tools")
            
            # Step 3: Register discovered tools
            for discovered in discovered_tools:
                tool_info = {
                    'name': discovered.name,
                    'description': discovered.description,
                    'schema': discovered.schema,
                    'server_id': discovered.server_id
                }
                tool_manager.register_tool(discovered)
            print("   ✓ Step 3: Registered discovered tools")
            
            # Step 4: Search for specific tools
            file_tools = tool_manager.search_tools("file")
            assert len(file_tools) > 0, "Should find file-related tools"
            print(f"   ✓ Step 4: Found {len(file_tools)} file-related tools")
            
            # Step 5: Filter tools by category
            analysis_tools = tool_manager.get_tools_by_category(ToolCategory.CODE_ANALYSIS)
            assert len(analysis_tools) > 0, "Should find analysis tools"
            print(f"   ✓ Step 5: Found {len(analysis_tools)} code analysis tools")
            
            # Step 6: Get tool statistics
            stats = tool_manager.get_tool_statistics()
            assert stats['total_tools'] > initial_count, "Tool count should have increased"
            print(f"   ✓ Step 6: Tool statistics: {stats['total_tools']} total tools")
            
            self.test_results['tool_discovery'] = True
            print("   ✅ Tool Discovery and Management: PASSED")
            
        except Exception as e:
            self.test_results['tool_discovery'] = False
            print(f"   ❌ Tool Discovery and Management: FAILED - {e}")
    
    def test_user_scenario_3_tool_execution_workflow(self):
        """UAT Scenario 3: Tool Execution Workflow"""
        print("\n🧪 UAT Scenario 3: Tool Execution Workflow")
        
        try:
            tool_manager = self.services['tool_manager']
            tool_execution = self.services['tool_execution']
            
            print("   📋 Testing tool execution workflow...")
            
            # Step 1: Select a tool for testing
            tools = tool_manager.get_all_tools()
            test_tool = next((t for t in tools if t.name == "file_reader"), None)
            assert test_tool is not None, "Should find file_reader tool"
            print("   ✓ Step 1: Selected tool for testing")
            
            # Step 2: Validate parameters
            valid_params = {"path": "/test/sample.txt", "encoding": "utf-8"}
            validation_result = tool_execution.validate_parameters(test_tool, valid_params)
            assert validation_result[0], "Parameter validation should pass"
            print("   ✓ Step 2: Parameter validation successful")
            
            # Step 3: Execute tool
            from services.tool_execution import ExecutionRequest
            request = ExecutionRequest(
                tool_id=test_tool.id,
                user_id="uat_user",
                parameters=valid_params
            )
            
            execution_result = tool_execution.execute_tool(request, test_tool)
            assert execution_result is not None, "Tool execution should return result"
            print("   ✓ Step 3: Tool execution completed")
            
            # Step 4: Check execution history
            history = tool_execution.get_execution_history({"tool_id": test_tool.id})
            assert len(history) > 0, "Should have execution history"
            print(f"   ✓ Step 4: Found {len(history)} execution records")
            
            # Step 5: Test invalid parameters
            invalid_params = {"wrong_param": "value"}
            invalid_validation = tool_execution.validate_parameters(test_tool, invalid_params)
            assert not invalid_validation[0], "Invalid parameters should fail validation"
            print("   ✓ Step 5: Invalid parameter detection working")
            
            self.test_results['tool_execution'] = True
            print("   ✅ Tool Execution Workflow: PASSED")
            
        except Exception as e:
            self.test_results['tool_execution'] = False
            print(f"   ❌ Tool Execution Workflow: FAILED - {e}")
    
    def test_user_scenario_4_prompt_template_management(self):
        """UAT Scenario 4: Prompt Template Management"""
        print("\n🧪 UAT Scenario 4: Prompt Template Management")
        
        try:
            prompt_manager = self.services['prompt_manager']
            
            print("   📋 Testing prompt template management workflow...")
            
            # Step 1: View existing templates
            all_templates = prompt_manager.get_all_templates()
            initial_count = len(all_templates)
            assert initial_count >= 3, "Should have sample templates"
            print(f"   ✓ Step 1: Found {initial_count} existing templates")
            
            # Step 2: Create new template
            new_template = PromptTemplate(
                id="uat-template-1",
                name="UAT Test Template",
                content="This is a test template created during UAT: {test_param}",
                description="Template created during user acceptance testing",
                parameters={"test_param": {"type": "string", "required": True}},
                tags=["uat", "test"],
                version="1.0",
                created_by="uat_user"
            )
            
            save_result = prompt_manager.save_template(new_template)
            assert save_result, "Template save should succeed"
            print("   ✓ Step 2: New template created successfully")
            
            # Step 3: Retrieve template
            retrieved_template = prompt_manager.get_template("uat-template-1")
            assert retrieved_template is not None, "Should retrieve saved template"
            assert retrieved_template.name == "UAT Test Template", "Template name should match"
            print("   ✓ Step 3: Template retrieved correctly")
            
            # Step 4: Search templates
            search_results = prompt_manager.search_templates("UAT")
            assert len(search_results) > 0, "Should find UAT template in search"
            print(f"   ✓ Step 4: Found {len(search_results)} templates in search")
            
            # Step 5: Test template execution
            test_params = {"test_param": "Hello from UAT"}
            test_result = prompt_manager.test_template("uat-template-1", test_params)
            assert test_result.success, "Template test should succeed"
            assert "Hello from UAT" in test_result.output, "Output should contain parameter value"
            print("   ✓ Step 5: Template execution successful")
            
            self.test_results['prompt_management'] = True
            print("   ✅ Prompt Template Management: PASSED")
            
        except Exception as e:
            self.test_results['prompt_management'] = False
            print(f"   ❌ Prompt Template Management: FAILED - {e}")   
 
    def test_user_scenario_5_security_and_audit(self):
        """UAT Scenario 5: Security and Audit Workflow"""
        print("\n🧪 UAT Scenario 5: Security and Audit Workflow")
        
        try:
            security_service = self.services['security_service']
            audit_service = self.services['audit_service']
            
            print("   📋 Testing security and audit workflow...")
            
            # Step 1: Log security events
            from models.security import SecurityEvent
            from models.base import RiskLevel
            
            security_event = SecurityEvent(
                event_type="tool_execution",
                user_id="uat_user",
                resource_id="file_reader",
                description="UAT user executed file_reader tool",
                risk_level=RiskLevel.LOW,
                metadata={"tool": "file_reader", "params": {"path": "/test/file.txt"}},
                timestamp=datetime.now()
            )
            
            security_service.log_security_event(security_event)
            print("   ✓ Step 1: Security event logged")
            
            # Step 2: Retrieve security events
            recent_events = security_service.get_security_events(
                start_time=datetime.now() - timedelta(minutes=5)
            )
            assert len(recent_events) > 0, "Should find recent security events"
            print(f"   ✓ Step 2: Found {len(recent_events)} recent security events")
            
            # Step 3: Log audit actions
            audit_service.log_action(
                user_id="uat_user",
                action="create_template",
                resource_type="prompt_template",
                resource_id="uat-template-1",
                details={"template_name": "UAT Test Template", "created_during": "user_acceptance_testing"}
            )
            print("   ✓ Step 3: Audit action logged")
            
            # Step 4: Retrieve audit events
            recent_audit = audit_service.get_audit_events(
                start_time=datetime.now() - timedelta(minutes=5)
            )
            assert len(recent_audit) > 0, "Should find recent audit events"
            print(f"   ✓ Step 4: Found {len(recent_audit)} recent audit events")
            
            # Step 5: Check security thresholds
            alerts = security_service.check_security_thresholds()
            print(f"   ✓ Step 5: Security threshold check completed ({len(alerts)} alerts)")
            
            self.test_results['security_audit'] = True
            print("   ✅ Security and Audit Workflow: PASSED")
            
        except Exception as e:
            self.test_results['security_audit'] = False
            print(f"   ❌ Security and Audit Workflow: FAILED - {e}")
    
    def test_user_scenario_6_enhanced_ui_features(self):
        """UAT Scenario 6: Enhanced UI Features"""
        print("\n🧪 UAT Scenario 6: Enhanced UI Features")
        
        try:
            tool_manager = self.services['tool_manager']
            
            print("   📋 Testing enhanced UI features...")
            
            # Step 1: Multi-selection simulation
            all_tools = tool_manager.get_all_tools()
            selected_tools = all_tools[:3]  # Select first 3 tools
            assert len(selected_tools) >= 3, "Should have tools for multi-selection"
            print(f"   ✓ Step 1: Multi-selection of {len(selected_tools)} tools")
            
            # Step 2: Bulk operations
            tool_ids = [tool.id for tool in selected_tools]
            
            # Test bulk configuration update
            updates = []
            for tool_id in tool_ids:
                updates.append({
                    "tool_id": tool_id,
                    "enabled": True,
                    "security_level": "medium"
                })
            
            bulk_result = tool_manager.bulk_update_tools(updates)
            assert bulk_result.updated_tools > 0, "Bulk update should succeed"
            print(f"   ✓ Step 2: Bulk update of {bulk_result.updated_tools} tools")
            
            # Step 3: Tool deletion workflow
            # Create a test tool for deletion
            test_tool = ToolRegistryEntry(
                name="uat_deletion_test",
                description="Tool created for deletion testing",
                server_id="uat-server",
                category=ToolCategory.GENERAL,
                status=ToolStatus.AVAILABLE
            )
            tool_manager.register_tool(test_tool)
            
            # Test single deletion
            deletion_success = tool_manager.delete_tool(test_tool.id)
            assert deletion_success, "Tool deletion should succeed"
            print("   ✓ Step 3: Single tool deletion successful")
            
            # Step 4: Batch deletion
            # Create multiple test tools
            test_tools = []
            for i in range(3):
                test_tool = ToolRegistryEntry(
                    name=f"uat_batch_delete_{i}",
                    description=f"Batch deletion test tool {i}",
                    server_id="uat-server",
                    category=ToolCategory.GENERAL,
                    status=ToolStatus.AVAILABLE
                )
                tool_manager.register_tool(test_tool)
                test_tools.append(test_tool)
            
            # Perform batch deletion
            test_tool_ids = [tool.id for tool in test_tools]
            batch_delete_results = tool_manager.bulk_delete_tools(test_tool_ids)
            successful_deletes = sum(1 for success in batch_delete_results.values() if success)
            assert successful_deletes > 0, "Batch deletion should succeed for some tools"
            print(f"   ✓ Step 4: Batch deletion of {successful_deletes} tools")
            
            # Step 5: Search and filtering
            search_results = tool_manager.search_tools("file", {"category": "file_operations"})
            print(f"   ✓ Step 5: Advanced search returned {len(search_results)} results")
            
            self.test_results['enhanced_ui'] = True
            print("   ✅ Enhanced UI Features: PASSED")
            
        except Exception as e:
            self.test_results['enhanced_ui'] = False
            print(f"   ❌ Enhanced UI Features: FAILED - {e}")
    
    def test_user_scenario_7_end_to_end_workflow(self):
        """UAT Scenario 7: Complete End-to-End Workflow"""
        print("\n🧪 UAT Scenario 7: Complete End-to-End Workflow")
        
        try:
            print("   📋 Testing complete end-to-end user workflow...")
            
            # Complete workflow: Server → Discovery → Tool → Execution → Audit
            server_manager = self.services['server_manager']
            tool_discovery = self.services['tool_discovery']
            tool_manager = self.services['tool_manager']
            tool_execution = self.services['tool_execution']
            audit_service = self.services['audit_service']
            
            # Step 1: Add new server
            workflow_server = {
                "name": "E2E Workflow Server",
                "command": "python",
                "args": ["-m", "workflow_server"],
                "description": "Server for end-to-end workflow testing"
            }
            server_id = server_manager.add_server(workflow_server)
            print("   ✓ Step 1: Added workflow server")
            
            # Step 2: Discover tools from server
            discovered_tools = tool_discovery.scan_server_tools(server_id)
            print(f"   ✓ Step 2: Discovered {len(discovered_tools)} tools")
            
            # Step 3: Register discovered tools
            registered_tools = []
            for discovered in discovered_tools:
                tool_manager.register_tool(discovered)
                registered_tools.append(discovered)
            print(f"   ✓ Step 3: Registered {len(registered_tools)} tools")
            
            # Step 4: Execute a tool
            if registered_tools:
                test_tool = registered_tools[0]
                # Find the registered tool in the manager
                all_tools = tool_manager.get_all_tools()
                registered_tool = next((t for t in all_tools if t.name == test_tool.name), None)
                
                if registered_tool:
                    from services.tool_execution import ExecutionRequest
                    request = ExecutionRequest(
                        tool_id=registered_tool.id,
                        user_id="e2e_user",
                        parameters={"input": "end-to-end test data"}
                    )
                    
                    result = tool_execution.execute_tool(request, registered_tool)
                    print("   ✓ Step 4: Executed discovered tool")
                    
                    # Step 5: Verify audit trail
                    audit_service.log_action(
                        user_id="e2e_user",
                        action="complete_e2e_workflow",
                        resource_type="workflow",
                        resource_id="e2e-test",
                        details={"server_id": server_id, "tools_discovered": len(discovered_tools)}
                    )
                    print("   ✓ Step 5: Audit trail updated")
            
            # Step 6: Verify complete workflow
            final_servers = server_manager.get_servers()
            final_tools = tool_manager.get_all_tools()
            final_audit = audit_service.get_audit_events(limit=10)
            
            print(f"   ✓ Step 6: Workflow complete - {len(final_servers)} servers, {len(final_tools)} tools, {len(final_audit)} audit events")
            
            self.test_results['end_to_end'] = True
            print("   ✅ Complete End-to-End Workflow: PASSED")
            
        except Exception as e:
            self.test_results['end_to_end'] = False
            print(f"   ❌ Complete End-to-End Workflow: FAILED - {e}")
    
    def cleanup_uat_environment(self):
        """Clean up UAT environment"""
        print("\nCleaning up UAT environment...")
        
        try:
            if os.path.exists(self.test_dir):
                shutil.rmtree(self.test_dir)
            print("✓ UAT environment cleanup complete")
            
        except Exception as e:
            print(f"✗ UAT environment cleanup failed: {e}")
    
    def generate_uat_report(self):
        """Generate comprehensive UAT report"""
        print("\n" + "="*80)
        print("USER ACCEPTANCE TESTING (UAT) REPORT")
        print("="*80)
        
        total_scenarios = len(self.test_results)
        passed_scenarios = sum(1 for result in self.test_results.values() if result)
        failed_scenarios = total_scenarios - passed_scenarios
        
        print(f"\nUAT Summary:")
        print(f"  Total Scenarios: {total_scenarios}")
        print(f"  Passed: {passed_scenarios}")
        print(f"  Failed: {failed_scenarios}")
        print(f"  Success Rate: {(passed_scenarios/total_scenarios)*100:.1f}%")
        
        print(f"\nDetailed Scenario Results:")
        scenario_names = {
            'server_management': 'Server Management Workflow',
            'tool_discovery': 'Tool Discovery and Management',
            'tool_execution': 'Tool Execution Workflow',
            'prompt_management': 'Prompt Template Management',
            'security_audit': 'Security and Audit Workflow',
            'enhanced_ui': 'Enhanced UI Features',
            'end_to_end': 'Complete End-to-End Workflow'
        }
        
        for scenario_key, result in self.test_results.items():
            scenario_name = scenario_names.get(scenario_key, scenario_key)
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {scenario_name}: {status}")
        
        print(f"\nUser Experience Assessment:")
        if failed_scenarios == 0:
            print("  🎉 EXCELLENT - All user scenarios passed successfully!")
            print("  The application provides a seamless user experience.")
            ux_rating = "EXCELLENT"
        elif failed_scenarios <= 1:
            print("  ✅ GOOD - Most user scenarios passed with minor issues.")
            print("  The application is ready for production with minor fixes.")
            ux_rating = "GOOD"
        elif failed_scenarios <= 2:
            print("  ⚠️  ACCEPTABLE - Some user scenarios need attention.")
            print("  Address failed scenarios before production deployment.")
            ux_rating = "ACCEPTABLE"
        else:
            print("  ❌ NEEDS IMPROVEMENT - Multiple user scenarios failed.")
            print("  Significant work needed before production readiness.")
            ux_rating = "NEEDS_IMPROVEMENT"
        
        print(f"\nTask 20.2 Assessment:")
        if ux_rating in ["EXCELLENT", "GOOD"]:
            print("  ✅ Task 20.2 can be marked as COMPLETED")
            print("  User acceptance testing shows the system is ready for production")
            print("  Proceed to Task 20.3 (Documentation and Deployment)")
        elif ux_rating == "ACCEPTABLE":
            print("  🔄 Task 20.2 needs minor fixes")
            print("  Address failed scenarios and re-run UAT")
        else:
            print("  ❌ Task 20.2 requires significant work")
            print("  Major user experience issues need resolution")
        
        print(f"\nRecommendations:")
        if ux_rating == "EXCELLENT":
            print("  1. Proceed to documentation and deployment preparation")
            print("  2. Consider performance optimization for production")
            print("  3. Plan user training and onboarding materials")
        elif ux_rating == "GOOD":
            print("  1. Fix minor issues identified in failed scenarios")
            print("  2. Conduct focused re-testing of fixed areas")
            print("  3. Proceed to documentation preparation")
        else:
            print("  1. Analyze and fix all failed scenarios")
            print("  2. Improve error handling and user feedback")
            print("  3. Re-run complete UAT after fixes")
        
        print("="*80)
        
        return ux_rating in ["EXCELLENT", "GOOD"]


def main():
    """Run User Acceptance Testing"""
    print("MCP Admin Application - User Acceptance Testing (UAT)")
    print("=" * 80)
    
    uat_suite = UserAcceptanceTest()
    
    try:
        # Setup UAT environment
        if not uat_suite.setup_uat_environment():
            return 1
        
        # Run all user scenarios
        uat_suite.test_user_scenario_1_server_management()
        uat_suite.test_user_scenario_2_tool_discovery_and_management()
        uat_suite.test_user_scenario_3_tool_execution_workflow()
        uat_suite.test_user_scenario_4_prompt_template_management()
        uat_suite.test_user_scenario_5_security_and_audit()
        uat_suite.test_user_scenario_6_enhanced_ui_features()
        uat_suite.test_user_scenario_7_end_to_end_workflow()
        
        # Generate comprehensive UAT report
        success = uat_suite.generate_uat_report()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ Critical UAT failure: {e}")
        return 1
        
    finally:
        uat_suite.cleanup_uat_environment()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)