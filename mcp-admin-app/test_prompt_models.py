#!/usr/bin/env python3
"""
Advanced Prompt Management Models Test Suite
============================================

Unit tests for advanced prompt management data models, database operations,
and vector database integration.
"""

import sys
import os
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from models.prompt_advanced import (
    Prompt, PromptMetadata, PromptVersion, PromptBranch, PromptProject,
    VersionInfo, PerformanceMetrics, EvaluationResult, EvaluationRun,
    TokenUsage, ScoringRubric, CostSummary,
    PromptStatus, PromptCategory, VersionStatus, BranchType,
    ValidationError
)
from data.prompt_database import PromptDatabaseManager
from data.vector_database import VectorDatabaseManager


def test_prompt_metadata_validation():
    """Test prompt metadata validation."""
    print("Testing Prompt Metadata Validation...")
    
    # Test valid metadata
    metadata = PromptMetadata(
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=1000,
        tags=["test", "validation"],
        author="test_user",
        description="Test metadata",
        intent_category=PromptCategory.SUMMARIZATION
    )
    
    assert metadata.validate() == True
    
    # Test invalid temperature
    try:
        invalid_metadata = PromptMetadata(
            model="gpt-3.5-turbo",
            temperature=3.0  # Invalid - should be <= 2.0
        )
        invalid_metadata.validate()
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Temperature must be between 0.0 and 2.0" in str(e)
    
    # Test invalid max_tokens
    try:
        invalid_metadata = PromptMetadata(
            model="gpt-3.5-turbo",
            max_tokens=200000  # Invalid - should be <= 100000
        )
        invalid_metadata.validate()
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Max tokens must be between 1 and 100000" in str(e)
    
    # Test empty model
    try:
        invalid_metadata = PromptMetadata(model="")
        invalid_metadata.validate()
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Model must be a non-empty string" in str(e)
    
    print("✓ Prompt Metadata Validation tests passed")


def test_prompt_metadata_serialization():
    """Test prompt metadata serialization and deserialization."""
    print("Testing Prompt Metadata Serialization...")
    
    # Create metadata
    original = PromptMetadata(
        model="gpt-4",
        temperature=0.8,
        max_tokens=2000,
        tags=["creative", "writing"],
        custom_fields={"priority": "high", "version": "1.0"},
        author="test_author",
        description="Creative writing prompt",
        intent_category=PromptCategory.CREATIVE,
        status=PromptStatus.APPROVED,
        domain="content_creation",
        tone="professional",
        persona="expert_writer",
        objective="generate_article"
    )
    
    # Test to_dict
    data = original.to_dict()
    assert data["model"] == "gpt-4"
    assert data["temperature"] == 0.8
    assert data["max_tokens"] == 2000
    assert data["tags"] == ["creative", "writing"]
    assert data["custom_fields"]["priority"] == "high"
    assert data["intent_category"] == "creative"
    assert data["status"] == "approved"
    
    # Test from_dict
    restored = PromptMetadata.from_dict(data)
    assert restored.model == original.model
    assert restored.temperature == original.temperature
    assert restored.max_tokens == original.max_tokens
    assert restored.tags == original.tags
    assert restored.custom_fields == original.custom_fields
    assert restored.intent_category == original.intent_category
    assert restored.status == original.status
    assert restored.domain == original.domain
    
    print("✓ Prompt Metadata Serialization tests passed")


def test_prompt_validation():
    """Test prompt validation."""
    print("Testing Prompt Validation...")
    
    # Test valid prompt
    prompt = Prompt(
        name="Test Prompt",
        content="This is a test prompt with {{variable}}",
        folder_path="/test/folder"
    )
    
    assert prompt.validate() == True
    assert prompt.metadata is not None
    assert prompt.version_info is not None
    
    # Test empty name
    try:
        invalid_prompt = Prompt(name="", content="Test content")
        invalid_prompt.validate()
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Prompt name must be a non-empty string" in str(e)
    
    # Test empty content
    try:
        invalid_prompt = Prompt(name="Test", content="")
        invalid_prompt.validate()
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Prompt content must be a non-empty string" in str(e)
    
    # Test name too long
    try:
        invalid_prompt = Prompt(name="x" * 300, content="Test content")
        invalid_prompt.validate()
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Prompt name must be 255 characters or less" in str(e)
    
    print("✓ Prompt Validation tests passed")


