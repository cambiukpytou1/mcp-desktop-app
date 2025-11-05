"""
Prompt Diff and Comparison Service
==================================

Advanced diff and comparison system for prompt versions with token-level analysis.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DiffType(Enum):
    """Types of differences in prompt comparison."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    MOVED = "moved"


class TokenType(Enum):
    """Types of tokens for analysis."""
    WORD = "word"
    PUNCTUATION = "punctuation"
    WHITESPACE = "whitespace"
    VARIABLE = "variable"
    INSTRUCTION = "instruction"
    EXAMPLE = "example"


@dataclass
class Token:
    """Represents a token in prompt content."""
    content: str
    token_type: TokenType
    position: int
    line_number: int
    column: int
    
    def __hash__(self):
        return hash((self.content, self.token_type))


@dataclass
class DiffChunk:
    """Represents a chunk of differences."""
    diff_type: DiffType
    old_tokens: List[Token] = field(default_factory=list)
    new_tokens: List[Token] = field(default_factory=list)
    old_start: int = 0
    old_end: int = 0
    new_start: int = 0
    new_end: int = 0
    context_before: List[Token] = field(default_factory=list)
    context_after: List[Token] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "diff_type": self.diff_type.value,
            "old_tokens": [{"content": t.content, "type": t.token_type.value} for t in self.old_tokens],
            "new_tokens": [{"content": t.content, "type": t.token_type.value} for t in self.new_tokens],
            "old_start": self.old_start,
            "old_end": self.old_end,
            "new_start": self.new_start,
            "new_end": self.new_end,
            "context_before": [{"content": t.content, "type": t.token_type.value} for t in self.context_before],
            "context_after": [{"content": t.content, "type": t.token_type.value} for t in self.context_after]
        }


