"""
Semantic Clustering Service
===========================

Provides embedding-based prompt clustering and similarity detection.
"""

import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class PromptCluster:
    """Represents a cluster of semantically similar prompts."""
    cluster_id: str
    name: str
    description: str
    prompt_ids: List[str]
    centroid_embedding: Optional[List[float]]
    avg_performance: float
    intent_category: str
    similarity_threshold: float
    created_at: datetime


@dataclass
class SimilarityMatch:
    """Represents a similarity match between prompts."""
    prompt_id_1: str
    prompt_id_2: str
    similarity_score: float
    match_type: str  # 'semantic', 'structural', 'intent'
    common_elements: List[str]
    reuse_suggestion: str


@dataclass
class IntentCategory:
    """Represents an automatically detected intent category."""
    category_id: str
    name: str
    description: str
    keywords: List[str]
    prompt_count: int
    avg_performance: float
    examples: List[str]


class SemanticClustering:
    """Handles embedding-based clustering and similarity detection."""
    
    def __init__(self, config_manager, db_manager, vector_db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.vector_db_manager = vector_db_manager
        
        # Clustering parameters
        self.similarity_threshold = 0.7
        self.min_cluster_size = 2
        self.max_clusters = 50
        
        # Intent detection patterns
        self.intent_patterns = self._initialize_intent_patterns()
        
        self.logger.info("Semantic clustering service initialized")
    
    def cluster_prompts_by_similarity(self, 
                                    prompt_ids: Optional[List[str]] = None,
                                    similarity_threshold: float = None) -> List[PromptCluster]:
        """
        Cluster prompts based on semantic similarity.
        
        Args:
            prompt_ids: Optional list of specific prompt IDs to cluster
            similarity_threshold: Minimum similarity for clustering
            
        Returns:
            List of prompt clusters
        """
        try:
            if similarity_threshold is None:
                similarity_threshold = self.similarity_threshold
            
            # Get prompts to cluster
            if prompt_ids is None:
                prompt_ids = self._get_all_prompt_ids()
            
            if len(prompt_ids) < 2:
                self.logger.warning("Not enough prompts for clustering")
                return []
            
            # Get embeddings for all prompts
            embeddings_data = self._get_prompt_embeddings(prompt_ids)
            
            if len(embeddings_data) < 2:
                self.logger.warning("Not enough embeddings for clustering")
                return []
            
            # Perform clustering
            clusters = self._perform_similarity_clustering(
                embeddings_data, similarity_threshold
            )
            
            # Enrich clusters with metadata
            enriched_clusters = []
            for cluster_data in clusters:
                enriched_cluster = self._enrich_cluster(cluster_data)
                enriched_clusters.append(enriched_cluster)
            
            self.logger.info(f"Created {len(enriched_clusters)} semantic clusters")
            return enriched_clusters
            
        except Exception as e:
            self.logger.error(f"Error clustering prompts: {e}")
            raise
    
    def detect_similar_prompts(self, 
                             prompt_id: str,
                             similarity_threshold: float = 0.8,
                             max_results: int = 10) -> List[SimilarityMatch]:
        """
        Detect prompts similar to a given prompt.
        
        Args:
            prompt_id: ID of the prompt to find similarities for
            similarity_threshold: Minimum similarity score
            max_results: Maximum number of results to return
            
        Returns:
            List of similarity matches
        """
        try:
            # Get embedding for the target prompt
            target_embedding = self._get_prompt_embedding(prompt_id)
            if not target_embedding:
                self.logger.warning(f"No embedding found for prompt {prompt_id}")
                return []
            
            # Search for similar prompts in vector database
            similar_prompts = self.vector_db_manager.search_similar(
                embedding=target_embedding,
                threshold=similarity_threshold,
                limit=max_results + 1  # +1 to exclude self
            )
            
            # Filter out the target prompt itself
            similar_prompts = [p for p in similar_prompts if p['id'] != prompt_id][:max_results]
            
            # Create similarity matches
            matches = []
            for similar_prompt in similar_prompts:
                match = self._create_similarity_match(
                    prompt_id, 
                    similar_prompt['id'],
                    similar_prompt['similarity']
                )
                matches.append(match)
            
            self.logger.info(f"Found {len(matches)} similar prompts for {prompt_id}")
            return matches
            
        except Exception as e:
            self.logger.error(f"Error detecting similar prompts: {e}")
            raise
    
    def categorize_prompts_by_intent(self, 
                                   prompt_ids: Optional[List[str]] = None) -> List[IntentCategory]:
        """
        Automatically categorize prompts by detected intent.
        
        Args:
            prompt_ids: Optional list of specific prompt IDs to categorize
            
        Returns:
            List of intent categories with assigned prompts
        """
        try:
            # Get prompts to categorize
            if prompt_ids is None:
                prompt_ids = self._get_all_prompt_ids()
            
            # Get prompt contents
            prompt_contents = self._get_prompt_contents(prompt_ids)
            
            # Detect intents for each prompt
            prompt_intents = {}
            for prompt_id, content in prompt_contents.items():
                intent = self._detect_prompt_intent(content)
                if intent not in prompt_intents:
                    prompt_intents[intent] = []
                prompt_intents[intent].append(prompt_id)
            
            # Create intent categories
            categories = []
            for intent, assigned_prompts in prompt_intents.items():
                if len(assigned_prompts) >= 1:  # At least one prompt per category
                    category = self._create_intent_category(intent, assigned_prompts)
                    categories.append(category)
            
            # Sort by prompt count
            categories.sort(key=lambda x: x.prompt_count, reverse=True)
            
            self.logger.info(f"Created {len(categories)} intent categories")
            return categories
            
        except Exception as e:
            self.logger.error(f"Error categorizing prompts by intent: {e}")
            raise
    
    def suggest_prompt_reuse(self, 
                           new_prompt_content: str,
                           similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
        """
        Suggest existing prompts that could be reused instead of creating new ones.
        
        Args:
            new_prompt_content: Content of the new prompt being created
            similarity_threshold: Minimum similarity for reuse suggestion
            
        Returns:
            List of reuse suggestions
        """
        try:
            # Generate embedding for new prompt
            new_embedding = self.vector_db_manager.generate_embedding(new_prompt_content)
            
            # Search for similar existing prompts
            similar_prompts = self.vector_db_manager.search_similar(
                embedding=new_embedding,
                threshold=similarity_threshold,
                limit=5
            )
            
            suggestions = []
            for similar_prompt in similar_prompts:
                # Get prompt details
                prompt_details = self._get_prompt_details(similar_prompt['id'])
                
                # Get performance metrics
                performance = self._get_prompt_performance_summary(similar_prompt['id'])
                
                suggestion = {
                    'prompt_id': similar_prompt['id'],
                    'similarity_score': similar_prompt['similarity'],
                    'prompt_name': prompt_details.get('name', 'Unknown'),
                    'avg_performance': performance.get('avg_score', 0.0),
                    'usage_count': performance.get('execution_count', 0),
                    'reuse_type': self._determine_reuse_type(similar_prompt['similarity']),
                    'modification_suggestions': self._generate_modification_suggestions(
                        new_prompt_content, 
                        prompt_details.get('content', '')
                    )
                }
                suggestions.append(suggestion)
            
            self.logger.info(f"Generated {len(suggestions)} reuse suggestions")
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error suggesting prompt reuse: {e}")
            raise
    
    def analyze_cluster_performance(self, cluster_id: str) -> Dict[str, Any]:
        """
        Analyze performance characteristics of a prompt cluster.
        
        Args:
            cluster_id: ID of the cluster to analyze
            
        Returns:
            Dictionary containing cluster performance analysis
        """
        try:
            # Get cluster details
            cluster = self._get_cluster_details(cluster_id)
            if not cluster:
                return {}
            
            # Get performance metrics for all prompts in cluster
            cluster_metrics = []
            for prompt_id in cluster['prompt_ids']:
                metrics = self._get_prompt_performance_summary(prompt_id)
                if metrics:
                    cluster_metrics.append(metrics)
            
            if not cluster_metrics:
                return {'cluster_id': cluster_id, 'analysis': 'no_data'}
            
            # Calculate cluster-level statistics
            avg_scores = [m['avg_score'] for m in cluster_metrics if m['avg_score'] > 0]
            success_rates = [m['success_rate'] for m in cluster_metrics if m['success_rate'] >= 0]
            costs = [m['avg_cost'] for m in cluster_metrics if m['avg_cost'] > 0]
            
            analysis = {
                'cluster_id': cluster_id,
                'prompt_count': len(cluster['prompt_ids']),
                'performance_summary': {
                    'avg_score': sum(avg_scores) / len(avg_scores) if avg_scores else 0,
                    'avg_success_rate': sum(success_rates) / len(success_rates) if success_rates else 0,
                    'avg_cost': sum(costs) / len(costs) if costs else 0,
                    'score_range': {
                        'min': min(avg_scores) if avg_scores else 0,
                        'max': max(avg_scores) if avg_scores else 0
                    }
                },
                'best_performer': self._find_best_performer_in_cluster(cluster_metrics),
                'optimization_opportunities': self._identify_cluster_optimization_opportunities(cluster_metrics),
                'common_patterns': self._identify_cluster_patterns(cluster['prompt_ids'])
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing cluster performance: {e}")
            return {}
    
    def _initialize_intent_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for intent detection."""
        return {
            'summarization': {
                'keywords': ['summarize', 'summary', 'brief', 'overview', 'key points', 'main ideas'],
                'patterns': [r'summarize.*', r'provide.*summary', r'give.*overview'],
                'description': 'Prompts that ask for summarization of content'
            },
            'translation': {
                'keywords': ['translate', 'translation', 'convert to', 'in spanish', 'in french'],
                'patterns': [r'translate.*to', r'convert.*language', r'in \w+ language'],
                'description': 'Prompts that request translation between languages'
            },
            'extraction': {
                'keywords': ['extract', 'find', 'identify', 'list', 'get', 'retrieve'],
                'patterns': [r'extract.*from', r'find all', r'identify.*in', r'list.*that'],
                'description': 'Prompts that extract specific information'
            },
            'generation': {
                'keywords': ['generate', 'create', 'write', 'compose', 'produce', 'make'],
                'patterns': [r'generate.*', r'create.*', r'write.*', r'compose.*'],
                'description': 'Prompts that generate new content'
            },
            'analysis': {
                'keywords': ['analyze', 'analysis', 'examine', 'evaluate', 'assess', 'review'],
                'patterns': [r'analyze.*', r'provide.*analysis', r'examine.*', r'evaluate.*'],
                'description': 'Prompts that perform analysis or evaluation'
            },
            'reasoning': {
                'keywords': ['explain', 'why', 'how', 'reason', 'logic', 'because'],
                'patterns': [r'explain.*why', r'how.*work', r'reason.*', r'logic.*'],
                'description': 'Prompts that require reasoning or explanation'
            },
            'classification': {
                'keywords': ['classify', 'categorize', 'sort', 'group', 'organize', 'label'],
                'patterns': [r'classify.*', r'categorize.*', r'sort.*into', r'group.*by'],
                'description': 'Prompts that classify or categorize items'
            },
            'comparison': {
                'keywords': ['compare', 'contrast', 'difference', 'similar', 'versus', 'vs'],
                'patterns': [r'compare.*', r'contrast.*', r'difference.*between', r'.*vs.*'],
                'description': 'Prompts that compare or contrast items'
            }
        }
    
    def _get_all_prompt_ids(self) -> List[str]:
        """Get all prompt IDs from database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM prompts")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting prompt IDs: {e}")
            return []
    
    def _get_prompt_embeddings(self, prompt_ids: List[str]) -> List[Dict[str, Any]]:
        """Get embeddings for multiple prompts."""
        embeddings_data = []
        
        for prompt_id in prompt_ids:
            embedding = self._get_prompt_embedding(prompt_id)
            if embedding:
                embeddings_data.append({
                    'prompt_id': prompt_id,
                    'embedding': embedding
                })
        
        return embeddings_data
    
    def _get_prompt_embedding(self, prompt_id: str) -> Optional[List[float]]:
        """Get embedding for a single prompt."""
        try:
            # Try to get from vector database first
            embedding = self.vector_db_manager.get_embedding(prompt_id)
            if embedding:
                return embedding
            
            # If not found, generate and store
            content = self._get_prompt_content(prompt_id)
            if content:
                embedding = self.vector_db_manager.generate_embedding(content)
                self.vector_db_manager.store_embedding(prompt_id, embedding, content)
                return embedding
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting prompt embedding: {e}")
            return None
    
    def _get_prompt_content(self, prompt_id: str) -> str:
        """Get prompt content by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT content_path FROM prompts WHERE id = ?
                """, (prompt_id,))
                
                row = cursor.fetchone()
                if row:
                    with open(row[0], 'r', encoding='utf-8') as f:
                        return f.read()
                
                return ""
                
        except Exception as e:
            self.logger.error(f"Error getting prompt content: {e}")
            return ""
    
    def _get_prompt_contents(self, prompt_ids: List[str]) -> Dict[str, str]:
        """Get contents for multiple prompts."""
        contents = {}
        for prompt_id in prompt_ids:
            content = self._get_prompt_content(prompt_id)
            if content:
                contents[prompt_id] = content
        return contents
    
    def _perform_similarity_clustering(self, 
                                     embeddings_data: List[Dict[str, Any]],
                                     similarity_threshold: float) -> List[Dict[str, Any]]:
        """Perform similarity-based clustering using a simple algorithm."""
        if not embeddings_data:
            return []
        
        clusters = []
        used_prompts = set()
        
        for i, data1 in enumerate(embeddings_data):
            if data1['prompt_id'] in used_prompts:
                continue
            
            # Start a new cluster
            cluster_prompts = [data1['prompt_id']]
            cluster_embeddings = [data1['embedding']]
            used_prompts.add(data1['prompt_id'])
            
            # Find similar prompts
            for j, data2 in enumerate(embeddings_data[i+1:], i+1):
                if data2['prompt_id'] in used_prompts:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_cosine_similarity(
                    data1['embedding'], 
                    data2['embedding']
                )
                
                if similarity >= similarity_threshold:
                    cluster_prompts.append(data2['prompt_id'])
                    cluster_embeddings.append(data2['embedding'])
                    used_prompts.add(data2['prompt_id'])
            
            # Only create cluster if it has minimum size
            if len(cluster_prompts) >= self.min_cluster_size:
                # Calculate centroid
                centroid = self._calculate_centroid(cluster_embeddings)
                
                clusters.append({
                    'prompt_ids': cluster_prompts,
                    'centroid_embedding': centroid,
                    'similarity_threshold': similarity_threshold
                })
        
        return clusters[:self.max_clusters]  # Limit number of clusters
    
    def _calculate_cosine_similarity(self, embedding1: List[float], 
                                   embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
            
            # Calculate magnitudes
            magnitude1 = sum(a * a for a in embedding1) ** 0.5
            magnitude2 = sum(b * b for b in embedding2) ** 0.5
            
            # Avoid division by zero
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
            
        except Exception as e:
            self.logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _calculate_centroid(self, embeddings: List[List[float]]) -> List[float]:
        """Calculate centroid of multiple embeddings."""
        if not embeddings:
            return []
        
        dimension = len(embeddings[0])
        centroid = [0.0] * dimension
        
        for embedding in embeddings:
            for i, value in enumerate(embedding):
                centroid[i] += value
        
        # Average
        for i in range(dimension):
            centroid[i] /= len(embeddings)
        
        return centroid
    
    def _enrich_cluster(self, cluster_data: Dict[str, Any]) -> PromptCluster:
        """Enrich cluster data with metadata and performance info."""
        prompt_ids = cluster_data['prompt_ids']
        
        # Generate cluster ID
        cluster_id = self._generate_cluster_id(prompt_ids)
        
        # Determine cluster name and description
        cluster_name, cluster_description = self._generate_cluster_name_description(prompt_ids)
        
        # Calculate average performance
        avg_performance = self._calculate_cluster_performance(prompt_ids)
        
        # Detect intent category
        intent_category = self._detect_cluster_intent(prompt_ids)
        
        return PromptCluster(
            cluster_id=cluster_id,
            name=cluster_name,
            description=cluster_description,
            prompt_ids=prompt_ids,
            centroid_embedding=cluster_data['centroid_embedding'],
            avg_performance=avg_performance,
            intent_category=intent_category,
            similarity_threshold=cluster_data['similarity_threshold'],
            created_at=datetime.now()
        )
    
    def _generate_cluster_id(self, prompt_ids: List[str]) -> str:
        """Generate unique cluster ID based on prompt IDs."""
        combined = ''.join(sorted(prompt_ids))
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    def _generate_cluster_name_description(self, prompt_ids: List[str]) -> Tuple[str, str]:
        """Generate name and description for cluster."""
        # Get prompt contents
        contents = []
        for prompt_id in prompt_ids[:3]:  # Sample first 3 prompts
            content = self._get_prompt_content(prompt_id)
            if content:
                contents.append(content)
        
        if not contents:
            return f"Cluster of {len(prompt_ids)} prompts", "Semantically similar prompts"
        
        # Detect common intent
        common_intent = self._detect_common_intent(contents)
        
        # Generate name based on intent
        if common_intent != 'general':
            name = f"{common_intent.title()} Prompts"
            description = f"Cluster of {len(prompt_ids)} prompts focused on {common_intent}"
        else:
            name = f"Similar Prompts ({len(prompt_ids)})"
            description = f"Cluster of {len(prompt_ids)} semantically similar prompts"
        
        return name, description
    
    def _calculate_cluster_performance(self, prompt_ids: List[str]) -> float:
        """Calculate average performance for cluster."""
        performances = []
        
        for prompt_id in prompt_ids:
            performance = self._get_prompt_performance_summary(prompt_id)
            if performance and performance.get('avg_score', 0) > 0:
                performances.append(performance['avg_score'])
        
        return sum(performances) / len(performances) if performances else 0.0
    
    def _detect_cluster_intent(self, prompt_ids: List[str]) -> str:
        """Detect the primary intent of a cluster."""
        contents = []
        for prompt_id in prompt_ids:
            content = self._get_prompt_content(prompt_id)
            if content:
                contents.append(content)
        
        return self._detect_common_intent(contents)
    
    def _detect_common_intent(self, contents: List[str]) -> str:
        """Detect common intent across multiple prompt contents."""
        intent_scores = {}
        
        for content in contents:
            intent = self._detect_prompt_intent(content)
            intent_scores[intent] = intent_scores.get(intent, 0) + 1
        
        if not intent_scores:
            return 'general'
        
        # Return most common intent
        return max(intent_scores.items(), key=lambda x: x[1])[0]
    
    def _detect_prompt_intent(self, content: str) -> str:
        """Detect the intent of a single prompt."""
        content_lower = content.lower()
        
        intent_scores = {}
        
        # Score each intent based on keywords and patterns
        for intent, config in self.intent_patterns.items():
            score = 0
            
            # Check keywords
            for keyword in config['keywords']:
                if keyword in content_lower:
                    score += 1
            
            # Check patterns
            for pattern in config['patterns']:
                if re.search(pattern, content_lower):
                    score += 2  # Patterns are weighted higher
            
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return 'general'
        
        # Return intent with highest score
        return max(intent_scores.items(), key=lambda x: x[1])[0]
    
    def _create_similarity_match(self, prompt_id_1: str, prompt_id_2: str, 
                               similarity_score: float) -> SimilarityMatch:
        """Create a similarity match object."""
        # Get prompt contents for analysis
        content_1 = self._get_prompt_content(prompt_id_1)
        content_2 = self._get_prompt_content(prompt_id_2)
        
        # Analyze common elements
        common_elements = self._find_common_elements(content_1, content_2)
        
        # Determine match type
        match_type = self._determine_match_type(similarity_score, common_elements)
        
        # Generate reuse suggestion
        reuse_suggestion = self._generate_reuse_suggestion(
            similarity_score, match_type, common_elements
        )
        
        return SimilarityMatch(
            prompt_id_1=prompt_id_1,
            prompt_id_2=prompt_id_2,
            similarity_score=similarity_score,
            match_type=match_type,
            common_elements=common_elements,
            reuse_suggestion=reuse_suggestion
        )
    
    def _find_common_elements(self, content_1: str, content_2: str) -> List[str]:
        """Find common elements between two prompt contents."""
        common_elements = []
        
        # Find common phrases (simplified approach)
        words_1 = set(content_1.lower().split())
        words_2 = set(content_2.lower().split())
        
        common_words = words_1.intersection(words_2)
        
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        meaningful_common = [word for word in common_words if word not in stop_words and len(word) > 2]
        
        return meaningful_common[:10]  # Limit to top 10
    
    def _determine_match_type(self, similarity_score: float, 
                            common_elements: List[str]) -> str:
        """Determine the type of match based on similarity and common elements."""
        if similarity_score >= 0.9:
            return 'semantic'
        elif len(common_elements) > 5:
            return 'structural'
        else:
            return 'intent'
    
    def _generate_reuse_suggestion(self, similarity_score: float, 
                                 match_type: str, common_elements: List[str]) -> str:
        """Generate a reuse suggestion based on similarity analysis."""
        if similarity_score >= 0.95:
            return "Consider using existing prompt instead of creating new one"
        elif similarity_score >= 0.85:
            return "Consider modifying existing prompt rather than creating from scratch"
        elif match_type == 'structural':
            return "Consider using similar structure and adapting content"
        else:
            return "Consider reviewing for potential consolidation opportunities"
    
    def _create_intent_category(self, intent: str, 
                              prompt_ids: List[str]) -> IntentCategory:
        """Create an intent category object."""
        # Get intent configuration
        intent_config = self.intent_patterns.get(intent, {})
        
        # Calculate average performance
        avg_performance = self._calculate_cluster_performance(prompt_ids)
        
        # Get examples
        examples = []
        for prompt_id in prompt_ids[:3]:
            content = self._get_prompt_content(prompt_id)
            if content:
                # Get first line or first 100 characters
                first_line = content.split('\n')[0]
                example = first_line[:100] + '...' if len(first_line) > 100 else first_line
                examples.append(example)
        
        return IntentCategory(
            category_id=f"intent_{intent}",
            name=intent.title(),
            description=intent_config.get('description', f'Prompts with {intent} intent'),
            keywords=intent_config.get('keywords', []),
            prompt_count=len(prompt_ids),
            avg_performance=avg_performance,
            examples=examples
        )
    
    def _get_prompt_details(self, prompt_id: str) -> Dict[str, Any]:
        """Get detailed information about a prompt."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.name, p.content_path, pm.description
                    FROM prompts p
                    LEFT JOIN prompt_metadata pm ON p.id = pm.prompt_id
                    WHERE p.id = ?
                """, (prompt_id,))
                
                row = cursor.fetchone()
                if row:
                    content = ""
                    try:
                        with open(row[1], 'r', encoding='utf-8') as f:
                            content = f.read()
                    except:
                        pass
                    
                    return {
                        'name': row[0],
                        'content': content,
                        'description': row[2] or ''
                    }
                
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting prompt details: {e}")
            return {}
    
    def _get_prompt_performance_summary(self, prompt_id: str) -> Dict[str, Any]:
        """Get performance summary for a prompt."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT AVG(er.score) as avg_score, 
                           COUNT(*) as execution_count,
                           AVG(er.cost) as avg_cost,
                           AVG(CASE WHEN er.score >= 0.8 THEN 1.0 ELSE 0.0 END) as success_rate
                    FROM evaluation_results er
                    JOIN evaluation_runs run ON er.run_id = run.run_id
                    JOIN prompt_versions pv ON run.prompt_version_id = pv.version_id
                    WHERE pv.prompt_id = ? AND er.score IS NOT NULL
                """, (prompt_id,))
                
                row = cursor.fetchone()
                if row and row[0] is not None:
                    return {
                        'avg_score': row[0],
                        'execution_count': row[1],
                        'avg_cost': row[2] or 0.0,
                        'success_rate': row[3] or 0.0
                    }
                
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting prompt performance: {e}")
            return {}
    
    def _determine_reuse_type(self, similarity_score: float) -> str:
        """Determine the type of reuse recommendation."""
        if similarity_score >= 0.95:
            return 'direct_reuse'
        elif similarity_score >= 0.85:
            return 'minor_modification'
        else:
            return 'template_reuse'
    
    def _generate_modification_suggestions(self, new_content: str, 
                                         existing_content: str) -> List[str]:
        """Generate suggestions for modifying existing prompt."""
        suggestions = []
        
        # Simple analysis - in practice, you'd use more sophisticated NLP
        new_words = set(new_content.lower().split())
        existing_words = set(existing_content.lower().split())
        
        unique_new = new_words - existing_words
        if unique_new:
            suggestions.append(f"Add concepts: {', '.join(list(unique_new)[:5])}")
        
        if len(new_content) > len(existing_content) * 1.2:
            suggestions.append("Consider expanding the existing prompt")
        elif len(new_content) < len(existing_content) * 0.8:
            suggestions.append("Consider simplifying the existing prompt")
        
        return suggestions
    
    def _get_cluster_details(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific cluster."""
        # In a real implementation, you'd store clusters in database
        # For now, return a placeholder
        return {
            'cluster_id': cluster_id,
            'prompt_ids': []  # Would be populated from database
        }
    
    def _find_best_performer_in_cluster(self, cluster_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find the best performing prompt in a cluster."""
        if not cluster_metrics:
            return {}
        
        best = max(cluster_metrics, key=lambda x: x.get('avg_score', 0))
        return {
            'prompt_id': best.get('prompt_id', ''),
            'avg_score': best.get('avg_score', 0),
            'success_rate': best.get('success_rate', 0)
        }
    
    def _identify_cluster_optimization_opportunities(self, 
                                                   cluster_metrics: List[Dict[str, Any]]) -> List[str]:
        """Identify optimization opportunities within a cluster."""
        opportunities = []
        
        if not cluster_metrics:
            return opportunities
        
        scores = [m.get('avg_score', 0) for m in cluster_metrics]
        
        # Check for high variance
        if len(scores) > 1:
            avg_score = sum(scores) / len(scores)
            variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            
            if variance > 0.1:
                opportunities.append("High performance variance - standardize approach")
        
        # Check for low performers
        low_performers = [s for s in scores if s < 0.6]
        if len(low_performers) > len(scores) * 0.3:
            opportunities.append("Multiple low performers - review cluster patterns")
        
        return opportunities
    
    def _identify_cluster_patterns(self, prompt_ids: List[str]) -> List[str]:
        """Identify common patterns within a cluster."""
        patterns = []
        
        # Get contents for analysis
        contents = []
        for prompt_id in prompt_ids:
            content = self._get_prompt_content(prompt_id)
            if content:
                contents.append(content)
        
        if len(contents) < 2:
            return patterns
        
        # Find common structural patterns
        if all('example:' in content.lower() for content in contents):
            patterns.append("All prompts use examples")
        
        if all(len(content.split('\n')) > 3 for content in contents):
            patterns.append("All prompts are multi-line structured")
        
        # Find common linguistic patterns
        common_starts = []
        for content in contents:
            first_word = content.split()[0].lower() if content.split() else ""
            common_starts.append(first_word)
        
        if len(set(common_starts)) == 1 and common_starts[0]:
            patterns.append(f"All prompts start with '{common_starts[0]}'")
        
        return patterns