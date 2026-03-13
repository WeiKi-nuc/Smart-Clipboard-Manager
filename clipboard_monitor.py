#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClipboardMonitor 剪贴板监听引擎
"""
import time
import threading
import pyperclip
from typing import Callable, Optional
from clip_item import ClipItem, ContentType


class ClipboardMonitor:
    """系统剪贴板后台监听与事件分发"""
    
    def __init__(self, repository, classifier):
        self.repository = repository
        self.classifier = classifier
        self.running = False
        self.last_content_hash = ""
        self.on_new_item: Optional[Callable[[ClipItem], None]] = None
        self.poll_interval = 0.5  # 500ms 轮询间隔
        
    def start(self):
        """启动剪贴板监听"""
        self.running = True
        print("剪贴板监听器已启动")
        
        while self.running:
            try:
                self._check_clipboard()
                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"剪贴板监听错误: {e}")
                time.sleep(self.poll_interval)
                
    def stop(self):
        """停止剪贴板监听"""
        self.running = False
        print("剪贴板监听器已停止")
        
    def _check_clipboard(self):
        """检查剪贴板内容变化"""
        try:
            content = pyperclip.paste()
            
            if not content:
                return
                
            # 计算当前内容哈希
            current_hash = self._compute_content_hash(content)
            
            # 去重检查
            if current_hash == self.last_content_hash:
                return
                
            # 检查数据库中是否已存在相同内容
            existing_item = self.repository.get_by_hash(current_hash)
            if existing_item:
                # 更新访问时间
                existing_item.mark_accessed()
                self.repository.save(existing_item)
                self.last_content_hash = current_hash
                return
                
            # 新内容，进行分类和处理
            content_type = self.classifier.classify(content)
            tags = self.classifier.extract_keywords(content)
            preview = self.classifier.generate_preview(content, content_type)
            
            # 创建新的剪贴项
            item = ClipItem(
                content_type=content_type,
                raw_data=content,
                text_preview=preview,
                tags=tags
            )
            
            # 保存到数据库
            self.repository.save(item)
            
            # 更新最后哈希
            self.last_content_hash = current_hash
            
            # 触发回调
            if self.on_new_item:
                self.on_new_item(item)
                
            print(f"捕获新内容: {item.get_display_text(50)}")
            
        except Exception as e:
            print(f"检查剪贴板错误: {e}")
            
    def _compute_content_hash(self, content: str) -> str:
        """计算内容哈希值"""
        import hashlib
        return hashlib.md5(content.encode('utf-8')).hexdigest()
