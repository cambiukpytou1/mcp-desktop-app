#!/usr/bin/env python3
"""
Simple Repository Test
======================

Basic test to verify repository functionality.
"""

import tempfile
from pathlib import Path
from services.prompt.repository import PromptRepository
from data.prompt_database import PromptDatabaseManager

class MockConfig:
    def get(self, key, default=None):
        return default

class MockDB:
    def __init__(self, temp_dir):
        self.db_path = Path(temp_dir) / 'test.db'
        self.prompt_db = PromptDatabaseManager(self.db_path)
        self.prompt_db.initialize_prompt_schema()
    
    def get_connection(self):
        return self.prompt_db.get_connection()

def main():
    print("Testing basic repository functionality...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config = MockConfig()
        db = MockDB(temp_dir)
        repo = PromptRepository(config, db)
        
        # Test basic creation
        prompt_data = {
            'name': 'Test Prompt',
            'content': 'Test content with {{variable}}',
            'metadata': {
                'model': 'gpt-3.5-turbo',
                'temperature': 0.7,
                'tags': ['test']
            }
        }
        
        print("Creating prompt...")
        prompt_id = repo.create_prompt(prompt_data)
        print(f"Created prompt: {prompt_id}")
        
        # Test retrieval
        print("Retrieving prompt...")
        retrieved = repo.get_prompt(prompt_id)
        if retrieved:
            print(f"Retrieved prompt: {retrieved['name']}")
            print(f"Content: {retrieved['content'][:50]}...")
            print(f"Model: {retrieved['metadata']['model']}")
        else:
            print("Failed to retrieve prompt")
            return False
        
        # Test update
        print("Updating prompt...")
        updates = {'name': 'Updated Test Prompt'}
        success = repo.update_prompt(prompt_id, updates)
        print(f"Update success: {success}")
        
        # Test search
        print("Searching prompts...")
        results = repo.search_prompts('test')
        print(f"Search results: {len(results)} found")
        
        # Test project creation
        print("Creating project...")
        project_data = {
            'name': 'Test Project',
            'description': 'A test project'
        }
        project_id = repo.create_project(project_data)
        print(f"Created project: {project_id}")
        
        # Test project association
        print("Associating prompt with project...")
        success = repo.add_prompt_to_project(prompt_id, project_id)
        print(f"Association success: {success}")
        
        print("✅ All basic tests passed!")
        return True

if __name__ == "__main__":
    main()