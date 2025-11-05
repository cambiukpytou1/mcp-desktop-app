"""
Advanced Tool Manager Service
============================

Comprehensive management of MCP tools including discovery, registry maintenance,
configuration, and lifecycle management.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from models.tool import (
    ToolRegistryEntry, ToolFilters, DiscoveredTool, ToolCategory, 
    ToolStatus, ToolParameter, ToolPermission, SecurityLevel
)
from models.base import generate_id
from models.server import MCPServer
from services.tool_discovery import ToolDiscoveryEngine, ToolAnalysis
from data.database import DatabaseManager


logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """Basic tool information for discovery."""
    name: str
    description: str
    schema: Dict[str, Any]
    server_id: str


@dataclass
class ToolConfiguration:
    """Tool configuration settings."""
    enabled: bool = True
    default_parameters: Dict[str, Any] = None
    aliases: List[str] = None
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    rate_limit: int = 0
    daily_quota: int = 0
    
    def __post_init__(self):
        if self.default_parameters is None:
            self.default_parameters = {}
        if self.aliases is None:
            self.aliases = []


@dataclass
class BulkUpdateResult:
    """Result of bulk tool update operation."""
    total_tools: int
    updated_tools: int
    failed_tools: int
    errors: List[str]


class AdvancedToolManager:
    """Advanced tool management service."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.discovery_engine = ToolDiscoveryEngine()
        self._tool_cache = {}  # Cache for frequently accessed tools
        self._last_cache_update = None
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure tool-related database tables exist."""
        try:
            # Create tool registry table
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_registry (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    server_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    schema TEXT NOT NULL,
                    parameters TEXT,
                    permissions TEXT,
                    status TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_used TEXT,
                    usage_count INTEGER DEFAULT 0,
                    average_execution_time REAL DEFAULT 0.0,
                    success_rate REAL DEFAULT 1.0,
                    enabled BOOLEAN DEFAULT 1,
                    aliases TEXT,
                    default_parameters TEXT,
                    security_level TEXT NOT NULL
                )
                """)
                
                # Create tool executions table
                conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_executions (
                    id TEXT PRIMARY KEY,
                    tool_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    parameters TEXT,
                    result TEXT,
                    status TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    execution_time REAL,
                    error_message TEXT,
                    resource_usage TEXT,
                    sandbox_id TEXT,
                    workflow_id TEXT,
                    parent_execution_id TEXT,
                    FOREIGN KEY (tool_id) REFERENCES tool_registry (id)
                )
                """)
                
                # Create discovery status table
                conn.execute("""
                CREATE TABLE IF NOT EXISTS discovery_status (
                    server_id TEXT PRIMARY KEY,
                    last_scan TEXT,
                    tools_discovered INTEGER DEFAULT 0,
                    tools_added INTEGER DEFAULT 0,
                    tools_updated INTEGER DEFAULT 0,
                    tools_removed INTEGER DEFAULT 0,
                    scan_duration REAL DEFAULT 0.0,
                    errors TEXT
                )
                """)
                
                # Create tool collections table
                conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_collections (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    tool_ids TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
                
                conn.commit()
                
            logger.info("Tool management tables initialized")
            
        except Exception as e:
            logger.error(f"Error creating tool tables: {e}")
    
    def discover_tools(self, server_id: str) -> List[ToolInfo]:
        """Discover tools from an MCP server."""
        logger.info(f"Discovering tools from server {server_id}")
        
        try:
            discovered_tools = self.discovery_engine.scan_server_tools(server_id)
            
            tool_infos = []
            for discovered in discovered_tools:
                tool_info = ToolInfo(
                    name=discovered.name,
                    description=discovered.description,
                    schema=discovered.schema,
                    server_id=discovered.server_id
                )
                tool_infos.append(tool_info)
            
            # Update discovery status
            self._update_discovery_status(server_id, len(discovered_tools))
            
            logger.info(f"Discovered {len(tool_infos)} tools from server {server_id}")
            return tool_infos
            
        except Exception as e:
            logger.error(f"Error discovering tools from server {server_id}: {e}")
            return []
    
    def register_tool(self, tool_info: ToolInfo) -> str:
        """Register a discovered tool in the registry."""
        logger.info(f"Registering tool {tool_info.name}")
        
        try:
            # Analyze the tool
            analysis = self.discovery_engine.analyze_tool_schema(tool_info.schema)
            metadata = self.discovery_engine.extract_tool_metadata(tool_info.schema)
            
            # Create registry entry
            registry_entry = ToolRegistryEntry(
                name=tool_info.name,
                description=tool_info.description,
                server_id=tool_info.server_id,
                category=analysis.category,
                schema=tool_info.schema,
                parameters=analysis.suggested_parameters,
                status=ToolStatus.AVAILABLE,
                metadata=metadata,
                security_level=analysis.security_level
            )
            
            # Save to database
            self._save_registry_entry(registry_entry)
            
            logger.info(f"Tool {tool_info.name} registered with ID {registry_entry.id}")
            return registry_entry.id
            
        except Exception as e:
            logger.error(f"Error registering tool {tool_info.name}: {e}")
            raise
    
    def get_tool_registry(self, filters: Optional[ToolFilters] = None) -> List[ToolRegistryEntry]:
        """Get tools from registry with optional filtering."""
        try:
            query = "SELECT * FROM tool_registry WHERE 1=1"
            params = []
            
            if filters:
                if filters.name:
                    query += " AND name LIKE ?"
                    params.append(f"%{filters.name}%")
                
                if filters.category:
                    query += " AND category = ?"
                    params.append(filters.category.value)
                
                if filters.server_id:
                    query += " AND server_id = ?"
                    params.append(filters.server_id)
                
                if filters.status:
                    query += " AND status = ?"
                    params.append(filters.status.value)
                
                if filters.enabled is not None:
                    query += " AND enabled = ?"
                    params.append(filters.enabled)
                
                if filters.security_level:
                    query += " AND security_level = ?"
                    params.append(filters.security_level.value)
                
                if filters.min_success_rate is not None:
                    query += " AND success_rate >= ?"
                    params.append(filters.min_success_rate)
                
                if filters.max_execution_time is not None:
                    query += " AND average_execution_time <= ?"
                    params.append(filters.max_execution_time)
            
            query += " ORDER BY name"
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
            
            registry_entries = []
            for row in rows:
                entry = self._row_to_registry_entry(row)
                registry_entries.append(entry)
            
            return registry_entries
            
        except Exception as e:
            logger.error(f"Error getting tool registry: {e}")
            return []
    
    def configure_tool(self, tool_id: str, config: ToolConfiguration) -> bool:
        """Configure tool settings."""
        logger.info(f"Configuring tool {tool_id}")
        
        try:
            # Get current tool
            tool = self.get_tool_by_id(tool_id)
            if not tool:
                logger.error(f"Tool {tool_id} not found")
                return False
            
            # Update configuration
            tool.enabled = config.enabled
            tool.default_parameters = config.default_parameters
            tool.aliases = config.aliases
            tool.security_level = config.security_level
            tool.updated_at = datetime.now()
            
            # Update permissions if rate limiting is specified
            if config.rate_limit > 0 or config.daily_quota > 0:
                # Create or update default permission
                default_permission = ToolPermission(
                    rate_limit=config.rate_limit,
                    daily_quota=config.daily_quota
                )
                tool.permissions = [default_permission]
            
            # Save changes
            self._save_registry_entry(tool)
            
            logger.info(f"Tool {tool_id} configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error configuring tool {tool_id}: {e}")
            return False
    
    def set_tool_permissions(self, tool_id: str, permissions: List[ToolPermission]) -> bool:
        """Set permissions for a tool."""
        logger.info(f"Setting permissions for tool {tool_id}")
        
        try:
            tool = self.get_tool_by_id(tool_id)
            if not tool:
                logger.error(f"Tool {tool_id} not found")
                return False
            
            tool.permissions = permissions
            tool.updated_at = datetime.now()
            
            self._save_registry_entry(tool)
            
            logger.info(f"Permissions set for tool {tool_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting permissions for tool {tool_id}: {e}")
            return False
    
    def get_tool_status(self, tool_id: str) -> Optional[ToolStatus]:
        """Get current status of a tool."""
        try:
            tool = self.get_tool_by_id(tool_id)
            return tool.status if tool else None
        except Exception as e:
            logger.error(f"Error getting tool status for {tool_id}: {e}")
            return None
    
    def get_tool_by_id(self, tool_id: str) -> Optional[ToolRegistryEntry]:
        """Get tool by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM tool_registry WHERE id = ?", (tool_id,))
                row = cursor.fetchone()
            return self._row_to_registry_entry(row) if row else None
        except Exception as e:
            logger.error(f"Error getting tool {tool_id}: {e}")
            return None
    
    def categorize_tool(self, tool_info: ToolInfo) -> ToolCategory:
        """Categorize a tool automatically."""
        return self.discovery_engine.categorize_tool_automatically(
            DiscoveredTool(
                name=tool_info.name,
                description=tool_info.description,
                schema=tool_info.schema,
                server_id=tool_info.server_id
            )
        )
    
    def search_tools(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[ToolRegistryEntry]:
        """Search tools by name, description, or tags."""
        try:
            search_query = """
                SELECT * FROM tool_registry 
                WHERE (name LIKE ? OR description LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]
            
            if filters:
                if "category" in filters:
                    search_query += " AND category = ?"
                    params.append(filters["category"])
                
                if "server_id" in filters:
                    search_query += " AND server_id = ?"
                    params.append(filters["server_id"])
            
            search_query += " ORDER BY name"
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(search_query, params)
                rows = cursor.fetchall()
            
            results = []
            for row in rows:
                entry = self._row_to_registry_entry(row)
                results.append(entry)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching tools: {e}")
            return []
    
    def bulk_update_tools(self, updates: List[Dict[str, Any]]) -> BulkUpdateResult:
        """Perform bulk updates on multiple tools."""
        logger.info(f"Performing bulk update on {len(updates)} tools")
        
        result = BulkUpdateResult(
            total_tools=len(updates),
            updated_tools=0,
            failed_tools=0,
            errors=[]
        )
        
        for update in updates:
            try:
                tool_id = update.get("tool_id")
                if not tool_id:
                    result.errors.append("Missing tool_id in update")
                    result.failed_tools += 1
                    continue
                
                tool = self.get_tool_by_id(tool_id)
                if not tool:
                    result.errors.append(f"Tool {tool_id} not found")
                    result.failed_tools += 1
                    continue
                
                # Apply updates
                if "enabled" in update:
                    tool.enabled = update["enabled"]
                
                if "category" in update:
                    tool.category = ToolCategory(update["category"])
                
                if "security_level" in update:
                    tool.security_level = SecurityLevel(update["security_level"])
                
                tool.updated_at = datetime.now()
                
                # Save changes
                self._save_registry_entry(tool)
                result.updated_tools += 1
                
            except Exception as e:
                result.errors.append(f"Error updating tool: {e}")
                result.failed_tools += 1
        
        logger.info(f"Bulk update completed: {result.updated_tools} updated, {result.failed_tools} failed")
        return result
    
    def _save_registry_entry(self, entry: ToolRegistryEntry):
        """Save registry entry to database."""
        import json
        
        query = """
            INSERT OR REPLACE INTO tool_registry (
                id, name, description, server_id, category, schema, parameters,
                permissions, status, metadata, created_at, updated_at, last_used,
                usage_count, average_execution_time, success_rate, enabled,
                aliases, default_parameters, security_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            entry.id,
            entry.name,
            entry.description,
            entry.server_id,
            entry.category.value,
            json.dumps(entry.schema),
            json.dumps([p.__dict__ for p in entry.parameters]),
            json.dumps([p.__dict__ for p in entry.permissions]),
            entry.status.value,
            json.dumps(entry.metadata.__dict__),
            entry.created_at.isoformat(),
            entry.updated_at.isoformat(),
            entry.last_used.isoformat() if entry.last_used else None,
            entry.usage_count,
            entry.average_execution_time,
            entry.success_rate,
            entry.enabled,
            json.dumps(entry.aliases),
            json.dumps(entry.default_parameters),
            entry.security_level.value
        )
        
        with self.db_manager.get_connection() as conn:
            conn.execute(query, params)
            conn.commit()
    
    def _row_to_registry_entry(self, row: tuple) -> ToolRegistryEntry:
        """Convert database row to registry entry."""
        import json
        
        entry = ToolRegistryEntry()
        entry.id = row[0]
        entry.name = row[1]
        entry.description = row[2]
        entry.server_id = row[3]
        entry.category = ToolCategory(row[4])
        entry.schema = json.loads(row[5])
        
        # Parse parameters
        if row[6]:
            param_data = json.loads(row[6])
            entry.parameters = [ToolParameter(**p) for p in param_data]
        
        # Parse permissions
        if row[7]:
            perm_data = json.loads(row[7])
            entry.permissions = [ToolPermission(**p) for p in perm_data]
        
        entry.status = ToolStatus(row[8])
        
        # Parse metadata
        if row[9]:
            metadata_data = json.loads(row[9])
            entry.metadata.__dict__.update(metadata_data)
        
        entry.created_at = datetime.fromisoformat(row[10])
        entry.updated_at = datetime.fromisoformat(row[11])
        entry.last_used = datetime.fromisoformat(row[12]) if row[12] else None
        entry.usage_count = row[13]
        entry.average_execution_time = row[14]
        entry.success_rate = row[15]
        entry.enabled = bool(row[16])
        entry.aliases = json.loads(row[17]) if row[17] else []
        entry.default_parameters = json.loads(row[18]) if row[18] else {}
        entry.security_level = SecurityLevel(row[19])
        
        return entry
    
    def advanced_search_tools(self, query: str, filters: Optional[Dict[str, Any]] = None, 
                             sort_by: str = "name", sort_order: str = "asc") -> List[ToolRegistryEntry]:
        """Advanced search with sorting and complex filtering."""
        try:
            # Build search query with full-text search capabilities
            search_query = """
                SELECT * FROM tool_registry 
                WHERE (
                    name LIKE ? OR 
                    description LIKE ? OR 
                    aliases LIKE ? OR
                    metadata LIKE ?
                )
            """
            params = [f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"]
            
            # Add filters
            if filters:
                if "category" in filters:
                    search_query += " AND category = ?"
                    params.append(filters["category"])
                
                if "server_id" in filters:
                    search_query += " AND server_id = ?"
                    params.append(filters["server_id"])
                
                if "status" in filters:
                    search_query += " AND status = ?"
                    params.append(filters["status"])
                
                if "security_level" in filters:
                    search_query += " AND security_level = ?"
                    params.append(filters["security_level"])
                
                if "min_success_rate" in filters:
                    search_query += " AND success_rate >= ?"
                    params.append(filters["min_success_rate"])
                
                if "has_aliases" in filters and filters["has_aliases"]:
                    search_query += " AND aliases != '[]'"
                
                if "recently_used" in filters and filters["recently_used"]:
                    search_query += " AND last_used IS NOT NULL AND last_used > datetime('now', '-7 days')"
            
            # Add sorting
            valid_sort_columns = ["name", "category", "usage_count", "success_rate", 
                                "average_execution_time", "created_at", "last_used"]
            if sort_by in valid_sort_columns:
                sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
                search_query += f" ORDER BY {sort_by} {sort_direction}"
            else:
                search_query += " ORDER BY name ASC"
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(search_query, params)
                rows = cursor.fetchall()
            
            results = []
            for row in rows:
                entry = self._row_to_registry_entry(row)
                results.append(entry)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return []
    
    def get_tool_suggestions(self, partial_name: str, limit: int = 10) -> List[str]:
        """Get tool name suggestions for autocomplete."""
        try:
            query = """
                SELECT name FROM tool_registry 
                WHERE name LIKE ? OR aliases LIKE ?
                ORDER BY usage_count DESC, name ASC
                LIMIT ?
            """
            params = [f"%{partial_name}%", f"%{partial_name}%", limit]
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
            
            suggestions = [row[0] for row in rows]
            
            # Also check aliases
            alias_query = """
                SELECT aliases FROM tool_registry 
                WHERE aliases LIKE ?
            """
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(alias_query, [f"%{partial_name}%"])
                alias_rows = cursor.fetchall()
            
            for row in alias_rows:
                if row[0]:
                    aliases = json.loads(row[0])
                    for alias in aliases:
                        if partial_name.lower() in alias.lower() and alias not in suggestions:
                            suggestions.append(alias)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting tool suggestions: {e}")
            return []
    
    def update_tool_metadata(self, tool_id: str, metadata_updates: Dict[str, Any]) -> bool:
        """Update tool metadata."""
        try:
            tool = self.get_tool_by_id(tool_id)
            if not tool:
                logger.error(f"Tool {tool_id} not found")
                return False
            
            # Update metadata fields
            for key, value in metadata_updates.items():
                if hasattr(tool.metadata, key):
                    setattr(tool.metadata, key, value)
            
            tool.updated_at = datetime.now()
            self._save_registry_entry(tool)
            
            # Clear cache for this tool
            if tool_id in self._tool_cache:
                del self._tool_cache[tool_id]
            
            logger.info(f"Updated metadata for tool {tool_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating tool metadata: {e}")
            return False
    
    def get_tools_by_category(self, category: ToolCategory) -> List[ToolRegistryEntry]:
        """Get all tools in a specific category."""
        try:
            query = "SELECT * FROM tool_registry WHERE category = ? ORDER BY name"
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(query, (category.value,))
                rows = cursor.fetchall()
            
            tools = []
            for row in rows:
                entry = self._row_to_registry_entry(row)
                tools.append(entry)
            
            return tools
            
        except Exception as e:
            logger.error(f"Error getting tools by category: {e}")
            return []
    
    def get_tools_by_server(self, server_id: str) -> List[ToolRegistryEntry]:
        """Get all tools from a specific server."""
        try:
            query = "SELECT * FROM tool_registry WHERE server_id = ? ORDER BY name"
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(query, (server_id,))
                rows = cursor.fetchall()
            
            tools = []
            for row in rows:
                entry = self._row_to_registry_entry(row)
                tools.append(entry)
            
            return tools
            
        except Exception as e:
            logger.error(f"Error getting tools by server: {e}")
            return []
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """Get comprehensive tool registry statistics."""
        try:
            stats = {
                "total_tools": 0,
                "enabled_tools": 0,
                "disabled_tools": 0,
                "categories": {},
                "security_levels": {},
                "servers": {},
                "most_used_tools": [],
                "recently_added": [],
                "performance_metrics": {}
            }
            
            # Get basic counts
            with self.db_manager.get_connection() as conn:
                # Total tools
                cursor = conn.execute("SELECT COUNT(*) FROM tool_registry")
                stats["total_tools"] = cursor.fetchone()[0]
                
                # Enabled/disabled
                cursor = conn.execute("SELECT COUNT(*) FROM tool_registry WHERE enabled = 1")
                stats["enabled_tools"] = cursor.fetchone()[0]
                stats["disabled_tools"] = stats["total_tools"] - stats["enabled_tools"]
                
                # Category breakdown
                cursor = conn.execute("""
                    SELECT category, COUNT(*) FROM tool_registry 
                    GROUP BY category ORDER BY COUNT(*) DESC
                """)
                for row in cursor.fetchall():
                    stats["categories"][row[0]] = row[1]
                
                # Security level breakdown
                cursor = conn.execute("""
                    SELECT security_level, COUNT(*) FROM tool_registry 
                    GROUP BY security_level ORDER BY COUNT(*) DESC
                """)
                for row in cursor.fetchall():
                    stats["security_levels"][row[0]] = row[1]
                
                # Server breakdown
                cursor = conn.execute("""
                    SELECT server_id, COUNT(*) FROM tool_registry 
                    GROUP BY server_id ORDER BY COUNT(*) DESC
                """)
                for row in cursor.fetchall():
                    stats["servers"][row[0]] = row[1]
                
                # Most used tools
                cursor = conn.execute("""
                    SELECT name, usage_count FROM tool_registry 
                    WHERE usage_count > 0
                    ORDER BY usage_count DESC LIMIT 10
                """)
                stats["most_used_tools"] = [{"name": row[0], "usage_count": row[1]} 
                                          for row in cursor.fetchall()]
                
                # Recently added tools
                cursor = conn.execute("""
                    SELECT name, created_at FROM tool_registry 
                    ORDER BY created_at DESC LIMIT 10
                """)
                stats["recently_added"] = [{"name": row[0], "created_at": row[1]} 
                                         for row in cursor.fetchall()]
                
                # Performance metrics
                cursor = conn.execute("""
                    SELECT 
                        AVG(average_execution_time) as avg_exec_time,
                        AVG(success_rate) as avg_success_rate,
                        SUM(usage_count) as total_executions
                    FROM tool_registry
                """)
                row = cursor.fetchone()
                if row:
                    stats["performance_metrics"] = {
                        "average_execution_time": row[0] or 0,
                        "average_success_rate": row[1] or 0,
                        "total_executions": row[2] or 0
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting tool statistics: {e}")
            return {}
    
    def sync_tools_with_server(self, server_id: str) -> Dict[str, int]:
        """Synchronize tools with a specific server and detect changes."""
        try:
            logger.info(f"Synchronizing tools with server {server_id}")
            
            # Get current tools from database
            current_tools = {tool.name: tool for tool in self.get_tools_by_server(server_id)}
            
            # Discover tools from server
            discovered_tools = self.discovery_engine.scan_server_tools(server_id)
            discovered_names = {tool.name for tool in discovered_tools}
            
            stats = {
                "added": 0,
                "updated": 0,
                "removed": 0,
                "unchanged": 0
            }
            
            # Process discovered tools
            for discovered in discovered_tools:
                if discovered.name in current_tools:
                    # Check if tool has changed
                    current_tool = current_tools[discovered.name]
                    if current_tool.schema != discovered.schema:
                        # Tool has been updated
                        self._update_existing_tool(current_tool, discovered)
                        stats["updated"] += 1
                    else:
                        stats["unchanged"] += 1
                else:
                    # New tool discovered
                    tool_info = ToolInfo(
                        name=discovered.name,
                        description=discovered.description,
                        schema=discovered.schema,
                        server_id=server_id
                    )
                    self.register_tool(tool_info)
                    stats["added"] += 1
            
            # Mark removed tools as unavailable
            for tool_name, tool in current_tools.items():
                if tool_name not in discovered_names:
                    tool.status = ToolStatus.UNAVAILABLE
                    tool.updated_at = datetime.now()
                    self._save_registry_entry(tool)
                    stats["removed"] += 1
            
            # Update discovery status
            self._update_discovery_status(server_id, len(discovered_tools), stats)
            
            logger.info(f"Sync completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error syncing tools with server {server_id}: {e}")
            return {"added": 0, "updated": 0, "removed": 0, "unchanged": 0}
    
    def _update_existing_tool(self, current_tool: ToolRegistryEntry, discovered: DiscoveredTool):
        """Update an existing tool with new information."""
        try:
            # Analyze the updated schema
            analysis = self.discovery_engine.analyze_tool_schema(discovered.schema)
            
            # Update tool information
            current_tool.description = discovered.description
            current_tool.schema = discovered.schema
            current_tool.parameters = analysis.suggested_parameters
            current_tool.category = analysis.category
            current_tool.security_level = analysis.security_level
            current_tool.updated_at = datetime.now()
            
            # Update metadata
            current_tool.metadata = self.discovery_engine.extract_tool_metadata(discovered.schema)
            
            self._save_registry_entry(current_tool)
            logger.info(f"Updated existing tool: {current_tool.name}")
            
        except Exception as e:
            logger.error(f"Error updating existing tool: {e}")
    
    def _update_discovery_status(self, server_id: str, tools_discovered: int, 
                               sync_stats: Optional[Dict[str, int]] = None):
        """Update discovery status for a server."""
        try:
            if sync_stats is None:
                sync_stats = {"added": tools_discovered, "updated": 0, "removed": 0, "unchanged": 0}
            
            query = """
                INSERT OR REPLACE INTO discovery_status (
                    server_id, last_scan, tools_discovered, tools_added,
                    tools_updated, tools_removed, scan_duration, errors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                server_id,
                datetime.now().isoformat(),
                tools_discovered,
                sync_stats["added"],
                sync_stats["updated"],
                sync_stats["removed"],
                1.0,  # Placeholder scan duration
                json.dumps([])
            )
            
            with self.db_manager.get_connection() as conn:
                conn.execute(query, params)
                conn.commit()
            
        except Exception as e:
            logger.error(f"Error updating discovery status: {e}")
    
    def add_tool_tags(self, tool_id: str, tags: List[str]) -> bool:
        """Add tags to a tool."""
        try:
            tool = self.get_tool_by_id(tool_id)
            if not tool:
                logger.error(f"Tool {tool_id} not found")
                return False
            
            # Add new tags (avoid duplicates)
            existing_tags = set(tool.metadata.tags)
            new_tags = set(tags)
            tool.metadata.tags = list(existing_tags.union(new_tags))
            
            tool.updated_at = datetime.now()
            self._save_registry_entry(tool)
            
            logger.info(f"Added tags {tags} to tool {tool_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding tags to tool {tool_id}: {e}")
            return False
    
    def remove_tool_tags(self, tool_id: str, tags: List[str]) -> bool:
        """Remove tags from a tool."""
        try:
            tool = self.get_tool_by_id(tool_id)
            if not tool:
                logger.error(f"Tool {tool_id} not found")
                return False
            
            # Remove specified tags
            existing_tags = set(tool.metadata.tags)
            tags_to_remove = set(tags)
            tool.metadata.tags = list(existing_tags - tags_to_remove)
            
            tool.updated_at = datetime.now()
            self._save_registry_entry(tool)
            
            logger.info(f"Removed tags {tags} from tool {tool_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing tags from tool {tool_id}: {e}")
            return False
    
    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all tags used across tools with usage counts."""
        try:
            query = "SELECT metadata FROM tool_registry WHERE metadata IS NOT NULL"
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(query)
                rows = cursor.fetchall()
            
            tag_counts = {}
            for row in rows:
                try:
                    metadata = json.loads(row[0])
                    tags = metadata.get("tags", [])
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                except (json.JSONDecodeError, KeyError):
                    continue
            
            # Convert to list of dictionaries sorted by usage
            tag_list = [{"tag": tag, "count": count} for tag, count in tag_counts.items()]
            tag_list.sort(key=lambda x: x["count"], reverse=True)
            
            return tag_list
            
        except Exception as e:
            logger.error(f"Error getting all tags: {e}")
            return []
    
    def get_tools_by_tags(self, tags: List[str], match_all: bool = False) -> List[ToolRegistryEntry]:
        """Get tools that have specific tags."""
        try:
            tools = self.get_tool_registry()
            matching_tools = []
            
            for tool in tools:
                tool_tags = set(tool.metadata.tags)
                search_tags = set(tags)
                
                if match_all:
                    # Tool must have all specified tags
                    if search_tags.issubset(tool_tags):
                        matching_tools.append(tool)
                else:
                    # Tool must have at least one specified tag
                    if search_tags.intersection(tool_tags):
                        matching_tools.append(tool)
            
            return matching_tools
            
        except Exception as e:
            logger.error(f"Error getting tools by tags: {e}")
            return []
    
    def recategorize_tool(self, tool_id: str, new_category: ToolCategory) -> bool:
        """Manually recategorize a tool."""
        try:
            tool = self.get_tool_by_id(tool_id)
            if not tool:
                logger.error(f"Tool {tool_id} not found")
                return False
            
            old_category = tool.category
            tool.category = new_category
            tool.updated_at = datetime.now()
            
            self._save_registry_entry(tool)
            
            logger.info(f"Recategorized tool {tool_id} from {old_category.value} to {new_category.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error recategorizing tool {tool_id}: {e}")
            return False
    
    def auto_recategorize_tools(self, tool_ids: Optional[List[str]] = None) -> Dict[str, str]:
        """Automatically recategorize tools using the discovery engine."""
        try:
            if tool_ids:
                tools = [self.get_tool_by_id(tid) for tid in tool_ids if self.get_tool_by_id(tid)]
            else:
                tools = self.get_tool_registry()
            
            results = {}
            categorizations = self.discovery_engine.auto_categorize_batch(tools)
            
            for tool in tools:
                if tool.id in categorizations:
                    new_category = categorizations[tool.id]
                    old_category = tool.category
                    
                    if new_category != old_category:
                        tool.category = new_category
                        tool.updated_at = datetime.now()
                        self._save_registry_entry(tool)
                        
                        results[tool.id] = f"Changed from {old_category.value} to {new_category.value}"
                    else:
                        results[tool.id] = "No change needed"
            
            logger.info(f"Auto-recategorized {len(results)} tools")
            return results
            
        except Exception as e:
            logger.error(f"Error auto-recategorizing tools: {e}")
            return {}
    
    def get_tool_recommendations(self, user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get tool recommendations based on user context."""
        try:
            available_tools = self.get_tool_registry()
            recommendations = self.discovery_engine.generate_tool_recommendations(
                user_context, available_tools
            )
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting tool recommendations: {e}")
            return []
    
    def get_related_tools(self, tool_id: str) -> List[Dict[str, Any]]:
        """Get tools related to the specified tool."""
        try:
            tool = self.get_tool_by_id(tool_id)
            if not tool:
                return []
            
            all_tools = self.get_tool_registry()
            related = self.discovery_engine.get_related_tools(
                tool.name, tool.metadata.tags, all_tools
            )
            return related
            
        except Exception as e:
            logger.error(f"Error getting related tools: {e}")
            return []
    
    def suggest_tool_improvements(self, tool_id: str) -> List[str]:
        """Get improvement suggestions for a tool."""
        try:
            tool = self.get_tool_by_id(tool_id)
            if not tool:
                return []
            
            suggestions = self.discovery_engine.suggest_tool_improvements(tool)
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting tool improvement suggestions: {e}")
            return []
    
    def create_tool_collection(self, name: str, description: str, tool_ids: List[str]) -> str:
        """Create a collection of related tools."""
        try:
            collection_id = generate_id()
            
            # Store collection in database
            query = """
                INSERT INTO tool_collections (
                    id, name, description, tool_ids, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            
            params = (
                collection_id,
                name,
                description,
                json.dumps(tool_ids),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            )
            
            with self.db_manager.get_connection() as conn:
                conn.execute(query, params)
                conn.commit()
            
            logger.info(f"Created tool collection {name} with {len(tool_ids)} tools")
            return collection_id
            
        except Exception as e:
            logger.error(f"Error creating tool collection: {e}")
            return ""
    
    def delete_tool(self, tool_id: str) -> bool:
        """Delete a tool from the registry."""
        try:
            # Check if tool exists
            tool = self.get_tool_by_id(tool_id)
            if not tool:
                logger.error(f"Tool {tool_id} not found")
                return False
            
            # Delete from database
            with self.db_manager.get_connection() as conn:
                # Delete tool executions first (foreign key constraint)
                conn.execute("DELETE FROM tool_executions WHERE tool_id = ?", (tool_id,))
                
                # Delete the tool
                conn.execute("DELETE FROM tool_registry WHERE id = ?", (tool_id,))
                
                conn.commit()
            
            # Clear from cache if exists
            if tool_id in self._tool_cache:
                del self._tool_cache[tool_id]
            
            logger.info(f"Deleted tool {tool.name} (ID: {tool_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting tool {tool_id}: {e}")
            return False
    
    def bulk_delete_tools(self, tool_ids: List[str]) -> Dict[str, bool]:
        """Delete multiple tools from the registry."""
        try:
            results = {}
            
            for tool_id in tool_ids:
                success = self.delete_tool(tool_id)
                results[tool_id] = success
            
            successful_deletes = sum(1 for success in results.values() if success)
            logger.info(f"Bulk delete completed: {successful_deletes}/{len(tool_ids)} tools deleted")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk delete: {e}")
            return {tool_id: False for tool_id in tool_ids}
    
    def get_all_tools(self) -> List[ToolRegistryEntry]:
        """Get all tools from the registry."""
        return self.get_tool_registry()
    
    def search_tools(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[ToolRegistryEntry]:
        """Search tools with query and optional filters."""
        try:
            # Build search filters
            search_filters = ToolFilters()
            
            if query:
                search_filters.name = query
            
            if filters:
                if "category" in filters:
                    if isinstance(filters["category"], str):
                        search_filters.category = ToolCategory(filters["category"])
                    else:
                        search_filters.category = filters["category"]
                
                if "server_id" in filters:
                    search_filters.server_id = filters["server_id"]
                
                if "status" in filters:
                    if isinstance(filters["status"], str):
                        search_filters.status = ToolStatus(filters["status"])
                    else:
                        search_filters.status = filters["status"]
                
                if "enabled" in filters:
                    search_filters.enabled = filters["enabled"]
            
            return self.get_tool_registry(search_filters)
            
        except Exception as e:
            logger.error(f"Error searching tools: {e}")
            return []