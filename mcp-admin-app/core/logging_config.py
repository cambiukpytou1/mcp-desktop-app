"""
Logging Configuration for MCP Admin Application
==============================================

Centralized logging setup with file and console handlers.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logging(log_level=logging.INFO):
    """Setup application logging with file and console handlers."""
    
    # Create logs directory
    logs_dir = Path.home() / ".kiro" / "mcp-admin" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # Application log file handler
    app_log_file = logs_dir / "application.log"
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(app_handler)
    
    # Error log file handler
    error_log_file = logs_dir / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=5*1024*1024, backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Advanced prompt management log file handler
    prompt_log_file = logs_dir / "prompt_management.log"
    prompt_handler = logging.handlers.RotatingFileHandler(
        prompt_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    prompt_handler.setLevel(logging.INFO)
    prompt_handler.setFormatter(detailed_formatter)
    
    # Evaluation log file handler
    evaluation_log_file = logs_dir / "evaluation.log"
    evaluation_handler = logging.handlers.RotatingFileHandler(
        evaluation_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    evaluation_handler.setLevel(logging.INFO)
    evaluation_handler.setFormatter(detailed_formatter)
    
    # Analytics log file handler
    analytics_log_file = logs_dir / "analytics.log"
    analytics_handler = logging.handlers.RotatingFileHandler(
        analytics_log_file, maxBytes=5*1024*1024, backupCount=3
    )
    analytics_handler.setLevel(logging.INFO)
    analytics_handler.setFormatter(detailed_formatter)
    
    # Setup specific loggers for advanced components
    setup_advanced_loggers(prompt_handler, evaluation_handler, analytics_handler)
    
    logging.info("Logging system initialized")


def setup_advanced_loggers(prompt_handler, evaluation_handler, analytics_handler):
    """Setup specific loggers for advanced prompt management components."""
    
    # Prompt management loggers
    prompt_loggers = [
        'services.prompt',
        'models.prompt_advanced',
        'ui.prompt_advanced'
    ]
    
    for logger_name in prompt_loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(prompt_handler)
        logger.setLevel(logging.INFO)
    
    # Evaluation loggers
    evaluation_loggers = [
        'services.evaluation',
        'services.analytics'
    ]
    
    for logger_name in evaluation_loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(evaluation_handler)
        logger.setLevel(logging.INFO)
    
    # Analytics loggers
    analytics_loggers = [
        'services.analytics',
        'data.vector'
    ]
    
    for logger_name in analytics_loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(analytics_handler)
        logger.setLevel(logging.INFO)
    
    # Collaboration and security loggers
    collab_loggers = [
        'services.collaboration',
        'services.integration'
    ]
    
    for logger_name in collab_loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(prompt_handler)  # Use prompt handler for now
        logger.setLevel(logging.INFO)