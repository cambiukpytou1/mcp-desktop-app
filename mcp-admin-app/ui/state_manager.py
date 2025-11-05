"""
UI State Management and Data Synchronization
============================================

Manages state across UI components and implements real-time updates and notifications.
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json


class EventType(Enum):
    """Types of events that can be published."""
    TEMPLATE_CREATED = "template_created"
    TEMPLATE_UPDATED = "template_updated"
    TEMPLATE_DELETED = "template_deleted"
    SECURITY_SCAN_COMPLETED = "security_scan_completed"
    APPROVAL_STATUS_CHANGED = "approval_status_changed"
    WORKSPACE_CHANGED = "workspace_changed"
    TEST_COMPLETED = "test_completed"
    ANALYTICS_UPDATED = "analytics_updated"
    USER_NOTIFICATION = "user_notification"


@dataclass
class StateEvent:
    """Event representing a state change."""
    event_type: EventType
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    target: Optional[str] = None  # Specific component target, None for broadcast


@dataclass
class CacheEntry:
    """Cache entry with expiration."""
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 300  # 5 minutes default
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return (datetime.now() - self.timestamp).total_seconds() > self.ttl_seconds


class UIStateManager:
    """Manages UI state and handles cross-component data synchronization."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Event system
        self.event_subscribers: Dict[EventType, List[Callable]] = {}
        self.event_queue: List[StateEvent] = []
        self.event_lock = threading.Lock()
        
        # State storage
        self.component_states: Dict[str, Dict[str, Any]] = {}
        self.shared_state: Dict[str, Any] = {}
        self.state_lock = threading.Lock()
        
        # Data cache
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_lock = threading.Lock()
        
        # Notification system
        self.notification_callbacks: List[Callable] = []
        self.notification_queue: List[Dict[str, Any]] = []
        
        # Background processing
        self.running = True
        self.background_thread = threading.Thread(target=self._background_processor, daemon=True)
        self.background_thread.start()
        
        self.logger.info("UI State Manager initialized")
    
    def subscribe(self, event_type: EventType, callback: Callable[[StateEvent], None]):
        """Subscribe to events of a specific type."""
        with self.event_lock:
            if event_type not in self.event_subscribers:
                self.event_subscribers[event_type] = []
            self.event_subscribers[event_type].append(callback)
        
        self.logger.debug(f"Subscribed to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[StateEvent], None]):
        """Unsubscribe from events."""
        with self.event_lock:
            if event_type in self.event_subscribers:
                try:
                    self.event_subscribers[event_type].remove(callback)
                except ValueError:
                    pass
    
    def publish_event(self, event_type: EventType, data: Any, source: str = "unknown", target: str = None):
        """Publish an event to subscribers."""
        event = StateEvent(
            event_type=event_type,
            data=data,
            source=source,
            target=target
        )
        
        with self.event_lock:
            self.event_queue.append(event)
        
        self.logger.debug(f"Published event: {event_type.value} from {source}")
    
    def _process_events(self):
        """Process queued events."""
        events_to_process = []
        
        with self.event_lock:
            events_to_process = self.event_queue.copy()
            self.event_queue.clear()
        
        for event in events_to_process:
            self._dispatch_event(event)
    
    def _dispatch_event(self, event: StateEvent):
        """Dispatch event to subscribers."""
        try:
            subscribers = self.event_subscribers.get(event.event_type, [])
            
            for callback in subscribers:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Error in event callback: {e}")
        
        except Exception as e:
            self.logger.error(f"Error dispatching event {event.event_type.value}: {e}")
    
    def set_component_state(self, component_id: str, key: str, value: Any):
        """Set state for a specific component."""
        with self.state_lock:
            if component_id not in self.component_states:
                self.component_states[component_id] = {}
            self.component_states[component_id][key] = value
        
        # Publish state change event
        self.publish_event(
            EventType.USER_NOTIFICATION,
            {"type": "state_change", "component": component_id, "key": key},
            source="state_manager"
        )
    
    def get_component_state(self, component_id: str, key: str, default: Any = None) -> Any:
        """Get state for a specific component."""
        with self.state_lock:
            return self.component_states.get(component_id, {}).get(key, default)
    
    def get_all_component_state(self, component_id: str) -> Dict[str, Any]:
        """Get all state for a component."""
        with self.state_lock:
            return self.component_states.get(component_id, {}).copy()
    
    def set_shared_state(self, key: str, value: Any):
        """Set shared state accessible by all components."""
        with self.state_lock:
            self.shared_state[key] = value
        
        # Publish shared state change
        self.publish_event(
            EventType.USER_NOTIFICATION,
            {"type": "shared_state_change", "key": key, "value": value},
            source="state_manager"
        )
    
    def get_shared_state(self, key: str, default: Any = None) -> Any:
        """Get shared state value."""
        with self.state_lock:
            return self.shared_state.get(key, default)
    
    def cache_data(self, key: str, data: Any, ttl_seconds: int = 300):
        """Cache data with expiration."""
        with self.cache_lock:
            self.cache[key] = CacheEntry(data=data, ttl_seconds=ttl_seconds)
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data if not expired."""
        with self.cache_lock:
            entry = self.cache.get(key)
            if entry and not entry.is_expired():
                return entry.data
            elif entry:
                # Remove expired entry
                del self.cache[key]
        return None
    
    def invalidate_cache(self, key: str = None):
        """Invalidate cache entry or all cache."""
        with self.cache_lock:
            if key:
                self.cache.pop(key, None)
            else:
                self.cache.clear()
    
    def add_notification_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for notifications."""
        self.notification_callbacks.append(callback)
    
    def show_notification(self, message: str, notification_type: str = "info", 
                         duration: int = 5000, actions: List[Dict[str, Any]] = None):
        """Show notification to user."""
        notification = {
            "message": message,
            "type": notification_type,
            "duration": duration,
            "actions": actions or [],
            "timestamp": datetime.now().isoformat()
        }
        
        self.notification_queue.append(notification)
        
        # Notify callbacks
        for callback in self.notification_callbacks:
            try:
                callback(notification)
            except Exception as e:
                self.logger.error(f"Error in notification callback: {e}")
    
    def _background_processor(self):
        """Background thread for processing events and cleanup."""
        while self.running:
            try:
                # Process events
                self._process_events()
                
                # Clean up expired cache entries
                self._cleanup_cache()
                
                # Sleep for a short interval
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in background processor: {e}")
                time.sleep(1)
    
    def _cleanup_cache(self):
        """Clean up expired cache entries."""
        with self.cache_lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.cache[key]
    
    def shutdown(self):
        """Shutdown the state manager."""
        self.running = False
        if self.background_thread.is_alive():
            self.background_thread.join(timeout=1)
        self.logger.info("UI State Manager shutdown")
    
    # Convenience methods for common state operations
    
    def set_current_template(self, template_id: str, template_data: Dict[str, Any]):
        """Set current template in shared state."""
        self.set_shared_state("current_template_id", template_id)
        self.set_shared_state("current_template_data", template_data)
        
        self.publish_event(
            EventType.TEMPLATE_UPDATED,
            {"template_id": template_id, "data": template_data},
            source="state_manager"
        )
    
    def get_current_template(self) -> Optional[Dict[str, Any]]:
        """Get current template from shared state."""
        template_id = self.get_shared_state("current_template_id")
        template_data = self.get_shared_state("current_template_data")
        
        if template_id and template_data:
            return {"id": template_id, "data": template_data}
        return None
    
    def set_current_workspace(self, workspace_id: str, workspace_data: Dict[str, Any]):
        """Set current workspace in shared state."""
        self.set_shared_state("current_workspace_id", workspace_id)
        self.set_shared_state("current_workspace_data", workspace_data)
        
        self.publish_event(
            EventType.WORKSPACE_CHANGED,
            {"workspace_id": workspace_id, "data": workspace_data},
            source="state_manager"
        )
    
    def get_current_workspace(self) -> Optional[Dict[str, Any]]:
        """Get current workspace from shared state."""
        workspace_id = self.get_shared_state("current_workspace_id")
        workspace_data = self.get_shared_state("current_workspace_data")
        
        if workspace_id and workspace_data:
            return {"id": workspace_id, "data": workspace_data}
        return None
    
    def update_security_status(self, template_id: str, scan_results: Dict[str, Any]):
        """Update security status for a template."""
        self.cache_data(f"security_scan_{template_id}", scan_results, ttl_seconds=600)
        
        self.publish_event(
            EventType.SECURITY_SCAN_COMPLETED,
            {"template_id": template_id, "results": scan_results},
            source="security_scanner"
        )
    
    def update_approval_status(self, item_id: str, status: str, details: Dict[str, Any]):
        """Update approval status for an item."""
        approval_data = {
            "item_id": item_id,
            "status": status,
            "details": details,
            "updated_at": datetime.now().isoformat()
        }
        
        self.cache_data(f"approval_status_{item_id}", approval_data)
        
        self.publish_event(
            EventType.APPROVAL_STATUS_CHANGED,
            approval_data,
            source="approval_workflow"
        )
    
    def update_test_results(self, test_session_id: str, results: Dict[str, Any]):
        """Update test results."""
        self.cache_data(f"test_results_{test_session_id}", results, ttl_seconds=3600)
        
        self.publish_event(
            EventType.TEST_COMPLETED,
            {"session_id": test_session_id, "results": results},
            source="testing_service"
        )
    
    def update_analytics_data(self, analytics_type: str, data: Dict[str, Any]):
        """Update analytics data."""
        self.cache_data(f"analytics_{analytics_type}", data, ttl_seconds=1800)
        
        self.publish_event(
            EventType.ANALYTICS_UPDATED,
            {"type": analytics_type, "data": data},
            source="analytics_service"
        )
    
    def get_component_registry(self) -> Dict[str, List[str]]:
        """Get registry of all components and their state keys."""
        with self.state_lock:
            registry = {}
            for component_id, state in self.component_states.items():
                registry[component_id] = list(state.keys())
            return registry
    
    def export_state(self) -> Dict[str, Any]:
        """Export current state for debugging or persistence."""
        with self.state_lock:
            return {
                "component_states": self.component_states.copy(),
                "shared_state": self.shared_state.copy(),
                "timestamp": datetime.now().isoformat()
            }
    
    def import_state(self, state_data: Dict[str, Any]):
        """Import state data."""
        with self.state_lock:
            if "component_states" in state_data:
                self.component_states.update(state_data["component_states"])
            
            if "shared_state" in state_data:
                self.shared_state.update(state_data["shared_state"])
        
        self.logger.info("State imported successfully")


# Global state manager instance
_state_manager = None


def get_state_manager() -> UIStateManager:
    """Get global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = UIStateManager()
    return _state_manager


def initialize_state_manager() -> UIStateManager:
    """Initialize global state manager."""
    global _state_manager
    if _state_manager is not None:
        _state_manager.shutdown()
    _state_manager = UIStateManager()
    return _state_manager


def shutdown_state_manager():
    """Shutdown global state manager."""
    global _state_manager
    if _state_manager is not None:
        _state_manager.shutdown()
        _state_manager = None