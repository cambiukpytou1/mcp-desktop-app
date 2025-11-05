"""
Authentication and Authorization for MCP Admin API
=================================================

JWT-based authentication and API key management.
"""

import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from models.base import generate_id


class User:
    """Simple user model for API authentication."""
    
    def __init__(self, user_id: str, username: str, email: str, roles: List[str] = None):
        """Initialize user."""
        self.user_id = user_id
        self.username = username
        self.email = email
        self.roles = roles or ["user"]
        self.created_at = datetime.now()
        self.last_login = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None
        }


class APIKey:
    """API key model."""
    
    def __init__(self, key_id: str, name: str, key_hash: str, user_id: str, 
                 permissions: List[str] = None, expires_at: datetime = None):
        """Initialize API key."""
        self.key_id = key_id
        self.name = name
        self.key_hash = key_hash
        self.user_id = user_id
        self.permissions = permissions or []
        self.created_at = datetime.now()
        self.expires_at = expires_at
        self.last_used = None
        self.is_active = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key_id": self.key_id,
            "name": self.name,
            "user_id": self.user_id,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "is_active": self.is_active
        }


class AuthenticationManager:
    """JWT-based authentication manager."""
    
    def __init__(self, secret_key: str = None, algorithm: str = "HS256"):
        """Initialize authentication manager."""
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = algorithm
        self.logger = logging.getLogger(__name__)
        
        # In-memory storage for demo (would use database in production)
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Create default admin user
        self._create_default_user()
    
    def _create_default_user(self):
        """Create default admin user."""
        admin_user = User(
            user_id="admin_001",
            username="admin",
            email="admin@example.com",
            roles=["admin", "user"]
        )
        self.users[admin_user.user_id] = admin_user
    
    def create_user(self, username: str, email: str, roles: List[str] = None) -> User:
        """Create a new user."""
        user_id = generate_id()
        user = User(user_id, username, email, roles)
        self.users[user_id] = user
        
        self.logger.info(f"Created user: {username} ({user_id})")
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token."""
        # Simplified authentication (would check password hash in production)
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break
        
        if not user:
            return None
        
        # Update last login
        user.last_login = datetime.now()
        
        # Create JWT token
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "roles": user.roles,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        # Store session
        self.sessions[token] = {
            "user_id": user.user_id,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=24)
        }
        
        self.logger.info(f"User authenticated: {username}")
        return token
    
    def validate_token(self, token: str) -> Optional[User]:
        """Validate JWT token and return user."""
        try:
            # Check if session exists and is not expired
            if token in self.sessions:
                session = self.sessions[token]
                if session["expires_at"] < datetime.now():
                    del self.sessions[token]
                    return None
            
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            
            if user_id in self.users:
                return self.users[user_id]
            
            return None
        
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            self.logger.warning("Invalid token")
            return None
        except Exception as e:
            self.logger.error(f"Token validation error: {e}")
            return None
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token."""
        if token in self.sessions:
            del self.sessions[token]
            self.logger.info("Token revoked")
            return True
        return False
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def list_users(self) -> List[User]:
        """List all users."""
        return list(self.users.values())
    
    def update_user_roles(self, user_id: str, roles: List[str]) -> bool:
        """Update user roles."""
        if user_id in self.users:
            self.users[user_id].roles = roles
            self.logger.info(f"Updated roles for user {user_id}: {roles}")
            return True
        return False


