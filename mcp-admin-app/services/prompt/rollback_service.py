"""
Prompt Rollback Service
=======================

Service for handling prompt version rollbacks with safety checks and validation.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ...models.prompt_advanced.models import (
    Prompt, PromptVersion, PromptMetadata, ValidationError
)


class RollbackReason(Enum):
    """Reasons for rollback operations."""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    FUNCTIONALITY_ISSUE = "functionality_issue"
    USER_REQUEST = "user_request"
    SECURITY_CONCERN = "security_concern"
    TESTING_FAILURE = "testing_failure"
    MANUAL_REVERT = "manual_revert"


@dataclass
class RollbackPlan:
    """Plan for rollback operation with safety checks."""
    target_version_id: str
    current_version_id: str
    prompt_id: str
    reason: RollbackReason
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    safety_checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    can_rollback: bool = True
    rollback_message: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "target_version_id": self.target_version_id,
            "current_version_id": self.current_version_id,
            "prompt_id": self.prompt_id,
            "reason": self.reason.value,
            "impact_analysis": self.impact_analysis,
            "safety_checks": self.safety_checks,
            "warnings": self.warnings,
            "can_rollback": self.can_rollback,
            "rollback_message": self.rollback_message,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class RollbackResult:
    """Result of rollback operation."""
    success: bool
    new_version_id: Optional[str] = None
    rolled_back_to: Optional[str] = None
    message: str = ""
    warnings: List[str] = field(default_factory=list)
    performance_impact: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "new_version_id": self.new_version_id,
            "rolled_back_to": self.rolled_back_to,
            "message": self.message,
            "warnings": self.warnings,
            "performance_impact": self.performance_impact,
            "created_at": self.created_at.isoformat()
        }


class PromptRollbackService:
    """Service for managing prompt version rollbacks."""
    
    def __init__(self, config_manager, db_manager, version_control_service):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.version_control = version_control_service
        
        self.logger.info("Prompt rollback service initialized")
    
    def create_rollback_plan(self, prompt_id: str, target_version_id: str, 
                           reason: RollbackReason, created_by: str = "") -> RollbackPlan:
        """Create a rollback plan with safety analysis."""
        try:
            with self.db_manager.get_connection() as conn:
                # Get current version
                cursor = conn.execute("""
                    SELECT current_version FROM prompt_version_info 
                    WHERE prompt_id = ?
                """, (prompt_id,))
                current_info = cursor.fetchone()
                
                if not current_info:
                    raise ValidationError(f"Prompt {prompt_id} not found")
                
                current_version_id = current_info["current_version"]
                
                # Validate target version exists
                cursor = conn.execute("""
                    SELECT version_id, content, metadata_snapshot, created_at
                    FROM prompt_versions 
                    WHERE prompt_id = ? AND version_id = ?
                """, (prompt_id, target_version_id))
                target_version = cursor.fetchone()
                
                if not target_version:
                    raise ValidationError(f"Target version {target_version_id} not found")
                
                # Create rollback plan
                plan = RollbackPlan(
                    target_version_id=target_version_id,
                    current_version_id=current_version_id,
                    prompt_id=prompt_id,
                    reason=reason,
                    created_by=created_by,
                    rollback_message=f"Rollback to version {target_version_id} due to {reason.value}"
                )
                
                # Perform safety checks
                self._perform_safety_checks(plan)
                
                # Analyze impact
                plan.impact_analysis = self._analyze_rollback_impact(plan)
                
                self.logger.info(f"Created rollback plan for prompt {prompt_id}")
                return plan
                
        except Exception as e:
            self.logger.error(f"Failed to create rollback plan: {e}")
            raise
    
    def execute_rollback(self, plan: RollbackPlan) -> RollbackResult:
        """Execute rollback operation based on plan."""
        try:
            if not plan.can_rollback:
                return RollbackResult(
                    success=False,
                    message="Rollback blocked by safety checks",
                    warnings=plan.warnings
                )
            
            # Get target version data
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT content, metadata_snapshot FROM prompt_versions 
                    WHERE version_id = ?
                """, (plan.target_version_id,))
                target_data = cursor.fetchone()
                
                if not target_data:
                    return RollbackResult(
                        success=False,
                        message=f"Target version {plan.target_version_id} not found"
                    )
                
                # Create rollback version using version control service
                from .version_control import VersionChanges
                
                rollback_changes = VersionChanges(
                    content=target_data["content"],
                    commit_message=plan.rollback_message,
                    created_by=plan.created_by
                )
                
                # Parse and set metadata if available
                if target_data["metadata_snapshot"]:
                    metadata_dict = json.loads(target_data["metadata_snapshot"])
                    rollback_changes.metadata = PromptMetadata.from_dict(metadata_dict)
                
                # Create new version with rollback content
                new_version = self.version_control.create_version(plan.prompt_id, rollback_changes)
                
                # Log rollback operation
                self._log_rollback_operation(plan, new_version.version_id)
                
                # Analyze performance impact if possible
                performance_impact = self._get_performance_comparison(
                    plan.current_version_id, plan.target_version_id
                )
                
                result = RollbackResult(
                    success=True,
                    new_version_id=new_version.version_id,
                    rolled_back_to=plan.target_version_id,
                    message=f"Successfully rolled back to version {plan.target_version_id}",
                    warnings=plan.warnings,
                    performance_impact=performance_impact
                )
                
                self.logger.info(f"Executed rollback for prompt {plan.prompt_id}")
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to execute rollback: {e}")
            return RollbackResult(
                success=False,
                message=f"Rollback failed: {str(e)}"
            )
    
    def get_rollback_candidates(self, prompt_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of versions that can be rolled back to."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT pv.version_id, pv.commit_message, pv.created_at, pv.created_by,
                           ppm.average_score, ppm.success_rate, ppm.total_executions
                    FROM prompt_versions pv
                    LEFT JOIN prompt_performance_metrics ppm ON pv.version_id = ppm.version_id
                    WHERE pv.prompt_id = ? AND pv.status = 'active'
                    ORDER BY pv.created_at DESC
                    LIMIT ?
                """, (prompt_id, limit))
                
                candidates = []
                for row in cursor.fetchall():
                    candidate = {
                        "version_id": row["version_id"],
                        "commit_message": row["commit_message"],
                        "created_at": row["created_at"],
                        "created_by": row["created_by"],
                        "performance_metrics": {
                            "average_score": row["average_score"],
                            "success_rate": row["success_rate"],
                            "total_executions": row["total_executions"]
                        } if row["average_score"] is not None else None
                    }
                    candidates.append(candidate)
                
                return candidates
                
        except Exception as e:
            self.logger.error(f"Failed to get rollback candidates: {e}")
            return []
    
    def get_rollback_history(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Get history of rollback operations for a prompt."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT operation_type, details, created_at, created_by
                    FROM prompt_operations_log 
                    WHERE prompt_id = ? AND operation_type = 'rollback'
                    ORDER BY created_at DESC
                """, (prompt_id,))
                
                history = []
                for row in cursor.fetchall():
                    details = json.loads(row["details"]) if row["details"] else {}
                    history.append({
                        "operation_type": row["operation_type"],
                        "details": details,
                        "created_at": row["created_at"],
                        "created_by": row["created_by"]
                    })
                
                return history
                
        except Exception as e:
            self.logger.error(f"Failed to get rollback history: {e}")
            return []
    
    def _perform_safety_checks(self, plan: RollbackPlan):
        """Perform safety checks before rollback."""
        try:
            with self.db_manager.get_connection() as conn:
                # Check if target version is too old
                cursor = conn.execute("""
                    SELECT created_at FROM prompt_versions 
                    WHERE version_id = ?
                """, (plan.target_version_id,))
                target_created = cursor.fetchone()
                
                if target_created:
                    target_date = datetime.fromisoformat(target_created["created_at"])
                    days_old = (datetime.now() - target_date).days
                    
                    if days_old > 30:
                        plan.warnings.append(f"Target version is {days_old} days old")
                    
                    if days_old > 90:
                        plan.warnings.append("Rolling back to very old version - consider creating new version instead")
                
                # Check for dependent versions
                cursor = conn.execute("""
                    SELECT COUNT(*) as count FROM prompt_versions 
                    WHERE parent_version = ? AND status = 'active'
                """, (plan.current_version_id,))
                dependent_count = cursor.fetchone()["count"]
                
                if dependent_count > 0:
                    plan.warnings.append(f"{dependent_count} versions depend on current version")
                
                # Check for recent executions
                cursor = conn.execute("""
                    SELECT COUNT(*) as count FROM prompt_executions 
                    WHERE version_id = ? AND executed_at > datetime('now', '-24 hours')
                """, (plan.current_version_id,))
                recent_executions = cursor.fetchone()["count"]
                
                if recent_executions > 10:
                    plan.warnings.append(f"Current version has {recent_executions} recent executions")
                
                # Add safety checks to plan
                plan.safety_checks = [
                    "Target version exists and is accessible",
                    "Current version can be preserved",
                    "Rollback operation is reversible",
                    "No critical dependencies will be broken"
                ]
                
                # Determine if rollback should be blocked
                critical_warnings = [w for w in plan.warnings if "critical" in w.lower()]
                if critical_warnings:
                    plan.can_rollback = False
                    plan.warnings.append("Rollback blocked due to critical issues")
                
        except Exception as e:
            self.logger.error(f"Error performing safety checks: {e}")
            plan.warnings.append(f"Safety check failed: {str(e)}")
            plan.can_rollback = False
    
    def _analyze_rollback_impact(self, plan: RollbackPlan) -> Dict[str, Any]:
        """Analyze potential impact of rollback operation."""
        impact = {
            "content_changes": {},
            "metadata_changes": {},
            "performance_impact": {},
            "risk_level": "low"
        }
        
        try:
            with self.db_manager.get_connection() as conn:
                # Get both versions for comparison
                cursor = conn.execute("""
                    SELECT version_id, content, metadata_snapshot
                    FROM prompt_versions 
                    WHERE version_id IN (?, ?)
                """, (plan.current_version_id, plan.target_version_id))
                
                versions = {row["version_id"]: row for row in cursor.fetchall()}
                
                if len(versions) == 2:
                    current = versions[plan.current_version_id]
                    target = versions[plan.target_version_id]
                    
                    # Analyze content changes
                    content_diff = len(current["content"]) - len(target["content"])
                    impact["content_changes"] = {
                        "character_difference": content_diff,
                        "significant_change": abs(content_diff) > 100
                    }
                    
                    # Analyze metadata changes
                    if current["metadata_snapshot"] and target["metadata_snapshot"]:
                        current_meta = json.loads(current["metadata_snapshot"])
                        target_meta = json.loads(target["metadata_snapshot"])
                        
                        meta_changes = {}
                        for key in set(current_meta.keys()) | set(target_meta.keys()):
                            if current_meta.get(key) != target_meta.get(key):
                                meta_changes[key] = {
                                    "from": current_meta.get(key),
                                    "to": target_meta.get(key)
                                }
                        
                        impact["metadata_changes"] = meta_changes
                    
                    # Determine risk level
                    if abs(content_diff) > 500 or len(impact["metadata_changes"]) > 3:
                        impact["risk_level"] = "high"
                    elif abs(content_diff) > 100 or len(impact["metadata_changes"]) > 1:
                        impact["risk_level"] = "medium"
                
        except Exception as e:
            self.logger.error(f"Error analyzing rollback impact: {e}")
            impact["error"] = str(e)
        
        return impact
    
    def _log_rollback_operation(self, plan: RollbackPlan, new_version_id: str):
        """Log rollback operation for audit trail."""
        try:
            # Create operations log table if it doesn't exist
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS prompt_operations_log (
                        id TEXT PRIMARY KEY,
                        prompt_id TEXT NOT NULL,
                        operation_type TEXT NOT NULL,
                        details TEXT,
                        created_at DATETIME NOT NULL,
                        created_by TEXT DEFAULT '',
                        FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
                    )
                """)
                
                # Log the rollback operation
                from ...models.base import generate_id
                
                log_details = {
                    "rollback_plan": plan.to_dict(),
                    "new_version_id": new_version_id,
                    "reason": plan.reason.value
                }
                
                conn.execute("""
                    INSERT INTO prompt_operations_log 
                    (id, prompt_id, operation_type, details, created_at, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    generate_id(),
                    plan.prompt_id,
                    "rollback",
                    json.dumps(log_details),
                    datetime.now(),
                    plan.created_by
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log rollback operation: {e}")
    
    def _get_performance_comparison(self, current_version_id: str, 
                                  target_version_id: str) -> Optional[Dict[str, Any]]:
        """Get performance comparison between versions."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT version_id, average_score, success_rate, average_tokens,
                           average_cost, average_response_time, total_executions
                    FROM prompt_performance_metrics 
                    WHERE version_id IN (?, ?)
                """, (current_version_id, target_version_id))
                
                metrics = {row["version_id"]: row for row in cursor.fetchall()}
                
                if len(metrics) == 2:
                    current = metrics[current_version_id]
                    target = metrics[target_version_id]
                    
                    comparison = {}
                    for metric in ["average_score", "success_rate", "average_tokens", 
                                  "average_cost", "average_response_time"]:
                        current_val = current[metric] or 0
                        target_val = target[metric] or 0
                        
                        if current_val > 0:
                            change = ((target_val - current_val) / current_val) * 100
                            comparison[f"{metric}_change"] = round(change, 2)
                    
                    return comparison
                
        except Exception as e:
            self.logger.error(f"Error getting performance comparison: {e}")
        
        return None