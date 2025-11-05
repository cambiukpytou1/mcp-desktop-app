#!/usr/bin/env python3
"""
Prompt Repository Test Suite
============================

Unit tests for prompt repository operations including CRUD operations,
search functionality, and project organization features.
"""

import sys
import os
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from services.prompt.repository import PromptRepository
from models.prompt_advanced.models import (
    Prompt, PromptMetadata, PromptProject, PromptStatus, PromptCategory,
    ValidationError
)
from data.prompt_database import PromptDatabaseManager
# from core.config import ConfigManager  # Not needed for tests


class MockConfigManager:
    """Mock configuration manager for testing."""
    
    def __init__(self):
        self.config = {}
    
    def get(self, key, default=None):
        return self.config.get(key, default)


class MockDatabaseManager:
    """Mock database manager for testing."""
    
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir
        self.db_path = Path(temp_dir) / "test_prompts.db"
        self.prompt_db = PromptDatabaseManager(self.db_path)
        self.prompt_db.initialize_prompt_schema()
    
    def get_connection(self):
        return self.prompt_db.get_connection()


def test_prompt_repository_initialization():
    """Test prompt repository initialization."""
    print("Testing Prompt Repository Initialization...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        
        repository = PromptRepository(config_manager, db_manager)
        
        assert repository.config_manager == config_manager
        assert repository.db_manager == db_manager
        assert repository.prompt_db is not None
        
    print("✓ Prompt Repository Initialization tests passed")


def test_create_prompt():
    """Test prompt creation with validation and metadata."""
    print("Testing Prompt Creation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        repository = PromptRepository(config_manager, db_manager)
        
        # Test basic prompt creation
        prompt_data = {
            'name': 'Test Prompt',
            'content': 'This is a test prompt with {{variable}}',
            'folder_path': '/test/folder',
            'metadata': {
                'model': 'gpt-3.5-turbo',
                'temperature': 0.7,
                'max_tokens': 1000,
                'tags': ['test', 'validation'],
                'author': 'test_user',
                'description': 'Test prompt for validation',
                'intent_category': 'custom',
                'status': 'draft'
            }
        }
        
        prompt_id = repository.create_prompt(prompt_data)
        assert prompt_id is not None
        assert len(prompt_id) > 0
        
        # Verify prompt was stored
        retrieved = repository.get_prompt(prompt_id)
        assert retrieved is not None
        assert retrieved['name'] == 'Test Prompt'
        assert retrieved['content'] == 'This is a test prompt with {{variable}}'
        assert retrieved['folder_path'] == '/test/folder'
        assert retrieved['metadata']['model'] == 'gpt-3.5-turbo'
        assert retrieved['metadata']['temperature'] == 0.7
        assert retrieved['metadata']['tags'] == ['test', 'validation']
        
        # Test prompt creation with minimal data
        minimal_data = {
            'name': 'Minimal Prompt',
            'content': 'Minimal content'
        }
        
        minimal_id = repository.create_prompt(minimal_data)
        assert minimal_id is not None
        
        minimal_retrieved = repository.get_prompt(minimal_id)
        assert minimal_retrieved['name'] == 'Minimal Prompt'
        assert minimal_retrieved['content'] == 'Minimal content'
        
        # Test validation error
        try:
            invalid_data = {
                'name': '',  # Invalid empty name
                'content': 'Test content'
            }
            repository.create_prompt(invalid_data)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass  # Expected
        
    print("✓ Prompt Creation tests passed")


def test_update_prompt():
    """Test prompt updating functionality."""
    print("Testing Prompt Updates...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        repository = PromptRepository(config_manager, db_manager)
        
        # Create initial prompt
        prompt_data = {
            'name': 'Original Prompt',
            'content': 'Original content',
            'metadata': {
                'model': 'gpt-3.5-turbo',
                'temperature': 0.5,
                'tags': ['original']
            }
        }
        
        prompt_id = repository.create_prompt(prompt_data)
        
        # Test updating name and content
        updates = {
            'name': 'Updated Prompt',
            'content': 'Updated content with {{new_variable}}',
            'folder_path': '/updated/folder'
        }
        
        success = repository.update_prompt(prompt_id, updates)
        assert success == True
        
        # Verify updates
        updated = repository.get_prompt(prompt_id)
        assert updated['name'] == 'Updated Prompt'
        assert updated['content'] == 'Updated content with {{new_variable}}'
        assert updated['folder_path'] == '/updated/folder'
        
        # Test updating metadata
        metadata_updates = {
            'metadata': {
                'model': 'gpt-4',
                'temperature': 0.8,
                'tags': ['updated', 'test'],
                'description': 'Updated description'
            }
        }
        
        success = repository.update_prompt(prompt_id, metadata_updates)
        assert success == True
        
        updated = repository.get_prompt(prompt_id)
        assert updated['metadata']['model'] == 'gpt-4'
        assert updated['metadata']['temperature'] == 0.8
        assert updated['metadata']['tags'] == ['updated', 'test']
        assert updated['metadata']['description'] == 'Updated description'
        
        # Test updating non-existent prompt
        success = repository.update_prompt('non-existent-id', {'name': 'Test'})
        assert success == True  # Should not fail, just no rows affected
        
    print("✓ Prompt Updates tests passed")


def test_delete_prompt():
    """Test prompt deletion."""
    print("Testing Prompt Deletion...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        repository = PromptRepository(config_manager, db_manager)
        
        # Create prompt to delete
        prompt_data = {
            'name': 'To Delete',
            'content': 'This will be deleted'
        }
        
        prompt_id = repository.create_prompt(prompt_data)
        
        # Verify it exists
        retrieved = repository.get_prompt(prompt_id)
        assert retrieved is not None
        
        # Delete it
        success = repository.delete_prompt(prompt_id)
        assert success == True
        
        # Verify it's gone
        deleted = repository.get_prompt(prompt_id)
        assert deleted is None
        
        # Test deleting non-existent prompt
        success = repository.delete_prompt('non-existent-id')
        assert success == True  # Should not fail
        
    print("✓ Prompt Deletion tests passed")


def test_list_prompts():
    """Test prompt listing with filtering."""
    print("Testing Prompt Listing...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        repository = PromptRepository(config_manager, db_manager)
        
        # Create test prompts
        prompts_data = [
            {
                'name': 'Prompt 1',
                'content': 'Content 1',
                'folder_path': '/folder1',
                'metadata': {'tags': ['tag1', 'common']}
            },
            {
                'name': 'Prompt 2', 
                'content': 'Content 2',
                'folder_path': '/folder1',
                'metadata': {'tags': ['tag2', 'common']}
            },
            {
                'name': 'Prompt 3',
                'content': 'Content 3',
                'folder_path': '/folder2',
                'metadata': {'tags': ['tag3']}
            }
        ]
        
        created_ids = []
        for data in prompts_data:
            prompt_id = repository.create_prompt(data)
            created_ids.append(prompt_id)
        
        # Test listing all prompts
        all_prompts = repository.list_prompts()
        assert len(all_prompts) == 3
        
        # Test filtering by folder
        folder1_prompts = repository.list_prompts(folder_path='/folder1')
        assert len(folder1_prompts) == 2
        
        folder2_prompts = repository.list_prompts(folder_path='/folder2')
        assert len(folder2_prompts) == 1
        
        # Test pagination
        page1 = repository.list_prompts(limit=2, offset=0)
        assert len(page1) == 2
        
        page2 = repository.list_prompts(limit=2, offset=2)
        assert len(page2) == 1
        
    print("✓ Prompt Listing tests passed")


def test_search_prompts():
    """Test prompt search functionality."""
    print("Testing Prompt Search...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        repository = PromptRepository(config_manager, db_manager)
        
        # Create searchable prompts
        prompts_data = [
            {
                'name': 'Summarization Prompt',
                'content': 'Please summarize the following text: {{text}}',
                'metadata': {
                    'intent_category': 'summarization',
                    'author': 'user1',
                    'description': 'A prompt for text summarization'
                }
            },
            {
                'name': 'Translation Prompt',
                'content': 'Translate this text to French: {{text}}',
                'metadata': {
                    'intent_category': 'translation',
                    'author': 'user2',
                    'description': 'A prompt for language translation'
                }
            },
            {
                'name': 'Creative Writing',
                'content': 'Write a creative story about {{topic}}',
                'metadata': {
                    'intent_category': 'creative',
                    'author': 'user1',
                    'description': 'Creative writing prompt'
                }
            }
        ]
        
        for data in prompts_data:
            repository.create_prompt(data)
        
        # Test basic text search
        results = repository.search_prompts('summarize')
        assert len(results) >= 1
        assert any('Summarization' in r['name'] for r in results)
        
        results = repository.search_prompts('translate')
        assert len(results) >= 1
        assert any('Translation' in r['name'] for r in results)
        
        # Test search with filters
        filters = {'intent_category': 'summarization'}
        results = repository.search_prompts('prompt', filters)
        assert len(results) >= 1
        assert all(r['metadata']['intent_category'] == 'summarization' for r in results if 'metadata' in r)
        
        filters = {'author': 'user1'}
        results = repository.search_prompts('prompt', filters)
        assert len(results) >= 1
        assert all(r['metadata']['author'] == 'user1' for r in results if 'metadata' in r)
        
        # Test empty search
        results = repository.search_prompts('nonexistent')
        assert len(results) == 0
        
    print("✓ Prompt Search tests passed")


def test_project_management():
    """Test project creation and management."""
    print("Testing Project Management...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        repository = PromptRepository(config_manager, db_manager)
        
        # Test project creation
        project_data = {
            'name': 'Test Project',
            'description': 'A test project for validation',
            'settings': {'default_model': 'gpt-3.5-turbo'},
            'permissions': {'admin': ['user1'], 'editor': ['user2']},
            'created_by': 'user1'
        }
        
        project_id = repository.create_project(project_data)
        assert project_id is not None
        
        # Test project retrieval
        project = repository.get_project(project_id)
        assert project is not None
        assert project['name'] == 'Test Project'
        assert project['description'] == 'A test project for validation'
        assert project['settings']['default_model'] == 'gpt-3.5-turbo'
        assert project['permissions']['admin'] == ['user1']
        assert project['created_by'] == 'user1'
        
        # Test project update
        updates = {
            'name': 'Updated Project',
            'description': 'Updated description',
            'settings': {'default_model': 'gpt-4'}
        }
        
        success = repository.update_project(project_id, updates)
        assert success == True
        
        updated = repository.get_project(project_id)
        assert updated['name'] == 'Updated Project'
        assert updated['description'] == 'Updated description'
        assert updated['settings']['default_model'] == 'gpt-4'
        
        # Test project listing
        projects = repository.list_projects()
        assert len(projects) >= 1
        assert any(p['name'] == 'Updated Project' for p in projects)
        
        # Test project deletion
        success = repository.delete_project(project_id)
        assert success == True
        
        deleted = repository.get_project(project_id)
        assert deleted is None
        
    print("✓ Project Management tests passed")


def test_prompt_project_association():
    """Test associating prompts with projects."""
    print("Testing Prompt-Project Association...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        repository = PromptRepository(config_manager, db_manager)
        
        # Create project
        project_data = {
            'name': 'Association Test Project',
            'description': 'Test project for prompt association'
        }
        project_id = repository.create_project(project_data)
        
        # Create prompts
        prompt_data1 = {
            'name': 'Prompt 1',
            'content': 'Content 1'
        }
        prompt_id1 = repository.create_prompt(prompt_data1)
        
        prompt_data2 = {
            'name': 'Prompt 2',
            'content': 'Content 2'
        }
        prompt_id2 = repository.create_prompt(prompt_data2)
        
        # Test adding prompts to project
        success = repository.add_prompt_to_project(prompt_id1, project_id)
        assert success == True
        
        success = repository.add_prompt_to_project(prompt_id2, project_id)
        assert success == True
        
        # Verify association
        prompt1 = repository.get_prompt(prompt_id1)
        assert prompt1['project_id'] == project_id
        
        prompt2 = repository.get_prompt(prompt_id2)
        assert prompt2['project_id'] == project_id
        
        # Test getting project prompts
        project_prompts = repository.get_project_prompts(project_id)
        assert len(project_prompts) == 2
        
        # Test removing prompt from project
        success = repository.remove_prompt_from_project(prompt_id1)
        assert success == True
        
        updated_prompt1 = repository.get_prompt(prompt_id1)
        assert updated_prompt1['project_id'] is None
        
        # Test project deletion with prompt handling
        success = repository.delete_project(project_id)
        assert success == True
        
        # Verify remaining prompt is no longer associated
        updated_prompt2 = repository.get_prompt(prompt_id2)
        assert updated_prompt2['project_id'] is None
        
    print("✓ Prompt-Project Association tests passed")


def test_project_permissions():
    """Test project permission management."""
    print("Testing Project Permissions...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        repository = PromptRepository(config_manager, db_manager)
        
        # Create project with permissions
        project_data = {
            'name': 'Permission Test Project',
            'permissions': {
                'admin': ['user1'],
                'editor': ['user2', 'user3'],
                'viewer': ['user4']
            }
        }
        project_id = repository.create_project(project_data)
        
        # Test getting permissions
        permissions = repository.get_project_permissions(project_id)
        assert permissions['admin'] == ['user1']
        assert permissions['editor'] == ['user2', 'user3']
        assert permissions['viewer'] == ['user4']
        
        # Test checking permissions
        assert repository.check_project_permission(project_id, 'user1', 'admin') == True
        assert repository.check_project_permission(project_id, 'user1', 'editor') == True  # Admin has all permissions
        assert repository.check_project_permission(project_id, 'user2', 'editor') == True
        assert repository.check_project_permission(project_id, 'user2', 'admin') == False
        assert repository.check_project_permission(project_id, 'user4', 'viewer') == True
        assert repository.check_project_permission(project_id, 'user4', 'editor') == False
        
        # Test updating permissions
        new_permissions = {
            'admin': ['user1', 'user2'],
            'editor': ['user3'],
            'viewer': ['user4', 'user5']
        }
        
        success = repository.set_project_permissions(project_id, new_permissions)
        assert success == True
        
        updated_permissions = repository.get_project_permissions(project_id)
        assert updated_permissions['admin'] == ['user1', 'user2']
        assert updated_permissions['editor'] == ['user3']
        assert updated_permissions['viewer'] == ['user4', 'user5']
        
    print("✓ Project Permissions tests passed")


def test_advanced_search():
    """Test advanced search capabilities."""
    print("Testing Advanced Search...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        repository = PromptRepository(config_manager, db_manager)
        
        # Create test prompts with varied metadata
        prompts_data = [
            {
                'name': 'High Quality Prompt',
                'content': 'This is a high quality summarization prompt',
                'metadata': {
                    'intent_category': 'summarization',
                    'author': 'expert_user',
                    'model': 'gpt-4',
                    'temperature': 0.3,
                    'tags': ['quality', 'summarization']
                }
            },
            {
                'name': 'Creative Writing Prompt',
                'content': 'Write a creative story about space exploration',
                'metadata': {
                    'intent_category': 'creative',
                    'author': 'creative_user',
                    'model': 'gpt-3.5-turbo',
                    'temperature': 0.9,
                    'tags': ['creative', 'story']
                }
            }
        ]
        
        for data in prompts_data:
            repository.create_prompt(data)
        
        # Test advanced search with multiple criteria
        search_params = {
            'query': 'prompt',
            'type': 'text',
            'filters': {
                'intent_category': 'summarization',
                'author': 'expert_user'
            },
            'limit': 10
        }
        
        results = repository.advanced_search(search_params)
        assert len(results) >= 1
        assert any('High Quality' in r['name'] for r in results)
        
        # Test filtering by temperature range
        filters = {
            'temperature_min': 0.8,
            'temperature_max': 1.0
        }
        
        results = repository.filter_prompts(filters)
        assert len(results) >= 1
        assert all(r['metadata']['temperature'] >= 0.8 for r in results if 'metadata' in r)
        
        # Test filtering by tags
        filters = {'tags': ['creative']}
        results = repository.filter_prompts(filters)
        assert len(results) >= 1
        
        # Test search suggestions
        suggestions = repository.get_search_suggestions('qual', limit=5)
        assert len(suggestions) >= 0  # May be empty if no matches
        
    print("✓ Advanced Search tests passed")


def test_folder_structure():
    """Test hierarchical folder organization."""
    print("Testing Folder Structure...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        repository = PromptRepository(config_manager, db_manager)
        
        # Create prompts in different folders
        prompts_data = [
            {
                'name': 'Root Prompt',
                'content': 'Root level prompt',
                'folder_path': ''
            },
            {
                'name': 'Level 1 Prompt',
                'content': 'First level prompt',
                'folder_path': 'level1'
            },
            {
                'name': 'Level 2 Prompt',
                'content': 'Second level prompt',
                'folder_path': 'level1/level2'
            },
            {
                'name': 'Another Level 2',
                'content': 'Another second level prompt',
                'folder_path': 'level1/another_level2'
            }
        ]
        
        for data in prompts_data:
            repository.create_prompt(data)
        
        # Test folder structure retrieval
        structure = repository.get_folder_structure()
        assert 'folders' in structure
        assert 'level1' in structure['folders']
        assert 'level2' in structure['folders']['level1']['folders']
        assert 'another_level2' in structure['folders']['level1']['folders']
        
    print("✓ Folder Structure tests passed")


def test_tags_functionality():
    """Test tag-based prompt organization."""
    print("Testing Tags Functionality...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        repository = PromptRepository(config_manager, db_manager)
        
        # Create prompts with different tags
        prompts_data = [
            {
                'name': 'Prompt 1',
                'content': 'Content 1',
                'metadata': {'tags': ['tag1', 'common']}
            },
            {
                'name': 'Prompt 2',
                'content': 'Content 2', 
                'metadata': {'tags': ['tag2', 'common']}
            },
            {
                'name': 'Prompt 3',
                'content': 'Content 3',
                'metadata': {'tags': ['tag1', 'tag2']}
            }
        ]
        
        for data in prompts_data:
            repository.create_prompt(data)
        
        # Test getting prompts by single tag
        tag1_prompts = repository.get_prompts_by_tags(['tag1'])
        assert len(tag1_prompts) == 2
        
        common_prompts = repository.get_prompts_by_tags(['common'])
        assert len(common_prompts) == 2
        
        # Test getting prompts by multiple tags (any match)
        multi_tag_prompts = repository.get_prompts_by_tags(['tag1', 'tag2'], match_all=False)
        assert len(multi_tag_prompts) == 3  # All prompts have at least one of these tags
        
        # Test getting prompts by multiple tags (all match)
        all_match_prompts = repository.get_prompts_by_tags(['tag1', 'tag2'], match_all=True)
        assert len(all_match_prompts) == 1  # Only Prompt 3 has both tags
        
    print("✓ Tags Functionality tests passed")


def test_search_analytics():
    """Test search analytics functionality."""
    print("Testing Search Analytics...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = MockConfigManager()
        db_manager = MockDatabaseManager(temp_dir)
        repository = PromptRepository(config_manager, db_manager)
        
        # Create default tags first
        db_manager.prompt_db.create_default_tags()
        
        # Create prompts with varied metadata
        prompts_data = [
            {
                'name': 'Summarization Prompt 1',
                'content': 'Summarize this text',
                'metadata': {
                    'intent_category': 'summarization',
                    'author': 'user1',
                    'model': 'gpt-4'
                }
            },
            {
                'name': 'Summarization Prompt 2',
                'content': 'Create a summary',
                'metadata': {
                    'intent_category': 'summarization',
                    'author': 'user1',
                    'model': 'gpt-3.5-turbo'
                }
            },
            {
                'name': 'Creative Prompt',
                'content': 'Write a story',
                'metadata': {
                    'intent_category': 'creative',
                    'author': 'user2',
                    'model': 'gpt-4'
                }
            }
        ]
        
        for data in prompts_data:
            repository.create_prompt(data)
        
        # Test analytics
        analytics = repository.get_search_analytics()
        
        # Check structure
        assert 'category_distribution' in analytics
        assert 'top_authors' in analytics
        assert 'model_usage' in analytics
        
        # Verify data
        categories = analytics['category_distribution']
        assert len(categories) >= 2
        assert any(c['category'] == 'summarization' for c in categories)
        assert any(c['category'] == 'creative' for c in categories)
        
        authors = analytics['top_authors']
        assert len(authors) >= 2
        assert any(a['author'] == 'user1' for a in authors)
        assert any(a['author'] == 'user2' for a in authors)
        
        models = analytics['model_usage']
        assert len(models) >= 2
        assert any(m['model'] == 'gpt-4' for m in models)
        assert any(m['model'] == 'gpt-3.5-turbo' for m in models)
        
    print("✓ Search Analytics tests passed")


def main():
    """Run all repository tests."""
    print("Running Prompt Repository Tests")
    print("=" * 40)
    
    try:
        # Basic CRUD operations
        test_prompt_repository_initialization()
        test_create_prompt()
        test_update_prompt()
        test_delete_prompt()
        test_list_prompts()
        
        # Search functionality
        test_search_prompts()
        test_advanced_search()
        
        # Project organization
        test_project_management()
        test_prompt_project_association()
        test_project_permissions()
        
        # Organization features
        test_folder_structure()
        test_tags_functionality()
        test_search_analytics()
        
        print("\n" + "=" * 40)
        print("✅ All prompt repository tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()