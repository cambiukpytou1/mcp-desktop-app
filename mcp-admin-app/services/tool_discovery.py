"""
Tool Discovery Engine
====================

Automatic detection, classification, and metadata extraction for MCP tools.
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from models.tool import (
    DiscoveredTool, ToolCategory, ToolRegistryEntry, ToolParameter, 
    ToolMetadata, ValidationRule, SecurityLevel, ToolStatus
)
from models.server import MCPServer


logger = logging.getLogger(__name__)


@dataclass
class ToolAnalysis:
    """Tool analysis results."""
    category: ToolCategory
    confidence: float
    security_level: SecurityLevel
    extracted_metadata: Dict[str, Any]
    suggested_parameters: List[ToolParameter]
    performance_hints: Dict[str, Any]


@dataclass
class ToolChange:
    """Tool change detection result."""
    tool_name: str
    change_type: str  # "added", "removed", "modified"
    old_schema: Optional[Dict[str, Any]] = None
    new_schema: Optional[Dict[str, Any]] = None
    detected_at: datetime = None


@dataclass
class DiscoveryStatus:
    """Discovery scan status."""
    server_id: str
    last_scan: Optional[datetime] = None
    tools_discovered: int = 0
    tools_added: int = 0
    tools_updated: int = 0
    tools_removed: int = 0
    scan_duration: float = 0.0
    errors: List[str] = None


class ToolDiscoveryEngine:
    """Engine for discovering and analyzing MCP tools."""
    
    def __init__(self):
        self.category_patterns = self._initialize_category_patterns()
        self.security_patterns = self._initialize_security_patterns()
        self.parameter_type_mapping = self._initialize_parameter_mapping()
        
    def _initialize_category_patterns(self) -> Dict[ToolCategory, List[str]]:
        """Initialize category classification patterns."""
        return {
            ToolCategory.FILE_OPERATIONS: [
                r'file|read|write|copy|move|delete|upload|download',
                r'directory|folder|path|filesystem',
                r'csv|json|xml|yaml|txt|pdf'
            ],
            ToolCategory.WEB_SEARCH: [
                r'search|query|find|lookup',
                r'web|internet|url|http|api',
                r'google|bing|duckduckgo'
            ],
            ToolCategory.CODE_ANALYSIS: [
                r'code|analyze|parse|compile|lint',
                r'python|javascript|java|cpp|rust',
                r'ast|syntax|semantic|static'
            ],
            ToolCategory.DATA_PROCESSING: [
                r'data|process|transform|convert',
                r'sql|database|query|aggregate',
                r'filter|sort|group|merge'
            ],
            ToolCategory.API_INTEGRATION: [
                r'api|rest|graphql|webhook',
                r'http|request|response|endpoint',
                r'oauth|auth|token|key'
            ],
            ToolCategory.SYSTEM_TOOLS: [
                r'system|process|service|daemon',
                r'monitor|status|health|ping',
                r'shell|command|execute|run'
            ],
            ToolCategory.COMMUNICATION: [
                r'email|send|notify|message',
                r'slack|discord|teams|chat',
                r'sms|phone|call|alert'
            ],
            ToolCategory.PRODUCTIVITY: [
                r'calendar|schedule|task|todo',
                r'note|document|template|format',
                r'time|date|reminder|deadline'
            ],
            ToolCategory.SECURITY: [
                r'security|encrypt|decrypt|hash',
                r'password|credential|certificate|key',
                r'scan|vulnerability|audit|compliance'
            ],
            ToolCategory.MONITORING: [
                r'monitor|watch|track|observe',
                r'metric|log|event|alert',
                r'performance|usage|statistics'
            ]
        }
    
    def _initialize_security_patterns(self) -> Dict[SecurityLevel, List[str]]:
        """Initialize security level patterns."""
        return {
            SecurityLevel.RESTRICTED: [
                r'delete|remove|destroy|kill',
                r'admin|root|sudo|privilege',
                r'system|kernel|registry|config'
            ],
            SecurityLevel.HIGH: [
                r'write|modify|update|change',
                r'execute|run|launch|start',
                r'network|internet|external'
            ],
            SecurityLevel.MEDIUM: [
                r'read|get|fetch|retrieve',
                r'search|find|query|list',
                r'analyze|process|transform'
            ],
            SecurityLevel.LOW: [
                r'view|display|show|format',
                r'validate|check|verify|test',
                r'calculate|compute|convert'
            ]
        }
    
    def _initialize_parameter_mapping(self) -> Dict[str, str]:
        """Initialize parameter type mapping."""
        return {
            'string': 'str',
            'integer': 'int',
            'number': 'float',
            'boolean': 'bool',
            'array': 'list',
            'object': 'dict'
        }
    
    def scan_server_tools(self, server_id: str) -> List[DiscoveredTool]:
        """Scan MCP server for available tools."""
        logger.info(f"Scanning server {server_id} for tools")
        
        try:
            # In a real implementation, this would connect to the MCP server
            # and retrieve the actual tool list. For now, we'll simulate this.
            discovered_tools = self._simulate_tool_discovery(server_id)
            
            logger.info(f"Discovered {len(discovered_tools)} tools from server {server_id}")
            return discovered_tools
            
        except Exception as e:
            logger.error(f"Error scanning server {server_id}: {e}")
            return []
    
    def _simulate_tool_discovery(self, server_id: str) -> List[DiscoveredTool]:
        """Simulate tool discovery for demonstration."""
        # Sample tools that might be discovered
        sample_tools = [
            {
                "name": "file_read",
                "description": "Read contents of a file from the filesystem",
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "file_read",
                        "description": "Read contents of a file",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Path to the file to read"
                                },
                                "encoding": {
                                    "type": "string",
                                    "description": "File encoding",
                                    "default": "utf-8"
                                }
                            },
                            "required": ["path"]
                        }
                    }
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for information",
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web using a search engine",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results",
                                    "default": 10
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }
            },
            {
                "name": "code_analyze",
                "description": "Analyze Python code for issues and suggestions",
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "code_analyze",
                        "description": "Analyze Python code",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": "Python code to analyze"
                                },
                                "check_style": {
                                    "type": "boolean",
                                    "description": "Check code style",
                                    "default": True
                                }
                            },
                            "required": ["code"]
                        }
                    }
                }
            }
        ]
        
        discovered_tools = []
        for tool_data in sample_tools:
            analysis = self.analyze_tool_schema(tool_data["schema"])
            
            discovered_tool = DiscoveredTool(
                name=tool_data["name"],
                description=tool_data["description"],
                schema=tool_data["schema"],
                server_id=server_id,
                classification_confidence=analysis.confidence,
                suggested_category=analysis.category,
                metadata_extracted=analysis.extracted_metadata
            )
            discovered_tools.append(discovered_tool)
        
        return discovered_tools
    
    def analyze_tool_schema(self, tool_schema: Dict[str, Any]) -> ToolAnalysis:
        """Analyze tool schema and extract metadata."""
        try:
            # Extract basic information
            function_info = tool_schema.get("function", {})
            name = function_info.get("name", "")
            description = function_info.get("description", "")
            parameters = function_info.get("parameters", {})
            
            # Classify tool category
            category, confidence = self._classify_tool_category(name, description)
            
            # Determine security level
            security_level = self._determine_security_level(name, description)
            
            # Extract parameter information
            suggested_parameters = self._extract_parameters(parameters)
            
            # Extract metadata
            metadata = self._extract_metadata(name, description, parameters)
            
            # Generate performance hints
            performance_hints = self._generate_performance_hints(name, description, parameters)
            
            return ToolAnalysis(
                category=category,
                confidence=confidence,
                security_level=security_level,
                extracted_metadata=metadata,
                suggested_parameters=suggested_parameters,
                performance_hints=performance_hints
            )
            
        except Exception as e:
            logger.error(f"Error analyzing tool schema: {e}")
            return ToolAnalysis(
                category=ToolCategory.GENERAL,
                confidence=0.0,
                security_level=SecurityLevel.MEDIUM,
                extracted_metadata={},
                suggested_parameters=[],
                performance_hints={}
            )
    
    def _classify_tool_category(self, name: str, description: str) -> Tuple[ToolCategory, float]:
        """Classify tool into category based on name and description."""
        text = f"{name} {description}".lower()
        
        category_scores = {}
        for category, patterns in self.category_patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, text))
                score += matches * (1.0 / len(patterns))
            category_scores[category] = score
        
        if not category_scores or max(category_scores.values()) == 0:
            return ToolCategory.GENERAL, 0.0
        
        best_category = max(category_scores, key=category_scores.get)
        confidence = min(category_scores[best_category], 1.0)
        
        return best_category, confidence
    
    def _determine_security_level(self, name: str, description: str) -> SecurityLevel:
        """Determine security level based on tool functionality."""
        text = f"{name} {description}".lower()
        
        for level, patterns in self.security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return level
        
        return SecurityLevel.MEDIUM
    
    def _extract_parameters(self, parameters_schema: Dict[str, Any]) -> List[ToolParameter]:
        """Extract parameter information from schema."""
        parameters = []
        
        properties = parameters_schema.get("properties", {})
        required = parameters_schema.get("required", [])
        
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "string")
            description = param_info.get("description", "")
            default_value = param_info.get("default")
            
            # Create validation rules based on schema
            validation_rules = []
            if "enum" in param_info:
                validation_rules.append(ValidationRule(
                    rule_type="enum",
                    value=param_info["enum"],
                    error_message=f"Value must be one of: {param_info['enum']}"
                ))
            
            if param_type == "integer" and "minimum" in param_info:
                validation_rules.append(ValidationRule(
                    rule_type="range",
                    value={"min": param_info["minimum"]},
                    error_message=f"Value must be >= {param_info['minimum']}"
                ))
            
            parameter = ToolParameter(
                name=param_name,
                type=self.parameter_type_mapping.get(param_type, param_type),
                description=description,
                required=param_name in required,
                default_value=default_value,
                validation_rules=validation_rules,
                examples=[],
                sensitive="password" in param_name.lower() or "key" in param_name.lower()
            )
            parameters.append(parameter)
        
        return parameters
    
    def _extract_metadata(self, name: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from tool information."""
        metadata = {
            "complexity": "simple",
            "estimated_execution_time": "fast",
            "resource_requirements": "low"
        }
        
        # Determine complexity based on parameter count
        param_count = len(parameters.get("properties", {}))
        if param_count > 5:
            metadata["complexity"] = "complex"
        elif param_count > 2:
            metadata["complexity"] = "moderate"
        
        # Estimate execution time based on tool type
        if any(keyword in name.lower() for keyword in ["search", "web", "api", "network"]):
            metadata["estimated_execution_time"] = "slow"
        elif any(keyword in name.lower() for keyword in ["file", "read", "write"]):
            metadata["estimated_execution_time"] = "moderate"
        
        # Estimate resource requirements
        if any(keyword in name.lower() for keyword in ["analyze", "process", "compile"]):
            metadata["resource_requirements"] = "high"
        elif any(keyword in name.lower() for keyword in ["search", "query", "transform"]):
            metadata["resource_requirements"] = "moderate"
        
        return metadata
    
    def _generate_performance_hints(self, name: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance optimization hints."""
        hints = {}
        
        # Caching hints
        if any(keyword in name.lower() for keyword in ["search", "lookup", "get"]):
            hints["cacheable"] = True
            hints["cache_duration"] = 300  # 5 minutes
        
        # Batching hints
        if any(keyword in name.lower() for keyword in ["process", "analyze", "transform"]):
            hints["batchable"] = True
            hints["optimal_batch_size"] = 10
        
        # Timeout hints
        if any(keyword in name.lower() for keyword in ["web", "api", "network"]):
            hints["timeout"] = 30  # 30 seconds
        else:
            hints["timeout"] = 10  # 10 seconds
        
        return hints
    
    def categorize_tool_automatically(self, tool_info: DiscoveredTool) -> ToolCategory:
        """Automatically categorize a discovered tool."""
        analysis = self.analyze_tool_schema(tool_info.schema)
        return analysis.category
    
    def detect_tool_changes(self, server_id: str) -> List[ToolChange]:
        """Detect changes in tools from a server."""
        # In a real implementation, this would compare current tools
        # with previously discovered tools to detect changes
        logger.info(f"Detecting tool changes for server {server_id}")
        
        # Simulate some changes for demonstration
        changes = [
            ToolChange(
                tool_name="example_tool",
                change_type="modified",
                detected_at=datetime.now()
            )
        ]
        
        return changes
    
    def schedule_discovery_scan(self, server_id: str, interval: int) -> bool:
        """Schedule periodic discovery scans for a server."""
        logger.info(f"Scheduling discovery scan for server {server_id} every {interval} seconds")
        # In a real implementation, this would set up a scheduled task
        return True
    
    def get_discovery_status(self, server_id: str) -> DiscoveryStatus:
        """Get discovery status for a server."""
        # In a real implementation, this would return actual status
        return DiscoveryStatus(
            server_id=server_id,
            last_scan=datetime.now(),
            tools_discovered=3,
            tools_added=3,
            tools_updated=0,
            tools_removed=0,
            scan_duration=1.5,
            errors=[]
        )
    
    def extract_tool_metadata(self, tool_schema: Dict[str, Any]) -> ToolMetadata:
        """Extract comprehensive metadata from tool schema."""
        analysis = self.analyze_tool_schema(tool_schema)
        
        return ToolMetadata(
            version="1.0.0",
            author="Unknown",
            documentation_url="",
            source_url="",
            license="Unknown",
            tags=self._generate_tags(tool_schema),
            dependencies=[],
            compatibility={"mcp_version": "1.0"},
            performance_hints=analysis.performance_hints
        )
    
    def _generate_tags(self, tool_schema: Dict[str, Any]) -> List[str]:
        """Generate comprehensive tags based on tool schema."""
        tags = []
        
        function_info = tool_schema.get("function", {})
        name = function_info.get("name", "").lower()
        description = function_info.get("description", "").lower()
        parameters = function_info.get("parameters", {}).get("properties", {})
        
        # Enhanced tag keywords with more categories
        tag_keywords = {
            # Core functionality tags
            "file": ["file", "filesystem", "read", "write", "upload", "download"],
            "web": ["web", "http", "api", "url", "request", "fetch"],
            "data": ["data", "process", "transform", "convert", "parse"],
            "search": ["search", "find", "query", "lookup", "discover"],
            "analysis": ["analyze", "check", "validate", "inspect", "audit"],
            "security": ["security", "encrypt", "decrypt", "auth", "permission"],
            "database": ["database", "sql", "query", "table", "record"],
            "network": ["network", "ping", "connect", "socket", "protocol"],
            "system": ["system", "process", "service", "monitor", "status"],
            "text": ["text", "string", "format", "template", "markdown"],
            "image": ["image", "photo", "picture", "visual", "graphic"],
            "email": ["email", "mail", "send", "notify", "message"],
            "time": ["time", "date", "schedule", "calendar", "timer"],
            "math": ["math", "calculate", "compute", "formula", "number"],
            "ai": ["ai", "ml", "model", "predict", "classify", "generate"],
            
            # Technology tags
            "python": ["python", "py", "pip", "conda"],
            "javascript": ["javascript", "js", "node", "npm"],
            "json": ["json", "parse", "stringify"],
            "xml": ["xml", "html", "xpath", "dom"],
            "csv": ["csv", "spreadsheet", "excel"],
            "pdf": ["pdf", "document", "report"],
            "git": ["git", "repository", "commit", "branch"],
            "docker": ["docker", "container", "image"],
            "cloud": ["aws", "azure", "gcp", "cloud", "s3"],
            
            # Action tags
            "create": ["create", "make", "generate", "build"],
            "read": ["read", "get", "fetch", "retrieve", "load"],
            "update": ["update", "modify", "change", "edit", "patch"],
            "delete": ["delete", "remove", "destroy", "clean"],
            "list": ["list", "show", "display", "enumerate"],
            "copy": ["copy", "duplicate", "clone", "backup"],
            "move": ["move", "transfer", "migrate", "relocate"],
            "sync": ["sync", "synchronize", "mirror", "replicate"]
        }
        
        text = f"{name} {description}"
        
        # Add tags based on name and description
        for tag, keywords in tag_keywords.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)
        
        # Add tags based on parameters
        for param_name, param_info in parameters.items():
            param_text = f"{param_name} {param_info.get('description', '')}".lower()
            
            # Parameter-specific tags
            if "path" in param_text or "file" in param_text:
                tags.append("file")
            if "url" in param_text or "endpoint" in param_text:
                tags.append("web")
            if "query" in param_text or "search" in param_text:
                tags.append("search")
            if "password" in param_text or "key" in param_text or "token" in param_text:
                tags.append("security")
            if "email" in param_text or "address" in param_text:
                tags.append("email")
        
        # Add complexity tags
        param_count = len(parameters)
        if param_count == 0:
            tags.append("simple")
        elif param_count <= 3:
            tags.append("moderate")
        else:
            tags.append("complex")
        
        # Add format tags based on expected inputs/outputs
        if any(keyword in text for keyword in ["json", "parse", "stringify"]):
            tags.append("json")
        if any(keyword in text for keyword in ["xml", "html", "xpath"]):
            tags.append("xml")
        if any(keyword in text for keyword in ["csv", "spreadsheet"]):
            tags.append("csv")
        
        # Remove duplicates and return
        return list(set(tags))
    
    def get_related_tools(self, tool_name: str, tool_tags: List[str], 
                         all_tools: List[ToolRegistryEntry]) -> List[str]:
        """Find tools related to the given tool based on tags and functionality."""
        related = []
        
        for tool in all_tools:
            if tool.name == tool_name:
                continue
            
            # Calculate similarity based on shared tags
            tool_tags_set = set(tool_tags)
            other_tags_set = set(tool.metadata.tags)
            
            shared_tags = tool_tags_set.intersection(other_tags_set)
            similarity = len(shared_tags) / max(len(tool_tags_set), len(other_tags_set), 1)
            
            # Also check category similarity
            if hasattr(tool, 'category') and similarity > 0.3:
                related.append({
                    "name": tool.name,
                    "similarity": similarity,
                    "shared_tags": list(shared_tags)
                })
        
        # Sort by similarity and return top matches
        related.sort(key=lambda x: x["similarity"], reverse=True)
        return related[:5]
    
    def suggest_tool_improvements(self, tool: ToolRegistryEntry) -> List[str]:
        """Suggest improvements for a tool based on analysis."""
        suggestions = []
        
        # Check if tool has description
        if not tool.description or len(tool.description) < 20:
            suggestions.append("Add a more detailed description")
        
        # Check if tool has tags
        if not tool.metadata.tags:
            suggestions.append("Add relevant tags for better discoverability")
        
        # Check parameter documentation
        poorly_documented_params = []
        for param in tool.parameters:
            if not param.description or len(param.description) < 10:
                poorly_documented_params.append(param.name)
        
        if poorly_documented_params:
            suggestions.append(f"Improve documentation for parameters: {', '.join(poorly_documented_params)}")
        
        # Check for examples
        params_without_examples = []
        for param in tool.parameters:
            if param.required and not param.examples:
                params_without_examples.append(param.name)
        
        if params_without_examples:
            suggestions.append(f"Add examples for required parameters: {', '.join(params_without_examples)}")
        
        # Check security level appropriateness
        if tool.security_level == SecurityLevel.LOW and any(
            keyword in tool.name.lower() for keyword in ["delete", "remove", "destroy", "admin"]
        ):
            suggestions.append("Consider increasing security level for potentially destructive operations")
        
        # Performance suggestions
        if tool.average_execution_time > 10.0:
            suggestions.append("Consider optimizing for better performance (current avg: {:.2f}s)".format(
                tool.average_execution_time
            ))
        
        if tool.success_rate < 0.9:
            suggestions.append("Investigate and fix reliability issues (current success rate: {:.1%})".format(
                tool.success_rate
            ))
        
        return suggestions
    
    def auto_categorize_batch(self, tools: List[ToolRegistryEntry]) -> Dict[str, ToolCategory]:
        """Automatically categorize a batch of tools."""
        categorizations = {}
        
        for tool in tools:
            try:
                analysis = self.analyze_tool_schema(tool.schema)
                categorizations[tool.id] = analysis.category
            except Exception as e:
                logger.error(f"Error categorizing tool {tool.name}: {e}")
                categorizations[tool.id] = ToolCategory.GENERAL
        
        return categorizations
    
    def generate_tool_recommendations(self, user_context: Dict[str, Any], 
                                    available_tools: List[ToolRegistryEntry]) -> List[Dict[str, Any]]:
        """Generate tool recommendations based on user context."""
        recommendations = []
        
        user_query = user_context.get("query", "").lower()
        user_category = user_context.get("preferred_category")
        user_security_level = user_context.get("max_security_level", SecurityLevel.HIGH)
        
        for tool in available_tools:
            if not tool.enabled or tool.status != ToolStatus.AVAILABLE:
                continue
            
            # Skip tools that exceed user's security level
            security_levels = [SecurityLevel.LOW, SecurityLevel.MEDIUM, SecurityLevel.HIGH, SecurityLevel.RESTRICTED]
            if security_levels.index(tool.security_level) > security_levels.index(user_security_level):
                continue
            
            score = 0.0
            reasons = []
            
            # Score based on query match
            if user_query:
                query_words = user_query.split()
                tool_text = f"{tool.name} {tool.description} {' '.join(tool.metadata.tags)}".lower()
                
                matches = sum(1 for word in query_words if word in tool_text)
                if matches > 0:
                    score += (matches / len(query_words)) * 0.4
                    reasons.append(f"Matches {matches}/{len(query_words)} query terms")
            
            # Score based on category preference
            if user_category and tool.category == user_category:
                score += 0.3
                reasons.append("Matches preferred category")
            
            # Score based on popularity and reliability
            if tool.usage_count > 0:
                popularity_score = min(tool.usage_count / 100, 0.2)  # Max 0.2 points
                score += popularity_score
                reasons.append(f"Popular tool ({tool.usage_count} uses)")
            
            if tool.success_rate > 0.9:
                score += 0.1
                reasons.append(f"High reliability ({tool.success_rate:.1%})")
            
            if score > 0.2:  # Minimum threshold
                recommendations.append({
                    "tool": tool,
                    "score": score,
                    "reasons": reasons
                })
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:10]
    
    def scan_server_tools(self, server_id: str) -> List[DiscoveredTool]:
        """Scan a server for available tools."""
        try:
            # In a real implementation, this would connect to the MCP server
            # and discover actual tools. For now, we'll return mock tools.
            
            logger.info(f"Scanning server {server_id} for tools")
            
            # Mock discovered tools for testing
            mock_tools = [
                DiscoveredTool(
                    name="file_reader",
                    description="Read files from the filesystem",
                    schema={
                        "type": "function",
                        "function": {
                            "name": "file_reader",
                            "description": "Read files from the filesystem",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "path": {
                                        "type": "string",
                                        "description": "Path to the file to read"
                                    }
                                },
                                "required": ["path"]
                            }
                        }
                    },
                    server_id=server_id
                ),
                DiscoveredTool(
                    name="web_search",
                    description="Search the web for information",
                    schema={
                        "type": "function",
                        "function": {
                            "name": "web_search",
                            "description": "Search the web for information",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "Search query"
                                    },
                                    "limit": {
                                        "type": "integer",
                                        "description": "Maximum number of results",
                                        "default": 10
                                    }
                                },
                                "required": ["query"]
                            }
                        }
                    },
                    server_id=server_id
                )
            ]
            
            logger.info(f"Discovered {len(mock_tools)} tools from server {server_id}")
            return mock_tools
            
        except Exception as e:
            logger.error(f"Error scanning server {server_id}: {e}")
            return []
    
    def discover_tools_from_server(self, server_id: str) -> List[DiscoveredTool]:
        """Discover tools from a specific server (alias for scan_server_tools)."""
        return self.scan_server_tools(server_id)