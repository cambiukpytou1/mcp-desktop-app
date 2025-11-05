"""
Vector Database Integration for Semantic Search
===============================================

ChromaDB integration for semantic search capabilities using embeddings.
"""

import logging
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    import numpy as np
    VECTOR_DEPENDENCIES_AVAILABLE = True
except ImportError:
    VECTOR_DEPENDENCIES_AVAILABLE = False
    chromadb = None
    SentenceTransformer = None
    np = None


class VectorDatabaseManager:
    """Manages vector database operations for semantic search."""
    
    def __init__(self, data_dir: Path, embedding_model: str = "all-MiniLM-L6-v2"):
        self.data_dir = data_dir
        self.vector_db_path = data_dir / "vector_db"
        self.embedding_model_name = embedding_model
        self.logger = logging.getLogger(__name__)
        
        self._client = None
        self._embedding_model = None
        self._collection = None
        
        # Check if dependencies are available
        if not VECTOR_DEPENDENCIES_AVAILABLE:
            self.logger.warning(
                "Vector database dependencies not available. "
                "Install with: pip install chromadb sentence-transformers"
            )
    
    @property
    def is_available(self) -> bool:
        """Check if vector database functionality is available."""
        return VECTOR_DEPENDENCIES_AVAILABLE
    
    def initialize(self):
        """Initialize vector database and embedding model."""
        if not self.is_available:
            self.logger.warning("Vector database not available - skipping initialization")
            return
        
        try:
            # Create data directory
            self.vector_db_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB client
            self._client = chromadb.PersistentClient(
                path=str(self.vector_db_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Initialize embedding model
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
            
            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name="prompt_embeddings",
                metadata={"description": "Embeddings for prompt semantic search"}
            )
            
            self.logger.info(f"Vector database initialized with model: {self.embedding_model_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize vector database: {e}")
            raise
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text."""
        if not self.is_available or not self._embedding_model:
            return None
        
        try:
            # Generate embedding
            embedding = self._embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def add_prompt_embedding(self, prompt_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Add or update prompt embedding in vector database."""
        if not self.is_available or not self._collection:
            return False
        
        try:
            # Generate content hash for change detection
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Generate embedding
            embedding = self.generate_embedding(content)
            if not embedding:
                return False
            
            # Prepare metadata
            doc_metadata = {
                "prompt_id": prompt_id,
                "content_hash": content_hash,
                "created_at": datetime.now().isoformat(),
                "embedding_model": self.embedding_model_name
            }
            if metadata:
                doc_metadata.update(metadata)
            
            # Add to collection
            self._collection.upsert(
                ids=[prompt_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[doc_metadata]
            )
            
            self.logger.debug(f"Added embedding for prompt {prompt_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add prompt embedding: {e}")
            return False
    
    def remove_prompt_embedding(self, prompt_id: str) -> bool:
        """Remove prompt embedding from vector database."""
        if not self.is_available or not self._collection:
            return False
        
        try:
            self._collection.delete(ids=[prompt_id])
            self.logger.debug(f"Removed embedding for prompt {prompt_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove prompt embedding: {e}")
            return False
    
    def search_similar_prompts(
        self, 
        query: str, 
        limit: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar prompts using semantic similarity."""
        if not self.is_available or not self._collection:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                return []
            
            # Prepare where clause for filtering
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    if key in ["prompt_id", "content_hash", "embedding_model"]:
                        where_clause[key] = value
            
            # Search similar embeddings
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            similar_prompts = []
            if results["ids"] and results["ids"][0]:
                for i, prompt_id in enumerate(results["ids"][0]):
                    similar_prompts.append({
                        "prompt_id": prompt_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "similarity_score": 1.0 - results["distances"][0][i] if results["distances"] else 0.0
                    })
            
            return similar_prompts
            
        except Exception as e:
            self.logger.error(f"Failed to search similar prompts: {e}")
            return []
    
    def get_prompt_embedding_info(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get embedding information for a specific prompt."""
        if not self.is_available or not self._collection:
            return None
        
        try:
            results = self._collection.get(
                ids=[prompt_id],
                include=["documents", "metadatas"]
            )
            
            if results["ids"] and prompt_id in results["ids"]:
                index = results["ids"].index(prompt_id)
                return {
                    "prompt_id": prompt_id,
                    "content": results["documents"][index] if results["documents"] else "",
                    "metadata": results["metadatas"][index] if results["metadatas"] else {}
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get prompt embedding info: {e}")
            return None
    
    def cluster_prompts(self, prompt_ids: List[str] = None, n_clusters: int = 5) -> Dict[str, Any]:
        """Cluster prompts based on semantic similarity."""
        if not self.is_available or not self._collection:
            return {"clusters": [], "error": "Vector database not available"}
        
        try:
            from sklearn.cluster import KMeans
            
            # Get embeddings
            if prompt_ids:
                results = self._collection.get(
                    ids=prompt_ids,
                    include=["embeddings", "metadatas"]
                )
            else:
                results = self._collection.get(include=["embeddings", "metadatas"])
            
            if not results["ids"] or len(results["ids"]) < n_clusters:
                return {"clusters": [], "error": "Not enough prompts for clustering"}
            
            # Extract embeddings
            embeddings = np.array(results["embeddings"])
            
            # Perform clustering
            kmeans = KMeans(n_clusters=min(n_clusters, len(embeddings)), random_state=42)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Group prompts by cluster
            clusters = {}
            for i, prompt_id in enumerate(results["ids"]):
                cluster_id = int(cluster_labels[i])
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                
                clusters[cluster_id].append({
                    "prompt_id": prompt_id,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                })
            
            return {
                "clusters": [{"id": k, "prompts": v} for k, v in clusters.items()],
                "n_clusters": len(clusters),
                "total_prompts": len(results["ids"])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to cluster prompts: {e}")
            return {"clusters": [], "error": str(e)}
    
    def find_duplicate_prompts(self, similarity_threshold: float = 0.95) -> List[Dict[str, Any]]:
        """Find potentially duplicate prompts based on high similarity."""
        if not self.is_available or not self._collection:
            return []
        
        try:
            # Get all prompts
            results = self._collection.get(include=["documents", "metadatas"])
            
            if not results["ids"] or len(results["ids"]) < 2:
                return []
            
            duplicates = []
            processed_pairs = set()
            
            # Compare each prompt with others
            for i, prompt_id in enumerate(results["ids"]):
                content = results["documents"][i] if results["documents"] else ""
                
                # Search for similar prompts
                similar = self.search_similar_prompts(content, limit=10)
                
                for similar_prompt in similar:
                    other_id = similar_prompt["prompt_id"]
                    similarity = similar_prompt["similarity_score"]
                    
                    # Skip self and already processed pairs
                    if (other_id == prompt_id or 
                        (prompt_id, other_id) in processed_pairs or 
                        (other_id, prompt_id) in processed_pairs):
                        continue
                    
                    # Check if similarity exceeds threshold
                    if similarity >= similarity_threshold:
                        duplicates.append({
                            "prompt_1": prompt_id,
                            "prompt_2": other_id,
                            "similarity_score": similarity,
                            "content_1": content,
                            "content_2": similar_prompt["content"]
                        })
                        processed_pairs.add((prompt_id, other_id))
            
            return duplicates
            
        except Exception as e:
            self.logger.error(f"Failed to find duplicate prompts: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database collection."""
        if not self.is_available or not self._collection:
            return {"available": False, "error": "Vector database not available"}
        
        try:
            # Get collection info
            collection_info = self._collection.get()
            
            stats = {
                "available": True,
                "total_embeddings": len(collection_info["ids"]) if collection_info["ids"] else 0,
                "embedding_model": self.embedding_model_name,
                "collection_name": self._collection.name,
                "database_path": str(self.vector_db_path)
            }
            
            # Get model info if available
            if self._embedding_model:
                stats["model_dimensions"] = self._embedding_model.get_sentence_embedding_dimension()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return {"available": False, "error": str(e)}
    
    def reset_collection(self) -> bool:
        """Reset the vector database collection (delete all embeddings)."""
        if not self.is_available or not self._client:
            return False
        
        try:
            # Delete existing collection
            if self._collection:
                self._client.delete_collection(name="prompt_embeddings")
            
            # Recreate collection
            self._collection = self._client.get_or_create_collection(
                name="prompt_embeddings",
                metadata={"description": "Embeddings for prompt semantic search"}
            )
            
            self.logger.info("Vector database collection reset successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset collection: {e}")
            return False
    
    def batch_add_embeddings(self, prompts: List[Dict[str, Any]]) -> int:
        """Add multiple prompt embeddings in batch."""
        if not self.is_available or not self._collection:
            return 0
        
        try:
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for prompt_data in prompts:
                prompt_id = prompt_data.get("id")
                content = prompt_data.get("content", "")
                metadata = prompt_data.get("metadata", {})
                
                if not prompt_id or not content:
                    continue
                
                # Generate embedding
                embedding = self.generate_embedding(content)
                if not embedding:
                    continue
                
                # Prepare data
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                doc_metadata = {
                    "prompt_id": prompt_id,
                    "content_hash": content_hash,
                    "created_at": datetime.now().isoformat(),
                    "embedding_model": self.embedding_model_name
                }
                doc_metadata.update(metadata)
                
                ids.append(prompt_id)
                embeddings.append(embedding)
                documents.append(content)
                metadatas.append(doc_metadata)
            
            if ids:
                # Add batch to collection
                self._collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                
                self.logger.info(f"Added {len(ids)} embeddings in batch")
                return len(ids)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to batch add embeddings: {e}")
            return 0