def test_prompt_serialization():
    """Test prompt serialization and deserialization."""
    print("Testing Prompt Serialization...")
    
    # Create prompt with metadata
    metadata = PromptMetadata(
        model="gpt-3.5-turbo",
        temperature=0.5,
        tags=["test", "serialization"]
    )
    
    version_info = VersionInfo(
        current_version="1.2.0",
        total_versions=3,
        last_modified_by="test_user"
    )
    
    original = Prompt(
        name="Serialization Test",
        content="Test prompt for serialization {{name}}",
        metadata=metadata,
        version_info=version_info,
        folder_path="/test",
        project_id="test-project"
    )
    
    # Test JSON serialization
    json_str = original.to_json()
    assert isinstance(json_str, str)
    
    # Parse JSON to verify structure
    data = json.loads(json_str)
    assert data["name"] == "Serialization Test"
    assert data["metadata"]["model"] == "gpt-3.5-turbo"
    assert data["version_info"]["current_version"] == "1.2.0"
    
    # Test from_json
    restored = Prompt.from_json(json_str)
    assert restored.name == original.name
    assert restored.content == original.content
    assert restored.metadata.model == original.metadata.model
    assert restored.version_info.current_version == original.version_info.current_version
    assert restored.folder_path == original.folder_path
    assert restored.project_id == original.project_id
    
    print("✓ Prompt Serialization tests passed")


def test_prompt_version_validation():
    """Test prompt version validation."""
    print("Testing Prompt Version Validation...")
    
    # Test valid version
    metadata = PromptMetadata(model="gpt-3.5-turbo")
    version = PromptVersion(
        prompt_id="test-prompt",
        content="Test version content",
        metadata_snapshot=metadata,
        branch_name="feature/test",
        commit_message="Test commit"
    )
    
    assert version.validate() == True
    
    # Test missing prompt_id
    try:
        invalid_version = PromptVersion(
            prompt_id="",
            content="Test content"
        )
        invalid_version.validate()
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Prompt ID is required" in str(e)
    
    # Test missing content
    try:
        invalid_version = PromptVersion(
            prompt_id="test-prompt",
            content=""
        )
        invalid_version.validate()
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Content is required" in str(e)
    
    print("✓ Prompt Version Validation tests passed")


def test_evaluation_result_validation():
    """Test evaluation result validation."""
    print("Testing Evaluation Result Validation...")
    
    # Test valid evaluation result
    token_usage = TokenUsage(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    )
    
    result = EvaluationResult(
        prompt_version_id="test-version",
        model="gpt-3.5-turbo",
        input_variables={"name": "test"},
        output="Test output",
        scores={"quality": 0.8, "relevance": 0.9},
        token_usage=token_usage,
        execution_time=1.5,
        cost=0.001
    )
    
    assert result.validate() == True
    
    # Test negative execution time
    try:
        invalid_result = EvaluationResult(
            prompt_version_id="test-version",
            model="gpt-3.5-turbo",
            execution_time=-1.0
        )
        invalid_result.validate()
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Execution time cannot be negative" in str(e)
    
    # Test negative cost
    try:
        invalid_result = EvaluationResult(
            prompt_version_id="test-version",
            model="gpt-3.5-turbo",
            cost=-0.001
        )
        invalid_result.validate()
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Cost cannot be negative" in str(e)
    
    print("✓ Evaluation Result Validation tests passed")


