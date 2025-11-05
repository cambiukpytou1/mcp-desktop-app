"""
Advanced Prompt Management Database Schema
==========================================

Database schema and migration system for advanced prompt management features.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime
from .vector_database import VectorDatabaseManager


class PromptDatabaseManager:
    """Manages database schema for advanced prompt management."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.current_schema_version = 4  # Latest schema version
        
        # Initialize vector database manager
        data_dir = db_path.parent
        self.vector_db = VectorDatabaseManager(data_dir)
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def initialize_prompt_schema(self):
        """Initialize advanced prompt management schema."""
        try:
            with self.get_connection() as conn:
                self._create_prompt_tables(conn)
                self._create_prompt_indexes(conn)
            
            # Apply any pending migrations
            self.migrate_prompt_schema()
            
            # Initialize vector database
            if self.vector_db.is_available:
                self.vector_db.initialize()
                self.logger.info("Vector database initialized for semantic search")
            else:
                self.logger.warning("Vector database dependencies not available - semantic search disabled")
            
            self.logger.info("Advanced prompt database schema initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize prompt schema: {e}")
            raise
    
    def _create_prompt_tables(self, conn: sqlite3.Connection):
        """Create tables for advanced prompt management."""
        
        # Projects table for organizing prompts
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                settings TEXT DEFAULT '{}',  -- JSON string
                permissions TEXT DEFAULT '{}',  -- JSON string
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                created_by TEXT DEFAULT ''
            )
        """)
        
        # Main prompts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                folder_path TEXT DEFAULT '',
                project_id TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (project_id) REFERENCES prompt_projects(id) ON DELETE SET NULL
            )
        """)
        
        # Prompt metadata table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_metadata (
                prompt_id TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 1000,
                tags TEXT DEFAULT '[]',  -- JSON array
                custom_fields TEXT DEFAULT '{}',  -- JSON object
                author TEXT DEFAULT '',
                description TEXT DEFAULT '',
                intent_category TEXT DEFAULT 'custom',
                status TEXT DEFAULT 'draft',
                domain TEXT DEFAULT '',
                tone TEXT DEFAULT '',
                persona TEXT DEFAULT '',
                objective TEXT DEFAULT '',
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
            )
        """)
        
        # Version information table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_version_info (
                prompt_id TEXT PRIMARY KEY,
                current_version TEXT NOT NULL,
                total_versions INTEGER DEFAULT 1,
                last_modified_by TEXT DEFAULT '',
                last_modified_at DATETIME NOT NULL,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
            )
        """)
        
        # Prompt versions table for version control
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_versions (
                version_id TEXT PRIMARY KEY,
                prompt_id TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata_snapshot TEXT,  -- JSON string
                parent_version TEXT,
                branch_name TEXT DEFAULT 'main',
                branch_type TEXT DEFAULT 'main',
                commit_message TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                created_at DATETIME NOT NULL,
                created_by TEXT DEFAULT '',
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_version) REFERENCES prompt_versions(version_id) ON DELETE SET NULL
            )
        """)
        
        # Performance metrics for versions
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_performance_metrics (
                version_id TEXT PRIMARY KEY,
                average_score REAL DEFAULT 0.0,
                total_executions INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                average_tokens INTEGER DEFAULT 0,
                average_cost REAL DEFAULT 0.0,
                average_response_time REAL DEFAULT 0.0,
                last_updated DATETIME NOT NULL,
                FOREIGN KEY (version_id) REFERENCES prompt_versions(version_id) ON DELETE CASCADE
            )
        """)
        
        # Prompt branches for version control
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_branches (
                branch_id TEXT PRIMARY KEY,
                prompt_id TEXT NOT NULL,
                name TEXT NOT NULL,
                base_version TEXT NOT NULL,
                head_version TEXT NOT NULL,
                branch_type TEXT DEFAULT 'feature',
                is_active BOOLEAN DEFAULT TRUE,
                created_by TEXT DEFAULT '',
                created_at DATETIME NOT NULL,
                merged_at DATETIME,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
                FOREIGN KEY (base_version) REFERENCES prompt_versions(version_id) ON DELETE CASCADE,
                FOREIGN KEY (head_version) REFERENCES prompt_versions(version_id) ON DELETE CASCADE
            )
        """)
        
        # Evaluation runs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_runs (
                run_id TEXT PRIMARY KEY,
                prompt_version_id TEXT NOT NULL,
                test_dataset TEXT DEFAULT '',
                models_tested TEXT DEFAULT '[]',  -- JSON array
                scoring_rubric TEXT,  -- JSON object
                cost_summary TEXT,  -- JSON object
                status TEXT DEFAULT 'pending',
                created_at DATETIME NOT NULL,
                completed_at DATETIME,
                FOREIGN KEY (prompt_version_id) REFERENCES prompt_versions(version_id) ON DELETE CASCADE
            )
        """)
        
        # Evaluation results table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_results (
                result_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                prompt_version_id TEXT NOT NULL,
                model TEXT NOT NULL,
                input_variables TEXT DEFAULT '{}',  -- JSON object
                output TEXT DEFAULT '',
                scores TEXT DEFAULT '{}',  -- JSON object
                token_usage TEXT,  -- JSON object
                execution_time REAL DEFAULT 0.0,
                cost REAL DEFAULT 0.0,
                error TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
                FOREIGN KEY (prompt_version_id) REFERENCES prompt_versions(version_id) ON DELETE CASCADE
            )
        """)
        
        # Prompt embeddings for semantic search
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_embeddings (
                prompt_id TEXT PRIMARY KEY,
                embedding_model TEXT NOT NULL,
                embedding_vector BLOB NOT NULL,
                content_hash TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
            )
        """)
        
        # Prompt usage analytics
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_usage_analytics (
                id TEXT PRIMARY KEY,
                prompt_id TEXT NOT NULL,
                version_id TEXT,
                execution_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                average_score REAL DEFAULT 0.0,
                last_used DATETIME,
                period_start DATETIME NOT NULL,
                period_end DATETIME NOT NULL,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
                FOREIGN KEY (version_id) REFERENCES prompt_versions(version_id) ON DELETE SET NULL
            )
        """)
        
        # Prompt tags for organization
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_tags (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                color TEXT DEFAULT '#007bff',
                created_at DATETIME NOT NULL
            )
        """)
        
        # Many-to-many relationship between prompts and tags
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_tag_associations (
                prompt_id TEXT NOT NULL,
                tag_id TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                PRIMARY KEY (prompt_id, tag_id),
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES prompt_tags(id) ON DELETE CASCADE
            )
        """)
        
        # Prompt templates for variable substitution
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_templates (
                id TEXT PRIMARY KEY,
                prompt_id TEXT NOT NULL,
                template_content TEXT NOT NULL,
                variables TEXT DEFAULT '[]',  -- JSON array of variable definitions
                test_data TEXT DEFAULT '{}',  -- JSON object with test variable values
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
            )
        """)
        
        # Prompt execution history
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_executions (
                id TEXT PRIMARY KEY,
                prompt_id TEXT NOT NULL,
                version_id TEXT,
                template_id TEXT,
                model TEXT NOT NULL,
                input_variables TEXT DEFAULT '{}',  -- JSON object
                output TEXT DEFAULT '',
                success BOOLEAN DEFAULT FALSE,
                error TEXT,
                tokens_used INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                execution_time REAL DEFAULT 0.0,
                quality_score REAL,
                executed_by TEXT DEFAULT '',
                executed_at DATETIME NOT NULL,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
                FOREIGN KEY (version_id) REFERENCES prompt_versions(version_id) ON DELETE SET NULL,
                FOREIGN KEY (template_id) REFERENCES prompt_templates(id) ON DELETE SET NULL
            )
        """)
        
        conn.commit()
    
    def _create_prompt_indexes(self, conn: sqlite3.Connection):
        """Create indexes for advanced prompt management tables."""
        
        indexes = [
            # Projects indexes
            "CREATE INDEX IF NOT EXISTS idx_prompt_projects_name ON prompt_projects(name)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_projects_created ON prompt_projects(created_at)",
            
            # Prompts indexes
            "CREATE INDEX IF NOT EXISTS idx_prompts_name ON prompts(name)",
            "CREATE INDEX IF NOT EXISTS idx_prompts_project ON prompts(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_prompts_folder ON prompts(folder_path)",
            "CREATE INDEX IF NOT EXISTS idx_prompts_created ON prompts(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_prompts_updated ON prompts(updated_at)",
            
            # Metadata indexes
            "CREATE INDEX IF NOT EXISTS idx_prompt_metadata_model ON prompt_metadata(model)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_metadata_category ON prompt_metadata(intent_category)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_metadata_status ON prompt_metadata(status)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_metadata_author ON prompt_metadata(author)",
            
            # Version indexes
            "CREATE INDEX IF NOT EXISTS idx_prompt_versions_prompt ON prompt_versions(prompt_id)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_versions_branch ON prompt_versions(branch_name)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_versions_parent ON prompt_versions(parent_version)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_versions_created ON prompt_versions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_versions_status ON prompt_versions(status)",
            
            # Branch indexes
            "CREATE INDEX IF NOT EXISTS idx_prompt_branches_prompt ON prompt_branches(prompt_id)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_branches_name ON prompt_branches(name)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_branches_active ON prompt_branches(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_branches_type ON prompt_branches(branch_type)",
            
            # Evaluation indexes
            "CREATE INDEX IF NOT EXISTS idx_evaluation_runs_version ON evaluation_runs(prompt_version_id)",
            "CREATE INDEX IF NOT EXISTS idx_evaluation_runs_status ON evaluation_runs(status)",
            "CREATE INDEX IF NOT EXISTS idx_evaluation_runs_created ON evaluation_runs(created_at)",
            
            "CREATE INDEX IF NOT EXISTS idx_evaluation_results_run ON evaluation_results(run_id)",
            "CREATE INDEX IF NOT EXISTS idx_evaluation_results_version ON evaluation_results(prompt_version_id)",
            "CREATE INDEX IF NOT EXISTS idx_evaluation_results_model ON evaluation_results(model)",
            "CREATE INDEX IF NOT EXISTS idx_evaluation_results_created ON evaluation_results(created_at)",
            
            # Embeddings indexes
            "CREATE INDEX IF NOT EXISTS idx_prompt_embeddings_model ON prompt_embeddings(embedding_model)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_embeddings_hash ON prompt_embeddings(content_hash)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_embeddings_updated ON prompt_embeddings(updated_at)",
            
            # Analytics indexes
            "CREATE INDEX IF NOT EXISTS idx_prompt_analytics_prompt ON prompt_usage_analytics(prompt_id)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_analytics_version ON prompt_usage_analytics(version_id)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_analytics_period ON prompt_usage_analytics(period_start, period_end)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_analytics_last_used ON prompt_usage_analytics(last_used)",
            
            # Tag indexes
            "CREATE INDEX IF NOT EXISTS idx_prompt_tags_name ON prompt_tags(name)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_tag_assoc_prompt ON prompt_tag_associations(prompt_id)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_tag_assoc_tag ON prompt_tag_associations(tag_id)",
            
            # Template indexes
            "CREATE INDEX IF NOT EXISTS idx_prompt_templates_prompt ON prompt_templates(prompt_id)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_templates_created ON prompt_templates(created_at)",
            
            # Execution indexes
            "CREATE INDEX IF NOT EXISTS idx_prompt_executions_prompt ON prompt_executions(prompt_id)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_executions_version ON prompt_executions(version_id)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_executions_model ON prompt_executions(model)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_executions_success ON prompt_executions(success)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_executions_executed ON prompt_executions(executed_at)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_executions_user ON prompt_executions(executed_by)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()
    
    def get_prompt_schema_version(self) -> int:
        """Get current prompt schema version."""
        try:
            with self.get_connection() as conn:
                # Create schema_version table if it doesn't exist
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS prompt_schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """)
                
                cursor = conn.execute("SELECT MAX(version) FROM prompt_schema_version")
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0
        except Exception as e:
            self.logger.error(f"Failed to get prompt schema version: {e}")
            return 0
    
    def apply_prompt_migration(self, version: int, description: str, migration_sql: str):
        """Apply a prompt database migration."""
        try:
            current_version = self.get_prompt_schema_version()
            if current_version >= version:
                self.logger.info(f"Prompt migration {version} already applied")
                return
            
            with self.get_connection() as conn:
                # Execute migration SQL
                for statement in migration_sql.split(';'):
                    statement = statement.strip()
                    if statement:
                        conn.execute(statement)
                
                # Record migration
                conn.execute("""
                    INSERT INTO prompt_schema_version (version, description)
                    VALUES (?, ?)
                """, (version, description))
                
                conn.commit()
                self.logger.info(f"Applied prompt migration {version}: {description}")
                
        except Exception as e:
            self.logger.error(f"Failed to apply prompt migration {version}: {e}")
            raise
    
    def migrate_prompt_schema(self):
        """Apply all pending prompt schema migrations."""
        migrations = [
            (1, "Initial advanced prompt management schema", """
                -- Tables are created in _create_prompt_tables method
                SELECT 1
            """),
            (2, "Add prompt embeddings support", """
                -- Embeddings table already included in main schema
                SELECT 1
            """),
            (3, "Add prompt templates and variables", """
                -- Template support already included in main schema
                SELECT 1
            """),
            (4, "Add comprehensive analytics and performance tracking", """
                -- Analytics tables already included in main schema
                SELECT 1
            """)
        ]
        
        for version, description, sql in migrations:
            self.apply_prompt_migration(version, description, sql)
    
    def create_default_project(self) -> str:
        """Create a default project for prompts."""
        try:
            project_id = "default-project"
            with self.get_connection() as conn:
                # Check if default project exists
                cursor = conn.execute(
                    "SELECT id FROM prompt_projects WHERE id = ?",
                    (project_id,)
                )
                if cursor.fetchone():
                    return project_id
                
                # Create default project
                conn.execute("""
                    INSERT INTO prompt_projects 
                    (id, name, description, created_at, updated_at, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    project_id,
                    "Default Project",
                    "Default project for organizing prompts",
                    datetime.now(),
                    datetime.now(),
                    "system"
                ))
                
                conn.commit()
                self.logger.info("Created default prompt project")
                return project_id
                
        except Exception as e:
            self.logger.error(f"Failed to create default project: {e}")
            raise
    
    def create_default_tags(self):
        """Create default tags for prompt organization."""
        default_tags = [
            ("summarization", "Prompts for text summarization", "#28a745"),
            ("translation", "Prompts for language translation", "#17a2b8"),
            ("extraction", "Prompts for information extraction", "#ffc107"),
            ("reasoning", "Prompts for logical reasoning", "#6f42c1"),
            ("creative", "Prompts for creative writing", "#e83e8c"),
            ("analysis", "Prompts for data analysis", "#fd7e14"),
            ("classification", "Prompts for text classification", "#20c997"),
            ("generation", "Prompts for content generation", "#6610f2"),
            ("conversation", "Prompts for conversational AI", "#0dcaf0")
        ]
        
        try:
            with self.get_connection() as conn:
                for tag_name, description, color in default_tags:
                    # Check if tag exists
                    cursor = conn.execute(
                        "SELECT id FROM prompt_tags WHERE name = ?",
                        (tag_name,)
                    )
                    if not cursor.fetchone():
                        # Create tag
                        tag_id = f"tag-{tag_name}"
                        conn.execute("""
                            INSERT INTO prompt_tags (id, name, description, color, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (tag_id, tag_name, description, color, datetime.now()))
                
                conn.commit()
                self.logger.info("Created default prompt tags")
                
        except Exception as e:
            self.logger.error(f"Failed to create default tags: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the prompt database."""
        try:
            with self.get_connection() as conn:
                stats = {}
                
                # Count records in each table
                tables = [
                    'prompt_projects', 'prompts', 'prompt_metadata', 'prompt_versions',
                    'prompt_branches', 'evaluation_runs', 'evaluation_results',
                    'prompt_embeddings', 'prompt_tags', 'prompt_templates',
                    'prompt_executions'
                ]
                
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # Get schema version
                stats['schema_version'] = self.get_prompt_schema_version()
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def add_prompt_embedding(self, prompt_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Add prompt embedding to vector database."""
        if not self.vector_db.is_available:
            return False
        
        try:
            # Add to vector database
            success = self.vector_db.add_prompt_embedding(prompt_id, content, metadata)
            
            if success:
                # Update embeddings table in SQL database
                with self.get_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO prompt_embeddings 
                        (prompt_id, embedding_model, embedding_vector, content_hash, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        prompt_id,
                        self.vector_db.embedding_model_name,
                        b"",  # Placeholder - actual embedding stored in ChromaDB
                        self._get_content_hash(content),
                        datetime.now(),
                        datetime.now()
                    ))
                    conn.commit()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to add prompt embedding: {e}")
            return False
    
    def remove_prompt_embedding(self, prompt_id: str) -> bool:
        """Remove prompt embedding from vector database."""
        if not self.vector_db.is_available:
            return False
        
        try:
            # Remove from vector database
            success = self.vector_db.remove_prompt_embedding(prompt_id)
            
            if success:
                # Remove from SQL database
                with self.get_connection() as conn:
                    conn.execute("DELETE FROM prompt_embeddings WHERE prompt_id = ?", (prompt_id,))
                    conn.commit()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to remove prompt embedding: {e}")
            return False
    
    def search_similar_prompts(self, query: str, limit: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar prompts using semantic similarity."""
        if not self.vector_db.is_available:
            return []
        
        return self.vector_db.search_similar_prompts(query, limit, filters)
    
    def cluster_prompts(self, prompt_ids: List[str] = None, n_clusters: int = 5) -> Dict[str, Any]:
        """Cluster prompts based on semantic similarity."""
        if not self.vector_db.is_available:
            return {"clusters": [], "error": "Vector database not available"}
        
        return self.vector_db.cluster_prompts(prompt_ids, n_clusters)
    
    def find_duplicate_prompts(self, similarity_threshold: float = 0.95) -> List[Dict[str, Any]]:
        """Find potentially duplicate prompts based on high similarity."""
        if not self.vector_db.is_available:
            return []
        
        return self.vector_db.find_duplicate_prompts(similarity_threshold)
    
    def get_vector_database_stats(self) -> Dict[str, Any]:
        """Get vector database statistics."""
        return self.vector_db.get_collection_stats()
    
    def rebuild_embeddings(self) -> int:
        """Rebuild all prompt embeddings from database."""
        if not self.vector_db.is_available:
            return 0
        
        try:
            # Get all prompts from database
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT p.id, p.content, pm.intent_category, pm.tags, pm.author
                    FROM prompts p
                    LEFT JOIN prompt_metadata pm ON p.id = pm.prompt_id
                """)
                prompts = cursor.fetchall()
            
            # Prepare batch data
            batch_data = []
            for prompt in prompts:
                batch_data.append({
                    "id": prompt["id"],
                    "content": prompt["content"],
                    "metadata": {
                        "intent_category": prompt["intent_category"] or "custom",
                        "tags": prompt["tags"] or "[]",
                        "author": prompt["author"] or ""
                    }
                })
            
            # Add embeddings in batch
            count = self.vector_db.batch_add_embeddings(batch_data)
            
            # Update SQL database records
            if count > 0:
                with self.get_connection() as conn:
                    for prompt_data in batch_data[:count]:
                        conn.execute("""
                            INSERT OR REPLACE INTO prompt_embeddings 
                            (prompt_id, embedding_model, embedding_vector, content_hash, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            prompt_data["id"],
                            self.vector_db.embedding_model_name,
                            b"",  # Placeholder
                            self._get_content_hash(prompt_data["content"]),
                            datetime.now(),
                            datetime.now()
                        ))
                    conn.commit()
            
            self.logger.info(f"Rebuilt {count} prompt embeddings")
            return count
            
        except Exception as e:
            self.logger.error(f"Failed to rebuild embeddings: {e}")
            return 0
    
    def _get_content_hash(self, content: str) -> str:
        """Generate hash for content."""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()