@dataclass
class ComparisonResult:
    """Result of prompt comparison with detailed analysis."""
    version1_id: str
    version2_id: str
    similarity_score: float
    diff_chunks: List[DiffChunk] = field(default_factory=list)
    token_changes: Dict[str, int] = field(default_factory=dict)
    structural_changes: Dict[str, Any] = field(default_factory=dict)
    metadata_changes: Dict[str, Any] = field(default_factory=dict)
    performance_impact: Optional[Dict[str, float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version1_id": self.version1_id,
            "version2_id": self.version2_id,
            "similarity_score": self.similarity_score,
            "diff_chunks": [chunk.to_dict() for chunk in self.diff_chunks],
            "token_changes": self.token_changes,
            "structural_changes": self.structural_changes,
            "metadata_changes": self.metadata_changes,
            "performance_impact": self.performance_impact,
            "created_at": self.created_at.isoformat()
        }


class PromptDiffService:
    """Advanced diff and comparison service for prompts."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Patterns for token classification
        self.variable_pattern = re.compile(r'\{\{[^}]+\}\}|\{[^}]+\}|\$\{[^}]+\}')
        self.instruction_pattern = re.compile(r'(?:^|\n)(?:You are|Please|Task:|Instruction:|Role:|Context:)', re.IGNORECASE)
        self.example_pattern = re.compile(r'(?:Example|Sample|Instance):\s*', re.IGNORECASE)
        
        self.logger.info("Prompt diff service initialized")
    
    def tokenize_content(self, content: str) -> List[Token]:
        """Tokenize prompt content into structured tokens."""
        tokens = []
        lines = content.split('\n')
        position = 0
        
        for line_num, line in enumerate(lines, 1):
            column = 0
            i = 0
            
            while i < len(line):
                char = line[i]
                
                # Handle whitespace
                if char.isspace():
                    whitespace = ''
                    start_col = column
                    while i < len(line) and line[i].isspace():
                        whitespace += line[i]
                        i += 1
                        column += 1
                    
                    if whitespace:
                        tokens.append(Token(
                            content=whitespace,
                            token_type=TokenType.WHITESPACE,
                            position=position,
                            line_number=line_num,
                            column=start_col
                        ))
                        position += len(whitespace)
                    continue
                
                # Handle punctuation
                if not char.isalnum() and char not in '{}$':
                    tokens.append(Token(
                        content=char,
                        token_type=TokenType.PUNCTUATION,
                        position=position,
                        line_number=line_num,
                        column=column
                    ))
                    position += 1
                    column += 1
                    i += 1
                    continue
                
                # Handle words and variables
                word_start = i
                start_col = column
                
                # Check for variables
                if char in '{$':
                    # Find end of variable
                    brace_count = 0
                    while i < len(line):
                        if line[i] in '{':
                            brace_count += 1
                        elif line[i] in '}':
                            brace_count -= 1
                            if brace_count == 0:
                                i += 1
                                break
                        i += 1
                        column += 1
                    
                    variable_content = line[word_start:i]
                    tokens.append(Token(
                        content=variable_content,
                        token_type=TokenType.VARIABLE,
                        position=position,
                        line_number=line_num,
                        column=start_col
                    ))
                    position += len(variable_content)
                    continue
                
                # Handle regular words
                while i < len(line) and (char.isalnum() or char in '_-'):
                    i += 1
                    column += 1
                    if i < len(line):
                        char = line[i]
                
                word_content = line[word_start:i]
                
                # Classify token type
                token_type = TokenType.WORD
                if self.instruction_pattern.search(word_content):
                    token_type = TokenType.INSTRUCTION
                elif self.example_pattern.search(word_content):
                    token_type = TokenType.EXAMPLE
                
                tokens.append(Token(
                    content=word_content,
                    token_type=token_type,
                    position=position,
                    line_number=line_num,
                    column=start_col
                ))
                position += len(word_content)
            
            # Add newline token
            if line_num < len(lines):
                tokens.append(Token(
                    content='\n',
                    token_type=TokenType.WHITESPACE,
                    position=position,
                    line_number=line_num,
                    column=len(line)
                ))
                position += 1
        
        return tokens
    
    def compare_versions(self, version1_id: str, version2_id: str, 
                        include_performance: bool = False) -> ComparisonResult:
        """Compare two prompt versions with detailed analysis."""
        try:
            with self.db_manager.get_connection() as conn:
                # Get version data
                cursor = conn.execute("""
                    SELECT version_id, content, metadata_snapshot
                    FROM prompt_versions 
                    WHERE version_id IN (?, ?)
                """, (version1_id, version2_id))
                
                versions = {row["version_id"]: row for row in cursor.fetchall()}
                
                if len(versions) != 2:
                    raise ValueError("One or both versions not found")
                
                v1_data = versions[version1_id]
                v2_data = versions[version2_id]
                
                # Tokenize content
                v1_tokens = self.tokenize_content(v1_data["content"])
                v2_tokens = self.tokenize_content(v2_data["content"])
                
                # Generate diff chunks
                diff_chunks = self._generate_diff_chunks(v1_tokens, v2_tokens)
                
                # Calculate similarity score
                similarity_score = self._calculate_similarity(v1_tokens, v2_tokens)
                
                # Analyze token changes
                token_changes = self._analyze_token_changes(v1_tokens, v2_tokens)
                
                # Analyze structural changes
                structural_changes = self._analyze_structural_changes(v1_data["content"], v2_data["content"])
                
                # Compare metadata
                metadata_changes = {}
                if v1_data["metadata_snapshot"] and v2_data["metadata_snapshot"]:
                    import json
                    meta1 = json.loads(v1_data["metadata_snapshot"])
                    meta2 = json.loads(v2_data["metadata_snapshot"])
                    metadata_changes = self._compare_metadata(meta1, meta2)
                
                # Get performance impact if requested
                performance_impact = None
                if include_performance:
                    performance_impact = self._analyze_performance_impact(version1_id, version2_id)
                
                result = ComparisonResult(
                    version1_id=version1_id,
                    version2_id=version2_id,
                    similarity_score=similarity_score,
                    diff_chunks=diff_chunks,
                    token_changes=token_changes,
                    structural_changes=structural_changes,
                    metadata_changes=metadata_changes,
                    performance_impact=performance_impact
                )
                
                self.logger.info(f"Compared versions {version1_id} and {version2_id}")
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to compare versions: {e}")
            raise
    
    def _generate_diff_chunks(self, tokens1: List[Token], tokens2: List[Token]) -> List[DiffChunk]:
        """Generate diff chunks using Myers algorithm."""
        # Simplified implementation of Myers diff algorithm
        chunks = []
        
        # Create content arrays for comparison
        content1 = [t.content for t in tokens1]
        content2 = [t.content for t in tokens2]
        
        import difflib
        matcher = difflib.SequenceMatcher(None, content1, content2)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            
            chunk = DiffChunk(
                diff_type=DiffType.UNCHANGED if tag == 'equal' else 
                         DiffType.REMOVED if tag == 'delete' else
                         DiffType.ADDED if tag == 'insert' else
                         DiffType.MODIFIED,
                old_tokens=tokens1[i1:i2] if i1 < len(tokens1) else [],
                new_tokens=tokens2[j1:j2] if j1 < len(tokens2) else [],
                old_start=i1,
                old_end=i2,
                new_start=j1,
                new_end=j2
            )
            
            # Add context
            context_size = 3
            chunk.context_before = tokens1[max(0, i1-context_size):i1]
            chunk.context_after = tokens1[i2:min(len(tokens1), i2+context_size)]
            
            chunks.append(chunk)
        
        return chunks
    
    def _calculate_similarity(self, tokens1: List[Token], tokens2: List[Token]) -> float:
        """Calculate similarity score between token sequences."""
        if not tokens1 and not tokens2:
            return 1.0
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Use Jaccard similarity on token content
        set1 = set(t.content for t in tokens1 if t.token_type != TokenType.WHITESPACE)
        set2 = set(t.content for t in tokens2 if t.token_type != TokenType.WHITESPACE)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _analyze_token_changes(self, tokens1: List[Token], tokens2: List[Token]) -> Dict[str, int]:
        """Analyze changes in token types and counts."""
        changes = {
            "total_added": 0,
            "total_removed": 0,
            "words_added": 0,
            "words_removed": 0,
            "variables_added": 0,
            "variables_removed": 0,
            "instructions_added": 0,
            "instructions_removed": 0
        }
        
        # Count tokens by type
        def count_by_type(tokens):
            counts = {}
            for token in tokens:
                if token.token_type != TokenType.WHITESPACE:
                    counts[token.token_type] = counts.get(token.token_type, 0) + 1
            return counts
        
        counts1 = count_by_type(tokens1)
        counts2 = count_by_type(tokens2)
        
        # Calculate changes
        for token_type in TokenType:
            if token_type == TokenType.WHITESPACE:
                continue
                
            old_count = counts1.get(token_type, 0)
            new_count = counts2.get(token_type, 0)
            diff = new_count - old_count
            
            if diff > 0:
                changes[f"{token_type.value}s_added"] = diff
                changes["total_added"] += diff
            elif diff < 0:
                changes[f"{token_type.value}s_removed"] = abs(diff)
                changes["total_removed"] += abs(diff)
        
        return changes
    
    def _analyze_structural_changes(self, content1: str, content2: str) -> Dict[str, Any]:
        """Analyze structural changes in prompt content."""
        changes = {}
        
        # Line count changes
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')
        changes["line_count_change"] = len(lines2) - len(lines1)
        
        # Character count changes
        changes["character_count_change"] = len(content2) - len(content1)
        
        # Variable count changes
        vars1 = len(self.variable_pattern.findall(content1))
        vars2 = len(self.variable_pattern.findall(content2))
        changes["variable_count_change"] = vars2 - vars1
        
        # Instruction section changes
        instr1 = len(self.instruction_pattern.findall(content1))
        instr2 = len(self.instruction_pattern.findall(content2))
        changes["instruction_count_change"] = instr2 - instr1
        
        # Example section changes
        ex1 = len(self.example_pattern.findall(content1))
        ex2 = len(self.example_pattern.findall(content2))
        changes["example_count_change"] = ex2 - ex1
        
        return changes
    
    def _compare_metadata(self, meta1: Dict[str, Any], meta2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare metadata between versions."""
        changes = {}
        
        all_keys = set(meta1.keys()) | set(meta2.keys())
        
        for key in all_keys:
            val1 = meta1.get(key)
            val2 = meta2.get(key)
            
            if val1 != val2:
                changes[key] = {
                    "old_value": val1,
                    "new_value": val2,
                    "change_type": "modified" if key in meta1 and key in meta2 else
                                  "added" if key not in meta1 else "removed"
                }
        
        return changes
    
    def _analyze_performance_impact(self, version1_id: str, version2_id: str) -> Dict[str, float]:
        """Analyze performance impact between versions."""
        try:
            with self.db_manager.get_connection() as conn:
                # Get performance metrics for both versions
                cursor = conn.execute("""
                    SELECT version_id, average_score, success_rate, average_tokens,
                           average_cost, average_response_time, total_executions
                    FROM prompt_performance_metrics 
                    WHERE version_id IN (?, ?)
                """, (version1_id, version2_id))
                
                metrics = {row["version_id"]: row for row in cursor.fetchall()}
                
                if len(metrics) != 2:
                    return {"error": "Performance metrics not available for comparison"}
                
                v1_metrics = metrics[version1_id]
                v2_metrics = metrics[version2_id]
                
                impact = {}
                
                # Calculate percentage changes
                for metric in ["average_score", "success_rate", "average_tokens", 
                              "average_cost", "average_response_time"]:
                    old_val = v1_metrics[metric] or 0
                    new_val = v2_metrics[metric] or 0
                    
                    if old_val > 0:
                        change = ((new_val - old_val) / old_val) * 100
                        impact[f"{metric}_change_percent"] = round(change, 2)
                    else:
                        impact[f"{metric}_change_percent"] = 0.0
                
                return impact
                
        except Exception as e:
            self.logger.error(f"Failed to analyze performance impact: {e}")
            return {"error": str(e)}
    
    def generate_visual_diff(self, comparison: ComparisonResult) -> Dict[str, Any]:
        """Generate visual diff representation for UI display."""
        visual_diff = {
            "summary": {
                "similarity_score": comparison.similarity_score,
                "total_chunks": len(comparison.diff_chunks),
                "token_changes": comparison.token_changes
            },
            "chunks": [],
            "metadata_changes": comparison.metadata_changes,
            "structural_changes": comparison.structural_changes
        }
        
        for chunk in comparison.diff_chunks:
            visual_chunk = {
                "type": chunk.diff_type.value,
                "old_content": "".join(t.content for t in chunk.old_tokens),
                "new_content": "".join(t.content for t in chunk.new_tokens),
                "context_before": "".join(t.content for t in chunk.context_before),
                "context_after": "".join(t.content for t in chunk.context_after),
                "line_numbers": {
                    "old_start": chunk.old_tokens[0].line_number if chunk.old_tokens else 0,
                    "new_start": chunk.new_tokens[0].line_number if chunk.new_tokens else 0
                }
            }
            visual_diff["chunks"].append(visual_chunk)
        
        return visual_diff
    
    def export_diff_report(self, comparison: ComparisonResult, format: str = "html") -> str:
        """Export diff comparison as a formatted report."""
        if format == "html":
            return self._generate_html_report(comparison)
        elif format == "markdown":
            return self._generate_markdown_report(comparison)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_html_report(self, comparison: ComparisonResult) -> str:
        """Generate HTML diff report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Prompt Version Comparison</title>
            <style>
                .diff-added {{ background-color: #d4edda; }}
                .diff-removed {{ background-color: #f8d7da; }}
                .diff-modified {{ background-color: #fff3cd; }}
                .similarity-score {{ font-size: 1.2em; font-weight: bold; }}
                .chunk {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <h1>Prompt Version Comparison</h1>
            <p class="similarity-score">Similarity Score: {comparison.similarity_score:.2%}</p>
            
            <h2>Changes Summary</h2>
            <ul>
        """
        
        for key, value in comparison.token_changes.items():
            if value > 0:
                html += f"<li>{key.replace('_', ' ').title()}: {value}</li>"
        
        html += "</ul><h2>Detailed Changes</h2>"
        
        for i, chunk in enumerate(comparison.diff_chunks):
            html += f"""
            <div class="chunk diff-{chunk.diff_type.value}">
                <h3>Change {i+1} ({chunk.diff_type.value})</h3>
                <pre>{chunk.context_before and ''.join(t.content for t in chunk.context_before)}
<span class="diff-removed">{''.join(t.content for t in chunk.old_tokens)}</span>
<span class="diff-added">{''.join(t.content for t in chunk.new_tokens)}</span>
{chunk.context_after and ''.join(t.content for t in chunk.context_after)}</pre>
            </div>
            """
        
        html += "</body></html>"
        return html
    
    def _generate_markdown_report(self, comparison: ComparisonResult) -> str:
        """Generate Markdown diff report."""
        md = f"""# Prompt Version Comparison

**Similarity Score:** {comparison.similarity_score:.2%}

## Changes Summary

"""
        
        for key, value in comparison.token_changes.items():
            if value > 0:
                md += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        md += "\n## Detailed Changes\n\n"
        
        for i, chunk in enumerate(comparison.diff_chunks):
            md += f"""### Change {i+1} ({chunk.diff_type.value})

```diff
{chunk.context_before and ''.join(t.content for t in chunk.context_before)}
- {''.join(t.content for t in chunk.old_tokens)}
+ {''.join(t.content for t in chunk.new_tokens)}
{chunk.context_after and ''.join(t.content for t in chunk.context_after)}
```

"""
        
        return md