#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HotkeyManager 热键管理：全局快捷键注册与处理
"""
import keyboard
from typing import Callable, Dict, Optional


class HotkeyManager:
    """全局热键管理"""
    
    def __init__(self):
        self.bindings: Dict[str, Callable] = {}
        self.running = False
        
    def register(self, hotkey: str, callback: Callable) -> None:
        """注册热键"""
        try:
            keyboard.add_hotkey(hotkey, callback)
            self.bindings[hotkey] = callback
            print(f"已注册热键: {hotkey}")
        except Exception as e:
            print(f"注册热键失败 {hotkey}: {e}")
            
    def unregister(self, hotkey: str) -> None:
        """注销热键"""
        if hotkey in self.bindings:
            try:
                keyboard.remove_hotkey(hotkey)
                del self.bindings[hotkey]
                print(f"已注销热键: {hotkey}")
            except Exception as e:
                print(f"注销热键失败 {hotkey}: {e}")
                
    def unregister_all(self) -> None:
        """注销所有热键"""
        for hotkey in list(self.bindings.keys()):
            self.unregister(hotkey)
            
    def listen(self) -> None:
        """开始监听热键"""
        self.running = True
        print("热键监听器已启动")
        keyboard.wait()
        
    def stop(self) -> None:
        """停止监听热键"""
        self.running = False
        self.unregister_all()
        keyboard.unhook_all()
        print("热键监听器已停止")
