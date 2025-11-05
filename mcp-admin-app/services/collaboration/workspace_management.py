"""
Workspace Management Service for MCP Admin Application
=====================================================

Service for managing workspaces and workspace membership.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import logging
import json

from models.collaboration import Workspace, User, UserRole
from data.database import DatabaseManager


class WorkspaceManagementService:
    """Service for workspace management and membership."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the workspace management service."""
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables for workspace management."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Workspace members table (if not already created)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workspace_members (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'viewer',
                    added_by TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (added_by) REFERENCES users(id),
                    UNIQUE(workspace_id, user_id)
                )
            """)
            
            conn.commit()
    
    def create_workspace(self, name: str, description: str, owner_id: str,
                        is_public: bool = False, settings: Dict = None) -> Workspace:
        """Create a new workspace."""
        try:
            workspace = Workspace(
                name=name,
                description=description,
                owner_id=owner_id,
                is_public=is_public,
                settings=settings or {}
            )
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO workspaces (
                        id, name, description, owner_id, is_public, settings,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    workspace.id, workspace.name, workspace.description,
                    workspace.owner_id, workspace.is_public,
                    json.dumps(workspace.settings),
                    workspace.created_at.isoformat(),
                    workspace.updated_at.isoformat()
                ))
                
                # Add owner as admin member
                cursor.execute("""
                    INSERT INTO workspace_members (
                        id, workspace_id, user_id, role, added_by, added_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    f"{workspace.id}_owner", workspace.id, owner_id,
                    UserRole.ADMIN.value, owner_id, datetime.now().isoformat()
                ))
                
                conn.commit()
            
            self.logger.info(f"Created workspace: {name} ({workspace.id})")
            return workspace
            
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Workspace creation failed: {e}")
        except Exception as e:
            self.logger.error(f"Error creating workspace {name}: {e}")
            raise
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get a workspace by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, description, owner_id, is_public, settings,
                           created_at, updated_at
                    FROM workspaces 
                    WHERE id = ?
                """, (workspace_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return Workspace(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    owner_id=row[3],
                    is_public=bool(row[4]),
                    settings=json.loads(row[5]) if row[5] else {},
                    created_at=datetime.fromisoformat(row[6]),
                    updated_at=datetime.fromisoformat(row[7])
                )
                
        except Exception as e:
            self.logger.error(f"Error getting workspace {workspace_id}: {e}")
            return None
    
    def update_workspace(self, workspace_id: str, updates: Dict[str, any]) -> bool:
        """Update workspace information."""
        try:
            allowed_fields = ['name', 'description', 'is_public', 'settings']
            update_fields = []
            values = []
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == 'settings' and isinstance(value, dict):
                        value = json.dumps(value)
                    
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                return False
            
            update_fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(workspace_id)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE workspaces 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, values)
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error updating workspace {workspace_id}: {e}")
            return False
    
    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a workspace and all its memberships."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete workspace members first
                cursor.execute("DELETE FROM workspace_members WHERE workspace_id = ?", (workspace_id,))
                
                # Delete workspace
                cursor.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
                
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    self.logger.info(f"Deleted workspace: {workspace_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Error deleting workspace {workspace_id}: {e}")
            return False
    
    def list_workspaces(self, user_id: str = None, include_public: bool = True) -> List[Workspace]:
        """List workspaces accessible to a user."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                if user_id:
                    # Get workspaces where user is a member or public workspaces
                    query = """
                        SELECT DISTINCT w.id, w.name, w.description, w.owner_id,
                               w.is_public, w.settings, w.created_at, w.updated_at
                        FROM workspaces w
                        LEFT JOIN workspace_members wm ON w.id = wm.workspace_id
                        WHERE wm.user_id = ? OR w.owner_id = ?
                    """
                    params = [user_id, user_id]
                    
                    if include_public:
                        query += " OR w.is_public = 1"
                    
                    query += " ORDER BY w.name"
                    cursor.execute(query, params)
                else:
                    # Get all workspaces
                    cursor.execute("""
                        SELECT id, name, description, owner_id, is_public, settings,
                               created_at, updated_at
                        FROM workspaces 
                        ORDER BY name
                    """)
                
                workspaces = []
                for row in cursor.fetchall():
                    workspace = Workspace(
                        id=row[0],
                        name=row[1],
                        description=row[2],
                        owner_id=row[3],
                        is_public=bool(row[4]),
                        settings=json.loads(row[5]) if row[5] else {},
                        created_at=datetime.fromisoformat(row[6]),
                        updated_at=datetime.fromisoformat(row[7])
                    )
                    workspaces.append(workspace)
                
                return workspaces
                
        except Exception as e:
            self.logger.error(f"Error listing workspaces: {e}")
            return []
    
    def add_member(self, workspace_id: str, user_id: str, role: UserRole,
                   added_by: str) -> bool:
        """Add a user to a workspace."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO workspace_members (
                        id, workspace_id, user_id, role, added_by, added_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    f"{workspace_id}_{user_id}", workspace_id, user_id,
                    role.value, added_by, datetime.now().isoformat()
                ))
                conn.commit()
            
            self.logger.info(f"Added user {user_id} to workspace {workspace_id} with role {role.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding member to workspace: {e}")
            return False
    
    def remove_member(self, workspace_id: str, user_id: str) -> bool:
        """Remove a user from a workspace."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM workspace_members 
                    WHERE workspace_id = ? AND user_id = ?
                """, (workspace_id, user_id))
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    self.logger.info(f"Removed user {user_id} from workspace {workspace_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Error removing member from workspace: {e}")
            return False
    
    def update_member_role(self, workspace_id: str, user_id: str, role: UserRole) -> bool:
        """Update a member's role in a workspace."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE workspace_members 
                    SET role = ?
                    WHERE workspace_id = ? AND user_id = ?
                """, (role.value, workspace_id, user_id))
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    self.logger.info(f"Updated user {user_id} role to {role.value} in workspace {workspace_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Error updating member role: {e}")
            return False
    
    def get_members(self, workspace_id: str) -> List[Dict[str, any]]:
        """Get all members of a workspace."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.id, u.username, u.email, u.full_name, wm.role,
                           wm.added_by, wm.added_at
                    FROM workspace_members wm
                    JOIN users u ON wm.user_id = u.id
                    WHERE wm.workspace_id = ? AND u.is_active = 1
                    ORDER BY u.username
                """, (workspace_id,))
                
                members = []
                for row in cursor.fetchall():
                    member = {
                        'user_id': row[0],
                        'username': row[1],
                        'email': row[2],
                        'full_name': row[3],
                        'role': row[4],
                        'added_by': row[5],
                        'added_at': row[6]
                    }
                    members.append(member)
                
                return members
                
        except Exception as e:
            self.logger.error(f"Error getting workspace members: {e}")
            return []
    
    def get_user_role(self, workspace_id: str, user_id: str) -> Optional[UserRole]:
        """Get a user's role in a workspace."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT role FROM workspace_members 
                    WHERE workspace_id = ? AND user_id = ?
                """, (workspace_id, user_id))
                
                row = cursor.fetchone()
                if row:
                    return UserRole(row[0])
                
                # Check if user is workspace owner
                cursor.execute("""
                    SELECT owner_id FROM workspaces WHERE id = ?
                """, (workspace_id,))
                
                owner_row = cursor.fetchone()
                if owner_row and owner_row[0] == user_id:
                    return UserRole.ADMIN
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting user role: {e}")
            return None
    
    def is_member(self, workspace_id: str, user_id: str) -> bool:
        """Check if a user is a member of a workspace."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM workspace_members 
                    WHERE workspace_id = ? AND user_id = ?
                """, (workspace_id, user_id))
                
                count = cursor.fetchone()[0]
                if count > 0:
                    return True
                
                # Check if user is workspace owner
                cursor.execute("""
                    SELECT COUNT(*) FROM workspaces 
                    WHERE id = ? AND owner_id = ?
                """, (workspace_id, user_id))
                
                return cursor.fetchone()[0] > 0
                
        except Exception as e:
            self.logger.error(f"Error checking workspace membership: {e}")
            return False
    
    def can_access_workspace(self, workspace_id: str, user_id: str) -> bool:
        """Check if a user can access a workspace."""
        try:
            # Check if user is a member
            if self.is_member(workspace_id, user_id):
                return True
            
            # Check if workspace is public
            workspace = self.get_workspace(workspace_id)
            return workspace and workspace.is_public
            
        except Exception as e:
            self.logger.error(f"Error checking workspace access: {e}")
            return False