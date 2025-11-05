"""
Cost Tracking and Monitoring Service
===================================

Real-time token counting, cost estimation, and tracking per model with visual reporting and alerts.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from collections import defaultdict
import threading

from models.llm import (
    LLMProviderConfig, ModelConfig, TokenEstimate, CostEstimate, 
    TestExecution, LLMUsageRecord, UsageMetrics
)
from models.base import generate_id


@dataclass
class RealTimeTokenCount:
    """Real-time token counting for active sessions."""
    session_id: str
    provider_id: str
    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost": self.estimated_cost,
            "actual_cost": self.actual_cost,
            "start_time": self.start_time.isoformat(),
            "last_update": self.last_update.isoformat()
        }


@dataclass
class CostAlert:
    """Cost alert configuration and tracking."""
    alert_id: str = field(default_factory=generate_id)
    name: str = ""
    alert_type: str = "threshold"  # threshold, rate, budget
    threshold_value: float = 0.0
    time_window_minutes: int = 60
    provider_id: Optional[str] = None
    model_id: Optional[str] = None
    is_active: bool = True
    triggered_count: int = 0
    last_triggered: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "alert_id": self.alert_id,
            "name": self.name,
            "alert_type": self.alert_type,
            "threshold_value": self.threshold_value,
            "time_window_minutes": self.time_window_minutes,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "is_active": self.is_active,
            "triggered_count": self.triggered_count,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class CostReport:
    """Cost reporting data structure."""
    report_id: str = field(default_factory=generate_id)
    report_type: str = "summary"  # summary, detailed, comparison
    time_period_start: datetime = field(default_factory=datetime.now)
    time_period_end: datetime = field(default_factory=datetime.now)
    total_cost: float = 0.0
    total_tokens: int = 0
    total_requests: int = 0
    provider_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    model_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    hourly_breakdown: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "time_period_start": self.time_period_start.isoformat(),
            "time_period_end": self.time_period_end.isoformat(),
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "provider_breakdown": self.provider_breakdown,
            "model_breakdown": self.model_breakdown,
            "hourly_breakdown": self.hourly_breakdown,
            "generated_at": self.generated_at.isoformat()
        }


class TokenCounter:
    """Real-time token counting system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_sessions: Dict[str, RealTimeTokenCount] = {}
        self.lock = threading.Lock()
    
    def start_session(self, session_id: str, provider_id: str, model_id: str) -> RealTimeTokenCount:
        """Start a new token counting session."""
        with self.lock:
            session = RealTimeTokenCount(
                session_id=session_id,
                provider_id=provider_id,
                model_id=model_id
            )
            self.active_sessions[session_id] = session
            self.logger.info(f"Started token counting session: {session_id}")
            return session
    
    def update_session(self, session_id: str, input_tokens: int = 0, 
                      output_tokens: int = 0, actual_cost: float = 0.0) -> Optional[RealTimeTokenCount]:
        """Update token counts for an active session."""
        with self.lock:
            if session_id not in self.active_sessions:
                self.logger.warning(f"Session not found: {session_id}")
                return None
            
            session = self.active_sessions[session_id]
            session.input_tokens += input_tokens
            session.output_tokens += output_tokens
            session.actual_cost += actual_cost
            session.last_update = datetime.now()
            
            self.logger.debug(f"Updated session {session_id}: +{input_tokens} input, +{output_tokens} output, +${actual_cost:.4f}")
            return session
    
    def end_session(self, session_id: str) -> Optional[RealTimeTokenCount]:
        """End a token counting session and return final counts."""
        with self.lock:
            if session_id not in self.active_sessions:
                return None
            
            session = self.active_sessions.pop(session_id)
            self.logger.info(f"Ended session {session_id}: {session.input_tokens + session.output_tokens} total tokens, ${session.actual_cost:.4f}")
            return session
    
    def get_session(self, session_id: str) -> Optional[RealTimeTokenCount]:
        """Get current session data."""
        with self.lock:
            return self.active_sessions.get(session_id)
    
    def get_all_sessions(self) -> List[RealTimeTokenCount]:
        """Get all active sessions."""
        with self.lock:
            return list(self.active_sessions.values())
    
    def cleanup_stale_sessions(self, max_age_hours: int = 24):
        """Clean up sessions older than specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        stale_sessions = []
        
        with self.lock:
            for session_id, session in list(self.active_sessions.items()):
                if session.last_update < cutoff_time:
                    stale_sessions.append(session_id)
                    del self.active_sessions[session_id]
        
        if stale_sessions:
            self.logger.info(f"Cleaned up {len(stale_sessions)} stale sessions")


class CostEstimator:
    """Cost estimation engine for different models and providers."""
    
    def __init__(self, config_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.model_pricing: Dict[str, Dict[str, ModelConfig]] = {}
        self._load_pricing_data()
    
    def _load_pricing_data(self):
        """Load pricing data from configuration."""
        try:
            # Load provider configurations to get model pricing
            provider_configs = self.config_manager.get("llm_providers", {})
            
            for provider_id, config_data in provider_configs.items():
                try:
                    config = LLMProviderConfig.from_dict(config_data)
                    self.model_pricing[provider_id] = {}
                    
                    for model in config.models:
                        self.model_pricing[provider_id][model.model_id] = model
                    
                    self.logger.debug(f"Loaded pricing for {len(config.models)} models from {config.name}")
                
                except Exception as e:
                    self.logger.error(f"Failed to load pricing for provider {provider_id}: {e}")
        
        except Exception as e:
            self.logger.error(f"Failed to load pricing data: {e}")
    
    def estimate_cost(self, provider_id: str, model_id: str, 
                     input_tokens: int, output_tokens: int) -> CostEstimate:
        """Estimate cost for given token counts."""
        try:
            if provider_id not in self.model_pricing:
                self.logger.warning(f"No pricing data for provider: {provider_id}")
                return CostEstimate(
                    input_cost=0.0,
                    estimated_output_cost=0.0,
                    total_estimated_cost=0.0,
                    confidence_level=0.0
                )
            
            if model_id not in self.model_pricing[provider_id]:
                self.logger.warning(f"No pricing data for model: {model_id}")
                return CostEstimate(
                    input_cost=0.0,
                    estimated_output_cost=0.0,
                    total_estimated_cost=0.0,
                    confidence_level=0.0
                )
            
            model_config = self.model_pricing[provider_id][model_id]
            input_cost = input_tokens * model_config.input_cost_per_token
            output_cost = output_tokens * model_config.output_cost_per_token
            
            return CostEstimate(
                input_cost=input_cost,
                estimated_output_cost=output_cost,
                total_estimated_cost=input_cost + output_cost,
                confidence_level=0.95
            )
        
        except Exception as e:
            self.logger.error(f"Cost estimation failed: {e}")
            return CostEstimate(
                input_cost=0.0,
                estimated_output_cost=0.0,
                total_estimated_cost=0.0,
                confidence_level=0.0
            )
    
    def estimate_prompt_cost(self, provider_id: str, model_id: str, 
                           prompt: str, estimated_output_tokens: int = None) -> CostEstimate:
        """Estimate cost for a prompt before execution."""
        try:
            # Simple token estimation (in production, use proper tokenizers)
            input_tokens = len(prompt.split()) * 1.3  # Rough conversion
            
            if estimated_output_tokens is None:
                estimated_output_tokens = int(input_tokens * 0.5)  # Assume 50% of input
            
            return self.estimate_cost(provider_id, model_id, int(input_tokens), estimated_output_tokens)
        
        except Exception as e:
            self.logger.error(f"Prompt cost estimation failed: {e}")
            return CostEstimate(
                input_cost=0.0,
                estimated_output_cost=0.0,
                total_estimated_cost=0.0,
                confidence_level=0.0
            )
    
    def get_model_pricing(self, provider_id: str, model_id: str) -> Optional[ModelConfig]:
        """Get pricing information for a specific model."""
        return self.model_pricing.get(provider_id, {}).get(model_id)
    
    def refresh_pricing_data(self):
        """Refresh pricing data from configuration."""
        self._load_pricing_data()


class CostTracker:
    """Cost tracking and monitoring system."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.token_counter = TokenCounter()
        self.cost_estimator = CostEstimator(config_manager)
        self.alerts: Dict[str, CostAlert] = {}
        self.alert_callbacks: List[Callable[[CostAlert, Dict[str, Any]], None]] = []
        
        # Initialize database tables
        self._initialize_database()
        self._load_alerts()
        
        # Start background monitoring
        self._start_monitoring()
    
    def _initialize_database(self):
        """Initialize cost tracking database tables."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Usage records table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS llm_usage_records (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        provider_id TEXT NOT NULL,
                        model_id TEXT NOT NULL,
                        tool_id TEXT,
                        prompt_template_id TEXT,
                        input_tokens INTEGER DEFAULT 0,
                        output_tokens INTEGER DEFAULT 0,
                        estimated_cost REAL DEFAULT 0.0,
                        actual_cost REAL DEFAULT 0.0,
                        response_time_ms INTEGER DEFAULT 0,
                        success BOOLEAN DEFAULT TRUE,
                        error TEXT,
                        error_type TEXT,
                        quality_score REAL,
                        user TEXT DEFAULT 'system',
                        session_id TEXT
                    )
                """)
                
                # Cost alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cost_alerts (
                        alert_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        threshold_value REAL NOT NULL,
                        time_window_minutes INTEGER DEFAULT 60,
                        provider_id TEXT,
                        model_id TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        triggered_count INTEGER DEFAULT 0,
                        last_triggered TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Usage metrics aggregation table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS usage_metrics (
                        id TEXT PRIMARY KEY,
                        provider_id TEXT NOT NULL,
                        model_id TEXT NOT NULL,
                        time_period_start TEXT NOT NULL,
                        time_period_end TEXT NOT NULL,
                        total_requests INTEGER DEFAULT 0,
                        successful_requests INTEGER DEFAULT 0,
                        failed_requests INTEGER DEFAULT 0,
                        total_input_tokens INTEGER DEFAULT 0,
                        total_output_tokens INTEGER DEFAULT 0,
                        total_cost REAL DEFAULT 0.0,
                        average_response_time REAL DEFAULT 0.0,
                        average_quality_score REAL DEFAULT 0.0,
                        last_updated TEXT NOT NULL
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON llm_usage_records(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_provider_model ON llm_usage_records(provider_id, model_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_provider_model ON usage_metrics(provider_id, model_id)")
                
                conn.commit()
                self.logger.info("Cost tracking database tables initialized")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize cost tracking database: {e}")
    
    def _load_alerts(self):
        """Load cost alerts from database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM cost_alerts WHERE is_active = TRUE")
                
                for row in cursor.fetchall():
                    alert = CostAlert(
                        alert_id=row[0],
                        name=row[1],
                        alert_type=row[2],
                        threshold_value=row[3],
                        time_window_minutes=row[4],
                        provider_id=row[5],
                        model_id=row[6],
                        is_active=bool(row[7]),
                        triggered_count=row[8],
                        last_triggered=datetime.fromisoformat(row[9]) if row[9] else None,
                        created_at=datetime.fromisoformat(row[10])
                    )
                    self.alerts[alert.alert_id] = alert
                
                self.logger.info(f"Loaded {len(self.alerts)} cost alerts")
        
        except Exception as e:
            self.logger.error(f"Failed to load cost alerts: {e}")
    
    def _start_monitoring(self):
        """Start background monitoring thread."""
        def monitor_loop():
            while True:
                try:
                    self._check_alerts()
                    self.token_counter.cleanup_stale_sessions()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    self.logger.error(f"Monitoring loop error: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        self.logger.info("Started cost monitoring background thread")
    
    def record_usage(self, usage_record: LLMUsageRecord) -> bool:
        """Record LLM usage for cost tracking."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO llm_usage_records (
                        id, timestamp, provider_id, model_id, tool_id, prompt_template_id,
                        input_tokens, output_tokens, estimated_cost, actual_cost,
                        response_time_ms, success, error, error_type, quality_score,
                        user, session_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    usage_record.id,
                    usage_record.timestamp.isoformat(),
                    usage_record.provider_id,
                    usage_record.model_id,
                    usage_record.tool_id,
                    usage_record.prompt_template_id,
                    usage_record.input_tokens,
                    usage_record.output_tokens,
                    usage_record.estimated_cost,
                    usage_record.actual_cost,
                    usage_record.response_time_ms,
                    usage_record.success,
                    usage_record.error,
                    usage_record.error_type.value if usage_record.error_type else None,
                    usage_record.quality_score,
                    usage_record.user,
                    usage_record.session_id
                ))
                conn.commit()
            
            # Update real-time session if exists
            if usage_record.session_id:
                self.token_counter.update_session(
                    usage_record.session_id,
                    usage_record.input_tokens,
                    usage_record.output_tokens,
                    usage_record.actual_cost
                )
            
            self.logger.debug(f"Recorded usage: {usage_record.id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to record usage: {e}")
            return False
    
    def start_session(self, provider_id: str, model_id: str, session_id: str = None) -> str:
        """Start a cost tracking session."""
        if not session_id:
            session_id = generate_id()
        
        self.token_counter.start_session(session_id, provider_id, model_id)
        self.logger.info(f"Started cost tracking session: {session_id}")
        return session_id
    
    def end_session(self, session_id: str) -> Optional[RealTimeTokenCount]:
        """End a cost tracking session."""
        session = self.token_counter.end_session(session_id)
        if session:
            self.logger.info(f"Ended cost tracking session: {session_id}")
        return session
    
    def get_session_cost(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current cost for an active session."""
        session = self.token_counter.get_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session_id,
            "provider_id": session.provider_id,
            "model_id": session.model_id,
            "input_tokens": session.input_tokens,
            "output_tokens": session.output_tokens,
            "total_tokens": session.input_tokens + session.output_tokens,
            "estimated_cost": session.estimated_cost,
            "actual_cost": session.actual_cost,
            "duration_minutes": (datetime.now() - session.start_time).total_seconds() / 60
        }
    
    def create_alert(self, alert: CostAlert) -> bool:
        """Create a new cost alert."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO cost_alerts (
                        alert_id, name, alert_type, threshold_value, time_window_minutes,
                        provider_id, model_id, is_active, triggered_count, last_triggered, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.alert_id,
                    alert.name,
                    alert.alert_type,
                    alert.threshold_value,
                    alert.time_window_minutes,
                    alert.provider_id,
                    alert.model_id,
                    alert.is_active,
                    alert.triggered_count,
                    alert.last_triggered.isoformat() if alert.last_triggered else None,
                    alert.created_at.isoformat()
                ))
                conn.commit()
            
            self.alerts[alert.alert_id] = alert
            self.logger.info(f"Created cost alert: {alert.name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to create cost alert: {e}")
            return False
    
    def _check_alerts(self):
        """Check all active alerts for threshold violations."""
        for alert in self.alerts.values():
            if not alert.is_active:
                continue
            
            try:
                if alert.alert_type == "threshold":
                    self._check_threshold_alert(alert)
                elif alert.alert_type == "rate":
                    self._check_rate_alert(alert)
                elif alert.alert_type == "budget":
                    self._check_budget_alert(alert)
            
            except Exception as e:
                self.logger.error(f"Alert check failed for {alert.name}: {e}")
    
    def _check_threshold_alert(self, alert: CostAlert):
        """Check threshold-based alert."""
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=alert.time_window_minutes)
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT SUM(actual_cost) FROM llm_usage_records 
                WHERE timestamp >= ? AND timestamp <= ?
            """
            params = [start_time.isoformat(), end_time.isoformat()]
            
            if alert.provider_id:
                query += " AND provider_id = ?"
                params.append(alert.provider_id)
            
            if alert.model_id:
                query += " AND model_id = ?"
                params.append(alert.model_id)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            total_cost = result[0] if result[0] else 0.0
            
            if total_cost >= alert.threshold_value:
                self._trigger_alert(alert, {
                    "current_cost": total_cost,
                    "threshold": alert.threshold_value,
                    "time_window": alert.time_window_minutes
                })
    
    def _check_rate_alert(self, alert: CostAlert):
        """Check rate-based alert (cost per minute)."""
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=alert.time_window_minutes)
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT SUM(actual_cost) FROM llm_usage_records 
                WHERE timestamp >= ? AND timestamp <= ?
            """
            params = [start_time.isoformat(), end_time.isoformat()]
            
            if alert.provider_id:
                query += " AND provider_id = ?"
                params.append(alert.provider_id)
            
            if alert.model_id:
                query += " AND model_id = ?"
                params.append(alert.model_id)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            total_cost = result[0] if result[0] else 0.0
            
            rate = total_cost / alert.time_window_minutes if alert.time_window_minutes > 0 else 0.0
            
            if rate >= alert.threshold_value:
                self._trigger_alert(alert, {
                    "current_rate": rate,
                    "threshold_rate": alert.threshold_value,
                    "total_cost": total_cost,
                    "time_window": alert.time_window_minutes
                })
    
    def _check_budget_alert(self, alert: CostAlert):
        """Check budget-based alert (daily/weekly/monthly spending)."""
        # For simplicity, treating as daily budget
        end_time = datetime.now()
        start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT SUM(actual_cost) FROM llm_usage_records 
                WHERE timestamp >= ? AND timestamp <= ?
            """
            params = [start_time.isoformat(), end_time.isoformat()]
            
            if alert.provider_id:
                query += " AND provider_id = ?"
                params.append(alert.provider_id)
            
            if alert.model_id:
                query += " AND model_id = ?"
                params.append(alert.model_id)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            total_cost = result[0] if result[0] else 0.0
            
            if total_cost >= alert.threshold_value:
                self._trigger_alert(alert, {
                    "current_spending": total_cost,
                    "budget": alert.threshold_value,
                    "period": "daily"
                })
    
    def _trigger_alert(self, alert: CostAlert, context: Dict[str, Any]):
        """Trigger a cost alert."""
        alert.triggered_count += 1
        alert.last_triggered = datetime.now()
        
        # Update database
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE cost_alerts 
                    SET triggered_count = ?, last_triggered = ?
                    WHERE alert_id = ?
                """, (alert.triggered_count, alert.last_triggered.isoformat(), alert.alert_id))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to update alert trigger count: {e}")
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert, context)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")
        
        self.logger.warning(f"Cost alert triggered: {alert.name} - {context}")
    
    def add_alert_callback(self, callback: Callable[[CostAlert, Dict[str, Any]], None]):
        """Add callback for alert notifications."""
        self.alert_callbacks.append(callback)
    
    def generate_cost_report(self, start_time: datetime, end_time: datetime, 
                           report_type: str = "summary") -> CostReport:
        """Generate comprehensive cost report."""
        report = CostReport(
            report_type=report_type,
            time_period_start=start_time,
            time_period_end=end_time
        )
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Overall statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_requests,
                        SUM(actual_cost) as total_cost,
                        SUM(input_tokens + output_tokens) as total_tokens
                    FROM llm_usage_records 
                    WHERE timestamp >= ? AND timestamp <= ?
                """, (start_time.isoformat(), end_time.isoformat()))
                
                result = cursor.fetchone()
                if result:
                    report.total_requests = result[0] or 0
                    report.total_cost = result[1] or 0.0
                    report.total_tokens = result[2] or 0
                
                # Provider breakdown
                cursor.execute("""
                    SELECT 
                        provider_id,
                        COUNT(*) as requests,
                        SUM(actual_cost) as cost,
                        SUM(input_tokens + output_tokens) as tokens,
                        AVG(response_time_ms) as avg_response_time
                    FROM llm_usage_records 
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY provider_id
                """, (start_time.isoformat(), end_time.isoformat()))
                
                for row in cursor.fetchall():
                    report.provider_breakdown[row[0]] = {
                        "requests": row[1],
                        "cost": row[2] or 0.0,
                        "tokens": row[3] or 0,
                        "avg_response_time": row[4] or 0.0
                    }
                
                # Model breakdown
                cursor.execute("""
                    SELECT 
                        provider_id,
                        model_id,
                        COUNT(*) as requests,
                        SUM(actual_cost) as cost,
                        SUM(input_tokens + output_tokens) as tokens
                    FROM llm_usage_records 
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY provider_id, model_id
                """, (start_time.isoformat(), end_time.isoformat()))
                
                for row in cursor.fetchall():
                    key = f"{row[0]}:{row[1]}"
                    report.model_breakdown[key] = {
                        "provider_id": row[0],
                        "model_id": row[1],
                        "requests": row[2],
                        "cost": row[3] or 0.0,
                        "tokens": row[4] or 0
                    }
                
                # Hourly breakdown for detailed reports
                if report_type == "detailed":
                    cursor.execute("""
                        SELECT 
                            strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                            COUNT(*) as requests,
                            SUM(actual_cost) as cost,
                            SUM(input_tokens + output_tokens) as tokens
                        FROM llm_usage_records 
                        WHERE timestamp >= ? AND timestamp <= ?
                        GROUP BY strftime('%Y-%m-%d %H:00:00', timestamp)
                        ORDER BY hour
                    """, (start_time.isoformat(), end_time.isoformat()))
                    
                    for row in cursor.fetchall():
                        report.hourly_breakdown.append({
                            "hour": row[0],
                            "requests": row[1],
                            "cost": row[2] or 0.0,
                            "tokens": row[3] or 0
                        })
            
            self.logger.info(f"Generated {report_type} cost report: ${report.total_cost:.4f} total")
            return report
        
        except Exception as e:
            self.logger.error(f"Failed to generate cost report: {e}")
            return report
    
    def get_real_time_costs(self) -> Dict[str, Any]:
        """Get real-time cost information for all active sessions."""
        sessions = self.token_counter.get_all_sessions()
        
        total_cost = sum(session.actual_cost for session in sessions)
        total_tokens = sum(session.input_tokens + session.output_tokens for session in sessions)
        
        return {
            "active_sessions": len(sessions),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "sessions": [session.to_dict() for session in sessions]
        }