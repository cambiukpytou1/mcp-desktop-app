#!/usr/bin/env python3
"""
Basic Test Script for MCP Admin Application
===========================================

Simple test to verify core functionality works correctly.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from core.config import ConfigurationManager
from data.database import DatabaseManager
from services.server_manager import ServerManager
from models.server import MCPServer
from models.base import ServerStatus


def test_configuration_manager():
    """Test configuration manager."""
    print("Testing Configuration Manager...")
    
    # Use temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override the config directory for testing
        config_manager = ConfigurationManager()
        config_manager.config_dir = Path(temp_dir) / "config"
        config_manager.data_dir = Path(temp_dir) / "data"
        config_manager.templates_dir = Path(temp_dir) / "templates"
        
        # Initialize
        config_manager.initialize()
        
        # Test app settings
        settings = config_manager.get_app_settings()
        assert settings.theme == "light"
        assert settings.auto_refresh_interval == 5
        
        # Test server config
        servers_config = config_manager.get_servers_config()
        assert "servers" in servers_config
        assert isinstance(servers_config["servers"], list)
        
        print("✓ Configuration Manager tests passed")


def test_database_manager():
    """Test database manager."""
    print("Testing Database Manager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        db_manager = DatabaseManager(db_path)
        
        # Initialize database
        db_manager.initialize()
        
        # Verify tables were created
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                "security_events",
                "audit_events", 
                "monitoring_metrics",
                "llm_usage_stats",
                "alerts"
            ]
            
            for table in expected_tables:
                assert table in tables, f"Table {table} not found"
        
        print("✓ Database Manager tests passed")


def test_server_manager():
    """Test server manager."""
    print("Testing Server Manager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup managers
        config_manager = ConfigurationManager()
        config_manager.config_dir = Path(temp_dir) / "config"
        config_manager.data_dir = Path(temp_dir) / "data"
        config_manager.templates_dir = Path(temp_dir) / "templates"
        config_manager.initialize()
        
        db_manager = DatabaseManager(config_manager.database_path)
        db_manager.initialize()
        
        server_manager = ServerManager(config_manager, db_manager)
        
        # Test adding a server
        server = server_manager.add_server(
            name="Test Server",
            command="echo",
            args=["hello"],
            description="Test server for unit testing"
        )
        
        assert server.name == "Test Server"
        assert server.command == "echo"
        assert server.args == ["hello"]
        assert server.status == ServerStatus.STOPPED
        
        # Test getting servers
        servers = server_manager.get_all_servers()
        assert len(servers) == 1
        assert servers[0].id == server.id
        
        # Test updating server
        success = server_manager.update_server(
            server.id,
            name="Updated Test Server",
            description="Updated description"
        )
        assert success
        
        updated_server = server_manager.get_server(server.id)
        assert updated_server.name == "Updated Test Server"
        assert updated_server.description == "Updated description"
        
        # Test removing server
        success = server_manager.remove_server(server.id)
        assert success
        
        servers = server_manager.get_all_servers()
        assert len(servers) == 0
        
        print("✓ Server Manager tests passed")


def test_server_validation():
    """Test server configuration validation."""
    print("Testing Server Validation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = ConfigurationManager()
        config_manager.config_dir = Path(temp_dir) / "config"
        config_manager.data_dir = Path(temp_dir) / "data"
        config_manager.templates_dir = Path(temp_dir) / "templates"
        config_manager.initialize()
        
        db_manager = DatabaseManager(config_manager.database_path)
        db_manager.initialize()
        
        server_manager = ServerManager(config_manager, db_manager)
        
        # Test valid command
        result = server_manager.validate_server_config("python", ["--version"])
        assert result["valid"] == True
        
        # Test empty command
        result = server_manager.validate_server_config("", [])
        assert result["valid"] == False
        assert len(result["errors"]) > 0
        
        print("✓ Server Validation tests passed")


def main():
    """Run all tests."""
    print("Running MCP Admin Application Tests")
    print("=" * 40)
    
    try:
        test_configuration_manager()
        test_database_manager()
        test_server_manager()
        test_server_validation()
        
        print("\n" + "=" * 40)
        print("✅ All tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()