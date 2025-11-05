"""
Middleware for MCP Admin API
===========================

Security, logging, and other middleware components.
"""

import time
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import json


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for API protection."""
    
    def __init__(self, app, config: Dict[str, Any] = None):
        """Initialize security middleware."""
        super().__init__(app)
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        
        # Rate limiting (simple in-memory implementation)
        self.rate_limit_storage = {}
        self.rate_limit_window = 60  # 1 minute
        self.rate_limit_max_requests = 100  # per window
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware."""
        start_time = time.time()
        
        # Rate limiting
        if not self._check_rate_limit(request):
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "message": "Too many requests"}
            )
        
        # IP filtering (if configured)
        if not self._check_ip_whitelist(request):
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied", "message": "IP not allowed"}
            )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add security headers
            for header, value in self.security_headers.items():
                response.headers[header] = value
            
            # Add custom headers
            response.headers["X-Response-Time"] = str(time.time() - start_time)
            response.headers["X-API-Version"] = "1.0.0"
            
            return response
        
        except Exception as e:
            self.logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "message": "Request processing failed"}
            )
    
    def _check_rate_limit(self, request: Request) -> bool:
        """Check rate limiting for client."""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_rate_limit_storage(current_time)
        
        # Check current requests
        if client_ip not in self.rate_limit_storage:
            self.rate_limit_storage[client_ip] = []
        
        client_requests = self.rate_limit_storage[client_ip]
        
        # Count requests in current window
        window_start = current_time - self.rate_limit_window
        recent_requests = [req_time for req_time in client_requests if req_time > window_start]
        
        if len(recent_requests) >= self.rate_limit_max_requests:
            return False
        
        # Add current request
        recent_requests.append(current_time)
        self.rate_limit_storage[client_ip] = recent_requests
        
        return True
    
    def _check_ip_whitelist(self, request: Request) -> bool:
        """Check IP whitelist if configured."""
        whitelist = self.config.get("ip_whitelist")
        if not whitelist:
            return True  # No whitelist configured
        
        client_ip = self._get_client_ip(request)
        return client_ip in whitelist
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _cleanup_rate_limit_storage(self, current_time: float):
        """Clean up old rate limit entries."""
        cutoff_time = current_time - self.rate_limit_window * 2
        
        for client_ip in list(self.rate_limit_storage.keys()):
            self.rate_limit_storage[client_ip] = [
                req_time for req_time in self.rate_limit_storage[client_ip]
                if req_time > cutoff_time
            ]
            
            # Remove empty entries
            if not self.rate_limit_storage[client_ip]:
                del self.rate_limit_storage[client_ip]


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging middleware for API requests and responses."""
    
    def __init__(self, app, config: Dict[str, Any] = None):
        """Initialize logging middleware."""
        super().__init__(app)
        self.config = config or {}
        self.logger = logging.getLogger("api.requests")
        
        # Configure logging format
        self.log_requests = self.config.get("log_requests", True)
        self.log_responses = self.config.get("log_responses", True)
        self.log_body = self.config.get("log_body", False)
        self.sensitive_headers = {"authorization", "x-api-key", "cookie"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through logging middleware."""
        start_time = time.time()
        request_id = self._generate_request_id()
        
        # Log request
        if self.log_requests:
            await self._log_request(request, request_id)
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        if self.log_responses:
            self._log_response(response, request_id, process_time)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request."""
        # Prepare request data
        request_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": self._sanitize_headers(dict(request.headers)),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "timestamp": time.time()
        }
        
        # Add body if configured
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Try to parse as JSON
                    try:
                        request_data["body"] = json.loads(body.decode())
                    except:
                        request_data["body"] = body.decode()[:1000]  # Limit body size
            except Exception as e:
                request_data["body_error"] = str(e)
        
        self.logger.info(f"Request: {json.dumps(request_data, default=str)}")
    
    def _log_response(self, response: Response, request_id: str, process_time: float):
        """Log outgoing response."""
        response_data = {
            "request_id": request_id,
            "status_code": response.status_code,
            "headers": self._sanitize_headers(dict(response.headers)),
            "process_time": process_time,
            "timestamp": time.time()
        }
        
        # Log level based on status code
        if response.status_code >= 500:
            self.logger.error(f"Response: {json.dumps(response_data, default=str)}")
        elif response.status_code >= 400:
            self.logger.warning(f"Response: {json.dumps(response_data, default=str)}")
        else:
            self.logger.info(f"Response: {json.dumps(response_data, default=str)}")
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize sensitive headers for logging."""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return str(uuid.uuid4())[:8]


