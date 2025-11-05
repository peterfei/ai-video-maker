"""
配置加载器
负责加载和管理配置文件
"""

import os
import yaml
from typing import Any, Dict
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class ConfigLoader:
    """配置加载器类"""

    def __init__(self, config_path: str = "config/default_config.yaml"):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # 处理环境变量替换
        self._replace_env_vars(self.config)

        return self.config

    def _replace_env_vars(self, config: Any) -> None:
        """
        递归替换配置中的环境变量

        Args:
            config: 配置对象
        """
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    config[key] = os.getenv(env_var, "")
                elif isinstance(value, (dict, list)):
                    self._replace_env_vars(value)
        elif isinstance(config, list):
            for item in config:
                self._replace_env_vars(item)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号访问嵌套配置

        Args:
            key: 配置键，支持 'video.resolution' 形式
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
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
        保存配置到文件

        Args:
            output_path: 输出路径，如果为None则覆盖原文件
        """
        output_path = output_path or self.config_path

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)

    def get_paths(self) -> Dict[str, Path]:
        """
        获取所有路径配置

        Returns:
            路径字典
        """
        paths = self.get('paths', {})
        return {key: Path(value) for key, value in paths.items()}


# 全局配置实例
_global_config = None


def get_config(config_path: str = "config/default_config.yaml") -> ConfigLoader:
    """
    获取全局配置实例

    Args:
        config_path: 配置文件路径

    Returns:
        ConfigLoader实例
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigLoader(config_path)
    return _global_config
