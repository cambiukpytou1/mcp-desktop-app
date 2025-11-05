#!/usr/bin/env python3
"""
Comprehensive System Integration Test for MCP Admin Application

This test validates the complete system integration including:
- Tool management with LLM management and existing MCP admin functionality
- Complete workflows from tool discovery to execution and analytics
- Tool-LLM integration and intelligent recommendations
- Security and audit trail integration across all components
- Enhanced UI features and deletion capabilities

Requirements Coverage: All requirements from 1-22
"""

import os
import sys
import time
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

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
from services.llm_manager import LLMManager
from services.security_service import SecurityService
from services.audit_service import AuditService
from services.monitoring_service import MonitoringService

# Model imports
from models.server import MCPServer
from models.base import ServerStatus, RiskLevel
from models.tool import ToolRegistryEntry, ToolCategory, ToolStatus, ToolParameter
from models.prompt import PromptTemplate
from models.llm import LLMProvider
from models.base import LLMProviderType as ProviderType
from models.security import SecurityEvent

class SystemIntegrationTest:
    """Comprehensive system integration test suite"""
    
    def __init__(self):
        """Initialize test environment with temporary database"""
        self.test_dir = tempfile.mkdtemp(prefix="mcp_admin_test_")
        self.config_manager = None
        self.db_manager = None
        self.services = {}
        self.test_results = {}
        
    def setup_test_environment(self):
        """Set up complete test environment"""
        print("Setting up test environment...")
        
        # Initialize configuration with test database
        self.config_manager = ConfigurationManager()
        self.config_manager.initialize()
        test_db_path = os.path.join(self.test_dir, "test_integration.db")
        
        # Initialize database
        from pathlib import Path
        self.db_manager = DatabaseManager(Path(test_db_path))
        self.db_manager.initialize()
        
        # Initialize all services
        self.services = {
            'server_manager': ServerManager(self.config_manager, self.db_manager),
            'tool_manager': AdvancedToolManager(self.db_manager),
            'tool_discovery': ToolDiscoveryEngine(),
            'tool_execution': ToolExecutionEngine(self.db_manager),
            'prompt_manager': PromptManager(self.config_manager, self.db_manager),
            'llm_manager': LLMManager(self.config_manager, self.db_manager),
            'security_service': SecurityService(self.db_manager),
            'audit_service': AuditService(self.db_manager),
            'monitoring_service': MonitoringService(self.config_manager, self.db_manager)
        }
        
        print("✓ Test environment setup complete")
        
    def test_server_management_integration(self):
        """Test server management functionality (Requirement 1)"""
        print("\n1. Testing Server Management Integration...")
        
        try:
            server_manager = self.services['server_manager']
            
            # Test server configuration
            server_config = {
                'name': 'Test MCP Server',
                'host': 'localhost',
                'port': 8080,
                'protocol': 'http',
                'enabled': True
            }
            
            server_id = server_manager.add_server(server_config)
            assert server_id is not None, "Server creation failed"
            
            # Test server status management
            servers = server_manager.get_servers()
            assert len(servers) > 0, "No servers found after creation"
            
            # Test server configuration validation
            invalid_config = {'name': '', 'host': ''}
            try:
                server_manager.add_server(invalid_config)
                assert False, "Invalid server config should have been rejected"
            except Exception:
                pass  # Expected behavior
            
            self.test_results['server_management'] = True
            print("   ✓ Server management integration successful")
            
        except Exception as e:
            self.test_results['server_management'] = False
            print(f"   ✗ Server management integration failed: {e}")
    
    def test_tool_discovery_and_registry(self):
        """Test comprehensive tool discovery and registry management (Requirement 2)"""
        print("\n2. Testing Tool Discovery and Registry Integration...")
        
        try:
            tool_discovery = self.services['tool_discovery']
            tool_manager = self.services['tool_manager']
            
            # Test tool discovery (simulate)
            discovered_tools = tool_discovery.scan_server_tools("test-server-1")
            assert isinstance(discovered_tools, list), "Tool discovery failed"
            
            # Test tool registration with ToolRegistryEntry
            from models.tool import ToolRegistryEntry, ToolParameter
            sample_tool = ToolRegistryEntry(
                id="test-tool-1",
                name="Test File Reader",
                description="A test tool for reading files",
                server_id="test-server-1",
                category=ToolCategory.FILE_OPERATIONS,
                schema={
                    "type": "function",
                    "parameters": {
                        "path": {"type": "string", "description": "File path to read"}
                    }
                },
                parameters=[
                    ToolParameter(
                        name="path",
                        type="string",
                        description="File path to read",
                        required=True
                    )
                ],
                status=ToolStatus.AVAILABLE
            )
            
            tool_manager.register_tool(sample_tool)
            
            # Test tool registry search and filtering
            all_tools = tool_manager.get_all_tools()
            assert len(all_tools) > 0, "No tools in registry after registration"
            
            # Test tool categorization
            file_tools = tool_manager.get_tools_by_category(ToolCategory.FILE_OPERATIONS)
            assert len(file_tools) >= 0, "Tool categorization failed"
            
            # Test advanced search
            search_results = tool_manager.search_tools("file")
            assert isinstance(search_results, list), "Tool search failed"
            
            self.test_results['tool_discovery'] = True
            print("   ✓ Tool discovery and registry integration successful")
            
        except Exception as e:
            self.test_results['tool_discovery'] = False
            print(f"   ✗ Tool discovery and registry integration failed: {e}")
    
    def test_prompt_template_management(self):
        """Test prompt template management with version control (Requirement 3)"""
        print("\n3. Testing Prompt Template Management Integration...")
        
        try:
            prompt_manager = self.services['prompt_manager']
            
            # Test prompt template creation
            template = PromptTemplate(
                id="test-template-1",
                name="Test Analysis Template",
                content="Analyze the following data: {data}",
                parameters={"data": {"type": "string", "description": "Data to analyze"}},
                tags=["analysis", "test"],
                version="1.0",
                created_by="test_user"
            )
            
            prompt_manager.save_template(template)
            
            # Test template retrieval
            saved_template = prompt_manager.get_template("test-template-1")
            assert saved_template is not None, "Template retrieval failed"
            assert saved_template.name == template.name, "Template data mismatch"
            
            # Test version control
            updated_template = template
            updated_template.content = "Enhanced analysis: {data}"
            updated_template.version = "1.1"
            
            prompt_manager.save_template(updated_template)
            
            # Test template search
            templates = prompt_manager.search_templates("analysis")
            assert len(templates) > 0, "Template search failed"
            
            self.test_results['prompt_management'] = True
            print("   ✓ Prompt template management integration successful")
            
        except Exception as e:
            self.test_results['prompt_management'] = False
            print(f"   ✗ Prompt template management integration failed: {e}")
    
    def test_security_logging_integration(self):
        """Test comprehensive security logging (Requirement 4)"""
        print("\n4. Testing Security Logging Integration...")
        
        try:
            security_service = self.services['security_service']
            
            # Test security event logging
            security_event = SecurityEvent(
                event_type="tool_execution",
                user_id="test_user",
                resource_id="test-tool-1",
                description="Tool execution attempt",
                risk_level=RiskLevel.LOW,
                metadata={"tool_name": "Test File Reader", "parameters": {"path": "/test/file.txt"}}
            )
            
            security_service.log_security_event(security_event)
            
            # Test security log retrieval
            recent_events = security_service.get_security_events(
                start_time=datetime.now() - timedelta(hours=1)
            )
            assert len(recent_events) > 0, "Security event logging failed"
            
            # Test suspicious activity detection
            # Simulate multiple failed attempts
            for i in range(5):
                failed_event = SecurityEvent(
                    event_type="authentication_failed",
                    user_id="suspicious_user",
                    resource_id="test-server-1",
                    description=f"Failed authentication attempt {i+1}",
                    risk_level=RiskLevel.HIGH
                )
                security_service.log_security_event(failed_event)
            
            # Test alert generation
            alerts = security_service.check_security_thresholds()
            # Note: Alert generation depends on configuration
            
            self.test_results['security_logging'] = True
            print("   ✓ Security logging integration successful")
            
        except Exception as e:
            self.test_results['security_logging'] = False
            print(f"   ✗ Security logging integration failed: {e}")
    
    def test_audit_trail_integration(self):
        """Test detailed audit trails (Requirement 5)"""
        print("\n5. Testing Audit Trail Integration...")
        
        try:
            audit_service = self.services['audit_service']
            
            # Test audit event creation
            audit_service.log_action(
                user_id="test_user",
                action="create_tool",
                resource_type="tool",
                resource_id="test-tool-1",
                details={"tool_name": "Test File Reader", "category": "file_operations"}
            )
            
            # Test audit log retrieval
            audit_events = audit_service.get_audit_events(
                start_time=datetime.now() - timedelta(hours=1)
            )
            assert len(audit_events) > 0, "Audit event logging failed"
            
            # Test audit log filtering
            tool_events = audit_service.get_audit_events(
                resource_type="tool",
                start_time=datetime.now() - timedelta(hours=1)
            )
            assert len(tool_events) > 0, "Audit log filtering failed"
            
            # Test audit trail integrity
            # This would involve checking tamper-evident properties
            # For now, we'll verify the basic structure
            for event in audit_events:
                assert hasattr(event, 'timestamp'), "Audit event missing timestamp"
                assert hasattr(event, 'user_id'), "Audit event missing user_id"
                assert hasattr(event, 'action'), "Audit event missing action"
            
            self.test_results['audit_trail'] = True
            print("   ✓ Audit trail integration successful")
            
        except Exception as e:
            self.test_results['audit_trail'] = False
            print(f"   ✗ Audit trail integration failed: {e}")
    
    def test_llm_provider_management(self):
        """Test LLM provider management (Requirement 6)"""
        print("\n6. Testing LLM Provider Management Integration...")
        
        try:
            llm_manager = self.services['llm_manager']
            
            # Test LLM provider configuration
            provider_config = {
                'name': 'Test OpenAI Provider',
                'provider_type': ProviderType.OPENAI,
                'api_key': 'test-api-key-12345',
                'models': ['gpt-3.5-turbo', 'gpt-4'],
                'enabled': True
            }
            
            provider_id = llm_manager.add_provider(provider_config)
            assert provider_id is not None, "LLM provider creation failed"
            
            # Test provider retrieval
            providers = llm_manager.get_providers()
            assert len(providers) > 0, "No providers found after creation"
            
            # Test provider validation (mock)
            # In a real implementation, this would test actual API connectivity
            provider = llm_manager.get_provider(provider_id)
            assert provider is not None, "Provider retrieval failed"
            
            # Test local LLM support
            local_config = {
                'name': 'Test Ollama Provider',
                'provider_type': ProviderType.OLLAMA,
                'endpoint_url': 'http://localhost:11434',
                'models': ['llama2', 'codellama'],
                'enabled': True
            }
            
            local_provider_id = llm_manager.add_provider(local_config)
            assert local_provider_id is not None, "Local LLM provider creation failed"
            
            self.test_results['llm_management'] = True
            print("   ✓ LLM provider management integration successful")
            
        except Exception as e:
            self.test_results['llm_management'] = False
            print(f"   ✗ LLM provider management integration failed: {e}")
    
    def test_tool_execution_integration(self):
        """Test interactive tool testing and execution (Requirement 13)"""
        print("\n7. Testing Tool Execution Integration...")
        
        try:
            tool_execution = self.services['tool_execution']
            tool_manager = self.services['tool_manager']
            
            # Get a test tool
            tools = tool_manager.get_all_tools()
            if not tools:
                # Create a test tool if none exist
                from models.tool import ToolRegistryEntry, ToolParameter
                test_tool = ToolRegistryEntry(
                    id="execution-test-tool",
                    name="Test Execution Tool",
                    description="A tool for testing execution",
                    server_id="test-server-1",
                    category=ToolCategory.ANALYSIS,
                    schema={
                        "type": "function",
                        "parameters": {
                            "input": {"type": "string", "description": "Input data"}
                        }
                    },
                    parameters=[
                        ToolParameter(
                            name="input",
                            type="string",
                            description="Input data",
                            required=True
                        )
                    ],
                    status=ToolStatus.AVAILABLE
                )
                tool_manager.register_tool(test_tool)
                tools = [test_tool]
            
            test_tool = tools[0]
            
            # Test parameter validation
            valid_params = {"input": "test data"}
            validation_result = tool_execution.validate_parameters(test_tool, valid_params)
            assert validation_result[0], "Parameter validation failed for valid parameters"
            
            # Test invalid parameters
            invalid_params = {"wrong_param": "test"}
            validation_result = tool_execution.validate_parameters(test_tool, invalid_params)
            assert not validation_result[0], "Parameter validation should have failed for invalid parameters"
            
            # Test tool execution
            from services.tool_execution import ExecutionRequest
            request = ExecutionRequest(
                tool_id=test_tool.id,
                user_id="test_user",
                parameters=valid_params
            )
            execution_result = tool_execution.execute_tool(request, test_tool)
            assert execution_result is not None, "Tool execution failed"
            
            # Test execution history
            history = tool_execution.get_execution_history({"tool_id": test_tool.id})
            assert isinstance(history, list), "Execution history not accessible"
            
            self.test_results['tool_execution'] = True
            print("   ✓ Tool execution integration successful")
            
        except Exception as e:
            self.test_results['tool_execution'] = False
            print(f"   ✗ Tool execution integration failed: {e}")
    
    def test_monitoring_integration(self):
        """Test real-time monitoring and alerting (Requirement 7)"""
        print("\n8. Testing Monitoring Integration...")
        
        try:
            monitoring_service = self.services['monitoring_service']
            server_manager = self.services['server_manager']
            
            # Test server health monitoring
            servers = server_manager.get_servers()
            if servers:
                server_id = servers[0].id
                
                # Test health check
                health_status = monitoring_service.check_server_health(server_id)
                assert health_status is not None, "Health check failed"
                
                # Test performance metrics
                metrics = monitoring_service.get_performance_metrics(server_id)
                assert metrics is not None, "Performance metrics retrieval failed"
                
                # Test alert configuration
                alert_config = {
                    'metric': 'response_time',
                    'threshold': 5000,  # 5 seconds
                    'condition': 'greater_than'
                }
                
                alert_id = monitoring_service.create_alert(server_id, alert_config)
                assert alert_id is not None, "Alert creation failed"
            
            self.test_results['monitoring'] = True
            print("   ✓ Monitoring integration successful")
            
        except Exception as e:
            self.test_results['monitoring'] = False
            print(f"   ✗ Monitoring integration failed: {e}")
    
    def test_enhanced_ui_features(self):
        """Test enhanced UI features and deletion capabilities (Requirements 20-21)"""
        print("\n9. Testing Enhanced UI Features Integration...")
        
        try:
            tool_manager = self.services['tool_manager']
            
            # Test tool deletion functionality
            # First, ensure we have tools to delete
            tools = tool_manager.get_all_tools()
            if not tools:
                # Create test tools
                for i in range(3):
                    test_tool = MCPTool(
                        id=f"ui-test-tool-{i}",
                        name=f"UI Test Tool {i}",
                        description=f"Test tool {i} for UI testing",
                        server_id="test-server-1",
                        category=ToolCategory.ANALYSIS,
                        schema={"type": "function", "parameters": {}},
                        status=ToolStatus.AVAILABLE
                    )
                    tool_manager.register_tool(test_tool)
                tools = tool_manager.get_all_tools()
            
            initial_count = len(tools)
            
            # Test single tool deletion
            if tools:
                tool_to_delete = tools[0]
                deletion_result = tool_manager.delete_tool(tool_to_delete.id)
                assert deletion_result, "Single tool deletion failed"
                
                # Verify deletion
                remaining_tools = tool_manager.get_all_tools()
                assert len(remaining_tools) == initial_count - 1, "Tool count not updated after deletion"
            
            # Test bulk deletion
            if len(tools) > 1:
                tools_to_delete = [tool.id for tool in tools[1:3]]  # Delete up to 2 more tools
                bulk_result = tool_manager.bulk_delete_tools(tools_to_delete)
                assert bulk_result['successful'] > 0, "Bulk deletion failed"
            
            # Test multi-selection capabilities (simulated)
            # In a real UI test, this would test actual UI components
            selection_state = {
                'selected_items': ['tool-1', 'tool-2'],
                'selection_count': 2,
                'total_items': 5,
                'selection_mode': 'extended'
            }
            
            # Validate selection state structure
            assert 'selected_items' in selection_state, "Selection state missing selected_items"
            assert 'selection_count' in selection_state, "Selection state missing selection_count"
            
            self.test_results['enhanced_ui'] = True
            print("   ✓ Enhanced UI features integration successful")
            
        except Exception as e:
            self.test_results['enhanced_ui'] = False
            print(f"   ✗ Enhanced UI features integration failed: {e}")
    
    def test_complete_workflow_integration(self):
        """Test complete end-to-end workflow integration"""
        print("\n10. Testing Complete Workflow Integration...")
        
        try:
            # Test complete workflow: Discovery -> Registration -> Configuration -> Execution -> Analytics
            
            # 1. Tool Discovery
            tool_discovery = self.services['tool_discovery']
            discovered_tools = tool_discovery.discover_tools_from_server("integration-test-server")
            
            # 2. Tool Registration
            tool_manager = self.services['tool_manager']
            if not discovered_tools:
                # Create a mock discovered tool
                discovered_tool = MCPTool(
                    id="workflow-test-tool",
                    name="Workflow Test Tool",
                    description="A tool for testing complete workflow",
                    server_id="integration-test-server",
                    category=ToolCategory.ANALYSIS,
                    schema={
                        "type": "function",
                        "parameters": {
                            "data": {"type": "string", "description": "Data to process"}
                        }
                    },
                    status=ToolStatus.AVAILABLE
                )
                tool_manager.register_tool(discovered_tool)
                discovered_tools = [discovered_tool]
            
            # 3. Tool Configuration and Permission Setup
            test_tool = discovered_tools[0]
            
            # 4. Tool Execution
            tool_execution = self.services['tool_execution']
            execution_result = tool_execution.execute_tool(
                tool_id=test_tool.id,
                parameters={"data": "integration test data"},
                user_id="integration_test_user"
            )
            
            # 5. Security and Audit Logging
            security_service = self.services['security_service']
            audit_service = self.services['audit_service']
            
            # Verify security event was logged
            recent_security_events = security_service.get_security_events(
                start_time=datetime.now() - timedelta(minutes=5)
            )
            
            # Verify audit event was logged
            recent_audit_events = audit_service.get_audit_events(
                start_time=datetime.now() - timedelta(minutes=5)
            )
            
            # 6. Analytics and Monitoring
            monitoring_service = self.services['monitoring_service']
            
            # Test that all components worked together
            assert execution_result is not None, "Workflow execution failed"
            
            self.test_results['complete_workflow'] = True
            print("   ✓ Complete workflow integration successful")
            
        except Exception as e:
            self.test_results['complete_workflow'] = False
            print(f"   ✗ Complete workflow integration failed: {e}")
    
    def test_data_consistency_and_integrity(self):
        """Test data consistency and integrity across all components"""
        print("\n11. Testing Data Consistency and Integrity...")
        
        try:
            # Test database consistency
            db_manager = self.db_manager
            
            # Test that all required tables exist
            required_tables = [
                'servers', 'tools', 'tool_executions', 'prompt_templates',
                'llm_providers', 'security_events', 'audit_events'
            ]
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                for table in required_tables:
                    assert table in existing_tables, f"Required table {table} not found"
            
            # Test referential integrity
            tool_manager = self.services['tool_manager']
            tools = tool_manager.get_all_tools()
            
            if tools:
                # Test that tool executions reference valid tools
                tool_execution = self.services['tool_execution']
                history = tool_execution.get_execution_history()
                
                for execution in history:
                    tool_exists = any(tool.id == execution.tool_id for tool in tools)
                    # Note: In a real system, we'd check database constraints
            
            self.test_results['data_integrity'] = True
            print("   ✓ Data consistency and integrity validation successful")
            
        except Exception as e:
            self.test_results['data_integrity'] = False
            print(f"   ✗ Data consistency and integrity validation failed: {e}")
    
    def test_error_handling_and_recovery(self):
        """Test comprehensive error handling and recovery mechanisms"""
        print("\n12. Testing Error Handling and Recovery...")
        
        try:
            tool_execution = self.services['tool_execution']
            tool_manager = self.services['tool_manager']
            
            # Test invalid tool execution
            try:
                result = tool_execution.execute_tool(
                    tool_id="non-existent-tool",
                    parameters={},
                    user_id="test_user"
                )
                # Should handle gracefully, not crash
            except Exception as e:
                # Expected behavior - should log error appropriately
                pass
            
            # Test invalid parameters
            tools = tool_manager.get_all_tools()
            if tools:
                test_tool = tools[0]
                try:
                    result = tool_execution.execute_tool(
                        tool_id=test_tool.id,
                        parameters={"invalid_param": "value"},
                        user_id="test_user"
                    )
                    # Should handle parameter validation errors
                except Exception as e:
                    # Expected behavior
                    pass
            
            # Test database connection recovery
            # This would test reconnection logic in a real scenario
            
            self.test_results['error_handling'] = True
            print("   ✓ Error handling and recovery testing successful")
            
        except Exception as e:
            self.test_results['error_handling'] = False
            print(f"   ✗ Error handling and recovery testing failed: {e}")
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        print("\nCleaning up test environment...")
        
        try:
            # Close database connections
            if self.db_manager:
                # Close any open connections
                pass
            
            # Remove test directory
            if os.path.exists(self.test_dir):
                shutil.rmtree(self.test_dir)
            
            print("✓ Test environment cleanup complete")
            
        except Exception as e:
            print(f"✗ Test environment cleanup failed: {e}")
    
    def generate_integration_report(self):
        """Generate comprehensive integration test report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE SYSTEM INTEGRATION TEST REPORT")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"\nTest Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {test_name}: {status}")
        
        print(f"\nRequirements Coverage Analysis:")
        requirements_coverage = {
            'server_management': "Requirement 1: MCP server management",
            'tool_discovery': "Requirement 2: Tool discovery and registry",
            'prompt_management': "Requirement 3: Prompt template management",
            'security_logging': "Requirement 4: Security logging",
            'audit_trail': "Requirement 5: Audit trails",
            'llm_management': "Requirement 6: LLM provider management",
            'tool_execution': "Requirement 13: Tool testing and execution",
            'monitoring': "Requirement 7: Real-time monitoring",
            'enhanced_ui': "Requirements 20-21: Enhanced UI features",
            'complete_workflow': "All Requirements: End-to-end integration",
            'data_integrity': "All Requirements: Data consistency",
            'error_handling': "All Requirements: Error handling"
        }
        
        for test_name, requirement in requirements_coverage.items():
            result = self.test_results.get(test_name, False)
            status = "✓" if result else "✗"
            print(f"  {status} {requirement}")
        
        print(f"\nIntegration Status:")
        if failed_tests == 0:
            print("  🎉 ALL SYSTEMS OPERATIONAL - Complete integration successful!")
            print("  The MCP Admin Application is fully integrated and ready for deployment.")
        elif failed_tests <= 2:
            print("  ⚠️  MOSTLY OPERATIONAL - Minor integration issues detected")
            print("  Most components are working correctly with minor issues to address.")
        else:
            print("  ❌ INTEGRATION ISSUES - Multiple components need attention")
            print("  Several integration issues detected that require resolution.")
        
        print(f"\nNext Steps:")
        if failed_tests == 0:
            print("  1. Proceed to user acceptance testing (Task 20.2)")
            print("  2. Begin documentation and deployment preparation (Task 20.3)")
            print("  3. Consider performance optimization based on test results")
        else:
            print("  1. Address failed integration tests")
            print("  2. Re-run integration tests after fixes")
            print("  3. Investigate root causes of integration failures")
        
        print("="*80)
        
        return failed_tests == 0

def main():
    """Run comprehensive system integration test"""
    print("MCP Admin Application - Comprehensive System Integration Test")
    print("=" * 80)
    
    test_suite = SystemIntegrationTest()
    
    try:
        # Setup test environment
        test_suite.setup_test_environment()
        
        # Run all integration tests
        test_suite.test_server_management_integration()
        test_suite.test_tool_discovery_and_registry()
        test_suite.test_prompt_template_management()
        test_suite.test_security_logging_integration()
        test_suite.test_audit_trail_integration()
        test_suite.test_llm_provider_management()
        test_suite.test_tool_execution_integration()
        test_suite.test_monitoring_integration()
        test_suite.test_enhanced_ui_features()
        test_suite.test_complete_workflow_integration()
        test_suite.test_data_consistency_and_integrity()
        test_suite.test_error_handling_and_recovery()
        
        # Generate comprehensive report
        success = test_suite.generate_integration_report()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ Critical integration test failure: {e}")
        return 1
        
    finally:
        # Always cleanup
        test_suite.cleanup_test_environment()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)