"""
Database Management for MCP Admin Application
=============================================

SQLite database initialization and connection management.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from .prompt_database import PromptDatabaseManager


class DatabaseManager:
    """Manages SQLite database connections and schema."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._connection: Optional[sqlite3.Connection] = None
        self.prompt_db = PromptDatabaseManager(db_path)
    
    def initialize(self):
        """Initialize database schema and apply migrations."""
        try:
            with self.get_connection() as conn:
                self._create_tables(conn)
                self._create_indexes(conn)
            
            # Apply any pending migrations
            self.migrate_to_latest()
            
            # Initialize advanced prompt management schema
            self.prompt_db.initialize_prompt_schema()
            self.prompt_db.create_default_project()
            self.prompt_db.create_default_tags()
            
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create database tables."""
        
        # Security Events Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                event_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                resource TEXT,
                details TEXT,
                risk_level TEXT NOT NULL,
                source_ip TEXT,
                user_agent TEXT
            )
        """)
        
        # Audit Events Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                checksum TEXT NOT NULL,
                session_id TEXT
            )
        """)
        
        # Monitoring Metrics Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS monitoring_metrics (
                id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                server_id TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT
            )
        """)
        
        # Enhanced LLM Provider Configurations Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider_type TEXT NOT NULL,
                endpoint_url TEXT,
                is_local BOOLEAN DEFAULT FALSE,
                status TEXT NOT NULL DEFAULT 'inactive',
                settings TEXT,  -- JSON string
                description TEXT,
                priority INTEGER DEFAULT 1,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        
        # LLM Model Configurations Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_models (
                id TEXT PRIMARY KEY,
                provider_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                display_name TEXT NOT NULL,
                max_tokens INTEGER NOT NULL,
                input_cost_per_token REAL NOT NULL,
                output_cost_per_token REAL NOT NULL,
                supports_streaming BOOLEAN DEFAULT FALSE,
                context_window INTEGER DEFAULT 4096,
                tokenizer_type TEXT DEFAULT 'default',
                FOREIGN KEY (provider_id) REFERENCES llm_providers (id) ON DELETE CASCADE
            )
        """)
        
        # Encrypted Credentials Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS encrypted_credentials (
                provider_id TEXT NOT NULL,
                credential_type TEXT NOT NULL,
                encrypted_value BLOB NOT NULL,
                encryption_method TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                expires_at DATETIME,
                last_used DATETIME,
                PRIMARY KEY (provider_id, credential_type),
                FOREIGN KEY (provider_id) REFERENCES llm_providers (id) ON DELETE CASCADE
            )
        """)
        
        # Test Executions Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_executions (
                id TEXT PRIMARY KEY,
                prompt_template_id TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                test_type TEXT NOT NULL DEFAULT 'single',
                status TEXT NOT NULL DEFAULT 'pending',
                parameters TEXT,  -- JSON string
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                estimated_cost REAL DEFAULT 0.0,
                actual_cost REAL DEFAULT 0.0,
                response_time REAL DEFAULT 0.0,
                success BOOLEAN DEFAULT FALSE,
                response_content TEXT,
                error_message TEXT,
                quality_score REAL,
                executed_at DATETIME NOT NULL,
                executed_by TEXT NOT NULL,
                metadata TEXT,  -- JSON string
                FOREIGN KEY (provider_id) REFERENCES llm_providers (id) ON DELETE CASCADE
            )
        """)
        
        # Usage Metrics Table (aggregated analytics)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_metrics (
                id TEXT PRIMARY KEY,
                provider_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                total_input_tokens INTEGER DEFAULT 0,
                total_output_tokens INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                average_response_time REAL DEFAULT 0.0,
                average_quality_score REAL DEFAULT 0.0,
                time_period_start DATETIME NOT NULL,
                time_period_end DATETIME NOT NULL,
                last_updated DATETIME NOT NULL,
                FOREIGN KEY (provider_id) REFERENCES llm_providers (id) ON DELETE CASCADE
            )
        """)
        
        # Enhanced LLM Usage Records Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_usage_records (
                id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
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
                user_id TEXT NOT NULL,
                session_id TEXT,
                FOREIGN KEY (provider_id) REFERENCES llm_providers (id) ON DELETE CASCADE
            )
        """)
        
        # Security Audit Events Table (enhanced for LLM operations)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS security_audit_events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                provider_id TEXT,
                user_id TEXT NOT NULL,
                description TEXT NOT NULL,
                risk_level TEXT NOT NULL DEFAULT 'low',
                metadata TEXT,  -- JSON string
                timestamp DATETIME NOT NULL,
                FOREIGN KEY (provider_id) REFERENCES llm_providers (id) ON DELETE SET NULL
            )
        """)
        
        # LLM Usage Statistics Table (legacy - kept for backward compatibility)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_usage_stats (
                id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                provider_id TEXT NOT NULL,
                tool_id TEXT,
                tokens_used INTEGER,
                response_time_ms INTEGER,
                success BOOLEAN,
                error TEXT,
                user_id TEXT
            )
        """)
        
        # Alerts Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT NOT NULL,
                source TEXT NOT NULL,
                acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_by TEXT,
                acknowledged_at DATETIME
            )
        """)
        
        # Trend Analysis Results Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trend_analysis_results (
                id TEXT PRIMARY KEY,
                prompt_id TEXT NOT NULL,
                analysis_data TEXT NOT NULL,  -- JSON string
                created_at DATETIME NOT NULL,
                FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
            )
        """)
        
        # Model Drift Alerts Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS model_drift_alerts (
                alert_id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                drift_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                current_value REAL NOT NULL,
                baseline_value REAL NOT NULL,
                drift_percentage REAL NOT NULL,
                description TEXT NOT NULL,
                recommended_actions TEXT,  -- JSON string
                acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_by TEXT,
                acknowledged_at DATETIME,
                created_at DATETIME NOT NULL
            )
        """)
        
        # Performance Baselines Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_baselines (
                id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                prompt_id TEXT,
                metric_type TEXT NOT NULL,
                baseline_value REAL NOT NULL,
                sample_size INTEGER NOT NULL,
                confidence_interval REAL,
                calculation_period_start DATETIME NOT NULL,
                calculation_period_end DATETIME NOT NULL,
                created_at DATETIME NOT NULL,
                expires_at DATETIME
            )
        """)
        
        # Historical Performance Snapshots Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_snapshots (
                id TEXT PRIMARY KEY,
                prompt_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                snapshot_date DATE NOT NULL,
                avg_score REAL DEFAULT 0.0,
                avg_cost REAL DEFAULT 0.0,
                avg_response_time REAL DEFAULT 0.0,
                success_rate REAL DEFAULT 0.0,
                execution_count INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                metadata TEXT,  -- JSON string
                created_at DATETIME NOT NULL,
                FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
    
    def _create_indexes(self, conn: sqlite3.Connection):
        """Create database indexes for performance."""
        
        indexes = [
            # Security events indexes
            "CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_events(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_security_user ON security_events(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_security_event_type ON security_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_security_risk_level ON security_events(risk_level)",
            
            # Audit events indexes
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_events(resource_type, resource_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_events(action)",
            
            # Monitoring metrics indexes
            "CREATE INDEX IF NOT EXISTS idx_monitoring_timestamp ON monitoring_metrics(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_monitoring_server ON monitoring_metrics(server_id)",
            "CREATE INDEX IF NOT EXISTS idx_monitoring_metric_type ON monitoring_metrics(metric_type)",
            
            # LLM providers indexes
            "CREATE INDEX IF NOT EXISTS idx_llm_providers_type ON llm_providers(provider_type)",
            "CREATE INDEX IF NOT EXISTS idx_llm_providers_status ON llm_providers(status)",
            "CREATE INDEX IF NOT EXISTS idx_llm_providers_created ON llm_providers(created_at)",
            
            # LLM models indexes
            "CREATE INDEX IF NOT EXISTS idx_llm_models_provider ON llm_models(provider_id)",
            "CREATE INDEX IF NOT EXISTS idx_llm_models_model_id ON llm_models(model_id)",
            
            # Encrypted credentials indexes
            "CREATE INDEX IF NOT EXISTS idx_credentials_provider ON encrypted_credentials(provider_id)",
            "CREATE INDEX IF NOT EXISTS idx_credentials_type ON encrypted_credentials(credential_type)",
            "CREATE INDEX IF NOT EXISTS idx_credentials_expires ON encrypted_credentials(expires_at)",
            
            # Test executions indexes
            "CREATE INDEX IF NOT EXISTS idx_test_executions_provider ON test_executions(provider_id)",
            "CREATE INDEX IF NOT EXISTS idx_test_executions_template ON test_executions(prompt_template_id)",
            "CREATE INDEX IF NOT EXISTS idx_test_executions_status ON test_executions(status)",
            "CREATE INDEX IF NOT EXISTS idx_test_executions_executed ON test_executions(executed_at)",
            "CREATE INDEX IF NOT EXISTS idx_test_executions_type ON test_executions(test_type)",
            
            # Usage metrics indexes
            "CREATE INDEX IF NOT EXISTS idx_usage_metrics_provider ON usage_metrics(provider_id)",
            "CREATE INDEX IF NOT EXISTS idx_usage_metrics_model ON usage_metrics(model_id)",
            "CREATE INDEX IF NOT EXISTS idx_usage_metrics_period ON usage_metrics(time_period_start, time_period_end)",
            
            # LLM usage records indexes
            "CREATE INDEX IF NOT EXISTS idx_llm_usage_records_timestamp ON llm_usage_records(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_llm_usage_records_provider ON llm_usage_records(provider_id)",
            "CREATE INDEX IF NOT EXISTS idx_llm_usage_records_model ON llm_usage_records(model_id)",
            "CREATE INDEX IF NOT EXISTS idx_llm_usage_records_user ON llm_usage_records(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_llm_usage_records_template ON llm_usage_records(prompt_template_id)",
            "CREATE INDEX IF NOT EXISTS idx_llm_usage_records_success ON llm_usage_records(success)",
            
            # Security audit events indexes
            "CREATE INDEX IF NOT EXISTS idx_security_audit_timestamp ON security_audit_events(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_security_audit_event_type ON security_audit_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_security_audit_provider ON security_audit_events(provider_id)",
            "CREATE INDEX IF NOT EXISTS idx_security_audit_user ON security_audit_events(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_security_audit_risk ON security_audit_events(risk_level)",
            
            # Legacy LLM usage stats indexes (backward compatibility)
            "CREATE INDEX IF NOT EXISTS idx_llm_timestamp ON llm_usage_stats(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_llm_provider ON llm_usage_stats(provider_id)",
            "CREATE INDEX IF NOT EXISTS idx_llm_tool ON llm_usage_stats(tool_id)",
            "CREATE INDEX IF NOT EXISTS idx_llm_user ON llm_usage_stats(user_id)",
            
            # Alerts indexes
            "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged)",
            
            # Trend analysis results indexes
            "CREATE INDEX IF NOT EXISTS idx_trend_analysis_prompt ON trend_analysis_results(prompt_id)",
            "CREATE INDEX IF NOT EXISTS idx_trend_analysis_created ON trend_analysis_results(created_at)",
            
            # Model drift alerts indexes
            "CREATE INDEX IF NOT EXISTS idx_drift_alerts_model ON model_drift_alerts(model_id)",
            "CREATE INDEX IF NOT EXISTS idx_drift_alerts_type ON model_drift_alerts(drift_type)",
            "CREATE INDEX IF NOT EXISTS idx_drift_alerts_severity ON model_drift_alerts(severity)",
            "CREATE INDEX IF NOT EXISTS idx_drift_alerts_created ON model_drift_alerts(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_drift_alerts_acknowledged ON model_drift_alerts(acknowledged)",
            
            # Performance baselines indexes
            "CREATE INDEX IF NOT EXISTS idx_baselines_model ON performance_baselines(model_id)",
            "CREATE INDEX IF NOT EXISTS idx_baselines_prompt ON performance_baselines(prompt_id)",
            "CREATE INDEX IF NOT EXISTS idx_baselines_metric ON performance_baselines(metric_type)",
            "CREATE INDEX IF NOT EXISTS idx_baselines_expires ON performance_baselines(expires_at)",
            
            # Performance snapshots indexes
            "CREATE INDEX IF NOT EXISTS idx_snapshots_prompt ON performance_snapshots(prompt_id)",
            "CREATE INDEX IF NOT EXISTS idx_snapshots_model ON performance_snapshots(model_id)",
            "CREATE INDEX IF NOT EXISTS idx_snapshots_date ON performance_snapshots(snapshot_date)",
            "CREATE INDEX IF NOT EXISTS idx_snapshots_created ON performance_snapshots(created_at)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()
    
    def vacuum(self):
        """Optimize database by running VACUUM."""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
            self.logger.info("Database vacuum completed")
        except Exception as e:
            self.logger.error(f"Failed to vacuum database: {e}")
    
    def get_table_info(self, table_name: str) -> list:
        """Get table schema information."""
        with self.get_connection() as conn:
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            return cursor.fetchall()
    
    def get_database_size(self) -> int:
        """Get database file size in bytes."""
        return self.db_path.stat().st_size if self.db_path.exists() else 0
    
    def get_schema_version(self) -> int:
        """Get current database schema version."""
        try:
            with self.get_connection() as conn:
                # Create schema_version table if it doesn't exist
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """)
                
                cursor = conn.execute("SELECT MAX(version) FROM schema_version")
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0
        except Exception as e:
            self.logger.error(f"Failed to get schema version: {e}")
            return 0
    
    def apply_migration(self, version: int, description: str, migration_sql: str):
        """Apply a database migration."""
        try:
            current_version = self.get_schema_version()
            if current_version >= version:
                self.logger.info(f"Migration {version} already applied")
                return
            
            with self.get_connection() as conn:
                # Execute migration SQL
                for statement in migration_sql.split(';'):
                    statement = statement.strip()
                    if statement:
                        conn.execute(statement)
                
                # Record migration
                conn.execute("""
                    INSERT INTO schema_version (version, description)
                    VALUES (?, ?)
                """, (version, description))
                
                conn.commit()
                self.logger.info(f"Applied migration {version}: {description}")
                
        except Exception as e:
            self.logger.error(f"Failed to apply migration {version}: {e}")
            raise
    
    def migrate_to_latest(self):
        """Apply all pending migrations to bring database to latest schema."""
        migrations = [
            (1, "Initial LLM integration schema", """
                -- This migration adds the enhanced LLM tables
                -- Tables are created in _create_tables method, so this is a placeholder
                SELECT 1
            """),
            (2, "Add encryption support for credentials", """
                -- Enhanced credential encryption support
                -- Already included in main schema
                SELECT 1
            """),
            (3, "Add comprehensive analytics tables", """
                -- Analytics and usage tracking enhancements
                -- Already included in main schema
                SELECT 1
            """),
            (4, "Add trend analysis and monitoring tables", """
                -- Trend analysis and monitoring tables already included in main schema
                SELECT 1
            """)
        ]
        
        for version, description, sql in migrations:
            self.apply_migration(version, description, sql)
    
    def backup_database(self, backup_path: Path):
        """Create a backup of the database."""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Database backed up to {backup_path}")
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}")
            raise
    
    def restore_database(self, backup_path: Path):
        """Restore database from backup."""
        try:
            import shutil
            if backup_path.exists():
                shutil.copy2(backup_path, self.db_path)
                self.logger.info(f"Database restored from {backup_path}")
            else:
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
        except Exception as e:
            self.logger.error(f"Failed to restore database: {e}")
            raise