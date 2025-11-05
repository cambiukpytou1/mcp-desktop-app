"""
Performance Analytics Service
============================

Provides statistical analysis of prompt effectiveness and pattern recognition.
"""

import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import re


@dataclass
class PerformanceMetrics:
    """Performance metrics for a prompt."""
    prompt_id: str
    avg_score: float
    score_variance: float
    execution_count: int
    avg_cost: float
    avg_tokens: int
    success_rate: float
    avg_response_time: float
    quality_trend: str  # 'improving', 'declining', 'stable'


@dataclass
class PromptPattern:
    """Identified pattern in high-performing prompts."""
    pattern_type: str
    pattern_description: str
    frequency: int
    avg_performance_boost: float
    examples: List[str]


@dataclass
class StructuralElement:
    """Structural element of a prompt."""
    element_type: str  # 'instruction', 'example', 'constraint', 'format'
    content: str
    position: int
    length: int


class PerformanceAnalytics:
    """Handles statistical analysis of prompt performance."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Performance thresholds
        self.high_performance_threshold = 0.8
        self.low_performance_threshold = 0.4
        self.trend_analysis_window = 30  # days
        
        self.logger.info("Performance analytics service initialized")
    
    def analyze_prompt_effectiveness(self, prompt_id: str, 
                                   time_window_days: int = 30) -> PerformanceMetrics:
        """
        Analyze the effectiveness of a specific prompt over time.
        
        Args:
            prompt_id: ID of the prompt to analyze
            time_window_days: Number of days to look back for analysis
            
        Returns:
            PerformanceMetrics object with statistical analysis
        """
        try:
            # Get evaluation results for the prompt
            results = self._get_evaluation_results(prompt_id, time_window_days)
            
            if not results:
                self.logger.warning(f"No evaluation results found for prompt {prompt_id}")
                return PerformanceMetrics(
                    prompt_id=prompt_id,
                    avg_score=0.0,
                    score_variance=0.0,
                    execution_count=0,
                    avg_cost=0.0,
                    avg_tokens=0,
                    success_rate=0.0,
                    avg_response_time=0.0,
                    quality_trend='unknown'
                )
            
            # Calculate basic statistics
            scores = [r['score'] for r in results if r['score'] is not None]
            costs = [r['cost'] for r in results if r['cost'] is not None]
            tokens = [r['tokens'] for r in results if r['tokens'] is not None]
            response_times = [r['response_time'] for r in results if r['response_time'] is not None]
            
            avg_score = statistics.mean(scores) if scores else 0.0
            score_variance = statistics.variance(scores) if len(scores) > 1 else 0.0
            avg_cost = statistics.mean(costs) if costs else 0.0
            avg_tokens = int(statistics.mean(tokens)) if tokens else 0
            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            
            # Calculate success rate (scores above threshold)
            successful_runs = len([s for s in scores if s >= self.high_performance_threshold])
            success_rate = successful_runs / len(scores) if scores else 0.0
            
            # Analyze quality trend
            quality_trend = self._analyze_quality_trend(results)
            
            metrics = PerformanceMetrics(
                prompt_id=prompt_id,
                avg_score=avg_score,
                score_variance=score_variance,
                execution_count=len(results),
                avg_cost=avg_cost,
                avg_tokens=avg_tokens,
                success_rate=success_rate,
                avg_response_time=avg_response_time,
                quality_trend=quality_trend
            )
            
            self.logger.info(f"Performance analysis completed for prompt {prompt_id}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error analyzing prompt effectiveness: {e}")
            raise
    
    def identify_high_performing_patterns(self, 
                                        min_frequency: int = 3) -> List[PromptPattern]:
        """
        Identify patterns in high-performing prompts.
        
        Args:
            min_frequency: Minimum frequency for a pattern to be considered significant
            
        Returns:
            List of identified patterns with performance impact
        """
        try:
            # Get high-performing prompts
            high_performers = self._get_high_performing_prompts()
            
            if len(high_performers) < min_frequency:
                self.logger.warning("Not enough high-performing prompts for pattern analysis")
                return []
            
            patterns = []
            
            # Analyze structural patterns
            structural_patterns = self._analyze_structural_patterns(high_performers)
            patterns.extend(structural_patterns)
            
            # Analyze linguistic patterns
            linguistic_patterns = self._analyze_linguistic_patterns(high_performers)
            patterns.extend(linguistic_patterns)
            
            # Analyze format patterns
            format_patterns = self._analyze_format_patterns(high_performers)
            patterns.extend(format_patterns)
            
            # Filter by minimum frequency
            significant_patterns = [p for p in patterns if p.frequency >= min_frequency]
            
            # Sort by performance boost
            significant_patterns.sort(key=lambda x: x.avg_performance_boost, reverse=True)
            
            self.logger.info(f"Identified {len(significant_patterns)} significant patterns")
            return significant_patterns
            
        except Exception as e:
            self.logger.error(f"Error identifying patterns: {e}")
            raise
    
    def correlate_structure_with_performance(self, 
                                           prompt_id: str) -> Dict[str, float]:
        """
        Correlate structural elements with performance metrics.
        
        Args:
            prompt_id: ID of the prompt to analyze
            
        Returns:
            Dictionary mapping structural elements to correlation coefficients
        """
        try:
            # Get prompt content and structure
            prompt_content = self._get_prompt_content(prompt_id)
            structural_elements = self._extract_structural_elements(prompt_content)
            
            # Get performance data
            results = self._get_evaluation_results(prompt_id, 90)  # 3 months
            
            if not results or not structural_elements:
                return {}
            
            correlations = {}
            
            # Analyze correlation between each structural element and performance
            for element in structural_elements:
                correlation = self._calculate_element_performance_correlation(
                    element, results
                )
                correlations[f"{element.element_type}_{element.position}"] = correlation
            
            self.logger.info(f"Structure-performance correlation analysis completed for {prompt_id}")
            return correlations
            
        except Exception as e:
            self.logger.error(f"Error correlating structure with performance: {e}")
            raise
    
    def generate_performance_insights(self, 
                                    prompt_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive performance insights.
        
        Args:
            prompt_ids: Optional list of specific prompt IDs to analyze
            
        Returns:
            Dictionary containing various performance insights
        """
        try:
            insights = {
                'summary': {},
                'top_performers': [],
                'improvement_opportunities': [],
                'patterns': [],
                'trends': {}
            }
            
            # Get prompts to analyze
            if prompt_ids is None:
                prompt_ids = self._get_all_prompt_ids()
            
            # Generate summary statistics
            insights['summary'] = self._generate_summary_statistics(prompt_ids)
            
            # Identify top performers
            insights['top_performers'] = self._identify_top_performers(prompt_ids)
            
            # Find improvement opportunities
            insights['improvement_opportunities'] = self._find_improvement_opportunities(prompt_ids)
            
            # Identify patterns
            insights['patterns'] = self.identify_high_performing_patterns()
            
            # Analyze trends
            insights['trends'] = self._analyze_performance_trends(prompt_ids)
            
            self.logger.info("Performance insights generated successfully")
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating performance insights: {e}")
            raise
    
    def _get_evaluation_results(self, prompt_id: str, 
                               days_back: int) -> List[Dict[str, Any]]:
        """Get evaluation results for a prompt within time window."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT er.score, er.cost, er.tokens, er.response_time, 
                           er.created_at, er.model
                    FROM evaluation_results er
                    JOIN evaluation_runs run ON er.run_id = run.run_id
                    JOIN prompt_versions pv ON run.prompt_version_id = pv.version_id
                    WHERE pv.prompt_id = ? AND er.created_at >= ?
                    ORDER BY er.created_at DESC
                """, (prompt_id, cutoff_date.isoformat()))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'score': row[0],
                        'cost': row[1],
                        'tokens': row[2],
                        'response_time': row[3],
                        'created_at': datetime.fromisoformat(row[4]),
                        'model': row[5]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Error getting evaluation results: {e}")
            return []
    
    def _analyze_quality_trend(self, results: List[Dict[str, Any]]) -> str:
        """Analyze the quality trend over time."""
        if len(results) < 3:
            return 'insufficient_data'
        
        # Sort by date
        sorted_results = sorted(results, key=lambda x: x['created_at'])
        scores = [r['score'] for r in sorted_results if r['score'] is not None]
        
        if len(scores) < 3:
            return 'insufficient_data'
        
        # Calculate trend using linear regression slope
        n = len(scores)
        x_values = list(range(n))
        
        # Simple linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(scores)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, scores))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 'stable'
        
        slope = numerator / denominator
        
        # Classify trend
        if slope > 0.01:
            return 'improving'
        elif slope < -0.01:
            return 'declining'
        else:
            return 'stable'
    
    def _get_high_performing_prompts(self) -> List[Dict[str, Any]]:
        """Get prompts with high performance scores."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.id, p.content_path, AVG(er.score) as avg_score
                    FROM prompts p
                    JOIN prompt_versions pv ON p.id = pv.prompt_id
                    JOIN evaluation_runs run ON pv.version_id = run.prompt_version_id
                    JOIN evaluation_results er ON run.run_id = er.run_id
                    WHERE er.score >= ?
                    GROUP BY p.id, p.content_path
                    HAVING COUNT(er.score) >= 3
                    ORDER BY avg_score DESC
                """, (self.high_performance_threshold,))
                
                prompts = []
                for row in cursor.fetchall():
                    content = self._read_prompt_content(row[1])
                    prompts.append({
                        'id': row[0],
                        'content': content,
                        'avg_score': row[2]
                    })
                
                return prompts
                
        except Exception as e:
            self.logger.error(f"Error getting high-performing prompts: {e}")
            return []
    
    def _analyze_structural_patterns(self, 
                                   prompts: List[Dict[str, Any]]) -> List[PromptPattern]:
        """Analyze structural patterns in prompts."""
        patterns = []
        
        # Pattern: Use of examples
        example_pattern = self._find_example_pattern(prompts)
        if example_pattern:
            patterns.append(example_pattern)
        
        # Pattern: Clear instructions
        instruction_pattern = self._find_instruction_pattern(prompts)
        if instruction_pattern:
            patterns.append(instruction_pattern)
        
        # Pattern: Constraints and limitations
        constraint_pattern = self._find_constraint_pattern(prompts)
        if constraint_pattern:
            patterns.append(constraint_pattern)
        
        return patterns
    
    def _analyze_linguistic_patterns(self, 
                                   prompts: List[Dict[str, Any]]) -> List[PromptPattern]:
        """Analyze linguistic patterns in prompts."""
        patterns = []
        
        # Pattern: Imperative language
        imperative_pattern = self._find_imperative_pattern(prompts)
        if imperative_pattern:
            patterns.append(imperative_pattern)
        
        # Pattern: Specific terminology
        terminology_pattern = self._find_terminology_pattern(prompts)
        if terminology_pattern:
            patterns.append(terminology_pattern)
        
        return patterns
    
    def _analyze_format_patterns(self, 
                               prompts: List[Dict[str, Any]]) -> List[PromptPattern]:
        """Analyze format patterns in prompts."""
        patterns = []
        
        # Pattern: Structured format
        structure_pattern = self._find_structure_pattern(prompts)
        if structure_pattern:
            patterns.append(structure_pattern)
        
        # Pattern: Length optimization
        length_pattern = self._find_length_pattern(prompts)
        if length_pattern:
            patterns.append(length_pattern)
        
        return patterns
    
    def _find_example_pattern(self, prompts: List[Dict[str, Any]]) -> Optional[PromptPattern]:
        """Find pattern of using examples in prompts."""
        example_keywords = ['example:', 'for example', 'e.g.', 'such as', 'like this:']
        
        prompts_with_examples = []
        for prompt in prompts:
            content = prompt['content'].lower()
            if any(keyword in content for keyword in example_keywords):
                prompts_with_examples.append(prompt)
        
        if len(prompts_with_examples) >= 3:
            avg_boost = self._calculate_pattern_boost(prompts_with_examples, prompts)
            return PromptPattern(
                pattern_type='structural',
                pattern_description='Use of examples and demonstrations',
                frequency=len(prompts_with_examples),
                avg_performance_boost=avg_boost,
                examples=[p['content'][:100] + '...' for p in prompts_with_examples[:3]]
            )
        
        return None
    
    def _find_instruction_pattern(self, prompts: List[Dict[str, Any]]) -> Optional[PromptPattern]:
        """Find pattern of clear instructions."""
        instruction_keywords = ['please', 'you should', 'make sure', 'ensure that', 'be sure to']
        
        prompts_with_instructions = []
        for prompt in prompts:
            content = prompt['content'].lower()
            if any(keyword in content for keyword in instruction_keywords):
                prompts_with_instructions.append(prompt)
        
        if len(prompts_with_instructions) >= 3:
            avg_boost = self._calculate_pattern_boost(prompts_with_instructions, prompts)
            return PromptPattern(
                pattern_type='structural',
                pattern_description='Clear instructional language',
                frequency=len(prompts_with_instructions),
                avg_performance_boost=avg_boost,
                examples=[p['content'][:100] + '...' for p in prompts_with_instructions[:3]]
            )
        
        return None
    
    def _find_constraint_pattern(self, prompts: List[Dict[str, Any]]) -> Optional[PromptPattern]:
        """Find pattern of using constraints."""
        constraint_keywords = ['do not', 'avoid', 'must not', 'should not', 'limit to']
        
        prompts_with_constraints = []
        for prompt in prompts:
            content = prompt['content'].lower()
            if any(keyword in content for keyword in constraint_keywords):
                prompts_with_constraints.append(prompt)
        
        if len(prompts_with_constraints) >= 3:
            avg_boost = self._calculate_pattern_boost(prompts_with_constraints, prompts)
            return PromptPattern(
                pattern_type='structural',
                pattern_description='Use of constraints and limitations',
                frequency=len(prompts_with_constraints),
                avg_performance_boost=avg_boost,
                examples=[p['content'][:100] + '...' for p in prompts_with_constraints[:3]]
            )
        
        return None
    
    def _find_imperative_pattern(self, prompts: List[Dict[str, Any]]) -> Optional[PromptPattern]:
        """Find pattern of imperative language."""
        imperative_keywords = ['analyze', 'create', 'generate', 'write', 'explain', 'describe']
        
        prompts_with_imperatives = []
        for prompt in prompts:
            content = prompt['content'].lower()
            if any(content.startswith(keyword) for keyword in imperative_keywords):
                prompts_with_imperatives.append(prompt)
        
        if len(prompts_with_imperatives) >= 3:
            avg_boost = self._calculate_pattern_boost(prompts_with_imperatives, prompts)
            return PromptPattern(
                pattern_type='linguistic',
                pattern_description='Use of imperative language',
                frequency=len(prompts_with_imperatives),
                avg_performance_boost=avg_boost,
                examples=[p['content'][:100] + '...' for p in prompts_with_imperatives[:3]]
            )
        
        return None
    
    def _find_terminology_pattern(self, prompts: List[Dict[str, Any]]) -> Optional[PromptPattern]:
        """Find pattern of specific terminology usage."""
        # This is a simplified implementation
        # In practice, you'd use NLP techniques to identify domain-specific terms
        
        technical_terms = ['algorithm', 'function', 'variable', 'parameter', 'output', 'input']
        
        prompts_with_terms = []
        for prompt in prompts:
            content = prompt['content'].lower()
            term_count = sum(1 for term in technical_terms if term in content)
            if term_count >= 2:
                prompts_with_terms.append(prompt)
        
        if len(prompts_with_terms) >= 3:
            avg_boost = self._calculate_pattern_boost(prompts_with_terms, prompts)
            return PromptPattern(
                pattern_type='linguistic',
                pattern_description='Use of specific technical terminology',
                frequency=len(prompts_with_terms),
                avg_performance_boost=avg_boost,
                examples=[p['content'][:100] + '...' for p in prompts_with_terms[:3]]
            )
        
        return None
    
    def _find_structure_pattern(self, prompts: List[Dict[str, Any]]) -> Optional[PromptPattern]:
        """Find pattern of structured formatting."""
        structure_indicators = ['1.', '2.', '-', '*', '###', '**']
        
        structured_prompts = []
        for prompt in prompts:
            content = prompt['content']
            if any(indicator in content for indicator in structure_indicators):
                structured_prompts.append(prompt)
        
        if len(structured_prompts) >= 3:
            avg_boost = self._calculate_pattern_boost(structured_prompts, prompts)
            return PromptPattern(
                pattern_type='format',
                pattern_description='Use of structured formatting',
                frequency=len(structured_prompts),
                avg_performance_boost=avg_boost,
                examples=[p['content'][:100] + '...' for p in structured_prompts[:3]]
            )
        
        return None
    
    def _find_length_pattern(self, prompts: List[Dict[str, Any]]) -> Optional[PromptPattern]:
        """Find optimal length patterns."""
        # Calculate average length of high-performing prompts
        lengths = [len(prompt['content']) for prompt in prompts]
        avg_length = statistics.mean(lengths)
        
        # Find prompts within optimal length range (±20% of average)
        optimal_range = (avg_length * 0.8, avg_length * 1.2)
        optimal_length_prompts = [
            p for p in prompts 
            if optimal_range[0] <= len(p['content']) <= optimal_range[1]
        ]
        
        if len(optimal_length_prompts) >= 3:
            return PromptPattern(
                pattern_type='format',
                pattern_description=f'Optimal length range: {int(optimal_range[0])}-{int(optimal_range[1])} characters',
                frequency=len(optimal_length_prompts),
                avg_performance_boost=0.1,  # Estimated boost
                examples=[f"Length: {len(p['content'])}" for p in optimal_length_prompts[:3]]
            )
        
        return None
    
    def _calculate_pattern_boost(self, pattern_prompts: List[Dict[str, Any]], 
                               all_prompts: List[Dict[str, Any]]) -> float:
        """Calculate average performance boost for a pattern."""
        pattern_scores = [p['avg_score'] for p in pattern_prompts]
        all_scores = [p['avg_score'] for p in all_prompts]
        
        pattern_avg = statistics.mean(pattern_scores)
        overall_avg = statistics.mean(all_scores)
        
        return pattern_avg - overall_avg
    
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
                    return self._read_prompt_content(row[0])
                
                return ""
                
        except Exception as e:
            self.logger.error(f"Error getting prompt content: {e}")
            return ""
    
    def _read_prompt_content(self, content_path: str) -> str:
        """Read prompt content from file."""
        try:
            with open(content_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading prompt content: {e}")
            return ""
    
    def _extract_structural_elements(self, content: str) -> List[StructuralElement]:
        """Extract structural elements from prompt content."""
        elements = []
        
        # Find instructions (imperative sentences)
        instruction_patterns = [
            r'^(Analyze|Create|Generate|Write|Explain|Describe|List|Identify).*$',
            r'^(Please|You should|Make sure|Ensure that).*$'
        ]
        
        for i, line in enumerate(content.split('\n')):
            line = line.strip()
            if not line:
                continue
                
            for pattern in instruction_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    elements.append(StructuralElement(
                        element_type='instruction',
                        content=line,
                        position=i,
                        length=len(line)
                    ))
                    break
        
        # Find examples
        example_patterns = [
            r'.*[Ee]xample:.*',
            r'.*[Ff]or example.*',
            r'.*[Ee]\.g\..*'
        ]
        
        for i, line in enumerate(content.split('\n')):
            line = line.strip()
            for pattern in example_patterns:
                if re.match(pattern, line):
                    elements.append(StructuralElement(
                        element_type='example',
                        content=line,
                        position=i,
                        length=len(line)
                    ))
                    break
        
        return elements
    
    def _calculate_element_performance_correlation(self, 
                                                 element: StructuralElement,
                                                 results: List[Dict[str, Any]]) -> float:
        """Calculate correlation between structural element and performance."""
        # Simplified correlation calculation
        # In practice, you'd use more sophisticated statistical methods
        
        scores = [r['score'] for r in results if r['score'] is not None]
        if not scores:
            return 0.0
        
        # For now, return a placeholder correlation based on element type
        correlation_map = {
            'instruction': 0.3,
            'example': 0.4,
            'constraint': 0.2,
            'format': 0.1
        }
        
        return correlation_map.get(element.element_type, 0.0)
    
    def _get_all_prompt_ids(self) -> List[str]:
        """Get all prompt IDs."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM prompts")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting prompt IDs: {e}")
            return []
    
    def _generate_summary_statistics(self, prompt_ids: List[str]) -> Dict[str, Any]:
        """Generate summary statistics for prompts."""
        try:
            total_prompts = len(prompt_ids)
            
            # Get performance metrics for all prompts
            all_metrics = []
            for prompt_id in prompt_ids:
                metrics = self.analyze_prompt_effectiveness(prompt_id)
                if metrics.execution_count > 0:
                    all_metrics.append(metrics)
            
            if not all_metrics:
                return {'total_prompts': total_prompts, 'analyzed_prompts': 0}
            
            # Calculate summary statistics
            avg_scores = [m.avg_score for m in all_metrics]
            success_rates = [m.success_rate for m in all_metrics]
            avg_costs = [m.avg_cost for m in all_metrics]
            
            return {
                'total_prompts': total_prompts,
                'analyzed_prompts': len(all_metrics),
                'overall_avg_score': statistics.mean(avg_scores),
                'overall_success_rate': statistics.mean(success_rates),
                'overall_avg_cost': statistics.mean(avg_costs),
                'score_distribution': {
                    'min': min(avg_scores),
                    'max': max(avg_scores),
                    'median': statistics.median(avg_scores),
                    'std_dev': statistics.stdev(avg_scores) if len(avg_scores) > 1 else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating summary statistics: {e}")
            return {}
    
    def _identify_top_performers(self, prompt_ids: List[str], 
                               top_n: int = 10) -> List[Dict[str, Any]]:
        """Identify top performing prompts."""
        try:
            prompt_metrics = []
            
            for prompt_id in prompt_ids:
                metrics = self.analyze_prompt_effectiveness(prompt_id)
                if metrics.execution_count >= 3:  # Minimum executions for reliability
                    prompt_metrics.append({
                        'prompt_id': prompt_id,
                        'avg_score': metrics.avg_score,
                        'success_rate': metrics.success_rate,
                        'execution_count': metrics.execution_count,
                        'quality_trend': metrics.quality_trend
                    })
            
            # Sort by average score
            prompt_metrics.sort(key=lambda x: x['avg_score'], reverse=True)
            
            return prompt_metrics[:top_n]
            
        except Exception as e:
            self.logger.error(f"Error identifying top performers: {e}")
            return []
    
    def _find_improvement_opportunities(self, prompt_ids: List[str]) -> List[Dict[str, Any]]:
        """Find prompts with improvement opportunities."""
        try:
            opportunities = []
            
            for prompt_id in prompt_ids:
                metrics = self.analyze_prompt_effectiveness(prompt_id)
                
                if metrics.execution_count < 3:
                    continue
                
                # Low performance opportunity
                if metrics.avg_score < self.low_performance_threshold:
                    opportunities.append({
                        'prompt_id': prompt_id,
                        'opportunity_type': 'low_performance',
                        'current_score': metrics.avg_score,
                        'improvement_potential': 'high',
                        'recommendation': 'Review prompt structure and clarity'
                    })
                
                # High variance opportunity
                elif metrics.score_variance > 0.1:
                    opportunities.append({
                        'prompt_id': prompt_id,
                        'opportunity_type': 'high_variance',
                        'score_variance': metrics.score_variance,
                        'improvement_potential': 'medium',
                        'recommendation': 'Improve prompt consistency and specificity'
                    })
                
                # Declining trend opportunity
                elif metrics.quality_trend == 'declining':
                    opportunities.append({
                        'prompt_id': prompt_id,
                        'opportunity_type': 'declining_trend',
                        'quality_trend': metrics.quality_trend,
                        'improvement_potential': 'medium',
                        'recommendation': 'Investigate recent changes and model drift'
                    })
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error finding improvement opportunities: {e}")
            return []
    
    def _analyze_performance_trends(self, prompt_ids: List[str]) -> Dict[str, Any]:
        """Analyze performance trends across prompts."""
        try:
            trends = {
                'improving': 0,
                'declining': 0,
                'stable': 0,
                'insufficient_data': 0
            }
            
            for prompt_id in prompt_ids:
                metrics = self.analyze_prompt_effectiveness(prompt_id)
                trends[metrics.quality_trend] += 1
            
            total = sum(trends.values())
            if total > 0:
                trend_percentages = {
                    trend: (count / total) * 100 
                    for trend, count in trends.items()
                }
            else:
                trend_percentages = trends
            
            return {
                'trend_counts': trends,
                'trend_percentages': trend_percentages,
                'overall_health': self._assess_overall_health(trend_percentages)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance trends: {e}")
            return {}
    
    def _assess_overall_health(self, trend_percentages: Dict[str, float]) -> str:
        """Assess overall health of prompt collection."""
        improving = trend_percentages.get('improving', 0)
        declining = trend_percentages.get('declining', 0)
        stable = trend_percentages.get('stable', 0)
        
        if improving > 40:
            return 'excellent'
        elif improving > 20 and declining < 20:
            return 'good'
        elif stable > 50:
            return 'stable'
        elif declining > 30:
            return 'concerning'
        else:
            return 'mixed'