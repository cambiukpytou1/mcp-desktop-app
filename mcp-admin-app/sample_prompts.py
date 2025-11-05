"""
Sample Prompt Templates
======================

Script to create sample prompt templates for demonstration.
"""

from datetime import datetime
from models.prompt import PromptTemplate
from models.base import PromptParameter
from services.prompt_manager import PromptManager
from core.config import ConfigurationManager
from data.database import DatabaseManager


def create_sample_prompts():
    """Create sample prompt templates."""
    
    # Initialize managers
    config_manager = ConfigurationManager()
    db_manager = DatabaseManager(config_manager)
    prompt_manager = PromptManager(config_manager, db_manager)
    
    # Sample 1: Code Review Prompt
    code_review_template = PromptTemplate()
    code_review_template.name = "Code Review Assistant"
    code_review_template.description = "Comprehensive code review with suggestions for improvement"
    code_review_template.content = """Please review the following {language} code and provide feedback:

Code to review:
```{language}
{code}
```

Please analyze:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Suggestions for improvement

Focus areas: {focus_areas}
"""
    code_review_template.parameters = [
        PromptParameter(name="language", type="string", description="Programming language", required=True),
        PromptParameter(name="code", type="string", description="Code to review", required=True),
        PromptParameter(name="focus_areas", type="string", description="Specific areas to focus on", required=False, default="general review")
    ]
    code_review_template.tags = ["code", "review", "development", "quality"]
    
    # Sample 2: Documentation Generator
    doc_generator_template = PromptTemplate()
    doc_generator_template.name = "API Documentation Generator"
    doc_generator_template.description = "Generate comprehensive API documentation from code"
    doc_generator_template.content = """Generate API documentation for the following {api_type} endpoint:

Endpoint: {endpoint}
Method: {method}
Function/Handler:
```{language}
{code}
```

Please provide:
1. Endpoint description
2. Parameters (query, path, body)
3. Response format
4. Example request/response
5. Error codes and descriptions

Documentation format: {format}
"""
    doc_generator_template.parameters = [
        PromptParameter(name="api_type", type="string", description="API type (REST, GraphQL, etc.)", required=True, default="REST"),
        PromptParameter(name="endpoint", type="string", description="API endpoint path", required=True),
        PromptParameter(name="method", type="string", description="HTTP method", required=True),
        PromptParameter(name="language", type="string", description="Programming language", required=True),
        PromptParameter(name="code", type="string", description="Handler code", required=True),
        PromptParameter(name="format", type="string", description="Documentation format", required=False, default="Markdown")
    ]
    doc_generator_template.tags = ["documentation", "api", "development", "markdown"]
    
    # Sample 3: Test Case Generator
    test_generator_template = PromptTemplate()
    test_generator_template.name = "Unit Test Generator"
    test_generator_template.description = "Generate comprehensive unit tests for functions"
    test_generator_template.content = """Generate unit tests for the following {language} function:

Function to test:
```{language}
{function_code}
```

Requirements:
- Test framework: {test_framework}
- Coverage: {coverage_type}
- Include edge cases: {include_edge_cases}
- Mock dependencies: {mock_dependencies}

Please generate:
1. Test setup and teardown
2. Happy path tests
3. Error condition tests
4. Edge case tests
5. Mock configurations (if needed)
"""
    test_generator_template.parameters = [
        PromptParameter(name="language", type="string", description="Programming language", required=True),
        PromptParameter(name="function_code", type="string", description="Function code to test", required=True),
        PromptParameter(name="test_framework", type="string", description="Testing framework", required=True),
        PromptParameter(name="coverage_type", type="string", description="Coverage requirements", required=False, default="comprehensive"),
        PromptParameter(name="include_edge_cases", type="boolean", description="Include edge case tests", required=False, default="true"),
        PromptParameter(name="mock_dependencies", type="boolean", description="Mock external dependencies", required=False, default="true")
    ]
    test_generator_template.tags = ["testing", "unit-tests", "development", "quality"]
    
    # Sample 4: Bug Report Analyzer
    bug_analyzer_template = PromptTemplate()
    bug_analyzer_template.name = "Bug Report Analyzer"
    bug_analyzer_template.description = "Analyze bug reports and suggest investigation steps"
    bug_analyzer_template.content = """Analyze the following bug report and provide investigation guidance:

Bug Report:
Title: {title}
Description: {description}
Steps to Reproduce: {steps}
Expected Behavior: {expected}
Actual Behavior: {actual}
Environment: {environment}
Priority: {priority}

Please provide:
1. Root cause analysis suggestions
2. Investigation steps
3. Potential fixes
4. Similar known issues
5. Testing recommendations

Focus on: {focus_area}
"""
    bug_analyzer_template.parameters = [
        PromptParameter(name="title", type="string", description="Bug title", required=True),
        PromptParameter(name="description", type="string", description="Bug description", required=True),
        PromptParameter(name="steps", type="string", description="Steps to reproduce", required=True),
        PromptParameter(name="expected", type="string", description="Expected behavior", required=True),
        PromptParameter(name="actual", type="string", description="Actual behavior", required=True),
        PromptParameter(name="environment", type="string", description="Environment details", required=False),
        PromptParameter(name="priority", type="string", description="Bug priority", required=False, default="medium"),
        PromptParameter(name="focus_area", type="string", description="Investigation focus", required=False, default="root cause analysis")
    ]
    bug_analyzer_template.tags = ["debugging", "analysis", "troubleshooting", "support"]
    
    # Sample 5: Database Query Optimizer
    query_optimizer_template = PromptTemplate()
    query_optimizer_template.name = "SQL Query Optimizer"
    query_optimizer_template.description = "Analyze and optimize SQL queries for better performance"
    query_optimizer_template.content = """Optimize the following SQL query for better performance:

Database: {database_type}
Query:
```sql
{query}
```

Table schemas (if available):
{schemas}

Current performance issues: {issues}

Please provide:
1. Performance analysis
2. Optimization suggestions
3. Index recommendations
4. Query rewrite options
5. Execution plan analysis

Target optimization: {optimization_goal}
"""
    query_optimizer_template.parameters = [
        PromptParameter(name="database_type", type="string", description="Database system", required=True),
        PromptParameter(name="query", type="string", description="SQL query to optimize", required=True),
        PromptParameter(name="schemas", type="string", description="Table schemas", required=False),
        PromptParameter(name="issues", type="string", description="Current performance issues", required=False),
        PromptParameter(name="optimization_goal", type="string", description="Optimization target", required=False, default="general performance")
    ]
    query_optimizer_template.tags = ["sql", "database", "optimization", "performance"]
    
    # Create all templates
    templates = [
        code_review_template,
        doc_generator_template,
        test_generator_template,
        bug_analyzer_template,
        query_optimizer_template
    ]
    
    created_count = 0
    for template in templates:
        try:
            prompt_manager.create_template(template, "system")
            created_count += 1
            print(f"Created template: {template.name}")
        except Exception as e:
            print(f"Error creating template {template.name}: {e}")
    
    print(f"\nCreated {created_count} sample templates successfully!")
    return created_count


if __name__ == "__main__":
    create_sample_prompts()