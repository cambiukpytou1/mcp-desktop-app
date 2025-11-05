"""
Human Rating Interface and Storage
=================================

System for collecting and managing human evaluations of prompt responses.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from .scoring_engine import EvaluationScore, EvaluationResult, ScoringRubric, ScoringCriterion, EvaluatorType
from .llm_provider_abstraction import LLMResponse
from models.base import generate_id


class RatingStatus(Enum):
    """Status of human rating tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    EXPIRED = "expired"


class RatingPriority(Enum):
    """Priority levels for rating tasks."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class HumanRater:
    """Human rater profile and capabilities."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    email: str = ""
    expertise_areas: List[str] = field(default_factory=list)
    rating_count: int = 0
    average_rating_time: float = 0.0
    reliability_score: float = 1.0  # 0.0 to 1.0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_active: Optional[datetime] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "expertise_areas": self.expertise_areas,
            "rating_count": self.rating_count,
            "average_rating_time": self.average_rating_time,
            "reliability_score": self.reliability_score,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "preferences": self.preferences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HumanRater':
        """Create instance from dictionary."""
        return cls(
            id=data.get("id", generate_id()),
            name=data.get("name", ""),
            email=data.get("email", ""),
            expertise_areas=data.get("expertise_areas", []),
            rating_count=data.get("rating_count", 0),
            average_rating_time=data.get("average_rating_time", 0.0),
            reliability_score=data.get("reliability_score", 1.0),
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            last_active=datetime.fromisoformat(data["last_active"]) if data.get("last_active") else None,
            preferences=data.get("preferences", {})
        )


@dataclass
class RatingTask:
    """Individual rating task assigned to a human rater."""
    id: str = field(default_factory=generate_id)
    response_id: str = ""
    rubric_id: str = ""
    rater_id: str = ""
    status: RatingStatus = RatingStatus.PENDING
    priority: RatingPriority = RatingPriority.NORMAL
    assigned_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_time_minutes: int = 10
    actual_time_minutes: Optional[int] = None
    context: Dict[str, Any] = field(default_factory=dict)
    instructions: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "response_id": self.response_id,
            "rubric_id": self.rubric_id,
            "rater_id": self.rater_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "assigned_at": self.assigned_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_time_minutes": self.estimated_time_minutes,
            "actual_time_minutes": self.actual_time_minutes,
            "context": self.context,
            "instructions": self.instructions,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RatingTask':
        """Create instance from dictionary."""
        return cls(
            id=data.get("id", generate_id()),
            response_id=data.get("response_id", ""),
            rubric_id=data.get("rubric_id", ""),
            rater_id=data.get("rater_id", ""),
            status=RatingStatus(data.get("status", "pending")),
            priority=RatingPriority(data.get("priority", "normal")),
            assigned_at=datetime.fromisoformat(data["assigned_at"]) if "assigned_at" in data else datetime.now(),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            estimated_time_minutes=data.get("estimated_time_minutes", 10),
            actual_time_minutes=data.get("actual_time_minutes"),
            context=data.get("context", {}),
            instructions=data.get("instructions", ""),
            metadata=data.get("metadata", {})
        )


