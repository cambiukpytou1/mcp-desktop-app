#!/usr/bin/env python3
"""
MCP Admin Application Demo
=========================

Demonstration script showing the enhanced MCP Admin application features.
"""

import sys
import os
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from core.app import MCPAdminApp
from core.config import ConfigurationManager
from services.server_manager import ServerManager
from data.database import DatabaseManager


def setup_demo_data():
    """Setup some demo data for the application."""
    print("Setting up demo data...")
    
    try:
        # Initialize components
        config_manager = ConfigurationManager()
        config_manager.initialize()
        
        db_manager = DatabaseManager(config_manager.database_path)
        db_manager.initialize()
        
        server_manager = ServerManager(config_manager, db_manager)
        
        # Add some demo servers
        demo_servers = [
            {
                "name": "File System Server",
                "command": "uvx",
                "args": ["mcp-server-filesystem", "/tmp"],
                "description": "MCP server for file system operations"
            },
            {
                "name": "Git Server",
                "command": "uvx", 
                "args": ["mcp-server-git", "--repository", "."],
                "description": "MCP server for Git operations"
            },
            {
                "name": "Web Search Server",
                "command": "uvx",
                "args": ["mcp-server-brave-search"],
                "description": "MCP server for web search capabilities"
            }
        ]
        
        # Check if servers already exist
        existing_servers = server_manager.get_all_servers()
        if len(existing_servers) == 0:
            for server_config in demo_servers:
                server = server_manager.add_server(**server_config)
                print(f"Added demo server: {server.name}")
        else:
            print(f"Found {len(existing_servers)} existing servers")
        
        print("Demo data setup complete!")
        
    except Exception as e:
        print(f"Failed to setup demo data: {e}")


def main():
    """Run the demo application."""
    print("MCP Admin Application - Enhanced Edition")
    print("=" * 50)
    print()
    
    # Setup demo data
    setup_demo_data()
    print()
    
    print("Starting MCP Admin Application...")
    print("Features demonstrated:")
    print("• Enhanced server management with modern UI")
    print("• Persistent configuration storage")
    print("• SQLite database integration")
    print("• Comprehensive logging system")
    print("• Modular architecture for future enhancements")
    print()
    print("Navigate through the sidebar to explore different sections.")
    print("Try adding, editing, and managing MCP servers!")
    print()
    
    # Start the application
    try:
        app = MCPAdminApp()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()