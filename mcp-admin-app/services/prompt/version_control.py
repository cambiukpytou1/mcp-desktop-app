"""
Prompt Version Control Service
=============================

Handles prompt versioning, branching, and change tracking with Git-like operations.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from models.prompt_advanced.models import (
    PromptVersion, PromptBranch, PerformanceMetrics, PromptMetadata, Prompt,
    BranchType, VersionStatus, ValidationError
)
from models.base import generate_id
from .performance_tracker import PerformanceTracker


class VersionChanges:
    """Represents changes to be made in a new version."""
    
    def __init__(self, content: str = None, metadata: PromptMetadata = None, 
                 commit_message: str = "", created_by: str = ""):
        self.content = content
        self.metadata = metadata
        self.commit_message = commit_message
        self.created_by = created_by


class MergeResult:
    """Result of a merge operation."""
    
    def __init__(self, success: bool, merged_version_id: str = None, 
                 conflicts: List[str] = None, message: str = ""):
        self.success = success
        self.merged_version_id = merged_version_id
        self.conflicts = conflicts or []
        self.message = message


class VersionDiff:
    """Represents differences between two versions."""
    
    def __init__(self, version1_id: str, version2_id: str, 
                 content_diff: List[Dict[str, Any]] = None,
                 metadata_diff: Dict[str, Any] = None):
        self.version1_id = version1_id
        self.version2_id = version2_id
        self.content_diff = content_diff or []
        self.metadata_diff = metadata_diff or {}


class VersionControlService:
    """Manages prompt version control operations with Git-like functionality."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Initialize performance tracker for integration
        self.performance_tracker = PerformanceTracker(config_manager, db_manager)
        
        self.logger.info("Version control service initialized")
    
    def create_version(self, prompt_id: str, changes: VersionChanges) -> PromptVersion:
        """Create a new version of a prompt with automatic versioning."""
        try:
            with self.db_manager.get_connection() as conn:
                # Get current version info
                cursor = conn.execute("""
                    SELECT current_version, total_versions 
                    FROM prompt_version_info 
                    WHERE prompt_id = ?
                """, (prompt_id,))
                version_info = cursor.fetchone()
                
                if not version_info:
                    # First version
                    current_version = "1.0.0"
                    total_versions = 1
                else:
                    # Increment version
                    current_version = self._increment_version(version_info["current_version"])
                    total_versions = version_info["total_versions"] + 1
                
                # Get current prompt content and metadata for snapshot
                cursor = conn.execute("""
                    SELECT p.content, pm.model, pm.temperature, pm.max_tokens, 
                           pm.tags, pm.custom_fields, pm.author, pm.description,
                           pm.intent_category, pm.status, pm.domain, pm.tone,
                           pm.persona, pm.objective
                    FROM prompts p
                    LEFT JOIN prompt_metadata pm ON p.id = pm.prompt_id
                    WHERE p.id = ?
                """, (prompt_id,))
                current_data = cursor.fetchone()
                
                if not current_data:
                    raise ValidationError(f"Prompt {prompt_id} not found")
                
                # Create metadata snapshot
                metadata_snapshot = PromptMetadata(
                    model=current_data["model"] or "gpt-3.5-turbo",
                    temperature=current_data["temperature"] or 0.7,
                    max_tokens=current_data["max_tokens"] or 1000,
                    tags=json.loads(current_data["tags"] or "[]"),
                    custom_fields=json.loads(current_data["custom_fields"] or "{}"),
                    author=current_data["author"] or "",
                    description=current_data["description"] or "",
                    intent_category=current_data["intent_category"] or "custom",
                    status=current_data["status"] or "draft",
                    domain=current_data["domain"] or "",
                    tone=current_data["tone"] or "",
                    persona=current_data["persona"] or "",
                    objective=current_data["objective"] or ""
                )
                
                # Override with changes if provided
                if changes.metadata:
                    metadata_snapshot = changes.metadata
                
                # Create new version
                new_version = PromptVersion(
                    prompt_id=prompt_id,
                    content=changes.content or current_data["content"],
                    metadata_snapshot=metadata_snapshot,
                    commit_message=changes.commit_message,
                    created_by=changes.created_by
                )
                
                # Get parent version (current head of main branch)
                cursor = conn.execute("""
                    SELECT version_id FROM prompt_versions 
                    WHERE prompt_id = ? AND branch_name = 'main' AND status = 'active'
                    ORDER BY created_at DESC LIMIT 1
                """, (prompt_id,))
                parent_result = cursor.fetchone()
                if parent_result:
                    new_version.parent_version = parent_result["version_id"]
                
                # Insert new version
                conn.execute("""
                    INSERT INTO prompt_versions 
                    (version_id, prompt_id, content, metadata_snapshot, parent_version,
                     branch_name, branch_type, commit_message, status, created_at, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_version.version_id, new_version.prompt_id, new_version.content,
                    json.dumps(new_version.metadata_snapshot.to_dict()),
                    new_version.parent_version, new_version.branch_name,
                    new_version.branch_type.value, new_version.commit_message,
                    new_version.status.value, new_version.created_at, new_version.created_by
                ))
                
                # Update prompt content if changed
                if changes.content:
                    conn.execute("""
                        UPDATE prompts SET content = ?, updated_at = ?
                        WHERE id = ?
                    """, (changes.content, datetime.now(), prompt_id))
                
                # Update metadata if changed
                if changes.metadata:
                    conn.execute("""
                        UPDATE prompt_metadata SET 
                        model = ?, temperature = ?, max_tokens = ?, tags = ?,
                        custom_fields = ?, author = ?, description = ?,
                        intent_category = ?, status = ?, domain = ?, tone = ?,
                        persona = ?, objective = ?
                        WHERE prompt_id = ?
                    """, (
                        changes.metadata.model, changes.metadata.temperature,
                        changes.metadata.max_tokens, json.dumps(changes.metadata.tags),
                        json.dumps(changes.metadata.custom_fields), changes.metadata.author,
                        changes.metadata.description, changes.metadata.intent_category.value,
                        changes.metadata.status.value, changes.metadata.domain,
                        changes.metadata.tone, changes.metadata.persona,
                        changes.metadata.objective, prompt_id
                    ))
                
                # Update version info
                conn.execute("""
                    INSERT OR REPLACE INTO prompt_version_info 
                    (prompt_id, current_version, total_versions, last_modified_by, last_modified_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (prompt_id, current_version, total_versions, changes.created_by, datetime.now()))
                
                conn.commit()
                self.logger.info(f"Created version {current_version} for prompt {prompt_id}")
                return new_version
                
        except Exception as e:
            self.logger.error(f"Failed to create version for prompt {prompt_id}: {e}")
            raise
    
    def create_branch(self, prompt_id: str, branch_name: str, base_version: str) -> PromptBranch:
        """Create a new branch from a base version."""
        try:
            with self.db_manager.get_connection() as conn:
                # Validate base version exists
                cursor = conn.execute("""
                    SELECT version_id FROM prompt_versions 
                    WHERE prompt_id = ? AND version_id = ?
                """, (prompt_id, base_version))
                if not cursor.fetchone():
                    raise ValidationError(f"Base version {base_version} not found")
                
                # Check if branch name already exists
                cursor = conn.execute("""
                    SELECT branch_id FROM prompt_branches 
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
                    head_version=base_version,  # Initially points to base
                    branch_type=branch_type,
                    created_by="system"  # TODO: Get from context
                )
                
                # Insert branch record
                conn.execute("""
                    INSERT INTO prompt_branches 
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
                self.logger.info(f"Created branch {branch_name} for prompt {prompt_id}")
                return new_branch
                
        except Exception as e:
            self.logger.error(f"Failed to create branch {branch_name}: {e}")
            raise
    
    def merge_branch(self, branch_id: str, target_branch: str) -> MergeResult:
        """Merge a branch into the target branch."""
        try:
            with self.db_manager.get_connection() as conn:
                # Get branch information
                cursor = conn.execute("""
                    SELECT prompt_id, name, head_version, base_version
                    FROM prompt_branches 
                    WHERE branch_id = ? AND is_active = TRUE
                """, (branch_id,))
                branch_info = cursor.fetchone()
                
                if not branch_info:
                    raise ValidationError(f"Branch {branch_id} not found or inactive")
                
                prompt_id = branch_info["prompt_id"]
                source_branch = branch_info["name"]
                head_version = branch_info["head_version"]
                
                # Get target branch head version
                cursor = conn.execute("""
                    SELECT head_version FROM prompt_branches 
                    WHERE prompt_id = ? AND name = ? AND is_active = TRUE
                """, (prompt_id, target_branch))
                target_info = cursor.fetchone()
                
                if not target_info:
                    raise ValidationError(f"Target branch {target_branch} not found")
                
                target_head = target_info["head_version"]
                
                # Check for conflicts (simplified - just check if both branches have changes)
                conflicts = self._detect_merge_conflicts(head_version, target_head)
                
                if conflicts:
                    return MergeResult(
                        success=False,
                        conflicts=conflicts,
                        message=f"Merge conflicts detected between {source_branch} and {target_branch}"
                    )
                
                # Create merge commit
                merge_changes = VersionChanges(
                    commit_message=f"Merge branch '{source_branch}' into '{target_branch}'",
                    created_by="system"  # TODO: Get from context
                )
                
                # Get content from head version
                cursor = conn.execute("""
                    SELECT content, metadata_snapshot FROM prompt_versions 
                    WHERE version_id = ?
                """, (head_version,))
                version_data = cursor.fetchone()
                
                if version_data:
                    merge_changes.content = version_data["content"]
                    if version_data["metadata_snapshot"]:
                        metadata_dict = json.loads(version_data["metadata_snapshot"])
                        merge_changes.metadata = PromptMetadata.from_dict(metadata_dict)
                
                # Create merge version
                merged_version = self.create_version(prompt_id, merge_changes)
                
                # Update target branch head
                conn.execute("""
                    UPDATE prompt_branches 
                    SET head_version = ? 
                    WHERE prompt_id = ? AND name = ? AND is_active = TRUE
                """, (merged_version.version_id, prompt_id, target_branch))
                
                # Mark source branch as merged
                conn.execute("""
                    UPDATE prompt_branches 
                    SET is_active = FALSE, merged_at = ?
                    WHERE branch_id = ?
                """, (datetime.now(), branch_id))
                
                conn.commit()
                
                self.logger.info(f"Merged branch {source_branch} into {target_branch}")
                return MergeResult(
                    success=True,
                    merged_version_id=merged_version.version_id,
                    message=f"Successfully merged {source_branch} into {target_branch}"
                )
                
        except Exception as e:
            self.logger.error(f"Failed to merge branch {branch_id}: {e}")
            return MergeResult(
                success=False,
                message=f"Merge failed: {str(e)}"
            )
    
    def get_version_history(self, prompt_id: str) -> List[PromptVersion]:
        """Get version history for a prompt."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT version_id, prompt_id, content, metadata_snapshot,
                           parent_version, branch_name, branch_type, commit_message,
                           status, created_at, created_by
                    FROM prompt_versions 
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
                    
                    # Parse metadata snapshot
                    if row["metadata_snapshot"]:
                        metadata_dict = json.loads(row["metadata_snapshot"])
                        version.metadata_snapshot = PromptMetadata.from_dict(metadata_dict)
                    
                    # Get performance metrics if available
                    perf_cursor = conn.execute("""
                        SELECT average_score, total_executions, success_rate,
                               average_tokens, average_cost, average_response_time
                        FROM prompt_performance_metrics 
                        WHERE version_id = ?
                    """, (version.version_id,))
                    perf_data = perf_cursor.fetchone()
                    
                    if perf_data:
                        version.performance_metrics = PerformanceMetrics(
                            average_score=perf_data["average_score"],
                            total_executions=perf_data["total_executions"],
                            success_rate=perf_data["success_rate"],
                            average_tokens=perf_data["average_tokens"],
                            average_cost=perf_data["average_cost"],
                            average_response_time=perf_data["average_response_time"]
                        )
                    
                    versions.append(version)
                
                return versions
                
        except Exception as e:
            self.logger.error(f"Failed to get version history for prompt {prompt_id}: {e}")
            return []
    
    def compare_versions(self, version1: str, version2: str) -> VersionDiff:
        """Compare two versions and return differences."""
        try:
            with self.db_manager.get_connection() as conn:
                # Get both versions
                cursor = conn.execute("""
                    SELECT version_id, content, metadata_snapshot
                    FROM prompt_versions 
                    WHERE version_id IN (?, ?)
                """, (version1, version2))
                
                versions = {row["version_id"]: row for row in cursor.fetchall()}
                
                if len(versions) != 2:
                    raise ValidationError("One or both versions not found")
                
                v1_data = versions[version1]
                v2_data = versions[version2]
                
                # Compare content
                content_diff = self._generate_content_diff(
                    v1_data["content"], v2_data["content"]
                )
                
                # Compare metadata
                metadata_diff = {}
                if v1_data["metadata_snapshot"] and v2_data["metadata_snapshot"]:
                    meta1 = json.loads(v1_data["metadata_snapshot"])
                    meta2 = json.loads(v2_data["metadata_snapshot"])
                    metadata_diff = self._generate_metadata_diff(meta1, meta2)
                
                return VersionDiff(
                    version1_id=version1,
                    version2_id=version2,
                    content_diff=content_diff,
                    metadata_diff=metadata_diff
                )
                
        except Exception as e:
            self.logger.error(f"Failed to compare versions {version1} and {version2}: {e}")
            return VersionDiff(version1, version2)
    
    def rollback_to_version(self, prompt_id: str, version_id: str) -> Prompt:
        """Rollback prompt to a specific version."""
        try:
            with self.db_manager.get_connection() as conn:
                # Get version data
                cursor = conn.execute("""
                    SELECT content, metadata_snapshot FROM prompt_versions 
                    WHERE prompt_id = ? AND version_id = ?
                """, (prompt_id, version_id))
                version_data = cursor.fetchone()
                
                if not version_data:
                    raise ValidationError(f"Version {version_id} not found")
                
                # Create rollback version
                rollback_changes = VersionChanges(
                    content=version_data["content"],
                    commit_message=f"Rollback to version {version_id}",
                    created_by="system"  # TODO: Get from context
                )
                
                if version_data["metadata_snapshot"]:
                    metadata_dict = json.loads(version_data["metadata_snapshot"])
                    rollback_changes.metadata = PromptMetadata.from_dict(metadata_dict)
                
                # Create new version with rollback content
                new_version = self.create_version(prompt_id, rollback_changes)
                
                # Get updated prompt
                cursor = conn.execute("""
                    SELECT p.id, p.name, p.content, p.folder_path, p.project_id,
                           p.created_at, p.updated_at
                    FROM prompts p
                    WHERE p.id = ?
                """, (prompt_id,))
                prompt_data = cursor.fetchone()
                
                if not prompt_data:
                    raise ValidationError(f"Prompt {prompt_id} not found")
                
                # Create prompt object
                prompt = Prompt(
                    id=prompt_data["id"],
                    name=prompt_data["name"],
                    content=prompt_data["content"],
                    folder_path=prompt_data["folder_path"],
                    project_id=prompt_data["project_id"],
                    created_at=datetime.fromisoformat(prompt_data["created_at"]),
                    updated_at=datetime.fromisoformat(prompt_data["updated_at"])
                )
                
                self.logger.info(f"Rolled back prompt {prompt_id} to version {version_id}")
                return prompt
                
        except Exception as e:
            self.logger.error(f"Failed to rollback prompt {prompt_id} to version {version_id}: {e}")
            raise
    
    def _increment_version(self, current_version: str) -> str:
        """Increment version number (semantic versioning)."""
        try:
            parts = current_version.split('.')
            if len(parts) != 3:
                return "1.0.0"
            
            major, minor, patch = map(int, parts)
            patch += 1
            
            return f"{major}.{minor}.{patch}"
        except:
            return "1.0.0"
    
    def _detect_merge_conflicts(self, version1: str, version2: str) -> List[str]:
        """Detect potential merge conflicts between versions."""
        # Simplified conflict detection
        # In a real implementation, this would do more sophisticated analysis
        conflicts = []
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT content FROM prompt_versions 
                    WHERE version_id IN (?, ?)
                """, (version1, version2))
                
                versions = cursor.fetchall()
                if len(versions) == 2:
                    content1 = versions[0]["content"]
                    content2 = versions[1]["content"]
                    
                    # Simple check - if contents are significantly different
                    if abs(len(content1) - len(content2)) > len(content1) * 0.5:
                        conflicts.append("Significant content differences detected")
                
        except Exception as e:
            self.logger.error(f"Error detecting conflicts: {e}")
            conflicts.append("Unable to analyze conflicts")
        
        return conflicts
    
    def _generate_content_diff(self, content1: str, content2: str) -> List[Dict[str, Any]]:
        """Generate content differences between two versions."""
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
    
    def _generate_metadata_diff(self, meta1: Dict[str, Any], meta2: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata differences between two versions."""
        diff = {}
        
        all_keys = set(meta1.keys()) | set(meta2.keys())
        
        for key in all_keys:
            val1 = meta1.get(key)
            val2 = meta2.get(key)
            
            if val1 != val2:
                diff[key] = {
                    "old_value": val1,
                    "new_value": val2
                }
        
        return diff
    
    def get_version_with_performance(self, version_id: str) -> Optional[PromptVersion]:
        """Get version with integrated performance metrics."""
        try:
            versions = self.get_version_history(version_id.split('-')[0])  # Get prompt_id from version_id
            version = next((v for v in versions if v.version_id == version_id), None)
            
            if version:
                # Get performance metrics
                performance = self.performance_tracker.get_version_performance(version_id)
                if performance:
                    version.performance_metrics = performance
            
            return version
            
        except Exception as e:
            self.logger.error(f"Failed to get version with performance: {e}")
            return None
    
    def analyze_version_performance_impact(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Analyze performance impact of a version compared to its parent."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT parent_version FROM prompt_versions 
                    WHERE version_id = ?
                """, (version_id,))
                
                result = cursor.fetchone()
                if not result or not result["parent_version"]:
                    return None
                
                parent_version = result["parent_version"]
                
                # Get performance impact analysis
                impact = self.performance_tracker.analyze_performance_impact(
                    parent_version, version_id
                )
                
                if impact:
                    return {
                        "impact_analysis": impact.to_dict(),
                        "parent_version": parent_version,
                        "current_version": version_id,
                        "timestamp": datetime.now().isoformat()
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to analyze version performance impact: {e}")
            return None
    
    def get_performance_optimized_versions(self, prompt_id: str, metric: str = "average_score", 
                                         limit: int = 5) -> List[PromptVersion]:
        """Get versions sorted by performance metrics."""
        try:
            with self.db_manager.get_connection() as conn:
                # Map metric names to database columns
                metric_column_map = {
                    "average_score": "average_score",
                    "success_rate": "success_rate", 
                    "cost": "average_cost",
                    "speed": "average_response_time",
                    "tokens": "average_tokens"
                }
                
                column = metric_column_map.get(metric, "average_score")
                order = "DESC" if metric in ["average_score", "success_rate"] else "ASC"
                
                cursor = conn.execute(f"""
                    SELECT pv.version_id, pv.prompt_id, pv.content, pv.metadata_snapshot,
                           pv.parent_version, pv.branch_name, pv.branch_type, pv.commit_message,
                           pv.status, pv.created_at, pv.created_by,
                           ppm.average_score, ppm.total_executions, ppm.success_rate,
                           ppm.average_tokens, ppm.average_cost, ppm.average_response_time
                    FROM prompt_versions pv
                    JOIN prompt_performance_metrics ppm ON pv.version_id = ppm.version_id
                    WHERE pv.prompt_id = ? AND ppm.total_executions >= 3
                    ORDER BY ppm.{column} {order}
                    LIMIT ?
                """, (prompt_id, limit))
                
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
                    
                    # Add metadata snapshot
                    if row["metadata_snapshot"]:
                        metadata_dict = json.loads(row["metadata_snapshot"])
                        version.metadata_snapshot = PromptMetadata.from_dict(metadata_dict)
                    
                    # Add performance metrics
                    version.performance_metrics = PerformanceMetrics(
                        average_score=row["average_score"],
                        total_executions=row["total_executions"],
                        success_rate=row["success_rate"],
                        average_tokens=row["average_tokens"],
                        average_cost=row["average_cost"],
                        average_response_time=row["average_response_time"]
                    )
                    
                    versions.append(version)
                
                return versions
                
        except Exception as e:
            self.logger.error(f"Failed to get performance optimized versions: {e}")
            return []
    
    def create_performance_optimized_branch(self, prompt_id: str, target_metric: str = "average_score") -> Optional[PromptBranch]:
        """Create a branch based on the best performing version for optimization."""
        try:
            # Get the best performing version
            best_versions = self.get_performance_optimized_versions(prompt_id, target_metric, 1)
            if not best_versions:
                self.logger.warning(f"No performance data available for prompt {prompt_id}")
                return None
            
            best_version = best_versions[0]
            
            # Create optimization branch
            branch_name = f"optimize-{target_metric}-{datetime.now().strftime('%Y%m%d')}"
            
            branch = self.create_branch(prompt_id, branch_name, best_version.version_id)
            
            self.logger.info(f"Created performance optimization branch {branch_name} based on version {best_version.version_id}")
            return branch
            
        except Exception as e:
            self.logger.error(f"Failed to create performance optimized branch: {e}")
            return None
    
    def get_version_performance_report(self, version_id: str) -> Dict[str, Any]:
        """Get comprehensive performance report for a version."""
        return self.performance_tracker.get_version_performance_report(version_id)
    
    def track_version_execution(self, version_id: str, evaluation_result) -> bool:
        """Track execution metrics for a version."""
        return self.performance_tracker.record_execution_metrics(version_id, evaluation_result)
              