@dataclass
class HumanRating:
    """Human rating submission for a response."""
    id: str = field(default_factory=generate_id)
    task_id: str = ""
    response_id: str = ""
    rater_id: str = ""
    rubric_id: str = ""
    scores: List[EvaluationScore] = field(default_factory=list)
    overall_score: float = 0.0
    confidence: float = 1.0
    comments: str = ""
    rating_time_minutes: int = 0
    submitted_at: datetime = field(default_factory=datetime.now)
    quality_flags: List[str] = field(default_factory=list)  # inconsistent, rushed, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "response_id": self.response_id,
            "rater_id": self.rater_id,
            "rubric_id": self.rubric_id,
            "scores": [score.to_dict() for score in self.scores],
            "overall_score": self.overall_score,
            "confidence": self.confidence,
            "comments": self.comments,
            "rating_time_minutes": self.rating_time_minutes,
            "submitted_at": self.submitted_at.isoformat(),
            "quality_flags": self.quality_flags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HumanRating':
        """Create instance from dictionary."""
        return cls(
            id=data.get("id", generate_id()),
            task_id=data.get("task_id", ""),
            response_id=data.get("response_id", ""),
            rater_id=data.get("rater_id", ""),
            rubric_id=data.get("rubric_id", ""),
            scores=[EvaluationScore(**score_data) for score_data in data.get("scores", [])],
            overall_score=data.get("overall_score", 0.0),
            confidence=data.get("confidence", 1.0),
            comments=data.get("comments", ""),
            rating_time_minutes=data.get("rating_time_minutes", 0),
            submitted_at=datetime.fromisoformat(data["submitted_at"]) if "submitted_at" in data else datetime.now(),
            quality_flags=data.get("quality_flags", [])
        )


