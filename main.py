#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能剪贴板管理器主程序入口
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clipboard_monitor import ClipboardMonitor
from clip_repository import ClipRepository
from ui_manager import UIManager
from hotkey_manager import HotkeyManager
from config_manager import ConfigManager
from content_classifier import ContentClassifier


class SmartClipboardManager:
    """智能剪贴板管理器主类"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config_manager.load()
        
        self.repository = ClipRepository(self.config_manager)
        self.classifier = ContentClassifier()
        
        self.clipboard_monitor = ClipboardMonitor(self.repository, self.classifier)
        self.hotkey_manager = HotkeyManager()
        
        self.root = tk.Tk()
        self.ui_manager = UIManager(self.root, self.repository, self.config_manager)
        
        self._setup_hotkeys()
        self._setup_callbacks()
        
    def _setup_hotkeys(self):
        """设置全局热键"""
        hotkey = self.config_manager.get('hotkey', 'ctrl+shift+v')
        self.hotkey_manager.register(hotkey, self.ui_manager.show_quick_panel)
        
    def _setup_callbacks(self):
        """设置回调函数"""
        self.clipboard_monitor.on_new_item = self.ui_manager.on_new_item
        
    def run(self):
        """启动应用程序"""
        # 启动剪贴板监听线程
        monitor_thread = threading.Thread(target=self.clipboard_monitor.start, daemon=True)
        monitor_thread.start()
        
        # 启动热键监听线程
        hotkey_thread = threading.Thread(target=self.hotkey_manager.listen, daemon=True)
        hotkey_thread.start()
        
        # 启动主UI循环
        self.ui_manager.run()
        
        # 清理资源
        self.clipboard_monitor.stop()
        self.repository.close()
        self.config_manager.save()


if __name__ == "__main__":
    app = SmartClipboardManager()
    app.run()
