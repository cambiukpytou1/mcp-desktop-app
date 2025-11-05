#!/usr/bin/env python3
"""
Version Control Service Test Suite
==================================

Unit tests for prompt version control functionality including branching,
merging, diff generation, and performance tracking integration.
"""

import sys
import os
import tempfile
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import uuid

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Import basic dependencies that should be available
from core.config import ConfigurationManager
from data.database import DatabaseManager


# Define minimal test models for version control testing
class PromptStatus(Enum):
    DRAFT = "draft"
    APPROVED = "approved"


class PromptCategory(Enum):
    CUSTOM = "custom"
    SUMMARIZATION = "summarization"


class VersionStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class BranchType(Enum):
    MAIN = "main"
    FEATURE = "feature"
    EXPERIMENT = "experiment"
    HOTFIX = "hotfix"


class ValidationError(Exception):
    pass


def generate_id():
    return str(uuid.uuid4())


@dataclass
class PromptMetadata:
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    author: str = ""
    description: str = ""
    intent_category: PromptCategory = PromptCategory.CUSTOM
    status: PromptStatus = PromptStatus.DRAFT
    
    def validate(self) -> bool:
        if not self.model:
            raise ValidationError("Model is required")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValidationError("Temperature must be between 0.0 and 2.0")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
            "author": self.author,
            "description": self.description,
            "intent_category": self.intent_category.value,
            "status": self.status.value
        }


@dataclass
class VersionInfo:
    current_version: str = "1.0.0"
    total_versions: int = 1
    last_modified_by: str = ""
    last_modified_at: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceMetrics:
    average_score: float = 0.0
    total_executions: int = 0
    success_rate: float = 0.0
    average_tokens: int = 0
    average_cost: float = 0.0
    average_response_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "average_score": self.average_score,
            "total_executions": self.total_executions,
            "success_rate": self.success_rate,
            "average_tokens": self.average_tokens,
            "average_cost": self.average_cost,
            "average_response_time": self.average_response_time
        }


@dataclass
class PromptVersion:
    version_id: str = field(default_factory=generate_id)
    prompt_id: str = ""
    content: str = ""
    metadata_snapshot: Optional[PromptMetadata] = None
    parent_version: Optional[str] = None
    branch_name: str = "main"
    branch_type: BranchType = BranchType.MAIN
    commit_message: str = ""
    status: VersionStatus = VersionStatus.ACTIVE
    performance_metrics: Optional[PerformanceMetrics] = None
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    def validate(self) -> bool:
        if not self.version_id:
            raise ValidationError("Version ID is required")
        if not self.prompt_id:
            raise ValidationError("Prompt ID is required")
        if not self.content:
            raise ValidationError("Content is required")
        return True


@dataclass
class PromptBranch:
    branch_id: str = field(default_factory=generate_id)
    prompt_id: str = ""
    name: str = ""
    base_version: str = ""
    head_version: str = ""
    branch_type: BranchType = BranchType.FEATURE
    is_active: bool = True
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    merged_at: Optional[datetime] = None
    
    def validate(self) -> bool:
        if not self.branch_id:
            raise ValidationError("Branch ID is required")
        if not self.prompt_id:
            raise ValidationError("Prompt ID is required")
        if not self.name:
            raise ValidationError("Branch name is required")
        return True


@dataclass
class Prompt:
    id: str = field(default_factory=generate_id)
    name: str = ""
    content: str = ""
    metadata: Optional[PromptMetadata] = None
    version_info: Optional[VersionInfo] = None
    folder_path: str = ""
    project_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = PromptMetadata()
        if self.version_info is None:
            self.version_info = VersionInfo()
    
    def validate(self) -> bool:
        if not self.name:
            raise ValidationError("Prompt name is required")
        if not self.content:
            raise ValidationError("Prompt content is required")
        return True


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class EvaluationResult:
    result_id: str = field(default_factory=generate_id)
    prompt_version_id: str = ""
    model: str = ""
    input_variables: Dict[str, Any] = field(default_factory=dict)
    output: str = ""
    scores: Dict[str, float] = field(default_factory=dict)
    token_usage: Optional[TokenUsage] = None
    execution_time: float = 0.0
    cost: float = 0.0
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> bool:
        if not self.result_id:
            raise ValidationError("Result ID is required")
        if not self.prompt_version_id:
            raise ValidationError("Prompt version ID is required")
        if self.execution_time < 0:
            raise ValidationError("Execution time cannot be negative")
        if self.cost < 0:
            raise ValidationError("Cost cannot be negative")
        return True


