"""
Test LLM Models and Database Schema
==================================

Test the enhanced LLM data models and database schema.
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.llm import (
    LLMProviderConfig, ModelConfig, EncryptedCredential, 
    TestExecution, UsageMetrics, LLMError, SecurityAuditEvent,
    LLMUsageRecord, TokenEstimate, CostEstimate
)
from models.base import (
    LLMProviderType, ProviderStatus, ErrorType, TestStatus, 
    TestType, SecurityEventType, RiskLevel
)
from data.database import DatabaseManager
from data.encryption import CredentialEncryption, CredentialManager


def test_llm_models():
    """Test LLM data models."""
    print("Testing LLM data models...")
    
    # Test ModelConfig
    model = ModelConfig(
        model_id="gpt-4",
        display_name="GPT-4",
        max_tokens=8192,
        input_cost_per_token=0.00003,
        output_cost_per_token=0.00006,
        supports_streaming=True,
        context_window=8192,
        tokenizer_type="tiktoken"
    )
    
    model_dict = model.to_dict()
    model_restored = ModelConfig.from_dict(model_dict)
    assert model_restored.model_id == model.model_id
    assert model_restored.max_tokens == model.max_tokens
    
    # Test LLMProviderConfig
    provider = LLMProviderConfig(
        name="OpenAI",
        provider_type=LLMProviderType.OPENAI,
        endpoint_url="https://api.openai.com/v1",
        models=[model],
        is_local=False,
        status=ProviderStatus.ACTIVE,
        description="OpenAI GPT models"
    )
    
    provider_dict = provider.to_dict()
    provider_restored = LLMProviderConfig.from_dict(provider_dict)
    assert provider_restored.name == provider.name
    assert provider_restored.provider_type == provider.provider_type
    assert len(provider_restored.models) == 1
    
    # Test TestExecution
    test_exec = TestExecution(
        prompt_template_id="test-prompt-1",
        provider_id=provider.id,
        model_id="gpt-4",
        test_type=TestType.SINGLE,
        status=TestStatus.COMPLETED,
        input_tokens=100,
        output_tokens=50,
        estimated_cost=0.009,
        actual_cost=0.0075,
        response_time=1.5,
        success=True,
        response_content="Test response",
        quality_score=0.95
    )
    
    test_dict = test_exec.to_dict()
    test_restored = TestExecution.from_dict(test_dict)
    assert test_restored.provider_id == test_exec.provider_id
    assert test_restored.success == test_exec.success
    
    # Test UsageMetrics
    metrics = UsageMetrics(
        provider_id=provider.id,
        model_id="gpt-4",
        total_requests=100,
        successful_requests=95,
        failed_requests=5,
        total_input_tokens=10000,
        total_output_tokens=5000,
        total_cost=1.5,
        average_response_time=1.2,
        average_quality_score=0.92
    )
    
    metrics_dict = metrics.to_dict()
    assert metrics_dict["total_requests"] == 100
    assert metrics_dict["average_quality_score"] == 0.92
    
    print("✓ LLM data models tests passed")


def test_database_schema():
    """Test enhanced database schema."""
    print("Testing enhanced database schema...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = Path(tmp_file.name)
    
    try:
        # Initialize database
        db_manager = DatabaseManager(db_path)
        db_manager.initialize()
        
        # Test schema version
        version = db_manager.get_schema_version()
        assert version >= 0
        
        # Test table creation
        with db_manager.get_connection() as conn:
            # Check if new LLM tables exist
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'llm_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'llm_models',
                'llm_providers', 
                'llm_usage_records',
                'llm_usage_stats'  # legacy table
            ]
            
            for table in expected_tables:
                assert table in tables, f"Table {table} not found"
            
            # Test inserting LLM provider
            conn.execute("""
                INSERT INTO llm_providers 
                (id, name, provider_type, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "test-provider-1",
                "Test Provider",
                "openai",
                "active",
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            # Test inserting LLM model
            conn.execute("""
                INSERT INTO llm_models 
                (id, provider_id, model_id, display_name, max_tokens, 
                 input_cost_per_token, output_cost_per_token)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "test-model-1",
                "test-provider-1",
                "gpt-4",
                "GPT-4",
                8192,
                0.00003,
                0.00006
            ))
            
            # Test inserting test execution
            conn.execute("""
                INSERT INTO test_executions 
                (id, prompt_template_id, provider_id, model_id, 
                 test_type, status, executed_at, executed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "test-exec-1",
                "prompt-1",
                "test-provider-1",
                "gpt-4",
                "single",
                "completed",
                datetime.now().isoformat(),
                "test-user"
            ))
            
            conn.commit()
            
            # Verify data was inserted
            cursor = conn.execute("SELECT COUNT(*) FROM llm_providers")
            assert cursor.fetchone()[0] == 1
            
            cursor = conn.execute("SELECT COUNT(*) FROM llm_models")
            assert cursor.fetchone()[0] == 1
            
            cursor = conn.execute("SELECT COUNT(*) FROM test_executions")
            assert cursor.fetchone()[0] == 1
        
        print("✓ Enhanced database schema tests passed")
        
    finally:
        # Cleanup
        if db_path.exists():
            db_path.unlink()


def test_encryption():
    """Test credential encryption system."""
    print("Testing credential encryption...")
    
    # Test encryption initialization
    encryption = CredentialEncryption()
    master_key = encryption.generate_master_key()
    encryption._initialize_encryption(master_key)
    
    # Test credential encryption/decryption
    test_credential = "sk-test-api-key-12345"
    encrypted_data, method = encryption.encrypt_credential(test_credential)
    
    assert method == "xor_hmac_pbkdf2"
    assert isinstance(encrypted_data, bytes)
    assert len(encrypted_data) > len(test_credential)  # Should be longer due to nonce
    
    # Test decryption
    decrypted_credential = encryption.decrypt_credential(encrypted_data, method)
    assert decrypted_credential == test_credential
    
    # Test credential hashing
    credential_hash = encryption.hash_credential(test_credential)
    assert len(credential_hash) == 64  # SHA256 hex digest
    assert encryption.verify_credential_hash(test_credential, credential_hash)
    
    print("✓ Credential encryption tests passed")


def test_credential_manager():
    """Test credential manager with database integration."""
    print("Testing credential manager...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = Path(tmp_file.name)
    
    try:
        # Initialize database and encryption
        db_manager = DatabaseManager(db_path)
        db_manager.initialize()
        
        encryption = CredentialEncryption()
        master_key = encryption.generate_master_key()
        encryption._initialize_encryption(master_key)
        
        credential_manager = CredentialManager(db_manager, encryption)
        
        # Test storing credential
        provider_id = "test-provider-1"
        credential_type = "API_KEY"
        credential_value = "sk-test-api-key-12345"
        
        success = credential_manager.store_credential(
            provider_id, credential_type, credential_value
        )
        assert success
        
        # Test retrieving credential
        retrieved_credential = credential_manager.retrieve_credential(
            provider_id, credential_type
        )
        assert retrieved_credential == credential_value
        
        # Test listing credentials
        credentials = credential_manager.list_credentials(provider_id)
        assert len(credentials) == 1
        assert credentials[0]['credential_type'] == credential_type
        
        # Test deleting credential
        success = credential_manager.delete_credential(provider_id, credential_type)
        assert success
        
        # Verify deletion
        retrieved_credential = credential_manager.retrieve_credential(
            provider_id, credential_type
        )
        assert retrieved_credential is None
        
        print("✓ Credential manager tests passed")
        
    finally:
        # Cleanup
        if db_path.exists():
            db_path.unlink()


def main():
    """Run all LLM model and database tests."""
    print("Running Enhanced LLM Models and Database Tests")
    print("=" * 50)
    
    try:
        test_llm_models()
        test_database_schema()
        test_encryption()
        test_credential_manager()
        
        print("=" * 50)
        print("✅ All enhanced LLM tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()