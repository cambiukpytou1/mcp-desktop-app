#!/usr/bin/env python3
"""
MCP Admin Application - Main Entry Point
========================================

Enhanced MCP Administration Application with comprehensive server management,
security logging, audit trails, and LLM provider integration.
"""

import sys
import os
import logging
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from core.app import MCPAdminApp
from core.config import ConfigurationManager
from core.logging_config import setup_logging


def main():
    """Main entry point for the MCP Admin application."""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting MCP Admin Application")
        
        # Initialize configuration
        config_manager = ConfigurationManager()
        config_manager.initialize()
        
        # Create and run the application
        app = MCPAdminApp()
        app.mainloop()
        
    except Exception as e:
        logging.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()