class HumanRatingInterface:
    """Interface for managing human rating tasks and collecting evaluations."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.raters: Dict[str, HumanRater] = {}
        self.tasks: Dict[str, RatingTask] = {}
        self.ratings: Dict[str, HumanRating] = {}
        
        # Load existing data
        self._load_raters()
        self._load_tasks()
        self._load_ratings()
    
    def _load_raters(self):
        """Load human raters from configuration."""
        try:
            raters_config = self.config_manager.get("human_raters", {})
            for rater_id, rater_data in raters_config.items():
                rater = HumanRater.from_dict(rater_data)
                self.raters[rater_id] = rater
            
            self.logger.info(f"Loaded {len(self.raters)} human raters")
        except Exception as e:
            self.logger.error(f"Failed to load raters: {e}")
    
    def _load_tasks(self):
        """Load rating tasks from storage."""
        try:
            tasks_config = self.config_manager.get("rating_tasks", {})
            for task_id, task_data in tasks_config.items():
                task = RatingTask.from_dict(task_data)
                self.tasks[task_id] = task
            
            self.logger.info(f"Loaded {len(self.tasks)} rating tasks")
        except Exception as e:
            self.logger.error(f"Failed to load tasks: {e}")
    
    def _load_ratings(self):
        """Load human ratings from storage."""
        try:
            ratings_config = self.config_manager.get("human_ratings", {})
            for rating_id, rating_data in ratings_config.items():
                rating = HumanRating.from_dict(rating_data)
                self.ratings[rating_id] = rating
            
            self.logger.info(f"Loaded {len(self.ratings)} human ratings")
        except Exception as e:
            self.logger.error(f"Failed to load ratings: {e}")
    
    def add_rater(self, rater: HumanRater) -> bool:
        """Add a new human rater."""
        try:
            self.raters[rater.id] = rater
            self._save_rater(rater)
            self.logger.info(f"Added rater: {rater.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add rater: {e}")
            return False
    
    def _save_rater(self, rater: HumanRater):
        """Save rater to configuration."""
        raters_config = self.config_manager.get("human_raters", {})
        raters_config[rater.id] = rater.to_dict()
        self.config_manager.set("human_raters", raters_config)
    
    def update_rater(self, rater: HumanRater) -> bool:
        """Update an existing rater."""
        if rater.id in self.raters:
            self.raters[rater.id] = rater
            self._save_rater(rater)
            self.logger.info(f"Updated rater: {rater.name}")
            return True
        return False
    
    def get_available_raters(self, expertise_area: str = None) -> List[HumanRater]:
        """Get list of available raters, optionally filtered by expertise."""
        available_raters = [
            rater for rater in self.raters.values() 
            if rater.is_active
        ]
        
        if expertise_area:
            available_raters = [
                rater for rater in available_raters
                if expertise_area in rater.expertise_areas
            ]
        
        # Sort by reliability score and availability
        available_raters.sort(key=lambda r: (-r.reliability_score, r.rating_count))
        
        return available_raters
    
    def create_rating_task(self, 
                          response_id: str,
                          rubric_id: str,
                          rater_id: str = None,
                          priority: RatingPriority = RatingPriority.NORMAL,
                          context: Dict[str, Any] = None,
                          instructions: str = "",
                          due_hours: int = 24) -> Optional[RatingTask]:
        """Create a new rating task."""
        try:
            # Auto-assign rater if not specified
            if not rater_id:
                available_raters = self.get_available_raters()
                if not available_raters:
                    self.logger.warning("No available raters for task assignment")
                    return None
                rater_id = available_raters[0].id
            
            # Calculate due date
            due_date = datetime.now()
            due_date = due_date.replace(hour=due_date.hour + due_hours)
            
            task = RatingTask(
                response_id=response_id,
                rubric_id=rubric_id,
                rater_id=rater_id,
                priority=priority,
                due_date=due_date,
                context=context or {},
                instructions=instructions
            )
            
            self.tasks[task.id] = task
            self._save_task(task)
            
            self.logger.info(f"Created rating task {task.id} for rater {rater_id}")
            return task
        
        except Exception as e:
            self.logger.error(f"Failed to create rating task: {e}")
            return None
    
    def _save_task(self, task: RatingTask):
        """Save task to configuration."""
        tasks_config = self.config_manager.get("rating_tasks", {})
        tasks_config[task.id] = task.to_dict()
        self.config_manager.set("rating_tasks", tasks_config)
    
    def get_tasks_for_rater(self, rater_id: str, status: RatingStatus = None) -> List[RatingTask]:
        """Get tasks assigned to a specific rater."""
        tasks = [
            task for task in self.tasks.values()
            if task.rater_id == rater_id
        ]
        
        if status:
            tasks = [task for task in tasks if task.status == status]
        
        # Sort by priority and due date
        priority_order = {
            RatingPriority.URGENT: 0,
            RatingPriority.HIGH: 1,
            RatingPriority.NORMAL: 2,
            RatingPriority.LOW: 3
        }
        
        tasks.sort(key=lambda t: (
            priority_order.get(t.priority, 2),
            t.due_date or datetime.max
        ))
        
        return tasks
    
    def start_rating_task(self, task_id: str, rater_id: str) -> bool:
        """Mark a rating task as started."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.rater_id == rater_id and task.status == RatingStatus.PENDING:
                task.status = RatingStatus.IN_PROGRESS
                task.started_at = datetime.now()
                self._save_task(task)
                
                # Update rater last active
                if rater_id in self.raters:
                    self.raters[rater_id].last_active = datetime.now()
                    self._save_rater(self.raters[rater_id])
                
                self.logger.info(f"Started rating task {task_id}")
                return True
        return False
    
    def submit_rating(self, 
                     task_id: str,
                     rater_id: str,
                     scores: List[EvaluationScore],
                     overall_score: float,
                     confidence: float = 1.0,
                     comments: str = "",
                     rating_time_minutes: int = 0) -> Optional[HumanRating]:
        """Submit a human rating for a task."""
        try:
            if task_id not in self.tasks:
                raise ValueError(f"Task not found: {task_id}")
            
            task = self.tasks[task_id]
            if task.rater_id != rater_id:
                raise ValueError("Task not assigned to this rater")
            
            if task.status != RatingStatus.IN_PROGRESS:
                raise ValueError(f"Task not in progress: {task.status}")
            
            # Create rating
            rating = HumanRating(
                task_id=task_id,
                response_id=task.response_id,
                rater_id=rater_id,
                rubric_id=task.rubric_id,
                scores=scores,
                overall_score=overall_score,
                confidence=confidence,
                comments=comments,
                rating_time_minutes=rating_time_minutes
            )
            
            # Validate scores
            if not self._validate_rating_scores(rating):
                raise ValueError("Invalid rating scores")
            
            # Save rating
            self.ratings[rating.id] = rating
            self._save_rating(rating)
            
            # Update task status
            task.status = RatingStatus.COMPLETED
            task.completed_at = datetime.now()
            task.actual_time_minutes = rating_time_minutes
            self._save_task(task)
            
            # Update rater statistics
            self._update_rater_statistics(rater_id, rating_time_minutes)
            
            self.logger.info(f"Submitted rating {rating.id} for task {task_id}")
            return rating
        
        except Exception as e:
            self.logger.error(f"Failed to submit rating: {e}")
            return None
    
    def _validate_rating_scores(self, rating: HumanRating) -> bool:
        """Validate that rating scores are within acceptable ranges."""
        try:
            # Check that all scores are within valid ranges
            for score in rating.scores:
                if score.score < 0 or score.score > 10:  # Assuming 0-10 scale
                    return False
                if score.confidence < 0 or score.confidence > 1:
                    return False
            
            # Check overall score
            if rating.overall_score < 0 or rating.overall_score > 10:
                return False
            
            if rating.confidence < 0 or rating.confidence > 1:
                return False
            
            return True
        except Exception:
            return False
    
    def _save_rating(self, rating: HumanRating):
        """Save rating to configuration."""
        ratings_config = self.config_manager.get("human_ratings", {})
        ratings_config[rating.id] = rating.to_dict()
        self.config_manager.set("human_ratings", ratings_config)
    
    def _update_rater_statistics(self, rater_id: str, rating_time_minutes: int):
        """Update rater statistics after completing a rating."""
        if rater_id in self.raters:
            rater = self.raters[rater_id]
            
            # Update rating count
            rater.rating_count += 1
            
            # Update average rating time
            if rater.average_rating_time == 0:
                rater.average_rating_time = rating_time_minutes
            else:
                rater.average_rating_time = (
                    (rater.average_rating_time * (rater.rating_count - 1) + rating_time_minutes) 
                    / rater.rating_count
                )
            
            # Update last active
            rater.last_active = datetime.now()
            
            self._save_rater(rater)
    
    def skip_rating_task(self, task_id: str, rater_id: str, reason: str = "") -> bool:
        """Skip a rating task."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.rater_id == rater_id:
                task.status = RatingStatus.SKIPPED
                task.completed_at = datetime.now()
                task.metadata["skip_reason"] = reason
                self._save_task(task)
                
                self.logger.info(f"Skipped rating task {task_id}: {reason}")
                return True
        return False
    
    def get_ratings_for_response(self, response_id: str) -> List[HumanRating]:
        """Get all human ratings for a specific response."""
        return [
            rating for rating in self.ratings.values()
            if rating.response_id == response_id
        ]
    
    def get_rater_statistics(self, rater_id: str) -> Dict[str, Any]:
        """Get statistics for a specific rater."""
        if rater_id not in self.raters:
            return {}
        
        rater = self.raters[rater_id]
        
        # Count tasks by status
        rater_tasks = [task for task in self.tasks.values() if task.rater_id == rater_id]
        task_counts = {}
        for status in RatingStatus:
            task_counts[status.value] = len([t for t in rater_tasks if t.status == status])
        
        # Get recent ratings
        rater_ratings = [r for r in self.ratings.values() if r.rater_id == rater_id]
        recent_ratings = sorted(rater_ratings, key=lambda r: r.submitted_at, reverse=True)[:10]
        
        return {
            "rater": rater.to_dict(),
            "task_counts": task_counts,
            "total_ratings": len(rater_ratings),
            "recent_ratings": [r.to_dict() for r in recent_ratings],
            "average_score": sum(r.overall_score for r in rater_ratings) / len(rater_ratings) if rater_ratings else 0.0
        }
    
    def get_rating_quality_metrics(self) -> Dict[str, Any]:
        """Get overall quality metrics for human ratings."""
        if not self.ratings:
            return {"total_ratings": 0}
        
        ratings = list(self.ratings.values())
        
        # Calculate inter-rater reliability (simplified)
        response_ratings = {}
        for rating in ratings:
            if rating.response_id not in response_ratings:
                response_ratings[rating.response_id] = []
            response_ratings[rating.response_id].append(rating.overall_score)
        
        # Find responses with multiple ratings
        multi_rated = {k: v for k, v in response_ratings.items() if len(v) > 1}
        
        agreement_scores = []
        for scores in multi_rated.values():
            if len(scores) >= 2:
                # Calculate standard deviation as a measure of disagreement
                mean_score = sum(scores) / len(scores)
                variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
                agreement_scores.append(1.0 / (1.0 + variance))  # Higher agreement = lower variance
        
        avg_agreement = sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0.0
        
        return {
            "total_ratings": len(ratings),
            "unique_responses_rated": len(response_ratings),
            "multi_rated_responses": len(multi_rated),
            "average_inter_rater_agreement": avg_agreement,
            "average_overall_score": sum(r.overall_score for r in ratings) / len(ratings),
            "average_confidence": sum(r.confidence for r in ratings) / len(ratings),
            "average_rating_time": sum(r.rating_time_minutes for r in ratings) / len(ratings)
        }
    
    def reassign_task(self, task_id: str, new_rater_id: str) -> bool:
        """Reassign a task to a different rater."""
        if task_id in self.tasks and new_rater_id in self.raters:
            task = self.tasks[task_id]
            if task.status == RatingStatus.PENDING:
                old_rater_id = task.rater_id
                task.rater_id = new_rater_id
                task.assigned_at = datetime.now()
                self._save_task(task)
                
                self.logger.info(f"Reassigned task {task_id} from {old_rater_id} to {new_rater_id}")
                return True
        return False
    
    def get_pending_tasks_summary(self) -> Dict[str, Any]:
        """Get summary of pending rating tasks."""
        pending_tasks = [task for task in self.tasks.values() if task.status == RatingStatus.PENDING]
        
        # Group by priority
        priority_counts = {}
        for priority in RatingPriority:
            priority_counts[priority.value] = len([t for t in pending_tasks if t.priority == priority])
        
        # Group by rater
        rater_counts = {}
        for task in pending_tasks:
            rater_counts[task.rater_id] = rater_counts.get(task.rater_id, 0) + 1
        
        # Overdue tasks
        now = datetime.now()
        overdue_tasks = [t for t in pending_tasks if t.due_date and t.due_date < now]
        
        return {
            "total_pending": len(pending_tasks),
            "priority_breakdown": priority_counts,
            "rater_workload": rater_counts,
            "overdue_count": len(overdue_tasks),
            "average_estimated_time": sum(t.estimated_time_minutes for t in pending_tasks) / len(pending_tasks) if pending_tasks else 0
        }


class HumanRatingService:
    """Service for managing human rating operations."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        self.logger.info("Human rating service initialized")
    
    def create_rating_task(self, response_id: str, rater_id: str, priority: RatingPriority = RatingPriority.NORMAL):
        """Create a new rating task."""
        try:
            # Implementation would go here
            self.logger.info(f"Created rating task for response {response_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create rating task: {e}")
            return False
    
    def get_pending_tasks(self, rater_id: str) -> List[Dict[str, Any]]:
        """Get pending rating tasks for a rater."""
        try:
            # Implementation would return actual tasks
            return []
        except Exception as e:
            self.logger.error(f"Failed to get pending tasks: {e}")
            return []
    
    def submit_rating(self, task_id: str, rating_data: Dict[str, Any]) -> bool:
        """Submit a human rating."""
        try:
            # Implementation would save the rating
            self.logger.info(f"Rating submitted for task {task_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to submit rating: {e}")
            return False