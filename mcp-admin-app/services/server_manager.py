"""
MCP Server Management Service
============================

Handles MCP server discovery, configuration, lifecycle management, and monitoring.
"""

import logging
import subprocess
import json
import time
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from models.server import MCPServer, MCPTool
from models.base import ServerStatus
from core.config import ConfigurationManager
from data.database import DatabaseManager


class ServerManager:
    """Manages MCP server operations and configurations."""
    
    def __init__(self, config_manager: ConfigurationManager, db_manager: DatabaseManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self._servers: Dict[str, MCPServer] = {}
        self._running_processes: Dict[str, subprocess.Popen] = {}
        
        # Load existing servers
        self._load_servers()
    
    def _load_servers(self):
        """Load servers from configuration."""
        try:
            config = self.config_manager.get_servers_config()
            servers_data = config.get("servers", [])
            
            for server_data in servers_data:
                server = MCPServer.from_dict(server_data)
                self._servers[server.id] = server
            
            self.logger.info(f"Loaded {len(self._servers)} servers from configuration")
            
        except Exception as e:
            self.logger.error(f"Failed to load servers: {e}")
    
    def _save_servers(self):
        """Save servers to configuration."""
        try:
            servers_data = [server.to_dict() for server in self._servers.values()]
            config = {
                "servers": servers_data,
                "last_updated": datetime.now().isoformat()
            }
            self.config_manager.save_servers_config(config)
            
        except Exception as e:
            self.logger.error(f"Failed to save servers: {e}")
            raise
    
    def discover_servers(self) -> List[MCPServer]:
        """Discover available MCP servers."""
        # For now, return configured servers
        # In a full implementation, this would scan for available MCP servers
        return list(self._servers.values())
    
    def add_server(self, name: str, command: str, args: List[str] = None, 
                   env: Dict[str, str] = None, description: str = "") -> MCPServer:
        """Add a new MCP server configuration."""
        try:
            server = MCPServer(
                name=name,
                command=command,
                args=args or [],
                env=env or {},
                description=description,
                status=ServerStatus.STOPPED
            )
            
            self._servers[server.id] = server
            self._save_servers()
            
            self.logger.info(f"Added new server: {name} ({server.id})")
            return server
            
        except Exception as e:
            self.logger.error(f"Failed to add server {name}: {e}")
            raise
    
    def remove_server(self, server_id: str) -> bool:
        """Remove a server configuration."""
        try:
            if server_id not in self._servers:
                return False
            
            # Stop server if running
            if server_id in self._running_processes:
                self.stop_server(server_id)
            
            server_name = self._servers[server_id].name
            del self._servers[server_id]
            self._save_servers()
            
            self.logger.info(f"Removed server: {server_name} ({server_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove server {server_id}: {e}")
            return False
    
    def start_server(self, server_id: str) -> bool:
        """Start an MCP server."""
        try:
            if server_id not in self._servers:
                self.logger.error(f"Server not found: {server_id}")
                return False
            
            server = self._servers[server_id]
            
            # Check if already running
            if server_id in self._running_processes:
                if self._running_processes[server_id].poll() is None:
                    self.logger.warning(f"Server {server.name} is already running")
                    return True
                else:
                    # Process died, clean up
                    del self._running_processes[server_id]
            
            # Start the server process
            cmd = [server.command] + server.args
            env = {**os.environ, **server.env} if server.env else None
            
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to start
            time.sleep(1)
            
            if process.poll() is None:
                # Process is running
                self._running_processes[server_id] = process
                server.status = ServerStatus.RUNNING
                server.last_seen = datetime.now()
                self._save_servers()
                
                self.logger.info(f"Started server: {server.name}")
                return True
            else:
                # Process failed to start
                stdout, stderr = process.communicate()
                self.logger.error(f"Failed to start server {server.name}: {stderr}")
                server.status = ServerStatus.ERROR
                self._save_servers()
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start server {server_id}: {e}")
            if server_id in self._servers:
                self._servers[server_id].status = ServerStatus.ERROR
                self._save_servers()
            return False
    
    def stop_server(self, server_id: str) -> bool:
        """Stop an MCP server."""
        try:
            if server_id not in self._servers:
                return False
            
            server = self._servers[server_id]
            
            if server_id in self._running_processes:
                process = self._running_processes[server_id]
                
                # Try graceful shutdown first
                process.terminate()
                
                # Wait up to 5 seconds for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    process.kill()
                    process.wait()
                
                del self._running_processes[server_id]
                
            server.status = ServerStatus.STOPPED
            self._save_servers()
            
            self.logger.info(f"Stopped server: {server.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop server {server_id}: {e}")
            return False
    
    def restart_server(self, server_id: str) -> bool:
        """Restart an MCP server."""
        if self.stop_server(server_id):
            time.sleep(1)  # Brief pause between stop and start
            return self.start_server(server_id)
        return False
    
    def get_server_status(self, server_id: str) -> ServerStatus:
        """Get the current status of a server."""
        if server_id not in self._servers:
            return ServerStatus.UNKNOWN
        
        server = self._servers[server_id]
        
        # Check if process is still running
        if server_id in self._running_processes:
            process = self._running_processes[server_id]
            if process.poll() is None:
                server.status = ServerStatus.RUNNING
                server.last_seen = datetime.now()
            else:
                # Process died
                del self._running_processes[server_id]
                server.status = ServerStatus.STOPPED
        
        return server.status
    
    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get server by ID."""
        return self._servers.get(server_id)
    
    def get_all_servers(self) -> List[MCPServer]:
        """Get all configured servers."""
        return list(self._servers.values())
    
    def update_server(self, server_id: str, **kwargs) -> bool:
        """Update server configuration."""
        try:
            if server_id not in self._servers:
                return False
            
            server = self._servers[server_id]
            
            # Update allowed fields
            allowed_fields = ['name', 'command', 'args', 'env', 'description', 'auto_start', 'health_check_url']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(server, field, value)
            
            self._save_servers()
            self.logger.info(f"Updated server: {server.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update server {server_id}: {e}")
            return False
    
    def validate_server_config(self, command: str, args: List[str] = None) -> Dict[str, Any]:
        """Validate server configuration."""
        result = {
            "valid": False,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check if command exists
            if not command:
                result["errors"].append("Command is required")
                return result
            
            # Try to find the command
            import shutil
            if not shutil.which(command):
                result["warnings"].append(f"Command '{command}' not found in PATH")
            
            # Basic validation passed
            result["valid"] = len(result["errors"]) == 0
            
        except Exception as e:
            result["errors"].append(f"Validation error: {e}")
        
        return result
    
    def get_server_logs(self, server_id: str, lines: int = 100) -> List[str]:
        """Get recent logs from a server."""
        # In a full implementation, this would read from server log files
        # For now, return placeholder logs
        if server_id in self._servers:
            server = self._servers[server_id]
            return [
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Server {server.name} status: {server.status.value}",
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Last seen: {server.last_seen or 'Never'}"
            ]
        return []
    
    def get_server_metrics(self, server_id: str) -> Dict[str, Any]:
        """Get performance metrics for a server."""
        # Placeholder implementation
        # In a full implementation, this would collect real metrics
        return {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "response_time": 0.0,
            "request_count": 0,
            "error_count": 0,
            "uptime": 0
        }
    
    def get_servers(self) -> List[MCPServer]:
        """Get all configured servers (alias for get_all_servers)."""
        return self.get_all_servers()
    
    def add_server(self, config: Dict[str, Any]) -> str:
        """Add a new server configuration."""
        try:
            # Validate required fields
            if "name" not in config:
                raise ValueError("Server name is required")
            
            if "command" not in config:
                raise ValueError("Server command is required")
            
            # Create new server
            server = MCPServer(
                name=config["name"],
                command=config["command"],
                args=config.get("args", []),
                env=config.get("env", {}),
                description=config.get("description", ""),
                auto_start=config.get("auto_start", False),
                health_check_url=config.get("health_check_url")
            )
            
            # Validate configuration
            validation = self.validate_server_config(server.command, server.args)
            if not validation["valid"]:
                raise ValueError(f"Invalid server configuration: {', '.join(validation['errors'])}")
            
            # Add to servers
            self._servers[server.id] = server
            
            # Save configuration
            self._save_servers()
            
            self.logger.info(f"Added new server: {server.name} (ID: {server.id})")
            return server.id
            
        except Exception as e:
            self.logger.error(f"Failed to add server: {e}")
            raise