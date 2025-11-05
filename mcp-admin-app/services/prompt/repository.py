"""
Prompt Repository Service
========================

Handles prompt storage, retrieval, and organization with CRUD operations,
hierarchical folder organization, and custom metadata support.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

from models.prompt_advanced.models import (
    Prompt, PromptMetadata, PromptProject, PromptStatus, PromptCategory,
    ValidationError
)
from models.base import generate_id


class PromptRepository:
    """Manages prompt storage and retrieval operations with advanced features."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Initialize prompt database if available
        if hasattr(db_manager, 'prompt_db'):
            self.prompt_db = db_manager.prompt_db
        else:
            self.prompt_db = None
            self.logger.warning("Prompt database not available")
        
        self.logger.info("Prompt repository initialized with advanced features")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        if self.prompt_db:
            with self.prompt_db.get_connection() as conn:
                yield conn
        else:
            # Fallback to main database
            with self.db_manager.get_connection() as conn:
                yield conn
    
    def create_prompt(self, prompt_data: Dict[str, Any]) -> str:
        """Create a new prompt with validation and metadata."""
        try:
            # Create prompt object from data
            prompt = Prompt(
                id=prompt_data.get('id', generate_id()),
                name=prompt_data.get('name', ''),
                content=prompt_data.get('content', ''),
                folder_path=prompt_data.get('folder_path', ''),
                project_id=prompt_data.get('project_id'),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Create metadata if provided
            if 'metadata' in prompt_data:
                metadata_dict = prompt_data['metadata']
                prompt.metadata = PromptMetadata(
                    model=metadata_dict.get('model', 'gpt-3.5-turbo'),
                    temperature=metadata_dict.get('temperature', 0.7),
                    max_tokens=metadata_dict.get('max_tokens', 1000),
                    tags=metadata_dict.get('tags', []),
                    custom_fields=metadata_dict.get('custom_fields', {}),
                    author=metadata_dict.get('author', ''),
                    description=metadata_dict.get('description', ''),
                    intent_category=PromptCategory(metadata_dict.get('intent_category', 'custom')),
                    status=PromptStatus(metadata_dict.get('status', 'draft')),
                    domain=metadata_dict.get('domain', ''),
                    tone=metadata_dict.get('tone', ''),
                    persona=metadata_dict.get('persona', ''),
                    objective=metadata_dict.get('objective', '')
                )
            
            # Validate prompt
            prompt.validate()
            
            # Store in database
            with self.get_connection() as conn:
                # Insert prompt
                conn.execute("""
                    INSERT INTO prompts (id, name, content, folder_path, project_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    prompt.id, prompt.name, prompt.content, prompt.folder_path,
                    prompt.project_id, prompt.created_at, prompt.updated_at
                ))
                
                # Insert metadata if available
                if prompt.metadata:
                    conn.execute("""
                        INSERT INTO prompt_metadata (
                            prompt_id, model, temperature, max_tokens, tags, custom_fields,
                            author, description, intent_category, status, domain, tone, persona, objective
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        prompt.id, prompt.metadata.model, prompt.metadata.temperature,
                        prompt.metadata.max_tokens, json.dumps(prompt.metadata.tags),
                        json.dumps(prompt.metadata.custom_fields), prompt.metadata.author,
                        prompt.metadata.description, prompt.metadata.intent_category.value,
                        prompt.metadata.status.value, prompt.metadata.domain,
                        prompt.metadata.tone, prompt.metadata.persona, prompt.metadata.objective
                    ))
                
                # Insert version info
                conn.execute("""
                    INSERT INTO prompt_version_info (
                        prompt_id, current_version, total_versions, last_modified_by, last_modified_at
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    prompt.id, prompt.version_info.current_version, prompt.version_info.total_versions,
                    prompt.version_info.last_modified_by, prompt.version_info.last_modified_at
                ))
                
                conn.commit()
            
            # Add to vector database for semantic search
            if self.prompt_db and prompt.metadata:
                metadata_for_vector = {
                    'intent_category': prompt.metadata.intent_category.value,
                    'tags': json.dumps(prompt.metadata.tags),
                    'author': prompt.metadata.author
                }
                self.prompt_db.add_prompt_embedding(prompt.id, prompt.content, metadata_for_vector)
            
            self.logger.info(f"Created prompt: {prompt.id} - {prompt.name}")
            return prompt.id
            
        except ValidationError as e:
            self.logger.error(f"Validation error creating prompt: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to create prompt: {e}")
            raise
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a prompt by ID with full metadata."""
        try:
            with self.get_connection() as conn:
                # Get prompt with metadata
                cursor = conn.execute("""
                    SELECT 
                        p.id, p.name, p.content, p.folder_path, p.project_id,
                        p.created_at, p.updated_at,
                        pm.model, pm.temperature, pm.max_tokens, pm.tags, pm.custom_fields,
                        pm.author, pm.description, pm.intent_category, pm.status,
                        pm.domain, pm.tone, pm.persona, pm.objective,
                        pvi.current_version, pvi.total_versions, pvi.last_modified_by, pvi.last_modified_at
                    FROM prompts p
                    LEFT JOIN prompt_metadata pm ON p.id = pm.prompt_id
                    LEFT JOIN prompt_version_info pvi ON p.id = pvi.prompt_id
                    WHERE p.id = ?
                """, (prompt_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Convert to dictionary
                prompt_dict = {
                    'id': row['id'],
                    'name': row['name'],
                    'content': row['content'],
                    'folder_path': row['folder_path'],
                    'project_id': row['project_id'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                
                # Add metadata if available
                if row['model']:
                    prompt_dict['metadata'] = {
                        'model': row['model'],
                        'temperature': row['temperature'],
                        'max_tokens': row['max_tokens'],
                        'tags': json.loads(row['tags']) if row['tags'] else [],
                        'custom_fields': json.loads(row['custom_fields']) if row['custom_fields'] else {},
                        'author': row['author'],
                        'description': row['description'],
                        'intent_category': row['intent_category'],
                        'status': row['status'],
                        'domain': row['domain'],
                        'tone': row['tone'],
                        'persona': row['persona'],
                        'objective': row['objective']
                    }
                
                # Add version info if available
                if row['current_version']:
                    prompt_dict['version_info'] = {
                        'current_version': row['current_version'],
                        'total_versions': row['total_versions'],
                        'last_modified_by': row['last_modified_by'],
                        'last_modified_at': row['last_modified_at']
                    }
                
                return prompt_dict
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve prompt {prompt_id}: {e}")
            return None
    
    def update_prompt(self, prompt_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing prompt."""
        try:
            with self.get_connection() as conn:
                # Update main prompt fields
                prompt_fields = []
                prompt_values = []
                
                if 'name' in updates:
                    prompt_fields.append('name = ?')
                    prompt_values.append(updates['name'])
                
                if 'content' in updates:
                    prompt_fields.append('content = ?')
                    prompt_values.append(updates['content'])
                
                if 'folder_path' in updates:
                    prompt_fields.append('folder_path = ?')
                    prompt_values.append(updates['folder_path'])
                
                if 'project_id' in updates:
                    prompt_fields.append('project_id = ?')
                    prompt_values.append(updates['project_id'])
                
                if prompt_fields:
                    prompt_fields.append('updated_at = ?')
                    prompt_values.append(datetime.now())
                    prompt_values.append(prompt_id)
                    
                    conn.execute(f"""
                        UPDATE prompts SET {', '.join(prompt_fields)}
                        WHERE id = ?
                    """, prompt_values)
                
                # Update metadata if provided
                if 'metadata' in updates:
                    metadata = updates['metadata']
                    conn.execute("""
                        UPDATE prompt_metadata SET
                            model = ?, temperature = ?, max_tokens = ?, tags = ?, custom_fields = ?,
                            author = ?, description = ?, intent_category = ?, status = ?,
                            domain = ?, tone = ?, persona = ?, objective = ?
                        WHERE prompt_id = ?
                    """, (
                        metadata.get('model'), metadata.get('temperature'), metadata.get('max_tokens'),
                        json.dumps(metadata.get('tags', [])), json.dumps(metadata.get('custom_fields', {})),
                        metadata.get('author'), metadata.get('description'), metadata.get('intent_category'),
                        metadata.get('status'), metadata.get('domain'), metadata.get('tone'),
                        metadata.get('persona'), metadata.get('objective'), prompt_id
                    ))
                
                conn.commit()
            
            # Update vector database if content changed
            if 'content' in updates and self.prompt_db:
                prompt_data = self.get_prompt(prompt_id)
                if prompt_data:
                    metadata_for_vector = {}
                    if 'metadata' in prompt_data:
                        metadata_for_vector = {
                            'intent_category': prompt_data['metadata'].get('intent_category', 'custom'),
                            'tags': json.dumps(prompt_data['metadata'].get('tags', [])),
                            'author': prompt_data['metadata'].get('author', '')
                        }
                    self.prompt_db.add_prompt_embedding(prompt_id, updates['content'], metadata_for_vector)
            
            self.logger.info(f"Updated prompt: {prompt_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update prompt {prompt_id}: {e}")
            return False
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt and all associated data."""
        try:
            with self.get_connection() as conn:
                # Delete from main table (cascades to related tables)
                conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
                conn.commit()
            
            # Remove from vector database
            if self.prompt_db:
                self.prompt_db.remove_prompt_embedding(prompt_id)
            
            self.logger.info(f"Deleted prompt: {prompt_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete prompt {prompt_id}: {e}")
            return False
    
    def list_prompts(self, folder_path: str = None, project_id: str = None, 
                    limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List prompts with optional filtering."""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT 
                        p.id, p.name, p.content, p.folder_path, p.project_id,
                        p.created_at, p.updated_at,
                        pm.model, pm.temperature, pm.tags, pm.author, pm.description,
                        pm.intent_category, pm.status
                    FROM prompts p
                    LEFT JOIN prompt_metadata pm ON p.id = pm.prompt_id
                """
                
                conditions = []
                params = []
                
                if folder_path is not None:
                    conditions.append("p.folder_path = ?")
                    params.append(folder_path)
                
                if project_id is not None:
                    conditions.append("p.project_id = ?")
                    params.append(project_id)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY p.updated_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                prompts = []
                for row in rows:
                    prompt_dict = {
                        'id': row['id'],
                        'name': row['name'],
                        'content': row['content'][:200] + '...' if len(row['content']) > 200 else row['content'],
                        'folder_path': row['folder_path'],
                        'project_id': row['project_id'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                    
                    if row['model']:
                        prompt_dict['metadata'] = {
                            'model': row['model'],
                            'temperature': row['temperature'],
                            'tags': json.loads(row['tags']) if row['tags'] else [],
                            'author': row['author'],
                            'description': row['description'],
                            'intent_category': row['intent_category'],
                            'status': row['status']
                        }
                    
                    prompts.append(prompt_dict)
                
                return prompts
                
        except Exception as e:
            self.logger.error(f"Failed to list prompts: {e}")
            return []
    
    def get_folder_structure(self, project_id: str = None) -> Dict[str, Any]:
        """Get hierarchical folder structure for prompts."""
        try:
            with self.get_connection() as conn:
                query = "SELECT DISTINCT folder_path FROM prompts"
                params = []
                
                if project_id:
                    query += " WHERE project_id = ?"
                    params.append(project_id)
                
                cursor = conn.execute(query, params)
                folder_paths = [row['folder_path'] for row in cursor.fetchall()]
                
                # Build hierarchical structure
                structure = {'folders': {}, 'prompts': []}
                
                for path in folder_paths:
                    if not path:
                        continue
                    
                    parts = path.split('/')
                    current = structure['folders']
                    
                    for part in parts:
                        if part not in current:
                            current[part] = {'folders': {}, 'prompts': []}
                        current = current[part]['folders']
                
                return structure
                
        except Exception as e:
            self.logger.error(f"Failed to get folder structure: {e}")
            return {'folders': {}, 'prompts': []}
    
    def search_prompts(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search prompts using full-text search with optional filters."""
        try:
            with self.get_connection() as conn:
                search_query = """
                    SELECT 
                        p.id, p.name, p.content, p.folder_path, p.project_id,
                        p.created_at, p.updated_at,
                        pm.model, pm.tags, pm.author, pm.description,
                        pm.intent_category, pm.status
                    FROM prompts p
                    LEFT JOIN prompt_metadata pm ON p.id = pm.prompt_id
                    WHERE (p.name LIKE ? OR p.content LIKE ? OR pm.description LIKE ?)
                """
                
                search_term = f"%{query}%"
                params = [search_term, search_term, search_term]
                
                # Add filters
                if filters:
                    if 'intent_category' in filters:
                        search_query += " AND pm.intent_category = ?"
                        params.append(filters['intent_category'])
                    
                    if 'status' in filters:
                        search_query += " AND pm.status = ?"
                        params.append(filters['status'])
                    
                    if 'author' in filters:
                        search_query += " AND pm.author = ?"
                        params.append(filters['author'])
                    
                    if 'project_id' in filters:
                        search_query += " AND p.project_id = ?"
                        params.append(filters['project_id'])
                    
                    if 'folder_path' in filters:
                        search_query += " AND p.folder_path LIKE ?"
                        params.append(f"{filters['folder_path']}%")
                
                search_query += " ORDER BY p.updated_at DESC LIMIT 50"
                
                cursor = conn.execute(search_query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    result = {
                        'id': row['id'],
                        'name': row['name'],
                        'content': row['content'][:200] + '...' if len(row['content']) > 200 else row['content'],
                        'folder_path': row['folder_path'],
                        'project_id': row['project_id'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'relevance_score': 1.0  # Placeholder for text search relevance
                    }
                    
                    if row['model']:
                        result['metadata'] = {
                            'model': row['model'],
                            'tags': json.loads(row['tags']) if row['tags'] else [],
                            'author': row['author'],
                            'description': row['description'],
                            'intent_category': row['intent_category'],
                            'status': row['status']
                        }
                    
                    results.append(result)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to search prompts: {e}")
            return []
    
    def get_prompts_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict[str, Any]]:
        """Get prompts that match specified tags."""
        try:
            with self.get_connection() as conn:
                if match_all:
                    # All tags must match
                    placeholders = ','.join(['?' for _ in tags])
                    query = f"""
                        SELECT p.id, p.name, p.content, p.folder_path, p.project_id,
                               pm.tags, pm.author, pm.intent_category, pm.status
                        FROM prompts p
                        JOIN prompt_metadata pm ON p.id = pm.prompt_id
                        WHERE p.id IN (
                            SELECT prompt_id FROM prompt_metadata
                            WHERE json_extract(tags, '$') LIKE '%' || ? || '%'
                            GROUP BY prompt_id
                            HAVING COUNT(*) = {len(tags)}
                        )
                    """
                    params = tags
                else:
                    # Any tag matches
                    conditions = []
                    params = []
                    for tag in tags:
                        conditions.append("json_extract(pm.tags, '$') LIKE ?")
                        params.append(f'%"{tag}"%')
                    
                    query = f"""
                        SELECT DISTINCT p.id, p.name, p.content, p.folder_path, p.project_id,
                               pm.tags, pm.author, pm.intent_category, pm.status
                        FROM prompts p
                        JOIN prompt_metadata pm ON p.id = pm.prompt_id
                        WHERE {' OR '.join(conditions)}
                    """
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    result = {
                        'id': row['id'],
                        'name': row['name'],
                        'content': row['content'][:200] + '...' if len(row['content']) > 200 else row['content'],
                        'folder_path': row['folder_path'],
                        'project_id': row['project_id'],
                        'metadata': {
                            'tags': json.loads(row['tags']) if row['tags'] else [],
                            'author': row['author'],
                            'intent_category': row['intent_category'],
                            'status': row['status']
                        }
                    }
                    results.append(result)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to get prompts by tags: {e}")
            return []    

    # Project Management Methods
    
    def create_project(self, project_data: Dict[str, Any]) -> str:
        """Create a new project for organizing prompts."""
        try:
            # Create project object
            project = PromptProject(
                id=project_data.get('id', generate_id()),
                name=project_data.get('name', ''),
                description=project_data.get('description', ''),
                settings=project_data.get('settings', {}),
                permissions=project_data.get('permissions', {}),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by=project_data.get('created_by', '')
            )
            
            # Validate project
            project.validate()
            
            # Store in database
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO prompt_projects (
                        id, name, description, settings, permissions, 
                        created_at, updated_at, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project.id, project.name, project.description,
                    json.dumps(project.settings), json.dumps(project.permissions),
                    project.created_at, project.updated_at, project.created_by
                ))
                conn.commit()
            
            self.logger.info(f"Created project: {project.id} - {project.name}")
            return project.id
            
        except ValidationError as e:
            self.logger.error(f"Validation error creating project: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to create project: {e}")
            raise
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a project by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, name, description, settings, permissions,
                           created_at, updated_at, created_by
                    FROM prompt_projects
                    WHERE id = ?
                """, (project_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Get associated prompts count
                cursor = conn.execute(
                    "SELECT COUNT(*) as prompt_count FROM prompts WHERE project_id = ?",
                    (project_id,)
                )
                prompt_count = cursor.fetchone()['prompt_count']
                
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'settings': json.loads(row['settings']) if row['settings'] else {},
                    'permissions': json.loads(row['permissions']) if row['permissions'] else {},
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'created_by': row['created_by'],
                    'prompt_count': prompt_count
                }
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve project {project_id}: {e}")
            return None
    
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing project."""
        try:
            with self.get_connection() as conn:
                fields = []
                values = []
                
                if 'name' in updates:
                    fields.append('name = ?')
                    values.append(updates['name'])
                
                if 'description' in updates:
                    fields.append('description = ?')
                    values.append(updates['description'])
                
                if 'settings' in updates:
                    fields.append('settings = ?')
                    values.append(json.dumps(updates['settings']))
                
                if 'permissions' in updates:
                    fields.append('permissions = ?')
                    values.append(json.dumps(updates['permissions']))
                
                if fields:
                    fields.append('updated_at = ?')
                    values.append(datetime.now())
                    values.append(project_id)
                    
                    conn.execute(f"""
                        UPDATE prompt_projects SET {', '.join(fields)}
                        WHERE id = ?
                    """, values)
                    conn.commit()
            
            self.logger.info(f"Updated project: {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update project {project_id}: {e}")
            return False
    
    def delete_project(self, project_id: str, move_prompts_to: str = None) -> bool:
        """Delete a project, optionally moving prompts to another project."""
        try:
            with self.get_connection() as conn:
                # Move prompts if specified
                if move_prompts_to:
                    conn.execute("""
                        UPDATE prompts SET project_id = ? WHERE project_id = ?
                    """, (move_prompts_to, project_id))
                else:
                    # Set prompts to no project
                    conn.execute("""
                        UPDATE prompts SET project_id = NULL WHERE project_id = ?
                    """, (project_id,))
                
                # Delete project
                conn.execute("DELETE FROM prompt_projects WHERE id = ?", (project_id,))
                conn.commit()
            
            self.logger.info(f"Deleted project: {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete project {project_id}: {e}")
            return False
    
    def list_projects(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all projects with prompt counts."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT pp.id, pp.name, pp.description, pp.created_at, pp.updated_at,
                           pp.created_by, COUNT(p.id) as prompt_count
                    FROM prompt_projects pp
                    LEFT JOIN prompts p ON pp.id = p.project_id
                    GROUP BY pp.id, pp.name, pp.description, pp.created_at, pp.updated_at, pp.created_by
                    ORDER BY pp.updated_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                projects = []
                for row in cursor.fetchall():
                    projects.append({
                        'id': row['id'],
                        'name': row['name'],
                        'description': row['description'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'created_by': row['created_by'],
                        'prompt_count': row['prompt_count']
                    })
                
                return projects
                
        except Exception as e:
            self.logger.error(f"Failed to list projects: {e}")
            return []
    
    def add_prompt_to_project(self, prompt_id: str, project_id: str) -> bool:
        """Associate a prompt with a project."""
        try:
            with self.get_connection() as conn:
                # Verify project exists
                cursor = conn.execute("SELECT id FROM prompt_projects WHERE id = ?", (project_id,))
                if not cursor.fetchone():
                    raise ValueError(f"Project {project_id} does not exist")
                
                # Update prompt
                cursor = conn.execute("""
                    UPDATE prompts SET project_id = ?, updated_at = ?
                    WHERE id = ?
                """, (project_id, datetime.now(), prompt_id))
                
                if cursor.rowcount == 0:
                    raise ValueError(f"Prompt {prompt_id} does not exist")
                
                conn.commit()
            
            self.logger.info(f"Added prompt {prompt_id} to project {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add prompt to project: {e}")
            return False
    
    def remove_prompt_from_project(self, prompt_id: str) -> bool:
        """Remove a prompt from its current project."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE prompts SET project_id = NULL, updated_at = ?
                    WHERE id = ?
                """, (datetime.now(), prompt_id))
                
                if cursor.rowcount == 0:
                    raise ValueError(f"Prompt {prompt_id} does not exist")
                
                conn.commit()
            
            self.logger.info(f"Removed prompt {prompt_id} from project")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove prompt from project: {e}")
            return False
    
    def get_project_prompts(self, project_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all prompts in a specific project."""
        return self.list_prompts(project_id=project_id, limit=limit, offset=offset)
    
    def get_project_permissions(self, project_id: str) -> Dict[str, List[str]]:
        """Get project permissions."""
        try:
            project = self.get_project(project_id)
            if project:
                return project.get('permissions', {})
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get project permissions: {e}")
            return {}
    
    def set_project_permissions(self, project_id: str, permissions: Dict[str, List[str]]) -> bool:
        """Set project permissions."""
        try:
            return self.update_project(project_id, {'permissions': permissions})
        except Exception as e:
            self.logger.error(f"Failed to set project permissions: {e}")
            return False
    
    def check_project_permission(self, project_id: str, user: str, permission: str) -> bool:
        """Check if user has specific permission for project."""
        try:
            permissions = self.get_project_permissions(project_id)
            
            # Check if user has the specific permission
            if permission in permissions:
                return user in permissions[permission]
            
            # Check if user is in 'admin' role (has all permissions)
            if 'admin' in permissions:
                return user in permissions['admin']
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check project permission: {e}")
            return False
    
    def get_project_settings(self, project_id: str) -> Dict[str, Any]:
        """Get project settings."""
        try:
            project = self.get_project(project_id)
            if project:
                return project.get('settings', {})
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get project settings: {e}")
            return {}
    
    def update_project_settings(self, project_id: str, settings: Dict[str, Any]) -> bool:
        """Update project settings."""
        try:
            return self.update_project(project_id, {'settings': settings})
        except Exception as e:
            self.logger.error(f"Failed to update project settings: {e}")
            return False    
    
# Advanced Search Methods
    
    def semantic_search(self, query: str, limit: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search prompts using semantic similarity via vector embeddings."""
        if not self.prompt_db or not self.prompt_db.vector_db.is_available:
            self.logger.warning("Semantic search not available - falling back to text search")
            return self.search_prompts(query, filters)
        
        try:
            # Use vector database for semantic search
            similar_prompts = self.prompt_db.search_similar_prompts(query, limit, filters)
            
            # Enhance results with full prompt data
            enhanced_results = []
            for result in similar_prompts:
                prompt_data = self.get_prompt(result['prompt_id'])
                if prompt_data:
                    prompt_data['similarity_score'] = result['similarity_score']
                    prompt_data['search_type'] = 'semantic'
                    enhanced_results.append(prompt_data)
            
            return enhanced_results
            
        except Exception as e:
            self.logger.error(f"Semantic search failed: {e}")
            # Fallback to text search
            return self.search_prompts(query, filters)
    
    def advanced_search(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Advanced search with multiple criteria and search types."""
        try:
            query = search_params.get('query', '')
            search_type = search_params.get('type', 'text')  # 'text', 'semantic', 'hybrid'
            filters = search_params.get('filters', {})
            limit = search_params.get('limit', 50)
            
            results = []
            
            if search_type == 'semantic':
                results = self.semantic_search(query, limit, filters)
            elif search_type == 'hybrid':
                # Combine text and semantic search
                text_results = self.search_prompts(query, filters)
                semantic_results = self.semantic_search(query, limit // 2, filters)
                
                # Merge and deduplicate results
                seen_ids = set()
                for result in text_results[:limit // 2]:
                    result['search_type'] = 'text'
                    results.append(result)
                    seen_ids.add(result['id'])
                
                for result in semantic_results:
                    if result['id'] not in seen_ids:
                        results.append(result)
                        seen_ids.add(result['id'])
            else:
                # Default text search
                results = self.search_prompts(query, filters)
                for result in results:
                    result['search_type'] = 'text'
            
            # Apply additional filtering
            if 'date_range' in search_params:
                date_range = search_params['date_range']
                if 'start' in date_range or 'end' in date_range:
                    results = self._filter_by_date_range(results, date_range)
            
            if 'score_threshold' in search_params:
                threshold = search_params['score_threshold']
                results = [r for r in results if r.get('similarity_score', 1.0) >= threshold]
            
            # Sort results
            sort_by = search_params.get('sort_by', 'relevance')
            results = self._sort_search_results(results, sort_by)
            
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Advanced search failed: {e}")
            return []
    
    def filter_prompts(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter prompts by various criteria."""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT 
                        p.id, p.name, p.content, p.folder_path, p.project_id,
                        p.created_at, p.updated_at,
                        pm.model, pm.temperature, pm.tags, pm.author, pm.description,
                        pm.intent_category, pm.status, pm.domain, pm.tone, pm.persona
                    FROM prompts p
                    LEFT JOIN prompt_metadata pm ON p.id = pm.prompt_id
                    WHERE 1=1
                """
                
                params = []
                
                # Apply filters
                if 'intent_category' in filters:
                    if isinstance(filters['intent_category'], list):
                        placeholders = ','.join(['?' for _ in filters['intent_category']])
                        query += f" AND pm.intent_category IN ({placeholders})"
                        params.extend(filters['intent_category'])
                    else:
                        query += " AND pm.intent_category = ?"
                        params.append(filters['intent_category'])
                
                if 'status' in filters:
                    if isinstance(filters['status'], list):
                        placeholders = ','.join(['?' for _ in filters['status']])
                        query += f" AND pm.status IN ({placeholders})"
                        params.extend(filters['status'])
                    else:
                        query += " AND pm.status = ?"
                        params.append(filters['status'])
                
                if 'author' in filters:
                    query += " AND pm.author = ?"
                    params.append(filters['author'])
                
                if 'model' in filters:
                    if isinstance(filters['model'], list):
                        placeholders = ','.join(['?' for _ in filters['model']])
                        query += f" AND pm.model IN ({placeholders})"
                        params.extend(filters['model'])
                    else:
                        query += " AND pm.model = ?"
                        params.append(filters['model'])
                
                if 'project_id' in filters:
                    query += " AND p.project_id = ?"
                    params.append(filters['project_id'])
                
                if 'folder_path' in filters:
                    query += " AND p.folder_path LIKE ?"
                    params.append(f"{filters['folder_path']}%")
                
                if 'domain' in filters:
                    query += " AND pm.domain = ?"
                    params.append(filters['domain'])
                
                if 'tone' in filters:
                    query += " AND pm.tone = ?"
                    params.append(filters['tone'])
                
                if 'persona' in filters:
                    query += " AND pm.persona = ?"
                    params.append(filters['persona'])
                
                # Date range filtering
                if 'created_after' in filters:
                    query += " AND p.created_at >= ?"
                    params.append(filters['created_after'])
                
                if 'created_before' in filters:
                    query += " AND p.created_at <= ?"
                    params.append(filters['created_before'])
                
                if 'updated_after' in filters:
                    query += " AND p.updated_at >= ?"
                    params.append(filters['updated_after'])
                
                if 'updated_before' in filters:
                    query += " AND p.updated_at <= ?"
                    params.append(filters['updated_before'])
                
                # Temperature range
                if 'temperature_min' in filters:
                    query += " AND pm.temperature >= ?"
                    params.append(filters['temperature_min'])
                
                if 'temperature_max' in filters:
                    query += " AND pm.temperature <= ?"
                    params.append(filters['temperature_max'])
                
                # Token range
                if 'max_tokens_min' in filters:
                    query += " AND pm.max_tokens >= ?"
                    params.append(filters['max_tokens_min'])
                
                if 'max_tokens_max' in filters:
                    query += " AND pm.max_tokens <= ?"
                    params.append(filters['max_tokens_max'])
                
                # Tag filtering
                if 'tags' in filters:
                    tags = filters['tags']
                    if isinstance(tags, list):
                        for tag in tags:
                            query += " AND json_extract(pm.tags, '$') LIKE ?"
                            params.append(f'%"{tag}"%')
                    else:
                        query += " AND json_extract(pm.tags, '$') LIKE ?"
                        params.append(f'%"{tags}"%')
                
                # Custom field filtering
                if 'custom_fields' in filters:
                    for field_name, field_value in filters['custom_fields'].items():
                        query += f" AND json_extract(pm.custom_fields, '$.{field_name}') = ?"
                        params.append(field_value)
                
                # Sorting
                sort_by = filters.get('sort_by', 'updated_at')
                sort_order = filters.get('sort_order', 'DESC')
                
                if sort_by in ['name', 'created_at', 'updated_at']:
                    query += f" ORDER BY p.{sort_by} {sort_order}"
                elif sort_by in ['model', 'author', 'status', 'intent_category']:
                    query += f" ORDER BY pm.{sort_by} {sort_order}"
                else:
                    query += " ORDER BY p.updated_at DESC"
                
                # Limit
                limit = filters.get('limit', 100)
                offset = filters.get('offset', 0)
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    result = {
                        'id': row['id'],
                        'name': row['name'],
                        'content': row['content'][:200] + '...' if len(row['content']) > 200 else row['content'],
                        'folder_path': row['folder_path'],
                        'project_id': row['project_id'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                    
                    if row['model']:
                        result['metadata'] = {
                            'model': row['model'],
                            'temperature': row['temperature'],
                            'tags': json.loads(row['tags']) if row['tags'] else [],
                            'author': row['author'],
                            'description': row['description'],
                            'intent_category': row['intent_category'],
                            'status': row['status'],
                            'domain': row['domain'],
                            'tone': row['tone'],
                            'persona': row['persona']
                        }
                    
                    results.append(result)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to filter prompts: {e}")
            return []
    
    def get_search_suggestions(self, partial_query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get search suggestions based on partial query."""
        try:
            suggestions = []
            
            with self.get_connection() as conn:
                # Suggest prompt names
                cursor = conn.execute("""
                    SELECT DISTINCT name FROM prompts 
                    WHERE name LIKE ? 
                    ORDER BY name LIMIT ?
                """, (f"%{partial_query}%", limit // 2))
                
                for row in cursor.fetchall():
                    suggestions.append({
                        'type': 'prompt_name',
                        'value': row['name'],
                        'display': f"Prompt: {row['name']}"
                    })
                
                # Suggest tags
                cursor = conn.execute("""
                    SELECT DISTINCT name FROM prompt_tags 
                    WHERE name LIKE ? 
                    ORDER BY name LIMIT ?
                """, (f"%{partial_query}%", limit // 2))
                
                for row in cursor.fetchall():
                    suggestions.append({
                        'type': 'tag',
                        'value': row['name'],
                        'display': f"Tag: {row['name']}"
                    })
                
                # Suggest authors
                cursor = conn.execute("""
                    SELECT DISTINCT author FROM prompt_metadata 
                    WHERE author LIKE ? AND author != ''
                    ORDER BY author LIMIT ?
                """, (f"%{partial_query}%", limit // 4))
                
                for row in cursor.fetchall():
                    suggestions.append({
                        'type': 'author',
                        'value': row['author'],
                        'display': f"Author: {row['author']}"
                    })
                
                # Suggest categories
                cursor = conn.execute("""
                    SELECT DISTINCT intent_category FROM prompt_metadata 
                    WHERE intent_category LIKE ?
                    ORDER BY intent_category LIMIT ?
                """, (f"%{partial_query}%", limit // 4))
                
                for row in cursor.fetchall():
                    suggestions.append({
                        'type': 'category',
                        'value': row['intent_category'],
                        'display': f"Category: {row['intent_category']}"
                    })
            
            return suggestions[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get search suggestions: {e}")
            return []
    
    def _filter_by_date_range(self, results: List[Dict[str, Any]], date_range: Dict[str, str]) -> List[Dict[str, Any]]:
        """Filter results by date range."""
        try:
            from datetime import datetime
            
            filtered = []
            for result in results:
                created_at = datetime.fromisoformat(result['created_at'].replace('Z', '+00:00'))
                
                if 'start' in date_range:
                    start_date = datetime.fromisoformat(date_range['start'])
                    if created_at < start_date:
                        continue
                
                if 'end' in date_range:
                    end_date = datetime.fromisoformat(date_range['end'])
                    if created_at > end_date:
                        continue
                
                filtered.append(result)
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"Failed to filter by date range: {e}")
            return results
    
    def _sort_search_results(self, results: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
        """Sort search results by specified criteria."""
        try:
            if sort_by == 'relevance':
                # Sort by similarity score if available, otherwise by updated_at
                return sorted(results, key=lambda x: (
                    x.get('similarity_score', 0.0),
                    x.get('updated_at', '')
                ), reverse=True)
            elif sort_by == 'name':
                return sorted(results, key=lambda x: x.get('name', '').lower())
            elif sort_by == 'created_at':
                return sorted(results, key=lambda x: x.get('created_at', ''), reverse=True)
            elif sort_by == 'updated_at':
                return sorted(results, key=lambda x: x.get('updated_at', ''), reverse=True)
            elif sort_by == 'author':
                return sorted(results, key=lambda x: x.get('metadata', {}).get('author', '').lower())
            else:
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to sort search results: {e}")
            return results
    
    def find_similar_prompts(self, prompt_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find prompts similar to a given prompt."""
        try:
            # Get the source prompt
            source_prompt = self.get_prompt(prompt_id)
            if not source_prompt:
                return []
            
            # Use semantic search if available
            if self.prompt_db and self.prompt_db.vector_db.is_available:
                similar = self.semantic_search(source_prompt['content'], limit + 1)
                # Remove the source prompt from results
                return [p for p in similar if p['id'] != prompt_id][:limit]
            else:
                # Fallback to tag-based similarity
                if 'metadata' in source_prompt and 'tags' in source_prompt['metadata']:
                    tags = source_prompt['metadata']['tags']
                    if tags:
                        similar = self.get_prompts_by_tags(tags, match_all=False)
                        return [p for p in similar if p['id'] != prompt_id][:limit]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to find similar prompts: {e}")
            return []
    
    def get_search_analytics(self) -> Dict[str, Any]:
        """Get analytics about search patterns and popular content."""
        try:
            with self.get_connection() as conn:
                analytics = {}
                
                # Most common tags
                cursor = conn.execute("""
                    SELECT name, COUNT(*) as usage_count
                    FROM prompt_tags pt
                    JOIN prompt_tag_associations pta ON pt.id = pta.tag_id
                    GROUP BY pt.name
                    ORDER BY usage_count DESC
                    LIMIT 10
                """)
                analytics['popular_tags'] = [
                    {'tag': row['name'], 'count': row['usage_count']}
                    for row in cursor.fetchall()
                ]
                
                # Most common categories
                cursor = conn.execute("""
                    SELECT intent_category, COUNT(*) as count
                    FROM prompt_metadata
                    WHERE intent_category IS NOT NULL
                    GROUP BY intent_category
                    ORDER BY count DESC
                """)
                analytics['category_distribution'] = [
                    {'category': row['intent_category'], 'count': row['count']}
                    for row in cursor.fetchall()
                ]
                
                # Most active authors
                cursor = conn.execute("""
                    SELECT author, COUNT(*) as prompt_count
                    FROM prompt_metadata
                    WHERE author IS NOT NULL AND author != ''
                    GROUP BY author
                    ORDER BY prompt_count DESC
                    LIMIT 10
                """)
                analytics['top_authors'] = [
                    {'author': row['author'], 'count': row['prompt_count']}
                    for row in cursor.fetchall()
                ]
                
                # Model usage
                cursor = conn.execute("""
                    SELECT model, COUNT(*) as usage_count
                    FROM prompt_metadata
                    WHERE model IS NOT NULL
                    GROUP BY model
                    ORDER BY usage_count DESC
                """)
                analytics['model_usage'] = [
                    {'model': row['model'], 'count': row['usage_count']}
                    for row in cursor.fetchall()
                ]
                
                return analytics
                
        except Exception as e:
            self.logger.error(f"Failed to get search analytics: {e}")
            return {}