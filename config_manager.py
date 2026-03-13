#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ConfigManager 配置管理：应用设置持久化
"""
import json
import os
from typing import Any, Dict


class ConfigManager:
    """应用配置管理"""
    
    DEFAULT_CONFIG = {
        'max_history': 1000,
        'auto_clean_days': 30,
        'hotkey': 'ctrl+shift+v',
        'theme': 'light',
        'db_path': 'clipboard_history.db',
        'storage_path': './clipboard_data',
        'show_preview': True,
        'auto_paste': True,
        'privacy_mode': False
    }
    
    def __init__(self, config_path: str = 'config.json'):
        self.config_path = config_path
        self.settings: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        
    def load(self) -> None:
        """从文件加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.settings.update(saved_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                
    def save(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.settings.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.settings[key] = value
        
    def reset_to_default(self) -> None:
        """重置为默认配置"""
        self.settings = self.DEFAULT_CONFIG.copy()
        
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.settings.copy()
