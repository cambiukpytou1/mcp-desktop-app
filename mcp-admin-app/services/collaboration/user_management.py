"""
User Management Service for MCP Admin Application
================================================

Service for managing users, authentication, and role-based access control.
"""

import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

from models.collaboration import User, UserRole, Permission, PermissionType, Workspace
from data.database import DatabaseManager


class UserManagementService:
    """Service for user management and authentication."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the user management service."""
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables for user management."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'viewer',
                    is_active BOOLEAN DEFAULT 1,
                    is_verified BOOLEAN DEFAULT 0,
                    last_login TIMESTAMP,
                    session_token TEXT,
                    session_expires TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    preferences TEXT DEFAULT '{}'
                )
            """)
            
            # Workspaces table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workspaces (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT NOT NULL,
                    is_public BOOLEAN DEFAULT 0,
                    settings TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (owner_id) REFERENCES users(id)
                )
            """)
            
            # Permissions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS permissions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    permission_type TEXT NOT NULL,
                    granted_by TEXT NOT NULL,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (granted_by) REFERENCES users(id)
                )
            """)
            
            # Workspace members table
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
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_permissions_user ON permissions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource_type, resource_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workspace_members ON workspace_members(workspace_id, user_id)")
            
            conn.commit()
    
    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash a password with salt."""
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return password_hash.hex(), salt
    
    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against its hash."""
        computed_hash, _ = self._hash_password(password, salt)
        return secrets.compare_digest(computed_hash, password_hash)
    
    def create_user(self, username: str, email: str, full_name: str, 
                   password: str, role: UserRole = UserRole.VIEWER,
                   created_by: str = None) -> User:
        """Create a new user account."""
        try:
            # Hash password
            password_hash, salt = self._hash_password(password)
            
            # Create user object
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                password_hash=password_hash,
                salt=salt,
                role=role,
                created_by=created_by
            )
            
            # Save to database
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (
                        id, username, email, full_name, password_hash, salt,
                        role, is_active, is_verified, created_at, updated_at, created_by,
                        preferences
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.id, user.username, user.email, user.full_name,
                    user.password_hash, user.salt, user.role.value,
                    user.is_active, user.is_verified,
                    user.created_at.isoformat(), user.updated_at.isoformat(),
                    user.created_by, "{}"
                ))
                conn.commit()
            
            self.logger.info(f"Created user: {username} ({user.id})")
            return user
            
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                raise ValueError(f"Username '{username}' already exists")
            elif "email" in str(e):
                raise ValueError(f"Email '{email}' already exists")
            else:
                raise ValueError(f"User creation failed: {e}")
        except Exception as e:
            self.logger.error(f"Error creating user {username}: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, full_name, password_hash, salt,
                           role, is_active, is_verified, last_login, created_at,
                           updated_at, created_by, preferences
                    FROM users 
                    WHERE username = ? AND is_active = 1
                """, (username,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Verify password
                if not self._verify_password(password, row[4], row[5]):
                    return None
                
                # Create user object
                user = User(
                    id=row[0],
                    username=row[1],
                    email=row[2],
                    full_name=row[3],
                    password_hash=row[4],
                    salt=row[5],
                    role=UserRole(row[6]),
                    is_active=bool(row[7]),
                    is_verified=bool(row[8]),
                    last_login=datetime.fromisoformat(row[9]) if row[9] else None,
                    created_at=datetime.fromisoformat(row[10]),
                    updated_at=datetime.fromisoformat(row[11]),
                    created_by=row[12],
                    preferences=eval(row[13]) if row[13] else {}
                )
                
                # Update last login
                self._update_last_login(user.id)
                
                return user
                
        except Exception as e:
            self.logger.error(f"Error authenticating user {username}: {e}")
            return None
    
    def _update_last_login(self, user_id: str):
        """Update user's last login timestamp."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET last_login = ? 
                    WHERE id = ?
                """, (datetime.now().isoformat(), user_id))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error updating last login for user {user_id}: {e}")
    
    def create_session(self, user_id: str, duration_hours: int = 24) -> str:
        """Create a session token for a user."""
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=duration_hours)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET session_token = ?, session_expires = ?
                    WHERE id = ?
                """, (session_token, expires_at.isoformat(), user_id))
                conn.commit()
            
            return session_token
            
        except Exception as e:
            self.logger.error(f"Error creating session for user {user_id}: {e}")
            raise
    
    def validate_session(self, session_token: str) -> Optional[User]:
        """Validate a session token and return the user."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, full_name, role, is_active,
                           is_verified, session_expires
                    FROM users 
                    WHERE session_token = ? AND is_active = 1
                """, (session_token,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Check if session is expired
                if row[7] and datetime.fromisoformat(row[7]) < datetime.now():
                    self._invalidate_session(row[0])
                    return None
                
                return User(
                    id=row[0],
                    username=row[1],
                    email=row[2],
                    full_name=row[3],
                    role=UserRole(row[4]),
                    is_active=bool(row[5]),
                    is_verified=bool(row[6])
                )
                
        except Exception as e:
            self.logger.error(f"Error validating session: {e}")
            return None
    
    def _invalidate_session(self, user_id: str):
        """Invalidate a user's session."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET session_token = NULL, session_expires = NULL
                    WHERE id = ?
                """, (user_id,))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error invalidating session for user {user_id}: {e}")
    
    def logout_user(self, user_id: str):
        """Log out a user by invalidating their session."""
        self._invalidate_session(user_id)
        self.logger.info(f"User logged out: {user_id}")
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, full_name, role, is_active,
                           is_verified, last_login, created_at, updated_at,
                           created_by, preferences
                    FROM users 
                    WHERE id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return User(
                    id=row[0],
                    username=row[1],
                    email=row[2],
                    full_name=row[3],
                    role=UserRole(row[4]),
                    is_active=bool(row[5]),
                    is_verified=bool(row[6]),
                    last_login=datetime.fromisoformat(row[7]) if row[7] else None,
                    created_at=datetime.fromisoformat(row[8]),
                    updated_at=datetime.fromisoformat(row[9]),
                    created_by=row[10],
                    preferences=eval(row[11]) if row[11] else {}
                )
                
        except Exception as e:
            self.logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def update_user(self, user_id: str, updates: Dict[str, any]) -> bool:
        """Update user information."""
        try:
            allowed_fields = ['email', 'full_name', 'role', 'is_active', 'is_verified', 'preferences']
            update_fields = []
            values = []
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == 'role' and isinstance(value, UserRole):
                        value = value.value
                    elif field == 'preferences' and isinstance(value, dict):
                        value = str(value)
                    
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                return False
            
            update_fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(user_id)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE users 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, values)
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error updating user {user_id}: {e}")
            return False
    
    def list_users(self, workspace_id: str = None) -> List[User]:
        """List all users or users in a specific workspace."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                if workspace_id:
                    cursor.execute("""
                        SELECT u.id, u.username, u.email, u.full_name, u.role,
                               u.is_active, u.is_verified, u.last_login,
                               u.created_at, u.updated_at, u.created_by, u.preferences
                        FROM users u
                        JOIN workspace_members wm ON u.id = wm.user_id
                        WHERE wm.workspace_id = ? AND u.is_active = 1
                        ORDER BY u.username
                    """, (workspace_id,))
                else:
                    cursor.execute("""
                        SELECT id, username, email, full_name, role, is_active,
                               is_verified, last_login, created_at, updated_at,
                               created_by, preferences
                        FROM users 
                        WHERE is_active = 1
                        ORDER BY username
                    """)
                
                users = []
                for row in cursor.fetchall():
                    user = User(
                        id=row[0],
                        username=row[1],
                        email=row[2],
                        full_name=row[3],
                        role=UserRole(row[4]),
                        is_active=bool(row[5]),
                        is_verified=bool(row[6]),
                        last_login=datetime.fromisoformat(row[7]) if row[7] else None,
                        created_at=datetime.fromisoformat(row[8]),
                        updated_at=datetime.fromisoformat(row[9]),
                        created_by=row[10],
                        preferences=eval(row[11]) if row[11] else {}
                    )
                    users.append(user)
                
                return users
                
        except Exception as e:
            self.logger.error(f"Error listing users: {e}")
            return []
    
    def delete_user(self, user_id: str) -> bool:
        """Soft delete a user by marking as inactive."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET is_active = 0, updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), user_id))
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    self.logger.info(f"Deleted user: {user_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    def check_permission(self, user_id: str, resource_type: str, 
                        resource_id: str, permission_type: PermissionType) -> bool:
        """Check if a user has a specific permission."""
        try:
            # Get user role first
            user = self.get_user(user_id)
            if not user or not user.is_active:
                return False
            
            # Admin users have all permissions
            if user.role == UserRole.ADMIN:
                return True
            
            # Check role-based permissions
            role_permissions = {
                UserRole.VIEWER: [PermissionType.READ],
                UserRole.EDITOR: [PermissionType.READ, PermissionType.WRITE],
                UserRole.REVIEWER: [PermissionType.READ, PermissionType.WRITE, PermissionType.APPROVE],
                UserRole.ADMIN: [PermissionType.READ, PermissionType.WRITE, PermissionType.DELETE, PermissionType.APPROVE, PermissionType.ADMIN]
            }
            
            if permission_type in role_permissions.get(user.role, []):
                return True
            
            # Check explicit permissions
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM permissions 
                    WHERE user_id = ? AND resource_type = ? AND resource_id = ?
                    AND permission_type = ? AND (expires_at IS NULL OR expires_at > ?)
                """, (user_id, resource_type, resource_id, permission_type.value, 
                     datetime.now().isoformat()))
                
                return cursor.fetchone()[0] > 0
                
        except Exception as e:
            self.logger.error(f"Error checking permission for user {user_id}: {e}")
            return False
    
    def grant_permission(self, user_id: str, resource_type: str, resource_id: str,
                        permission_type: PermissionType, granted_by: str,
                        expires_at: datetime = None) -> bool:
        """Grant a permission to a user."""
        try:
            permission = Permission(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                permission_type=permission_type,
                granted_by=granted_by,
                expires_at=expires_at
            )
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO permissions (
                        id, user_id, resource_type, resource_id, permission_type,
                        granted_by, granted_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    permission.id, permission.user_id, permission.resource_type,
                    permission.resource_id, permission.permission_type.value,
                    permission.granted_by, permission.granted_at.isoformat(),
                    permission.expires_at.isoformat() if permission.expires_at else None
                ))
                conn.commit()
            
            self.logger.info(f"Granted {permission_type.value} permission to user {user_id} for {resource_type}:{resource_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error granting permission: {e}")
            return False
    
    def revoke_permission(self, user_id: str, resource_type: str, resource_id: str,
                         permission_type: PermissionType) -> bool:
        """Revoke a permission from a user."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM permissions 
                    WHERE user_id = ? AND resource_type = ? AND resource_id = ?
                    AND permission_type = ?
                """, (user_id, resource_type, resource_id, permission_type.value))
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    self.logger.info(f"Revoked {permission_type.value} permission from user {user_id} for {resource_type}:{resource_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Error revoking permission: {e}")
            return False