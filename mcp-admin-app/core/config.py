"""
Configuration Management for MCP Admin Application
=================================================

Handles application settings, server configurations, and data persistence.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class AppSettings:
    """Application settings configuration."""
    theme: str = "light"
    auto_refresh_interval: int = 5
    max_log_entries: int = 1000
    backup_retention_days: int = 30
    security_alert_threshold: int = 5
    notification_enabled: bool = True


@dataclass
class AdvancedPromptSettings:
    """Advanced prompt management settings."""
    enable_semantic_search: bool = True
    enable_version_control: bool = True
    enable_analytics: bool = True
    enable_collaboration: bool = True
    enable_security_scanning: bool = True
    vector_db_path: str = "vector_store"
    embedding_model: str = "all-MiniLM-L6-v2"
    max_prompt_versions: int = 100
    evaluation_timeout: int = 300
    cost_tracking_enabled: bool = True
    auto_optimization: bool = False
    backup_prompts: bool = True
    
    
class ConfigurationManager:
    """Manages application configuration and settings."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path.home() / ".kiro" / "mcp-admin" / "config"
        self.data_dir = Path.home() / ".kiro" / "mcp-admin" / "data"
        self.templates_dir = Path.home() / ".kiro" / "mcp-admin" / "templates"
        self.vector_dir = Path.home() / ".kiro" / "mcp-admin" / "vector"
        self.prompts_dir = Path.home() / ".kiro" / "mcp-admin" / "prompts"
        
        self._app_settings: Optional[AppSettings] = None
        self._advanced_prompt_settings: Optional[AdvancedPromptSettings] = None
        
    def initialize(self):
        """Initialize configuration directories and files."""
        try:
            # Create directories
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            self.vector_dir.mkdir(parents=True, exist_ok=True)
            self.prompts_dir.mkdir(parents=True, exist_ok=True)
            (self.templates_dir / "prompts").mkdir(exist_ok=True)
            (self.data_dir / "backups").mkdir(exist_ok=True)
            (self.prompts_dir / "projects").mkdir(exist_ok=True)
            (self.prompts_dir / "templates").mkdir(exist_ok=True)
            (self.prompts_dir / "evaluations").mkdir(exist_ok=True)
            
            # Initialize default configurations
            self._initialize_default_configs()
            
            self.logger.info("Configuration manager initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration: {e}")
            raise
    
    def _initialize_default_configs(self):
        """Create default configuration files if they don't exist."""
        
        # App settings
        settings_file = self.config_dir / "app-settings.json"
        if not settings_file.exists():
            default_settings = AppSettings()
            self._save_json(settings_file, asdict(default_settings))
        
        # Servers configuration
        servers_file = self.config_dir / "servers.json"
        if not servers_file.exists():
            default_servers = {
                "servers": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_json(servers_file, default_servers)
        
        # LLM providers configuration
        llm_file = self.config_dir / "llm-providers.json"
        if not llm_file.exists():
            default_llm = {
                "providers": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_json(llm_file, default_llm)
        
        # Notification channels
        notifications_file = self.config_dir / "notification-channels.json"
        if not notifications_file.exists():
            default_notifications = {
                "channels": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_json(notifications_file, default_notifications)
        
        # Advanced prompt management settings
        advanced_prompt_file = self.config_dir / "advanced-prompt-settings.json"
        if not advanced_prompt_file.exists():
            default_advanced_prompt = AdvancedPromptSettings()
            self._save_json(advanced_prompt_file, asdict(default_advanced_prompt))
        
        # Prompt projects configuration
        prompt_projects_file = self.config_dir / "prompt-projects.json"
        if not prompt_projects_file.exists():
            default_projects = {
                "projects": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_json(prompt_projects_file, default_projects)
        
        # Evaluation configurations
        evaluation_config_file = self.config_dir / "evaluation-configs.json"
        if not evaluation_config_file.exists():
            default_evaluation = {
                "scoring_rubrics": [],
                "test_datasets": [],
                "model_configurations": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_json(evaluation_config_file, default_evaluation)
    
    def get_app_settings(self) -> AppSettings:
        """Get application settings."""
        if self._app_settings is None:
            settings_file = self.config_dir / "app-settings.json"
            try:
                data = self._load_json(settings_file)
                self._app_settings = AppSettings(**data)
            except Exception as e:
                self.logger.warning(f"Failed to load app settings: {e}")
                self._app_settings = AppSettings()
        
        return self._app_settings
    
    def save_app_settings(self, settings: AppSettings):
        """Save application settings."""
        settings_file = self.config_dir / "app-settings.json"
        try:
            self._save_json(settings_file, asdict(settings))
            self._app_settings = settings
            self.logger.info("App settings saved")
        except Exception as e:
            self.logger.error(f"Failed to save app settings: {e}")
            raise
    
    def get_servers_config(self) -> Dict[str, Any]:
        """Get servers configuration."""
        servers_file = self.config_dir / "servers.json"
        return self._load_json(servers_file)
    
    def save_servers_config(self, config: Dict[str, Any]):
        """Save servers configuration."""
        servers_file = self.config_dir / "servers.json"
        config["last_updated"] = datetime.now().isoformat()
        self._save_json(servers_file, config)
        self.logger.info("Servers configuration saved")
    
    def get_llm_providers_config(self) -> Dict[str, Any]:
        """Get LLM providers configuration."""
        llm_file = self.config_dir / "llm-providers.json"
        return self._load_json(llm_file)
    
    def save_llm_providers_config(self, config: Dict[str, Any]):
        """Save LLM providers configuration."""
        llm_file = self.config_dir / "llm-providers.json"
        config["last_updated"] = datetime.now().isoformat()
        self._save_json(llm_file, config)
        self.logger.info("LLM providers configuration saved")
    
    def get_notification_channels_config(self) -> Dict[str, Any]:
        """Get notification channels configuration."""
        notifications_file = self.config_dir / "notification-channels.json"
        return self._load_json(notifications_file)
    
    def save_notification_channels_config(self, config: Dict[str, Any]):
        """Save notification channels configuration."""
        notifications_file = self.config_dir / "notification-channels.json"
        config["last_updated"] = datetime.now().isoformat()
        self._save_json(notifications_file, config)
        self.logger.info("Notification channels configuration saved")
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON data from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Configuration file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {file_path}: {e}")
            raise
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        """Save JSON data to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save JSON to {file_path}: {e}")
            raise
    
    def get_advanced_prompt_settings(self) -> AdvancedPromptSettings:
        """Get advanced prompt management settings."""
        if self._advanced_prompt_settings is None:
            settings_file = self.config_dir / "advanced-prompt-settings.json"
            try:
                data = self._load_json(settings_file)
                self._advanced_prompt_settings = AdvancedPromptSettings(**data)
            except Exception as e:
                self.logger.warning(f"Failed to load advanced prompt settings: {e}")
                self._advanced_prompt_settings = AdvancedPromptSettings()
        
        return self._advanced_prompt_settings
    
    def save_advanced_prompt_settings(self, settings: AdvancedPromptSettings):
        """Save advanced prompt management settings."""
        settings_file = self.config_dir / "advanced-prompt-settings.json"
        try:
            self._save_json(settings_file, asdict(settings))
            self._advanced_prompt_settings = settings
            self.logger.info("Advanced prompt settings saved")
        except Exception as e:
            self.logger.error(f"Failed to save advanced prompt settings: {e}")
            raise
    
    def get_prompt_projects_config(self) -> Dict[str, Any]:
        """Get prompt projects configuration."""
        projects_file = self.config_dir / "prompt-projects.json"
        return self._load_json(projects_file)
    
    def save_prompt_projects_config(self, config: Dict[str, Any]):
        """Save prompt projects configuration."""
        projects_file = self.config_dir / "prompt-projects.json"
        config["last_updated"] = datetime.now().isoformat()
        self._save_json(projects_file, config)
        self.logger.info("Prompt projects configuration saved")
    
    def get_evaluation_configs(self) -> Dict[str, Any]:
        """Get evaluation configurations."""
        evaluation_file = self.config_dir / "evaluation-configs.json"
        return self._load_json(evaluation_file)
    
    def save_evaluation_configs(self, config: Dict[str, Any]):
        """Save evaluation configurations."""
        evaluation_file = self.config_dir / "evaluation-configs.json"
        config["last_updated"] = datetime.now().isoformat()
        self._save_json(evaluation_file, config)
        self.logger.info("Evaluation configurations saved")

    @property
    def database_path(self) -> Path:
        """Get the path to the SQLite database."""
        return self.data_dir / "admin.db"
    
    @property
    def vector_database_path(self) -> Path:
        """Get the path to the vector database."""
        return self.vector_dir / "chroma_db"
    
    @property
    def prompts_storage_path(self) -> Path:
        """Get the path to prompt storage."""
        return self.prompts_dir
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (dictionary-like interface)."""
        # Map common keys to appropriate methods
        key_mapping = {
            'app_settings': self.get_app_settings,
            'servers': self.get_servers_config,
            'llm_providers': self.get_llm_providers_config,
            'notification_channels': self.get_notification_channels_config,
            'advanced_prompt_settings': self.get_advanced_prompt_settings,
            'prompt_projects': self.get_prompt_projects_config,
            'evaluation_configs': self.get_evaluation_configs,
            'database_path': lambda: self.database_path,
            'vector_database_path': lambda: self.vector_database_path,
            'prompts_storage_path': lambda: self.prompts_storage_path,
            'config_dir': lambda: self.config_dir,
            'data_dir': lambda: self.data_dir,
            'templates_dir': lambda: self.templates_dir,
            'vector_dir': lambda: self.vector_dir,
            'prompts_dir': lambda: self.prompts_dir
        }
        
        if key in key_mapping:
            try:
                return key_mapping[key]()
            except Exception as e:
                self.logger.error(f"Failed to get config key '{key}': {e}")
                return default
        
        # Try to get from app settings if it's an attribute
        try:
            app_settings = self.get_app_settings()
            if hasattr(app_settings, key):
                return getattr(app_settings, key)
        except Exception:
            pass
        
        # Try to get from advanced prompt settings
        try:
            advanced_settings = self.get_advanced_prompt_settings()
            if hasattr(advanced_settings, key):
                return getattr(advanced_settings, key)
        except Exception:
            pass
        
        self.logger.warning(f"Configuration key '{key}' not found, returning default: {default}")
        return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value by key (dictionary-like interface)."""
        # Map common keys to appropriate save methods
        try:
            if key == 'app_settings':
                if isinstance(value, dict):
                    settings = AppSettings(**value)
                else:
                    settings = value
                self.save_app_settings(settings)
                return True
            elif key == 'servers':
                self.save_servers_config(value)
                return True
            elif key == 'llm_providers':
                self.save_llm_providers_config(value)
                return True
            elif key == 'notification_channels':
                self.save_notification_channels_config(value)
                return True
            elif key == 'advanced_prompt_settings':
                if isinstance(value, dict):
                    settings = AdvancedPromptSettings(**value)
                else:
                    settings = value
                self.save_advanced_prompt_settings(settings)
                return True
            elif key == 'prompt_projects':
                self.save_prompt_projects_config(value)
                return True
            elif key == 'evaluation_configs':
                self.save_evaluation_configs(value)
                return True
            elif key == 'scoring_rubrics':
                # Handle scoring rubrics as part of evaluation configs
                eval_config = self.get_evaluation_configs()
                eval_config['scoring_rubrics'] = value
                self.save_evaluation_configs(eval_config)
                return True
            else:
                # Try to set in app settings if it's an attribute
                app_settings = self.get_app_settings()
                if hasattr(app_settings, key):
                    setattr(app_settings, key, value)
                    self.save_app_settings(app_settings)
                    return True
                
                # Try to set in advanced prompt settings
                advanced_settings = self.get_advanced_prompt_settings()
                if hasattr(advanced_settings, key):
                    setattr(advanced_settings, key, value)
                    self.save_advanced_prompt_settings(advanced_settings)
                    return True
                
                self.logger.warning(f"Configuration key '{key}' not found for setting")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set config key '{key}': {e}")
            return False