class APIKeyManager:
    """API key management for service-to-service authentication."""
    
    def __init__(self):
        """Initialize API key manager."""
        self.logger = logging.getLogger(__name__)
        
        # In-memory storage for demo (would use database in production)
        self.api_keys: Dict[str, APIKey] = {}
        self.key_hashes: Dict[str, str] = {}  # hash -> key_id mapping
    
    def _hash_key(self, key: str) -> str:
        """Hash an API key."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def create_api_key(self, name: str, user_id: str, permissions: List[str] = None,
                      expires_days: int = None) -> Tuple[str, APIKey]:
        """Create a new API key."""
        # Generate API key
        key = f"mcp_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(key)
        key_id = generate_id()
        
        # Set expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        
        # Create API key object
        api_key = APIKey(
            key_id=key_id,
            name=name,
            key_hash=key_hash,
            user_id=user_id,
            permissions=permissions or [],
            expires_at=expires_at
        )
        
        # Store API key
        self.api_keys[key_id] = api_key
        self.key_hashes[key_hash] = key_id
        
        self.logger.info(f"Created API key: {name} for user {user_id}")
        return key, api_key
    
    def validate_api_key(self, key: str) -> Optional[APIKey]:
        """Validate an API key."""
        try:
            key_hash = self._hash_key(key)
            
            if key_hash not in self.key_hashes:
                return None
            
            key_id = self.key_hashes[key_hash]
            api_key = self.api_keys.get(key_id)
            
            if not api_key or not api_key.is_active:
                return None
            
            # Check expiration
            if api_key.expires_at and api_key.expires_at < datetime.now():
                api_key.is_active = False
                return None
            
            # Update last used
            api_key.last_used = datetime.now()
            
            return api_key
        
        except Exception as e:
            self.logger.error(f"API key validation error: {e}")
            return None
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        if key_id in self.api_keys:
            api_key = self.api_keys[key_id]
            api_key.is_active = False
            
            # Remove from hash mapping
            if api_key.key_hash in self.key_hashes:
                del self.key_hashes[api_key.key_hash]
            
            self.logger.info(f"Revoked API key: {key_id}")
            return True
        return False
    
    def list_api_keys(self, user_id: str = None) -> List[APIKey]:
        """List API keys, optionally filtered by user."""
        keys = list(self.api_keys.values())
        
        if user_id:
            keys = [k for k in keys if k.user_id == user_id]
        
        return keys
    
    def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """Get API key by ID."""
        return self.api_keys.get(key_id)
    
    def update_api_key_permissions(self, key_id: str, permissions: List[str]) -> bool:
        """Update API key permissions."""
        if key_id in self.api_keys:
            self.api_keys[key_id].permissions = permissions
            self.logger.info(f"Updated permissions for API key {key_id}: {permissions}")
            return True
        return False


class PermissionManager:
    """Permission management for role-based access control."""
    
    def __init__(self):
        """Initialize permission manager."""
        self.logger = logging.getLogger(__name__)
        
        # Define default permissions
        self.permissions = {
            "prompts.read": "Read prompts",
            "prompts.write": "Create and update prompts",
            "prompts.delete": "Delete prompts",
            "evaluations.read": "Read evaluations",
            "evaluations.write": "Create evaluations",
            "security.scan": "Perform security scans",
            "analytics.read": "Read analytics data",
            "admin.users": "Manage users",
            "admin.system": "System administration"
        }
        
        # Define role permissions
        self.role_permissions = {
            "user": [
                "prompts.read",
                "prompts.write",
                "evaluations.read",
                "evaluations.write",
                "security.scan"
            ],
            "admin": [
                "prompts.read",
                "prompts.write",
                "prompts.delete",
                "evaluations.read",
                "evaluations.write",
                "security.scan",
                "analytics.read",
                "admin.users",
                "admin.system"
            ],
            "readonly": [
                "prompts.read",
                "evaluations.read",
                "analytics.read"
            ]
        }
    
    def check_permission(self, user_roles: List[str], required_permission: str) -> bool:
        """Check if user roles have required permission."""
        for role in user_roles:
            if role in self.role_permissions:
                if required_permission in self.role_permissions[role]:
                    return True
        return False
    
    def get_user_permissions(self, user_roles: List[str]) -> List[str]:
        """Get all permissions for user roles."""
        permissions = set()
        for role in user_roles:
            if role in self.role_permissions:
                permissions.update(self.role_permissions[role])
        return list(permissions)
    
    def add_role_permission(self, role: str, permission: str) -> bool:
        """Add permission to role."""
        if role not in self.role_permissions:
            self.role_permissions[role] = []
        
        if permission not in self.role_permissions[role]:
            self.role_permissions[role].append(permission)
            self.logger.info(f"Added permission {permission} to role {role}")
            return True
        return False
    
    def remove_role_permission(self, role: str, permission: str) -> bool:
        """Remove permission from role."""
        if role in self.role_permissions and permission in self.role_permissions[role]:
            self.role_permissions[role].remove(permission)
            self.logger.info(f"Removed permission {permission} from role {role}")
            return True
        return False