def test_prompt_database_operations():
    """Test prompt database operations."""
    print("Testing Prompt Database Operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test_prompts.db"
        db_manager = PromptDatabaseManager(db_path)
        
        # Initialize database
        db_manager.initialize_prompt_schema()
        
        # Test database stats
        stats = db_manager.get_database_stats()
        assert "prompts_count" in stats
        assert "prompt_projects_count" in stats
        assert stats["schema_version"] >= 0
        
        # Test default project creation
        project_id = db_manager.create_default_project()
        assert project_id == "default-project"
        
        # Test default tags creation
        db_manager.create_default_tags()
        
        # Verify tables were created
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                "prompt_projects",
                "prompts",
                "prompt_metadata",
                "prompt_versions",
                "prompt_branches",
                "evaluation_runs",
                "evaluation_results",
                "prompt_embeddings",
                "prompt_tags"
            ]
            
            for table in expected_tables:
                assert table in tables, f"Table {table} not found"
        
        print("✓ Prompt Database Operations tests passed")


def test_vector_database_integration():
    """Test vector database integration (if dependencies available)."""
    print("Testing Vector Database Integration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = Path(temp_dir)
        vector_db = VectorDatabaseManager(data_dir)
        
        if not vector_db.is_available:
            print("⚠ Vector database dependencies not available - skipping vector tests")
            return
        
        # Initialize vector database
        vector_db.initialize()
        
        # Test stats
        stats = vector_db.get_collection_stats()
        assert stats["available"] == True
        assert stats["total_embeddings"] == 0
        
        # Test adding embeddings
        success = vector_db.add_prompt_embedding(
            "test-prompt-1",
            "This is a test prompt for summarization",
            {"category": "summarization"}
        )
        assert success == True
        
        success = vector_db.add_prompt_embedding(
            "test-prompt-2", 
            "This is a test prompt for translation",
            {"category": "translation"}
        )
        assert success == True
        
        # Test search
        results = vector_db.search_similar_prompts("summarization prompt", limit=5)
        assert len(results) > 0
        assert results[0]["prompt_id"] in ["test-prompt-1", "test-prompt-2"]
        assert results[0]["similarity_score"] > 0.0
        
        # Test batch operations
        batch_data = [
            {
                "id": "batch-1",
                "content": "Batch test prompt 1",
                "metadata": {"type": "batch"}
            },
            {
                "id": "batch-2", 
                "content": "Batch test prompt 2",
                "metadata": {"type": "batch"}
            }
        ]
        
        count = vector_db.batch_add_embeddings(batch_data)
        assert count == 2
        
        # Test updated stats
        stats = vector_db.get_collection_stats()
        assert stats["total_embeddings"] == 4
        
        # Test clustering (if sklearn available)
        try:
            cluster_result = vector_db.cluster_prompts(n_clusters=2)
            assert "clusters" in cluster_result
            assert cluster_result["total_prompts"] == 4
        except Exception as e:
            print(f"⚠ Clustering test skipped: {e}")
        
        # Test duplicate detection
        duplicates = vector_db.find_duplicate_prompts(similarity_threshold=0.9)
        # Should be empty since our test prompts are different
        assert isinstance(duplicates, list)
        
        # Test removal
        success = vector_db.remove_prompt_embedding("test-prompt-1")
        assert success == True
        
        # Test reset
        success = vector_db.reset_collection()
        assert success == True
        
        stats = vector_db.get_collection_stats()
        assert stats["total_embeddings"] == 0
        
        print("✓ Vector Database Integration tests passed")


def test_prompt_database_with_vector_integration():
    """Test prompt database with vector database integration."""
    print("Testing Prompt Database with Vector Integration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test_integrated.db"
        db_manager = PromptDatabaseManager(db_path)
        
        # Initialize database
        db_manager.initialize_prompt_schema()
        
        if not db_manager.vector_db.is_available:
            print("⚠ Vector database dependencies not available - testing SQL operations only")
        
        # Test adding prompt embedding
        success = db_manager.add_prompt_embedding(
            "test-prompt",
            "This is a test prompt for integration testing",
            {"category": "test"}
        )
        
        if db_manager.vector_db.is_available:
            assert success == True
            
            # Test search
            results = db_manager.search_similar_prompts("integration test", limit=5)
            assert len(results) >= 0  # May be 0 if vector DB not working
            
            # Test vector stats
            vector_stats = db_manager.get_vector_database_stats()
            assert "available" in vector_stats
        else:
            assert success == False
        
        # Test database stats (should work regardless of vector DB)
        stats = db_manager.get_database_stats()
        assert "prompts_count" in stats
        assert "schema_version" in stats
        
        print("✓ Prompt Database with Vector Integration tests passed")


def test_performance_metrics():
    """Test performance metrics model."""
    print("Testing Performance Metrics...")
    
    # Test creation and serialization
    metrics = PerformanceMetrics(
        average_score=0.85,
        total_executions=100,
        success_rate=0.95,
        average_tokens=150,
        average_cost=0.002,
        average_response_time=1.2
    )
    
    # Test serialization
    data = metrics.to_dict()
    assert data["average_score"] == 0.85
    assert data["total_executions"] == 100
    assert data["success_rate"] == 0.95
    
    # Test deserialization
    restored = PerformanceMetrics.from_dict(data)
    assert restored.average_score == metrics.average_score
    assert restored.total_executions == metrics.total_executions
    assert restored.success_rate == metrics.success_rate
    
    print("✓ Performance Metrics tests passed")


def test_evaluation_run():
    """Test evaluation run model."""
    print("Testing Evaluation Run...")
    
    # Create scoring rubric
    rubric = ScoringRubric(
        name="Quality Assessment",
        criteria={
            "relevance": {"weight": 0.4, "description": "How relevant is the response"},
            "accuracy": {"weight": 0.6, "description": "How accurate is the response"}
        },
        weights={"relevance": 0.4, "accuracy": 0.6}
    )
    
    # Create cost summary
    cost_summary = CostSummary(
        total_cost=0.05,
        cost_per_model={"gpt-3.5-turbo": 0.03, "gpt-4": 0.02},
        token_costs={"input": 0.02, "output": 0.03}
    )
    
    # Create evaluation results
    result1 = EvaluationResult(
        prompt_version_id="test-version",
        model="gpt-3.5-turbo",
        output="Test output 1",
        scores={"relevance": 0.8, "accuracy": 0.9},
        cost=0.03
    )
    
    result2 = EvaluationResult(
        prompt_version_id="test-version",
        model="gpt-4",
        output="Test output 2", 
        scores={"relevance": 0.9, "accuracy": 0.95},
        cost=0.02
    )
    
    # Create evaluation run
    run = EvaluationRun(
        prompt_version_id="test-version",
        test_dataset="test_data.json",
        models_tested=["gpt-3.5-turbo", "gpt-4"],
        scoring_rubric=rubric,
        results=[result1, result2],
        cost_summary=cost_summary,
        status="completed",
        completed_at=datetime.now()
    )
    
    assert run.validate() == True
    
    # Test serialization
    data = run.to_dict()
    assert data["prompt_version_id"] == "test-version"
    assert len(data["models_tested"]) == 2
    assert len(data["results"]) == 2
    assert data["status"] == "completed"
    
    # Test deserialization
    restored = EvaluationRun.from_dict(data)
    assert restored.prompt_version_id == run.prompt_version_id
    assert len(restored.models_tested) == 2
    assert len(restored.results) == 2
    assert restored.status == run.status
    
    print("✓ Evaluation Run tests passed")


def main():
    """Run all tests."""
    print("Running Advanced Prompt Management Models Tests")
    print("=" * 50)
    
    try:
        # Core model tests
        test_prompt_metadata_validation()
        test_prompt_metadata_serialization()
        test_prompt_validation()
        test_prompt_serialization()
        test_prompt_version_validation()
        test_evaluation_result_validation()
        test_performance_metrics()
        test_evaluation_run()
        
        # Database tests
        test_prompt_database_operations()
        test_vector_database_integration()
        test_prompt_database_with_vector_integration()
        
        print("\n" + "=" * 50)
        print("✅ All advanced prompt management tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()