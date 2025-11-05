"""
Prompt Template Management Service
=================================

Comprehensive prompt template management with version control and testing.
"""

import logging
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

from models.prompt import PromptTemplate, TemplateVersion, TestResult, ExecutionResult
from models.base import PromptParameter
from core.config import ConfigurationManager
from data.database import DatabaseManager


class PromptManager:
    """Manages prompt template operations with version control and testing."""
    
    def __init__(self, config_manager: ConfigurationManager, db_manager: DatabaseManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self._templates: Dict[str, PromptTemplate] = {}
        self._template_versions: Dict[str, List[TemplateVersion]] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load templates from storage."""
        try:
            templates_dir = os.path.join(str(self.config_manager.templates_dir), "prompts")
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir, exist_ok=True)
                return
            
            for filename in os.listdir(templates_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(templates_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            template = PromptTemplate.from_dict(data)
                            self._templates[template.id] = template
                            
                            # Load version history if exists
                            versions_file = filepath.replace('.json', '_versions.json')
                            if os.path.exists(versions_file):
                                with open(versions_file, 'r', encoding='utf-8') as vf:
                                    versions_data = json.load(vf)
                                    versions = [
                                        TemplateVersion(
                                            version=v['version'],
                                            content=v['content'],
                                            created_at=datetime.fromisoformat(v['created_at']),
                                            created_by=v['created_by'],
                                            change_notes=v.get('change_notes', '')
                                        ) for v in versions_data
                                    ]
                                    self._template_versions[template.id] = versions
                    except Exception as e:
                        self.logger.error(f"Error loading template {filename}: {e}")
        except Exception as e:
            self.logger.error(f"Error loading templates: {e}")
    
    def _save_template(self, template: PromptTemplate):
        """Save template to storage."""
        try:
            templates_dir = os.path.join(str(self.config_manager.templates_dir), "prompts")
            os.makedirs(templates_dir, exist_ok=True)
            
            filepath = os.path.join(templates_dir, f"{template.id}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Save version history
            if template.id in self._template_versions:
                versions_file = filepath.replace('.json', '_versions.json')
                versions_data = [v.to_dict() for v in self._template_versions[template.id]]
                with open(versions_file, 'w', encoding='utf-8') as f:
                    json.dump(versions_data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            self.logger.error(f"Error saving template {template.id}: {e}")
            raise
    
    def get_all_templates(self) -> List[PromptTemplate]:
        """Get all prompt templates."""
        return list(self._templates.values())
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a specific template by ID."""
        return self._templates.get(template_id)
    
    def search_templates(self, query: str, tags: List[str] = None) -> List[PromptTemplate]:
        """Search templates by name, description, or tags."""
        results = []
        query_lower = query.lower() if query else ""
        
        for template in self._templates.values():
            # Text search
            if query_lower:
                if (query_lower in template.name.lower() or 
                    query_lower in template.description.lower() or
                    query_lower in template.content.lower()):
                    match = True
                else:
                    match = False
            else:
                match = True
            
            # Tag filter
            if tags and match:
                match = any(tag in template.tags for tag in tags)
            
            if match:
                results.append(template)
        
        return results
    
    def create_template(self, template: PromptTemplate, created_by: str = "system") -> str:
        """Create a new prompt template."""
        try:
            template.created_by = created_by
            template.created_at = datetime.now()
            template.updated_at = datetime.now()
            template.version = 1
            
            # Create initial version
            initial_version = TemplateVersion(
                version=1,
                content=template.content,
                created_at=template.created_at,
                created_by=created_by,
                change_notes="Initial version"
            )
            self._template_versions[template.id] = [initial_version]
            
            self._templates[template.id] = template
            self._save_template(template)
            
            self.logger.info(f"Created template: {template.name} ({template.id})")
            return template.id
            
        except Exception as e:
            self.logger.error(f"Error creating template: {e}")
            raise
    
    def update_template(self, template_id: str, updated_template: PromptTemplate, 
                       updated_by: str = "system", change_notes: str = "") -> bool:
        """Update a prompt template with version control."""
        try:
            if template_id not in self._templates:
                return False
            
            current_template = self._templates[template_id]
            
            # Check if content actually changed
            if current_template.content != updated_template.content:
                # Create new version
                new_version = current_template.version + 1
                version_entry = TemplateVersion(
                    version=new_version,
                    content=updated_template.content,
                    created_at=datetime.now(),
                    created_by=updated_by,
                    change_notes=change_notes
                )
                
                if template_id not in self._template_versions:
                    self._template_versions[template_id] = []
                self._template_versions[template_id].append(version_entry)
                
                updated_template.version = new_version
            
            # Update template
            updated_template.id = template_id
            updated_template.created_at = current_template.created_at
            updated_template.created_by = current_template.created_by
            updated_template.updated_at = datetime.now()
            updated_template.usage_count = current_template.usage_count
            updated_template.last_used = current_template.last_used
            
            self._templates[template_id] = updated_template
            self._save_template(updated_template)
            
            self.logger.info(f"Updated template: {updated_template.name} ({template_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating template {template_id}: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a prompt template."""
        try:
            if template_id not in self._templates:
                return False
            
            template = self._templates[template_id]
            
            # Remove files
            templates_dir = os.path.join(str(self.config_manager.templates_dir), "prompts")
            template_file = os.path.join(templates_dir, f"{template_id}.json")
            versions_file = os.path.join(templates_dir, f"{template_id}_versions.json")
            
            if os.path.exists(template_file):
                os.remove(template_file)
            if os.path.exists(versions_file):
                os.remove(versions_file)
            
            # Remove from memory
            del self._templates[template_id]
            if template_id in self._template_versions:
                del self._template_versions[template_id]
            
            self.logger.info(f"Deleted template: {template.name} ({template_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting template {template_id}: {e}")
            return False
    
    def get_template_versions(self, template_id: str) -> List[TemplateVersion]:
        """Get version history for a template."""
        return self._template_versions.get(template_id, [])
    
    def revert_to_version(self, template_id: str, version: int, reverted_by: str = "system") -> bool:
        """Revert template to a specific version."""
        try:
            if template_id not in self._templates:
                return False
            
            versions = self._template_versions.get(template_id, [])
            target_version = next((v for v in versions if v.version == version), None)
            
            if not target_version:
                return False
            
            template = self._templates[template_id]
            template.content = target_version.content
            template.updated_at = datetime.now()
            
            # Create new version entry for the revert
            new_version = template.version + 1
            revert_entry = TemplateVersion(
                version=new_version,
                content=target_version.content,
                created_at=datetime.now(),
                created_by=reverted_by,
                change_notes=f"Reverted to version {version}"
            )
            
            self._template_versions[template_id].append(revert_entry)
            template.version = new_version
            
            self._save_template(template)
            
            self.logger.info(f"Reverted template {template_id} to version {version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error reverting template {template_id}: {e}")
            return False
    
    def test_template(self, template_id: str, parameters: Dict[str, Any]) -> TestResult:
        """Test a template with given parameters."""
        try:
            template = self._templates.get(template_id)
            if not template:
                return TestResult(
                    success=False,
                    output="",
                    error="Template not found"
                )
            
            start_time = datetime.now()
            
            # Substitute parameters in template content
            content = template.content
            for param_name, param_value in parameters.items():
                placeholder = f"{{{param_name}}}"
                content = content.replace(placeholder, str(param_value))
            
            # Check for missing required parameters
            missing_params = []
            for param in template.parameters:
                if param.required and param.name not in parameters:
                    if param.default is None:
                        missing_params.append(param.name)
            
            if missing_params:
                return TestResult(
                    success=False,
                    output="",
                    error=f"Missing required parameters: {', '.join(missing_params)}"
                )
            
            # Check for unsubstituted placeholders
            unsubstituted = re.findall(r'\{(\w+)\}', content)
            if unsubstituted:
                return TestResult(
                    success=False,
                    output=content,
                    error=f"Unsubstituted parameters: {', '.join(set(unsubstituted))}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                success=True,
                output=content,
                execution_time=execution_time
            )
            
        except Exception as e:
            return TestResult(
                success=False,
                output="",
                error=str(e)
            )
    
    def execute_template(self, template_id: str, parameters: Dict[str, Any], 
                        user: str = "system") -> ExecutionResult:
        """Execute a template and record usage."""
        try:
            result = self.test_template(template_id, parameters)
            
            # Update usage statistics
            if template_id in self._templates:
                template = self._templates[template_id]
                template.usage_count += 1
                template.last_used = datetime.now()
                self._save_template(template)
            
            return ExecutionResult(
                template_id=template_id,
                parameters=parameters,
                result=result,
                user=user
            )
            
        except Exception as e:
            self.logger.error(f"Error executing template {template_id}: {e}")
            return ExecutionResult(
                template_id=template_id,
                parameters=parameters,
                result=TestResult(success=False, output="", error=str(e)),
                user=user
            )
    
    def get_available_tags(self) -> List[str]:
        """Get all unique tags used in templates."""
        tags = set()
        for template in self._templates.values():
            tags.update(template.tags)
        return sorted(list(tags))
    
    def export_templates(self, template_ids: List[str] = None) -> Dict[str, Any]:
        """Export templates to a dictionary for backup/sharing."""
        if template_ids is None:
            template_ids = list(self._templates.keys())
        
        export_data = {
            "templates": [],
            "versions": {},
            "exported_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        for template_id in template_ids:
            if template_id in self._templates:
                export_data["templates"].append(self._templates[template_id].to_dict())
                if template_id in self._template_versions:
                    export_data["versions"][template_id] = [
                        v.to_dict() for v in self._template_versions[template_id]
                    ]
        
        return export_data
    
    def import_templates(self, import_data: Dict[str, Any], overwrite: bool = False) -> Tuple[int, int]:
        """Import templates from exported data. Returns (imported, skipped) counts."""
        imported = 0
        skipped = 0
        
        try:
            templates_data = import_data.get("templates", [])
            versions_data = import_data.get("versions", {})
            
            for template_data in templates_data:
                template = PromptTemplate.from_dict(template_data)
                
                if template.id in self._templates and not overwrite:
                    skipped += 1
                    continue
                
                self._templates[template.id] = template
                
                # Import version history
                if template.id in versions_data:
                    versions = [
                        TemplateVersion(
                            version=v['version'],
                            content=v['content'],
                            created_at=datetime.fromisoformat(v['created_at']),
                            created_by=v['created_by'],
                            change_notes=v.get('change_notes', '')
                        ) for v in versions_data[template.id]
                    ]
                    self._template_versions[template.id] = versions
                
                self._save_template(template)
                imported += 1
            
            self.logger.info(f"Imported {imported} templates, skipped {skipped}")
            return imported, skipped
            
        except Exception as e:
            self.logger.error(f"Error importing templates: {e}")
            raise
    
    def save_template(self, template: PromptTemplate) -> bool:
        """Save a template to storage."""
        try:
            # Add to memory
            self._templates[template.id] = template
            
            # Save to file
            self._save_template(template)
            
            self.logger.info(f"Saved template: {template.name} ({template.id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving template {template.id}: {e}")
            return False
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a template by ID."""
        return self._templates.get(template_id)
    
    def search_templates(self, query: str) -> List[PromptTemplate]:
        """Search templates by name, description, or tags."""
        try:
            query_lower = query.lower()
            matching_templates = []
            
            for template in self._templates.values():
                # Search in name
                if query_lower in template.name.lower():
                    matching_templates.append(template)
                    continue
                
                # Search in description
                if query_lower in template.description.lower():
                    matching_templates.append(template)
                    continue
                
                # Search in tags
                if any(query_lower in tag.lower() for tag in template.tags):
                    matching_templates.append(template)
                    continue
            
            return matching_templates
            
        except Exception as e:
            self.logger.error(f"Error searching templates: {e}")
            return []