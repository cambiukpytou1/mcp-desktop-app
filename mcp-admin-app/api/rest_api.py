"""
REST API Framework for MCP Admin Application
===========================================

FastAPI-based REST API for external integrations.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

from .auth import AuthenticationManager
from .middleware import SecurityMiddleware, LoggingMiddleware


# Pydantic models for API requests/responses
class PromptCreateRequest(BaseModel):
    """Request model for creating a prompt."""
    name: str = Field(..., description="Prompt name")
    content: str = Field(..., description="Prompt content")
    description: Optional[str] = Field(None, description="Prompt description")
    category: Optional[str] = Field(None, description="Prompt category")
    tags: List[str] = Field(default_factory=list, description="Prompt tags")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Prompt variables")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PromptUpdateRequest(BaseModel):
    """Request model for updating a prompt."""
    name: Optional[str] = Field(None, description="Prompt name")
    content: Optional[str] = Field(None, description="Prompt content")
    description: Optional[str] = Field(None, description="Prompt description")
    category: Optional[str] = Field(None, description="Prompt category")
    tags: Optional[List[str]] = Field(None, description="Prompt tags")
    variables: Optional[Dict[str, Any]] = Field(None, description="Prompt variables")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PromptResponse(BaseModel):
    """Response model for prompt data."""
    id: str
    name: str
    content: str
    description: Optional[str]
    category: Optional[str]
    tags: List[str]
    variables: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    version: str


class EvaluationRequest(BaseModel):
    """Request model for prompt evaluation."""
    prompt_id: str = Field(..., description="Prompt ID to evaluate")
    test_data: List[Dict[str, Any]] = Field(..., description="Test data for evaluation")
    models: List[str] = Field(..., description="Models to test against")
    scoring_criteria: Dict[str, Any] = Field(default_factory=dict, description="Scoring criteria")


class EvaluationResponse(BaseModel):
    """Response model for evaluation results."""
    evaluation_id: str
    prompt_id: str
    status: str
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    created_at: datetime


class SecurityScanRequest(BaseModel):
    """Request model for security scanning."""
    content: str = Field(..., description="Content to scan")
    scan_types: List[str] = Field(default_factory=list, description="Types of scans to perform")


class SecurityScanResponse(BaseModel):
    """Response model for security scan results."""
    scan_id: str
    issues: List[Dict[str, Any]]
    overall_risk_level: str
    scan_duration: float
    scanned_at: datetime


class APIResponse(BaseModel):
    """Generic API response model."""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None


class APIRouter:
    """API router for organizing endpoints."""
    
    def __init__(self, prefix: str = "", tags: List[str] = None):
        """Initialize API router."""
        self.prefix = prefix
        self.tags = tags or []
        self.routes = []
    
    def add_route(self, method: str, path: str, handler, **kwargs):
        """Add a route to the router."""
        self.routes.append({
            'method': method,
            'path': path,
            'handler': handler,
            **kwargs
        })


def create_app(config: Dict[str, Any] = None) -> FastAPI:
    """Create and configure FastAPI application."""
    config = config or {}
    
    # Create FastAPI app
    app = FastAPI(
        title="MCP Admin API",
        description="REST API for MCP Admin Application",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get("cors_origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # Initialize authentication
    auth_manager = AuthenticationManager()
    security = HTTPBearer()
    
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current authenticated user."""
        user = auth_manager.validate_token(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        return user
    
    # Health check endpoint
    @app.get("/health", tags=["System"])
    async def health_check():
        """Health check endpoint."""
        return APIResponse(
            success=True,
            message="API is healthy",
            data={
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        )
    
    # Prompt management endpoints
    @app.post("/api/v1/prompts", response_model=PromptResponse, tags=["Prompts"])
    async def create_prompt(
        request: PromptCreateRequest,
        current_user = Depends(get_current_user)
    ):
        """Create a new prompt."""
        try:
            # This would integrate with the actual prompt management service
            # For now, return a mock response
            prompt_data = {
                "id": "prompt_123",
                "name": request.name,
                "content": request.content,
                "description": request.description,
                "category": request.category,
                "tags": request.tags,
                "variables": request.variables,
                "metadata": request.metadata,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "version": "1.0.0"
            }
            return PromptResponse(**prompt_data)
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/prompts/{prompt_id}", response_model=PromptResponse, tags=["Prompts"])
    async def get_prompt(
        prompt_id: str,
        current_user = Depends(get_current_user)
    ):
        """Get a prompt by ID."""
        try:
            # Mock response - would integrate with actual service
            prompt_data = {
                "id": prompt_id,
                "name": "Sample Prompt",
                "content": "This is a sample prompt content",
                "description": "Sample prompt description",
                "category": "general",
                "tags": ["sample", "test"],
                "variables": {},
                "metadata": {},
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "version": "1.0.0"
            }
            return PromptResponse(**prompt_data)
        
        except Exception as e:
            raise HTTPException(status_code=404, detail="Prompt not found")
    
    @app.put("/api/v1/prompts/{prompt_id}", response_model=PromptResponse, tags=["Prompts"])
    async def update_prompt(
        prompt_id: str,
        request: PromptUpdateRequest,
        current_user = Depends(get_current_user)
    ):
        """Update a prompt."""
        try:
            # Mock response - would integrate with actual service
            prompt_data = {
                "id": prompt_id,
                "name": request.name or "Updated Prompt",
                "content": request.content or "Updated content",
                "description": request.description,
                "category": request.category,
                "tags": request.tags or [],
                "variables": request.variables or {},
                "metadata": request.metadata or {},
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "version": "1.1.0"
            }
            return PromptResponse(**prompt_data)
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/v1/prompts/{prompt_id}", tags=["Prompts"])
    async def delete_prompt(
        prompt_id: str,
        current_user = Depends(get_current_user)
    ):
        """Delete a prompt."""
        try:
            # Mock response - would integrate with actual service
            return APIResponse(
                success=True,
                message=f"Prompt {prompt_id} deleted successfully"
            )
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/prompts", tags=["Prompts"])
    async def list_prompts(
        category: Optional[str] = None,
        tags: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        current_user = Depends(get_current_user)
    ):
        """List prompts with optional filtering."""
        try:
            # Mock response - would integrate with actual service
            prompts = []
            for i in range(min(limit, 10)):  # Return up to 10 mock prompts
                prompt_data = {
                    "id": f"prompt_{i}",
                    "name": f"Sample Prompt {i}",
                    "content": f"Sample content {i}",
                    "description": f"Description {i}",
                    "category": category or "general",
                    "tags": tags.split(",") if tags else ["sample"],
                    "variables": {},
                    "metadata": {},
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "version": "1.0.0"
                }
                prompts.append(PromptResponse(**prompt_data))
            
            return APIResponse(
                success=True,
                message="Prompts retrieved successfully",
                data={
                    "prompts": [p.dict() for p in prompts],
                    "total": len(prompts),
                    "limit": limit,
                    "offset": offset
                }
            )
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Evaluation endpoints
    @app.post("/api/v1/evaluations", response_model=EvaluationResponse, tags=["Evaluation"])
    async def create_evaluation(
        request: EvaluationRequest,
        current_user = Depends(get_current_user)
    ):
        """Create a new evaluation."""
        try:
            # Mock response - would integrate with actual evaluation service
            evaluation_data = {
                "evaluation_id": "eval_123",
                "prompt_id": request.prompt_id,
                "status": "completed",
                "results": [
                    {
                        "model": model,
                        "score": 0.85,
                        "metrics": {"accuracy": 0.9, "coherence": 0.8}
                    } for model in request.models
                ],
                "summary": {
                    "average_score": 0.85,
                    "best_model": request.models[0] if request.models else "gpt-4",
                    "total_tests": len(request.test_data)
                },
                "created_at": datetime.now()
            }
            return EvaluationResponse(**evaluation_data)
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/evaluations/{evaluation_id}", response_model=EvaluationResponse, tags=["Evaluation"])
    async def get_evaluation(
        evaluation_id: str,
        current_user = Depends(get_current_user)
    ):
        """Get evaluation results."""
        try:
            # Mock response
            evaluation_data = {
                "evaluation_id": evaluation_id,
                "prompt_id": "prompt_123",
                "status": "completed",
                "results": [],
                "summary": {},
                "created_at": datetime.now()
            }
            return EvaluationResponse(**evaluation_data)
        
        except Exception as e:
            raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Security endpoints
    @app.post("/api/v1/security/scan", response_model=SecurityScanResponse, tags=["Security"])
    async def security_scan(
        request: SecurityScanRequest,
        current_user = Depends(get_current_user)
    ):
        """Perform security scan on content."""
        try:
            # Mock response - would integrate with actual security scanner
            scan_data = {
                "scan_id": "scan_123",
                "issues": [
                    {
                        "type": "pii_detected",
                        "severity": "medium",
                        "description": "Email address detected",
                        "location": {"line": 1, "column": 10}
                    }
                ],
                "overall_risk_level": "medium",
                "scan_duration": 0.5,
                "scanned_at": datetime.now()
            }
            return SecurityScanResponse(**scan_data)
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Analytics endpoints
    @app.get("/api/v1/analytics/summary", tags=["Analytics"])
    async def get_analytics_summary(
        current_user = Depends(get_current_user)
    ):
        """Get analytics summary."""
        try:
            return APIResponse(
                success=True,
                message="Analytics summary retrieved",
                data={
                    "total_prompts": 150,
                    "total_evaluations": 75,
                    "average_quality_score": 0.82,
                    "security_issues": 5,
                    "compliance_rate": 0.95
                }
            )
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


def run_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
    """Run the API server."""
    app = create_app()
    uvicorn.run(app, host=host, port=port, debug=debug)