class CacheMiddleware(BaseHTTPMiddleware):
    """Caching middleware for API responses."""
    
    def __init__(self, app, config: Dict[str, Any] = None):
        """Initialize cache middleware."""
        super().__init__(app)
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Simple in-memory cache (would use Redis in production)
        self.cache = {}
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5 minutes default
        self.cacheable_methods = {"GET"}
        self.cacheable_paths = self.config.get("cacheable_paths", ["/api/v1/prompts"])
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through cache middleware."""
        # Check if request is cacheable
        if not self._is_cacheable(request):
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Check cache
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            self.logger.debug(f"Cache hit for key: {cache_key}")
            return cached_response
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            self._cache_response(cache_key, response)
            self.logger.debug(f"Cached response for key: {cache_key}")
        
        return response
    
    def _is_cacheable(self, request: Request) -> bool:
        """Check if request is cacheable."""
        if request.method not in self.cacheable_methods:
            return False
        
        # Check if path is cacheable
        for path_pattern in self.cacheable_paths:
            if request.url.path.startswith(path_pattern):
                return True
        
        return False
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        import hashlib
        
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Response]:
        """Get cached response if available and not expired."""
        if cache_key not in self.cache:
            return None
        
        cached_data = self.cache[cache_key]
        
        # Check expiration
        if time.time() > cached_data["expires_at"]:
            del self.cache[cache_key]
            return None
        
        # Return cached response
        return Response(
            content=cached_data["content"],
            status_code=cached_data["status_code"],
            headers=cached_data["headers"],
            media_type=cached_data["media_type"]
        )
    
    def _cache_response(self, cache_key: str, response: Response):
        """Cache response data."""
        try:
            # Store response data
            self.cache[cache_key] = {
                "content": response.body,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type,
                "expires_at": time.time() + self.cache_ttl,
                "cached_at": time.time()
            }
            
            # Clean up old cache entries periodically
            self._cleanup_cache()
        
        except Exception as e:
            self.logger.error(f"Error caching response: {e}")
    
    def _cleanup_cache(self):
        """Clean up expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.cache.items()
            if current_time > data["expires_at"]
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        # Log cache statistics
        if len(expired_keys) > 0:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


class MetricsMiddleware(BaseHTTPMiddleware):
    """Metrics collection middleware."""
    
    def __init__(self, app, config: Dict[str, Any] = None):
        """Initialize metrics middleware."""
        super().__init__(app)
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Metrics storage (would use proper metrics system in production)
        self.metrics = {
            "requests_total": 0,
            "requests_by_method": {},
            "requests_by_status": {},
            "response_times": [],
            "errors_total": 0
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through metrics middleware."""
        start_time = time.time()
        
        # Increment request counter
        self.metrics["requests_total"] += 1
        
        # Track by method
        method = request.method
        self.metrics["requests_by_method"][method] = self.metrics["requests_by_method"].get(method, 0) + 1
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        self.metrics["response_times"].append(response_time)
        
        # Keep only last 1000 response times
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
        
        # Track by status code
        status_code = response.status_code
        self.metrics["requests_by_status"][status_code] = self.metrics["requests_by_status"].get(status_code, 0) + 1
        
        # Track errors
        if status_code >= 400:
            self.metrics["errors_total"] += 1
        
        return response
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        response_times = self.metrics["response_times"]
        
        return {
            "requests_total": self.metrics["requests_total"],
            "requests_by_method": self.metrics["requests_by_method"],
            "requests_by_status": self.metrics["requests_by_status"],
            "errors_total": self.metrics["errors_total"],
            "response_time_stats": {
                "count": len(response_times),
                "avg": sum(response_times) / len(response_times) if response_times else 0,
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0
            }
        }