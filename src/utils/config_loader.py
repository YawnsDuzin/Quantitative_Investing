"""
Configuration loader for Quantitative Investing System
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class ConfigLoader:
    """
    Configuration loader that handles YAML config files and environment variables
    """

    def __init__(self, config_path: str = None):
        """
        Initialize configuration loader

        Args:
            config_path: Path to config.yaml file
        """
        # Get project root directory
        self.project_root = Path(__file__).parent.parent.parent

        # Default config path
        if config_path is None:
            config_path = self.project_root / "config" / "config.yaml"
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self.config: Dict[str, Any] = {}

        # Load environment variables
        env_path = self.project_root / "config" / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        # Load config file
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file

        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports nested keys with dot notation)

        Args:
            key: Configuration key (e.g., 'database.type' or 'strategy.max_positions')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_env(self, key: str, default: str = None) -> str:
        """
        Get environment variable

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value
        """
        return os.getenv(key, default)

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.get('database', {})

    def get_strategy_config(self) -> Dict[str, Any]:
        """Get strategy configuration"""
        return self.get('strategy', {})

    def get_backtesting_config(self) -> Dict[str, Any]:
        """Get backtesting configuration"""
        return self.get('backtesting', {})

    def get_data_collection_config(self) -> Dict[str, Any]:
        """Get data collection configuration"""
        return self.get('data_collection', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.get('logging', {})

    def update_config(self, key: str, value: Any) -> None:
        """
        Update configuration value

        Args:
            key: Configuration key (supports dot notation)
            value: New value
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save_config(self, output_path: str = None) -> None:
        """
        Save configuration to YAML file

        Args:
            output_path: Output file path (defaults to original config path)
        """
        if output_path is None:
            output_path = self.config_path

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)


# Global config instance
_config_instance = None


def get_config(config_path: str = None) -> ConfigLoader:
    """
    Get global configuration instance (singleton pattern)

    Args:
        config_path: Path to config file

    Returns:
        ConfigLoader instance
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = ConfigLoader(config_path)

    return _config_instance


def reload_config(config_path: str = None) -> ConfigLoader:
    """
    Reload configuration

    Args:
        config_path: Path to config file

    Returns:
        New ConfigLoader instance
    """
    global _config_instance
    _config_instance = ConfigLoader(config_path)
    return _config_instance