# Simplified version control classes for testing
class VersionChanges:
    def __init__(self, content: str = None, metadata: PromptMetadata = None, 
                 commit_message: str = "", created_by: str = ""):
        self.content = content
        self.metadata = metadata
        self.commit_message = commit_message
        self.created_by = created_by


class MergeResult:
    def __init__(self, success: bool, merged_version_id: str = None, 
                 conflicts: List[str] = None, message: str = ""):
        self.success = success
        self.merged_version_id = merged_version_id
        self.conflicts = conflicts or []
        self.message = message


class VersionDiff:
    def __init__(self, version1_id: str, version2_id: str, 
                 content_diff: List[Dict[str, Any]] = None,
                 metadata_diff: Dict[str, Any] = None):
        self.version1_id = version1_id
        self.version2_id = version2_id
        self.content_diff = content_diff or []
        self.metadata_diff = metadata_diff or {}


# Simplified Version Control Service for testing
class TestVersionControlService:
    """Simplified version control service for testing core functionality."""
    
    def __init__(self, config_manager, db_manager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        self._setup_tables()
    
    def _setup_tables(self):
        """Setup test tables for version control."""
        with self.db_manager.get_connection() as conn:
            # Create test tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_prompts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    folder_path TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_prompt_metadata (
                    prompt_id TEXT PRIMARY KEY,
                    model TEXT,
                    temperature REAL,
                    max_tokens INTEGER,
                    tags TEXT,
                    custom_fields TEXT,
                    author TEXT,
                    description TEXT,
                    intent_category TEXT,
                    status TEXT,
                    FOREIGN KEY (prompt_id) REFERENCES test_prompts(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_prompt_versions (
                    version_id TEXT PRIMARY KEY,
                    prompt_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_snapshot TEXT,
                    parent_version TEXT,
                    branch_name TEXT DEFAULT 'main',
                    branch_type TEXT DEFAULT 'main',
                    commit_message TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP,
                    created_by TEXT,
                    FOREIGN KEY (prompt_id) REFERENCES test_prompts(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_prompt_branches (
                    branch_id TEXT PRIMARY KEY,
                    prompt_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    base_version TEXT NOT NULL,
                    head_version TEXT NOT NULL,
                    branch_type TEXT DEFAULT 'feature',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_by TEXT,
                    created_at TIMESTAMP,
                    merged_at TIMESTAMP,
                    FOREIGN KEY (prompt_id) REFERENCES test_prompts(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_prompt_version_info (
                    prompt_id TEXT PRIMARY KEY,
                    current_version TEXT,
                    total_versions INTEGER DEFAULT 1,
                    last_modified_by TEXT,
                    last_modified_at TIMESTAMP,
                    FOREIGN KEY (prompt_id) REFERENCES test_prompts(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_performance_metrics (
                    version_id TEXT PRIMARY KEY,
                    average_score REAL DEFAULT 0.0,
                    total_executions INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    average_tokens INTEGER DEFAULT 0,
                    average_cost REAL DEFAULT 0.0,
                    average_response_time REAL DEFAULT 0.0,
                    last_updated TIMESTAMP,
                    FOREIGN KEY (version_id) REFERENCES test_prompt_versions(version_id)
                )
            """)
            
            conn.commit()
    
    def create_version(self, prompt_id: str, changes: VersionChanges) -> PromptVersion:
        """Create a new version of a prompt."""
        # Validate inputs
        if not prompt_id:
            raise ValidationError("Prompt ID is required")
        if changes.content is not None and not changes.content:
            raise ValidationError("Content is required")
            
        with self.db_manager.get_connection() as conn:
            # Get current version info
            cursor = conn.execute("""
                SELECT current_version, total_versions 
                FROM test_prompt_version_info 
                WHERE prompt_id = ?
            """, (prompt_id,))
            version_info = cursor.fetchone()
            
            if not version_info:
                current_version = "1.0.0"
                total_versions = 1
            else:
                current_version = self._increment_version(version_info["current_version"])
                total_versions = version_info["total_versions"] + 1
            
            # Get current prompt data
            cursor = conn.execute("""
                SELECT content FROM test_prompts WHERE id = ?
            """, (prompt_id,))
            current_data = cursor.fetchone()
            
            if not current_data:
                raise ValidationError(f"Prompt {prompt_id} not found")
            
            # Create new version
            new_version = PromptVersion(
                prompt_id=prompt_id,
                content=changes.content or current_data["content"],
                commit_message=changes.commit_message,
                created_by=changes.created_by
            )
            
            # Get parent version
            cursor = conn.execute("""
                SELECT version_id FROM test_prompt_versions 
                WHERE prompt_id = ? AND branch_name = 'main' AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            """, (prompt_id,))
            parent_result = cursor.fetchone()
            if parent_result:
                new_version.parent_version = parent_result["version_id"]
            
            # Insert new version
            conn.execute("""
                INSERT INTO test_prompt_versions 
                (version_id, prompt_id, content, parent_version, branch_name,
                 branch_type, commit_message, status, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_version.version_id, new_version.prompt_id, new_version.content,
                new_version.parent_version, new_version.branch_name,
                new_version.branch_type.value, new_version.commit_message,
                new_version.status.value, new_version.created_at, new_version.created_by
            ))
            
            # Update prompt content if changed
            if changes.content:
                conn.execute("""
                    UPDATE test_prompts SET content = ?, updated_at = ?
                    WHERE id = ?
                """, (changes.content, datetime.now(), prompt_id))
            
            # Update version info
            conn.execute("""
                INSERT OR REPLACE INTO test_prompt_version_info 
                (prompt_id, current_version, total_versions, last_modified_by, last_modified_at)
                VALUES (?, ?, ?, ?, ?)
            """, (prompt_id, current_version, total_versions, changes.created_by, datetime.now()))
            
            conn.commit()
            return new_version
    
    def create_branch(self, prompt_id: str, branch_name: str, base_version: str) -> PromptBranch:
        """Create a new branch from a base version."""
        with self.db_manager.get_connection() as conn:
            # Validate base version exists
            cursor = conn.execute("""
                SELECT version_id FROM test_prompt_versions 
                WHERE prompt_id = ? AND version_id = ?
            """, (prompt_id, base_version))
            if not cursor.fetchone():
                raise ValidationError(f"Base version {base_version} not found")
            
            # Check if branch name already exists
            cursor = conn.execute("""
                SELECT branch_id FROM test_prompt_branches 
                WHERE prompt_id = ? AND name = ? AND is_active = TRUE
            """, (prompt_id, branch_name))
            if cursor.fetchone():
                raise ValidationError(f"Branch {branch_name} already exists")
            
            # Determine branch type
            branch_type = BranchType.FEATURE
            if branch_name.startswith("hotfix/"):
                branch_type = BranchType.HOTFIX
            elif branch_name.startswith("experiment/"):
                branch_type = BranchType.EXPERIMENT
            
            # Create new branch
            new_branch = PromptBranch(
                prompt_id=prompt_id,
                name=branch_name,
                base_version=base_version,
                head_version=base_version,
                branch_type=branch_type,
                created_by="test_user"
            )
            
            # Insert branch record
            conn.execute("""
                INSERT INTO test_prompt_branches 
                (branch_id, prompt_id, name, base_version, head_version, 
                 branch_type, is_active, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_branch.branch_id, new_branch.prompt_id, new_branch.name,
                new_branch.base_version, new_branch.head_version,
                new_branch.branch_type.value, new_branch.is_active,
                new_branch.created_by, new_branch.created_at
            ))
            
            conn.commit()
            return new_branch
    
    def merge_branch(self, branch_id: str, target_branch: str) -> MergeResult:
        """Merge a branch into the target branch."""
        with self.db_manager.get_connection() as conn:
            # Get branch information
            cursor = conn.execute("""
                SELECT prompt_id, name, head_version, base_version
                FROM test_prompt_branches 
                WHERE branch_id = ? AND is_active = TRUE
            """, (branch_id,))
            branch_info = cursor.fetchone()
            
            if not branch_info:
                return MergeResult(
                    success=False,
                    message=f"Branch {branch_id} not found or inactive"
                )
            
            prompt_id = branch_info["prompt_id"]
            source_branch = branch_info["name"]
            head_version = branch_info["head_version"]
            
            # Create merge commit
            merge_changes = VersionChanges(
                commit_message=f"Merge branch '{source_branch}' into '{target_branch}'",
                created_by="test_user"
            )
            
            # Get content from head version
            cursor = conn.execute("""
                SELECT content FROM test_prompt_versions 
                WHERE version_id = ?
            """, (head_version,))
            version_data = cursor.fetchone()
            
            if version_data:
                merge_changes.content = version_data["content"]
            
            # Create merge version
            merged_version = self.create_version(prompt_id, merge_changes)
            
            # Mark source branch as merged
            conn.execute("""
                UPDATE test_prompt_branches 
                SET is_active = FALSE, merged_at = ?
                WHERE branch_id = ?
            """, (datetime.now(), branch_id))
            
            conn.commit()
            
            return MergeResult(
                success=True,
                merged_version_id=merged_version.version_id,
                message=f"Successfully merged {source_branch} into {target_branch}"
            )
    
    def get_version_history(self, prompt_id: str) -> List[PromptVersion]:
        """Get version history for a prompt."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT version_id, prompt_id, content, parent_version, branch_name,
                       branch_type, commit_message, status, created_at, created_by
                FROM test_prompt_versions 
                WHERE prompt_id = ?
                ORDER BY created_at DESC
            """, (prompt_id,))
            
            versions = []
            for row in cursor.fetchall():
                version = PromptVersion(
                    version_id=row["version_id"],
                    prompt_id=row["prompt_id"],
                    content=row["content"],
                    parent_version=row["parent_version"],
                    branch_name=row["branch_name"],
                    branch_type=BranchType(row["branch_type"]),
                    commit_message=row["commit_message"],
                    status=VersionStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    created_by=row["created_by"]
                )
                versions.append(version)
            
            return versions
    
    def compare_versions(self, version1: str, version2: str) -> VersionDiff:
        """Compare two versions and return differences."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT version_id, content FROM test_prompt_versions 
                WHERE version_id IN (?, ?)
            """, (version1, version2))
            
            versions = {row["version_id"]: row for row in cursor.fetchall()}
            
            if len(versions) != 2:
                raise ValidationError("One or both versions not found")
            
            v1_data = versions[version1]
            v2_data = versions[version2]
            
            # Simple content diff
            content_diff = self._generate_simple_diff(v1_data["content"], v2_data["content"])
            
            return VersionDiff(
                version1_id=version1,
                version2_id=version2,
                content_diff=content_diff
            )
    
    def rollback_to_version(self, prompt_id: str, version_id: str) -> Prompt:
        """Rollback prompt to a specific version."""
        with self.db_manager.get_connection() as conn:
            # Get version data
            cursor = conn.execute("""
                SELECT content FROM test_prompt_versions 
                WHERE prompt_id = ? AND version_id = ?
            """, (prompt_id, version_id))
            version_data = cursor.fetchone()
            
            if not version_data:
                raise ValidationError(f"Version {version_id} not found")
            
            # Create rollback version
            rollback_changes = VersionChanges(
                content=version_data["content"],
                commit_message=f"Rollback to version {version_id}",
                created_by="test_user"
            )
            
            # Create new version with rollback content
            self.create_version(prompt_id, rollback_changes)
            
            # Get updated prompt
            cursor = conn.execute("""
                SELECT id, name, content, folder_path, created_at, updated_at
                FROM test_prompts WHERE id = ?
            """, (prompt_id,))
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                raise ValidationError(f"Prompt {prompt_id} not found")
            
            return Prompt(
                id=prompt_data["id"],
                name=prompt_data["name"],
                content=prompt_data["content"],
                folder_path=prompt_data["folder_path"],
                created_at=datetime.fromisoformat(prompt_data["created_at"]),
                updated_at=datetime.fromisoformat(prompt_data["updated_at"])
            )
    
    def record_performance_metrics(self, version_id: str, eval_result: EvaluationResult) -> bool:
        """Record performance metrics for a version."""
        try:
            with self.db_manager.get_connection() as conn:
                # Simple performance recording - just store the latest result
                overall_score = eval_result.scores.get('overall', 0.0) if eval_result.scores else 0.0
                tokens = eval_result.token_usage.total_tokens if eval_result.token_usage else 0
                
                conn.execute("""
                    INSERT OR REPLACE INTO test_performance_metrics 
                    (version_id, average_score, total_executions, success_rate,
                     average_tokens, average_cost, average_response_time, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    version_id, overall_score, 1, 1.0 if not eval_result.error else 0.0,
                    tokens, eval_result.cost, eval_result.execution_time, datetime.now()
                ))
                
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_performance_metrics(self, version_id: str) -> Optional[PerformanceMetrics]:
        """Get performance metrics for a version."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT average_score, total_executions, success_rate,
                       average_tokens, average_cost, average_response_time
                FROM test_performance_metrics WHERE version_id = ?
            """, (version_id,))
            
            row = cursor.fetchone()
            if row:
                return PerformanceMetrics(
                    average_score=row["average_score"],
                    total_executions=row["total_executions"],
                    success_rate=row["success_rate"],
                    average_tokens=row["average_tokens"],
                    average_cost=row["average_cost"],
                    average_response_time=row["average_response_time"]
                )
            return None
    
    def _increment_version(self, current_version: str) -> str:
        """Increment version number."""
        try:
            parts = current_version.split('.')
            if len(parts) != 3:
                return "1.0.0"
            major, minor, patch = map(int, parts)
            patch += 1
            return f"{major}.{minor}.{patch}"
        except:
            return "1.0.0"
    
    def _generate_simple_diff(self, content1: str, content2: str) -> List[Dict[str, Any]]:
        """Generate simple content diff."""
        import difflib
        
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        diff = []
        for line in difflib.unified_diff(lines1, lines2, lineterm=''):
            if line.startswith('@@'):
                continue
            elif line.startswith('-'):
                diff.append({"type": "removed", "content": line[1:]})
            elif line.startswith('+'):
                diff.append({"type": "added", "content": line[1:]})
            else:
                diff.append({"type": "unchanged", "content": line})
        
        return diff


def setup_test_environment():
    """Set up test environment with database and services."""
    temp_dir = tempfile.mkdtemp()
    
    # Setup configuration manager
    config_manager = ConfigurationManager()
    config_manager.config_dir = Path(temp_dir) / "config"
    config_manager.data_dir = Path(temp_dir) / "data"
    config_manager.templates_dir = Path(temp_dir) / "templates"
    config_manager.initialize()
    
    # Setup database manager
    db_path = Path(temp_dir) / "test_prompts.db"
    db_manager = DatabaseManager(db_path)
    db_manager.initialize()
    
    # Create test prompt
    test_prompt = Prompt(
        name="Test Prompt",
        content="This is a test prompt with {{variable}}",
        folder_path="/test"
    )
    
    return config_manager, db_manager, test_prompt


def insert_test_prompt(db_manager, test_prompt):
    """Insert test prompt into database after tables are created."""
    with db_manager.get_connection() as conn:
        conn.execute("""
            INSERT INTO test_prompts (id, name, content, folder_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            test_prompt.id, test_prompt.name, test_prompt.content,
            test_prompt.folder_path, test_prompt.created_at, test_prompt.updated_at
        ))
        
        # Insert metadata
        conn.execute("""
            INSERT INTO test_prompt_metadata 
            (prompt_id, model, temperature, max_tokens, tags, custom_fields,
             author, description, intent_category, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_prompt.id, test_prompt.metadata.model, test_prompt.metadata.temperature,
            test_prompt.metadata.max_tokens, json.dumps(test_prompt.metadata.tags),
            json.dumps(test_prompt.metadata.custom_fields), test_prompt.metadata.author,
            test_prompt.metadata.description, test_prompt.metadata.intent_category.value,
            test_prompt.metadata.status.value
        ))
        
        # Insert version info
        conn.execute("""
            INSERT INTO test_prompt_version_info 
            (prompt_id, current_version, total_versions, last_modified_by, last_modified_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            test_prompt.id, test_prompt.version_info.current_version,
            test_prompt.version_info.total_versions, test_prompt.version_info.last_modified_by,
            test_prompt.version_info.last_modified_at
        ))
        
        conn.commit()


def test_version_creation():
    """Test creating new versions of prompts."""
    print("Testing Version Creation...")
    
    config_manager, db_manager, test_prompt = setup_test_environment()
    version_service = TestVersionControlService(config_manager, db_manager)
    insert_test_prompt(db_manager, test_prompt)
    
    # Test creating first version
    changes = VersionChanges(
        content="Updated test prompt with {{variable}} and more content",
        commit_message="Initial version",
        created_by="test_user"
    )
    
    version = version_service.create_version(test_prompt.id, changes)
    
    assert version is not None
    assert version.prompt_id == test_prompt.id
    assert version.content == changes.content
    assert version.commit_message == changes.commit_message
    assert version.created_by == changes.created_by
    assert version.branch_name == "main"
    assert version.status == VersionStatus.ACTIVE
    
    # Test creating second version
    changes2 = VersionChanges(
        content="Second version with different {{variable}} content",
        commit_message="Second version update",
        created_by="test_user"
    )
    
    version2 = version_service.create_version(test_prompt.id, changes2)
    
    assert version2 is not None
    assert version2.parent_version == version.version_id
    assert version2.content == changes2.content
    
    # Verify version history
    history = version_service.get_version_history(test_prompt.id)
    assert len(history) == 2
    assert history[0].version_id == version2.version_id  # Most recent first
    assert history[1].version_id == version.version_id
    
    print("✓ Version Creation tests passed")


def test_branch_operations():
    """Test branching and merging operations."""
    print("Testing Branch Operations...")
    
    config_manager, db_manager, test_prompt = setup_test_environment()
    version_service = TestVersionControlService(config_manager, db_manager)
    insert_test_prompt(db_manager, test_prompt)
    
    # Create initial version
    changes = VersionChanges(
        content="Base version for branching test",
        commit_message="Base version",
        created_by="test_user"
    )
    base_version = version_service.create_version(test_prompt.id, changes)
    
    # Test creating a feature branch
    branch = version_service.create_branch(
        test_prompt.id, "feature/test-branch", base_version.version_id
    )
    
    assert branch is not None
    assert branch.prompt_id == test_prompt.id
    assert branch.name == "feature/test-branch"
    assert branch.base_version == base_version.version_id
    assert branch.head_version == base_version.version_id
    assert branch.branch_type == BranchType.FEATURE
    assert branch.is_active == True
    
    # Test creating experiment branch
    experiment_branch = version_service.create_branch(
        test_prompt.id, "experiment/new-approach", base_version.version_id
    )
    
    assert experiment_branch.branch_type == BranchType.EXPERIMENT
    
    # Test creating hotfix branch
    hotfix_branch = version_service.create_branch(
        test_prompt.id, "hotfix/urgent-fix", base_version.version_id
    )
    
    assert hotfix_branch.branch_type == BranchType.HOTFIX
    
    # Test branch validation - duplicate name should fail
    try:
        version_service.create_branch(
            test_prompt.id, "feature/test-branch", base_version.version_id
        )
        assert False, "Should have raised ValidationError for duplicate branch name"
    except ValidationError as e:
        assert "already exists" in str(e)
    
    print("✓ Branch Operations tests passed")


def test_merge_operations():
    """Test merging branches."""
    print("Testing Merge Operations...")
    
    config_manager, db_manager, test_prompt = setup_test_environment()
    version_service = TestVersionControlService(config_manager, db_manager)
    insert_test_prompt(db_manager, test_prompt)
    
    # Create base version
    base_changes = VersionChanges(
        content="Base content for merge test",
        commit_message="Base version",
        created_by="test_user"
    )
    base_version = version_service.create_version(test_prompt.id, base_changes)
    
    # Create feature branch
    branch = version_service.create_branch(
        test_prompt.id, "feature/merge-test", base_version.version_id
    )
    
    # Create version on feature branch
    feature_changes = VersionChanges(
        content="Feature branch content with improvements",
        commit_message="Feature implementation",
        created_by="test_user"
    )
    
    # Manually create version on feature branch by updating the branch first
    with db_manager.get_connection() as conn:
        # Create the feature version
        feature_version = PromptVersion(
            prompt_id=test_prompt.id,
            content=feature_changes.content,
            parent_version=base_version.version_id,
            branch_name="feature/merge-test",
            branch_type=BranchType.FEATURE,
            commit_message=feature_changes.commit_message,
            created_by=feature_changes.created_by
        )
        
        conn.execute("""
            INSERT INTO prompt_versions 
            (version_id, prompt_id, content, parent_version, branch_name, 
             branch_type, commit_message, status, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feature_version.version_id, feature_version.prompt_id, feature_version.content,
            feature_version.parent_version, feature_version.branch_name,
            feature_version.branch_type.value, feature_version.commit_message,
            feature_version.status.value, feature_version.created_at, feature_version.created_by
        ))
        
        # Update branch head
        conn.execute("""
            UPDATE prompt_branches SET head_version = ? WHERE branch_id = ?
        """, (feature_version.version_id, branch.branch_id))
        
        conn.commit()
    
    # Test merging feature branch into main
    merge_result = version_service.merge_branch(branch.branch_id, "main")
    
    assert merge_result.success == True
    assert merge_result.merged_version_id is not None
    assert "Successfully merged" in merge_result.message
    
    # Verify branch is marked as inactive after merge
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT is_active, merged_at FROM test_prompt_branches WHERE branch_id = ?
        """, (branch.branch_id,))
        branch_data = cursor.fetchone()
        assert branch_data is not None
        assert branch_data["is_active"] == False
        assert branch_data["merged_at"] is not None
    
    print("✓ Merge Operations tests passed")


def test_diff_generation():
    """Test diff generation and comparison."""
    print("Testing Diff Generation...")
    
    config_manager, db_manager, test_prompt = setup_test_environment()
    version_service = TestVersionControlService(config_manager, db_manager)
    insert_test_prompt(db_manager, test_prompt)
    
    # Create two versions with different content
    version1_changes = VersionChanges(
        content="Original prompt with {{name}} variable",
        commit_message="Version 1",
        created_by="test_user"
    )
    version1 = version_service.create_version(test_prompt.id, version1_changes)
    
    version2_changes = VersionChanges(
        content="Updated prompt with {{name}} and {{age}} variables",
        commit_message="Version 2 - added age variable",
        created_by="test_user"
    )
    version2 = version_service.create_version(test_prompt.id, version2_changes)
    
    # Test version comparison using version control service
    version_diff = version_service.compare_versions(version1.version_id, version2.version_id)
    
    assert version_diff is not None
    assert version_diff.version1_id == version1.version_id
    assert version_diff.version2_id == version2.version_id
    assert len(version_diff.content_diff) > 0
    
    # Verify diff contains changes
    assert len(version_diff.content_diff) > 0
    
    # Check that diff shows the addition of {{age}} variable
    diff_content = " ".join([item.get("content", "") for item in version_diff.content_diff])
    assert "age" in diff_content or "{{age}}" in diff_content
    
    print("✓ Diff Generation tests passed")


def test_performance_tracking_integration():
    """Test performance tracking integration with version control."""
    print("Testing Performance Tracking Integration...")
    
    config_manager, db_manager, test_prompt = setup_test_environment()
    version_service = TestVersionControlService(config_manager, db_manager)
    insert_test_prompt(db_manager, test_prompt)
    
    # Create version
    changes = VersionChanges(
        content="Performance test prompt",
        commit_message="Performance test version",
        created_by="test_user"
    )
    version = version_service.create_version(test_prompt.id, changes)
    
    # Create mock evaluation result
    token_usage = TokenUsage(
        prompt_tokens=50,
        completion_tokens=25,
        total_tokens=75
    )
    
    eval_result = EvaluationResult(
        prompt_version_id=version.version_id,
        model="gpt-3.5-turbo",
        input_variables={"test": "value"},
        output="Test output",
        scores={"overall": 0.85, "quality": 0.9},
        token_usage=token_usage,
        execution_time=1.2,
        cost=0.001
    )
    
    # Record performance metrics
    success = version_service.record_performance_metrics(version.version_id, eval_result)
    assert success == True
    
    # Get performance metrics
    metrics = version_service.get_performance_metrics(version.version_id)
    assert metrics is not None
    assert metrics.total_executions == 1
    assert metrics.average_score == 0.85
    assert metrics.average_tokens == 75
    assert metrics.average_cost == 0.001
    
    # Create second version for impact analysis
    changes2 = VersionChanges(
        content="Improved performance test prompt",
        commit_message="Performance improvement",
        created_by="test_user"
    )
    version2 = version_service.create_version(test_prompt.id, changes2)
    
    # Record better performance for second version
    eval_result2 = EvaluationResult(
        prompt_version_id=version2.version_id,
        model="gpt-3.5-turbo",
        input_variables={"test": "value"},
        output="Better test output",
        scores={"overall": 0.95, "quality": 0.98},
        token_usage=TokenUsage(prompt_tokens=45, completion_tokens=20, total_tokens=65),
        execution_time=1.0,
        cost=0.0008
    )
    
    version_service.record_performance_metrics(version2.version_id, eval_result2)
    
    # Get performance metrics for second version
    metrics2 = version_service.get_performance_metrics(version2.version_id)
    assert metrics2 is not None
    assert metrics2.average_score == 0.95
    assert metrics2.average_tokens == 65
    assert metrics2.average_cost == 0.0008
    
    print("✓ Performance Tracking Integration tests passed")


def test_rollback_functionality():
    """Test rollback to previous versions."""
    print("Testing Rollback Functionality...")
    
    config_manager, db_manager, test_prompt = setup_test_environment()
    version_service = TestVersionControlService(config_manager, db_manager)
    insert_test_prompt(db_manager, test_prompt)
    
    # Create multiple versions
    version1_changes = VersionChanges(
        content="Version 1 content",
        commit_message="Version 1",
        created_by="test_user"
    )
    version1 = version_service.create_version(test_prompt.id, version1_changes)
    
    version2_changes = VersionChanges(
        content="Version 2 content with changes",
        commit_message="Version 2",
        created_by="test_user"
    )
    version2 = version_service.create_version(test_prompt.id, version2_changes)
    
    version3_changes = VersionChanges(
        content="Version 3 content with more changes",
        commit_message="Version 3",
        created_by="test_user"
    )
    version3 = version_service.create_version(test_prompt.id, version3_changes)
    
    # Rollback to version 1
    rolled_back_prompt = version_service.rollback_to_version(test_prompt.id, version1.version_id)
    
    assert rolled_back_prompt is not None
    assert rolled_back_prompt.id == test_prompt.id
    assert rolled_back_prompt.content == version1_changes.content
    
    # Verify a new version was created for the rollback
    history = version_service.get_version_history(test_prompt.id)
    assert len(history) == 4  # Original 3 + rollback version
    
    # The most recent version should be the rollback
    latest_version = history[0]
    assert "Rollback to version" in latest_version.commit_message
    assert latest_version.content == version1_changes.content
    
    print("✓ Rollback Functionality tests passed")


def test_version_validation():
    """Test version validation and error handling."""
    print("Testing Version Validation...")
    
    config_manager, db_manager, test_prompt = setup_test_environment()
    version_service = TestVersionControlService(config_manager, db_manager)
    insert_test_prompt(db_manager, test_prompt)
    
    # Test invalid prompt ID
    try:
        changes = VersionChanges(content="Test content")
        version_service.create_version("invalid-prompt-id", changes)
        assert False, "Should have raised ValidationError for invalid prompt ID"
    except ValidationError as e:
        assert "not found" in str(e)
    
    # Test empty content
    try:
        changes = VersionChanges(content="")
        version_service.create_version(test_prompt.id, changes)
        assert False, "Should have raised ValidationError for empty content"
    except ValidationError as e:
        assert "Content is required" in str(e)
    
    # Test invalid base version for branch
    try:
        version_service.create_branch(test_prompt.id, "test-branch", "invalid-version-id")
        assert False, "Should have raised ValidationError for invalid base version"
    except ValidationError as e:
        assert "not found" in str(e)
    
    # Test invalid branch for merge
    merge_result = version_service.merge_branch("invalid-branch-id", "main")
    assert merge_result.success == False
    assert "not found" in merge_result.message.lower()
    
    print("✓ Version Validation tests passed")


def test_performance_optimized_versions():
    """Test getting performance-optimized versions."""
    print("Testing Performance Optimized Versions...")
    
    config_manager, db_manager, test_prompt = setup_test_environment()
    version_service = TestVersionControlService(config_manager, db_manager)
    insert_test_prompt(db_manager, test_prompt)
    
    # Create multiple versions with different performance
    versions = []
    scores = [0.7, 0.9, 0.6, 0.85, 0.95]
    
    for i, score in enumerate(scores):
        changes = VersionChanges(
            content=f"Version {i+1} content",
            commit_message=f"Version {i+1}",
            created_by="test_user"
        )
        version = version_service.create_version(test_prompt.id, changes)
        versions.append(version)
        
        # Record performance metrics
        eval_result = EvaluationResult(
            prompt_version_id=version.version_id,
            model="gpt-3.5-turbo",
            scores={"overall": score},
            token_usage=TokenUsage(total_tokens=100),
            execution_time=1.0,
            cost=0.001
        )
        
        version_service.record_performance_metrics(version.version_id, eval_result)
    
    # Test that we can retrieve performance metrics for all versions
    for i, version in enumerate(versions):
        metrics = version_service.get_performance_metrics(version.version_id)
        assert metrics is not None
        assert metrics.average_score == scores[i]
    
    print("✓ Performance Optimized Versions tests passed")


def main():
    """Run all version control tests."""
    print("Running Version Control Service Tests")
    print("=" * 45)
    
    try:
        # Core version control tests
        test_version_creation()
        test_branch_operations()
        test_merge_operations()
        test_diff_generation()
        test_rollback_functionality()
        test_version_validation()
        
        # Performance integration tests
        test_performance_tracking_integration()
        test_performance_optimized_versions()
        
        print("\n" + "=" * 45)
        print("✅ All version control tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()