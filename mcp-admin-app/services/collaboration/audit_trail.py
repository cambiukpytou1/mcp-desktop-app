"""
Audit Trail Service for MCP Admin Application
============================================

Service for comprehensive audit logging with tamper-evident records and compliance reporting.
"""

import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import logging
import json
import csv
import io

from models.collaboration import AuditEvent, AuditEventType
from data.database import DatabaseManager


class AuditTrailService:
    """Service for audit trail management and compliance reporting."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the audit trail service."""
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self._init_database()
        self._previous_checksum = self._get_last_checksum()
    
    def _init_database(self):
        """Initialize database tables for audit trail."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Audit events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT DEFAULT '{}',
                    ip_address TEXT,
                    user_agent TEXT,
                    session_id TEXT,
                    old_values TEXT,
                    new_values TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT NOT NULL
                )
            """)
            
            # Audit trail integrity table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_integrity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_start TIMESTAMP NOT NULL,
                    period_end TIMESTAMP NOT NULL,
                    event_count INTEGER NOT NULL,
                    chain_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_user ON audit_events(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_resource ON audit_events(resource_type, resource_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type)")
            
            conn.commit()
    
    def _calculate_checksum(self, event: AuditEvent, previous_checksum: str = "") -> str:
        """Calculate tamper-evident checksum for an audit event."""
        try:
            # Create a string representation of the event for hashing
            event_data = {
                "id": event.id,
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "action": event.action,
                "details": event.details,
                "timestamp": event.timestamp.isoformat(),
                "previous_checksum": previous_checksum
            }
            
            # Convert to JSON string for consistent hashing
            event_json = json.dumps(event_data, sort_keys=True)
            
            # Calculate SHA-256 hash
            return hashlib.sha256(event_json.encode('utf-8')).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating checksum: {e}")
            return ""
    
    def _get_last_checksum(self) -> str:
        """Get the checksum of the last audit event."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT checksum FROM audit_events 
                    ORDER BY timestamp DESC, id DESC 
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                return row[0] if row else ""
                
        except Exception as e:
            self.logger.error(f"Error getting last checksum: {e}")
            return ""
    
    def log_event(self, event_type: AuditEventType, user_id: str, resource_type: str,
                  resource_id: str, action: str, details: Dict[str, Any] = None,
                  ip_address: str = None, user_agent: str = None, session_id: str = None,
                  old_values: Dict[str, Any] = None, new_values: Dict[str, Any] = None) -> AuditEvent:
        """Log an audit event with tamper-evident checksum."""
        try:
            # Create audit event
            event = AuditEvent(
                event_type=event_type,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                old_values=old_values,
                new_values=new_values
            )
            
            # Calculate checksum
            event.checksum = self._calculate_checksum(event, self._previous_checksum)
            
            # Save to database
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_events (
                        id, event_type, user_id, resource_type, resource_id, action,
                        details, ip_address, user_agent, session_id, old_values,
                        new_values, timestamp, checksum
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.id, event.event_type.value, event.user_id,
                    event.resource_type, event.resource_id, event.action,
                    json.dumps(event.details), event.ip_address, event.user_agent,
                    event.session_id,
                    json.dumps(event.old_values) if event.old_values else None,
                    json.dumps(event.new_values) if event.new_values else None,
                    event.timestamp.isoformat(), event.checksum
                ))
                conn.commit()
            
            # Update previous checksum for next event
            self._previous_checksum = event.checksum
            
            self.logger.debug(f"Logged audit event: {event_type.value} by {user_id}")
            return event
            
        except Exception as e:
            self.logger.error(f"Error logging audit event: {e}")
            raise
    
    def get_events(self, start_date: datetime = None, end_date: datetime = None,
                   user_id: str = None, resource_type: str = None, resource_id: str = None,
                   event_type: AuditEventType = None, limit: int = 1000) -> List[AuditEvent]:
        """Get audit events with optional filters."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, event_type, user_id, resource_type, resource_id, action,
                           details, ip_address, user_agent, session_id, old_values,
                           new_values, timestamp, checksum
                    FROM audit_events
                    WHERE 1=1
                """
                params = []
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date.isoformat())
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                if resource_type:
                    query += " AND resource_type = ?"
                    params.append(resource_type)
                
                if resource_id:
                    query += " AND resource_id = ?"
                    params.append(resource_id)
                
                if event_type:
                    query += " AND event_type = ?"
                    params.append(event_type.value)
                
                query += " ORDER BY timestamp DESC, id DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                
                events = []
                for row in cursor.fetchall():
                    event = AuditEvent(
                        id=row[0],
                        event_type=AuditEventType(row[1]),
                        user_id=row[2],
                        resource_type=row[3],
                        resource_id=row[4],
                        action=row[5],
                        details=json.loads(row[6]) if row[6] else {},
                        ip_address=row[7],
                        user_agent=row[8],
                        session_id=row[9],
                        old_values=json.loads(row[10]) if row[10] else None,
                        new_values=json.loads(row[11]) if row[11] else None,
                        timestamp=datetime.fromisoformat(row[12]),
                        checksum=row[13]
                    )
                    events.append(event)
                
                return events
                
        except Exception as e:
            self.logger.error(f"Error getting audit events: {e}")
            return []
    
    def verify_integrity(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Verify the integrity of the audit trail."""
        try:
            events = self.get_events(start_date=start_date, end_date=end_date, limit=None)
            
            if not events:
                return {
                    "valid": True,
                    "total_events": 0,
                    "verified_events": 0,
                    "invalid_events": [],
                    "message": "No events to verify"
                }
            
            # Sort events by timestamp for verification
            events.sort(key=lambda x: (x.timestamp, x.id))
            
            invalid_events = []
            previous_checksum = ""
            
            # Get the checksum before the first event in our range
            if events and start_date:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT checksum FROM audit_events 
                        WHERE timestamp < ? 
                        ORDER BY timestamp DESC, id DESC 
                        LIMIT 1
                    """, (start_date.isoformat(),))
                    
                    row = cursor.fetchone()
                    if row:
                        previous_checksum = row[0]
            
            for event in events:
                # Calculate expected checksum
                expected_checksum = self._calculate_checksum(event, previous_checksum)
                
                # Compare with stored checksum
                if event.checksum != expected_checksum:
                    invalid_events.append({
                        "event_id": event.id,
                        "timestamp": event.timestamp.isoformat(),
                        "expected_checksum": expected_checksum,
                        "actual_checksum": event.checksum,
                        "reason": "Checksum mismatch"
                    })
                
                previous_checksum = event.checksum
            
            result = {
                "valid": len(invalid_events) == 0,
                "total_events": len(events),
                "verified_events": len(events) - len(invalid_events),
                "invalid_events": invalid_events,
                "verification_date": datetime.now().isoformat()
            }
            
            if invalid_events:
                result["message"] = f"Found {len(invalid_events)} invalid events"
                self.logger.warning(f"Audit trail integrity check failed: {len(invalid_events)} invalid events")
            else:
                result["message"] = "Audit trail integrity verified"
                self.logger.info(f"Audit trail integrity verified: {len(events)} events")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error verifying audit trail integrity: {e}")
            return {
                "valid": False,
                "error": str(e),
                "verification_date": datetime.now().isoformat()
            }
    
    def export_audit_trail(self, format_type: str = "csv", start_date: datetime = None,
                          end_date: datetime = None, user_id: str = None,
                          resource_type: str = None) -> Union[str, bytes]:
        """Export audit trail for compliance reporting."""
        try:
            events = self.get_events(
                start_date=start_date,
                end_date=end_date,
                user_id=user_id,
                resource_type=resource_type,
                limit=None
            )
            
            if format_type.lower() == "csv":
                return self._export_csv(events)
            elif format_type.lower() == "json":
                return self._export_json(events)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            self.logger.error(f"Error exporting audit trail: {e}")
            raise
    
    def _export_csv(self, events: List[AuditEvent]) -> str:
        """Export events to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Event ID", "Event Type", "User ID", "Resource Type", "Resource ID",
            "Action", "Timestamp", "IP Address", "User Agent", "Session ID",
            "Details", "Old Values", "New Values", "Checksum"
        ])
        
        # Write events
        for event in events:
            writer.writerow([
                event.id,
                event.event_type.value,
                event.user_id,
                event.resource_type,
                event.resource_id,
                event.action,
                event.timestamp.isoformat(),
                event.ip_address or "",
                event.user_agent or "",
                event.session_id or "",
                json.dumps(event.details) if event.details else "",
                json.dumps(event.old_values) if event.old_values else "",
                json.dumps(event.new_values) if event.new_values else "",
                event.checksum
            ])
        
        return output.getvalue()
    
    def _export_json(self, events: List[AuditEvent]) -> str:
        """Export events to JSON format."""
        export_data = {
            "export_metadata": {
                "export_date": datetime.now().isoformat(),
                "total_events": len(events),
                "format_version": "1.0"
            },
            "events": [event.to_dict() for event in events]
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    def get_audit_summary(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get audit trail summary statistics."""
        try:
            events = self.get_events(start_date=start_date, end_date=end_date, limit=None)
            
            if not events:
                return {
                    "total_events": 0,
                    "date_range": {
                        "start": start_date.isoformat() if start_date else None,
                        "end": end_date.isoformat() if end_date else None
                    },
                    "event_types": {},
                    "users": {},
                    "resources": {}
                }
            
            # Calculate statistics
            event_types = {}
            users = {}
            resources = {}
            
            for event in events:
                # Event type counts
                event_type = event.event_type.value
                event_types[event_type] = event_types.get(event_type, 0) + 1
                
                # User activity counts
                users[event.user_id] = users.get(event.user_id, 0) + 1
                
                # Resource activity counts
                resource_key = f"{event.resource_type}:{event.resource_id}"
                resources[resource_key] = resources.get(resource_key, 0) + 1
            
            # Get date range from actual events
            events.sort(key=lambda x: x.timestamp)
            actual_start = events[0].timestamp
            actual_end = events[-1].timestamp
            
            return {
                "total_events": len(events),
                "date_range": {
                    "start": actual_start.isoformat(),
                    "end": actual_end.isoformat(),
                    "requested_start": start_date.isoformat() if start_date else None,
                    "requested_end": end_date.isoformat() if end_date else None
                },
                "event_types": dict(sorted(event_types.items(), key=lambda x: x[1], reverse=True)),
                "top_users": dict(sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]),
                "top_resources": dict(sorted(resources.items(), key=lambda x: x[1], reverse=True)[:10]),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating audit summary: {e}")
            return {"error": str(e)}
    
    def create_integrity_checkpoint(self) -> Dict[str, Any]:
        """Create an integrity checkpoint for the audit trail."""
        try:
            # Get current period
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)  # Daily checkpoints
            
            # Get events in period
            events = self.get_events(start_date=start_time, end_date=end_time, limit=None)
            
            if not events:
                return {
                    "checkpoint_created": False,
                    "reason": "No events in period",
                    "period": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat()
                    }
                }
            
            # Calculate chain hash
            event_checksums = [event.checksum for event in events]
            chain_data = {
                "period_start": start_time.isoformat(),
                "period_end": end_time.isoformat(),
                "event_count": len(events),
                "event_checksums": event_checksums
            }
            
            chain_json = json.dumps(chain_data, sort_keys=True)
            chain_hash = hashlib.sha256(chain_json.encode('utf-8')).hexdigest()
            
            # Save checkpoint
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_integrity (
                        period_start, period_end, event_count, chain_hash
                    ) VALUES (?, ?, ?, ?)
                """, (
                    start_time.isoformat(),
                    end_time.isoformat(),
                    len(events),
                    chain_hash
                ))
                conn.commit()
            
            self.logger.info(f"Created audit integrity checkpoint: {len(events)} events")
            
            return {
                "checkpoint_created": True,
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "event_count": len(events),
                "chain_hash": chain_hash,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error creating integrity checkpoint: {e}")
            return {
                "checkpoint_created": False,
                "error": str(e)
            }
    
    def search_events(self, query: str, search_fields: List[str] = None) -> List[AuditEvent]:
        """Search audit events by text query."""
        try:
            if not search_fields:
                search_fields = ["action", "details", "resource_id"]
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build search query
                search_conditions = []
                params = []
                
                for field in search_fields:
                    if field in ["action", "resource_id", "resource_type"]:
                        search_conditions.append(f"{field} LIKE ?")
                        params.append(f"%{query}%")
                    elif field == "details":
                        search_conditions.append("details LIKE ?")
                        params.append(f"%{query}%")
                
                if not search_conditions:
                    return []
                
                query_sql = f"""
                    SELECT id, event_type, user_id, resource_type, resource_id, action,
                           details, ip_address, user_agent, session_id, old_values,
                           new_values, timestamp, checksum
                    FROM audit_events
                    WHERE ({' OR '.join(search_conditions)})
                    ORDER BY timestamp DESC
                    LIMIT 100
                """
                
                cursor.execute(query_sql, params)
                
                events = []
                for row in cursor.fetchall():
                    event = AuditEvent(
                        id=row[0],
                        event_type=AuditEventType(row[1]),
                        user_id=row[2],
                        resource_type=row[3],
                        resource_id=row[4],
                        action=row[5],
                        details=json.loads(row[6]) if row[6] else {},
                        ip_address=row[7],
                        user_agent=row[8],
                        session_id=row[9],
                        old_values=json.loads(row[10]) if row[10] else None,
                        new_values=json.loads(row[11]) if row[11] else None,
                        timestamp=datetime.fromisoformat(row[12]),
                        checksum=row[13]
                    )
                    events.append(event)
                
                return events
                
        except Exception as e:
            self.logger.error(f"Error searching audit events: {e}")
            return []