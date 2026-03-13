#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClipItem 数据模型：单条剪贴板内容的抽象
"""
import hashlib
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ContentType(Enum):
    """内容类型枚举"""
    TEXT = "text"
    RTF = "rtf"
    IMAGE = "image"
    FILES = "files"
    CODE = "code"
    LINK = "link"
    EMAIL = "email"
    COMMAND = "command"


class ClipItem:
    """单条剪贴板记录"""
    
    def __init__(self, 
                 content_type: ContentType,
                 raw_data: Any,
                 text_preview: str = "",
                 is_pinned: bool = False,
                 is_sensitive: bool = False,
                 tags: Optional[List[str]] = None,
                 source_app: str = ""):
        self.id: Optional[int] = None
        self.content_type = content_type
        self.raw_data = raw_data
        self.text_preview = text_preview
        self.created_at = int(time.time())
        self.access_count = 0
        self.last_accessed = self.created_at
        self.is_pinned = is_pinned
        self.is_sensitive = is_sensitive
        self.tags = tags or []
        self.source_app = source_app
        
        # 计算内容哈希用于去重
        self.content_hash = self._compute_hash()
        
    def _compute_hash(self) -> str:
        """计算内容哈希值用于去重"""
        if isinstance(self.raw_data, str):
            content = self.raw_data.encode('utf-8')
        elif isinstance(self.raw_data, list):
            content = '\n'.join(str(item) for item in self.raw_data).encode('utf-8')
        else:
            content = str(self.raw_data).encode('utf-8')
            
        return hashlib.md5(content).hexdigest()
    
    def get_display_text(self, max_length: int = 100) -> str:
        """获取用于显示的文本摘要"""
        if self.text_preview:
            text = self.text_preview
        elif isinstance(self.raw_data, str):
            text = self.raw_data
        elif isinstance(self.raw_data, list):
            text = '\n'.join(str(item) for item in self.raw_data)
        else:
            text = str(self.raw_data)
            
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    
    def mark_accessed(self):
        """标记为已访问，更新访问时间和次数"""
        self.access_count += 1
        self.last_accessed = int(time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'content_type': self.content_type.value,
            'text_preview': self.text_preview,
            'created_at': self.created_at,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed,
            'is_pinned': self.is_pinned,
            'is_sensitive': self.is_sensitive,
            'tags': ','.join(self.tags),
            'source_app': self.source_app,
            'content_hash': self.content_hash,
            'raw_data': str(self.raw_data)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClipItem':
        """从字典创建ClipItem实例"""
        item = cls(
            content_type=ContentType(data['content_type']),
            raw_data=data['raw_data'],
            text_preview=data['text_preview'],
            is_pinned=data['is_pinned'],
            is_sensitive=data['is_sensitive'],
            tags=data['tags'].split(',') if data['tags'] else [],
            source_app=data['source_app']
        )
        item.id = data['id']
        item.created_at = data['created_at']
        item.access_count = data['access_count']
        item.last_accessed = data['last_accessed']
        item.content_hash = data['content_hash']
        return item
    
    def get_formatted_date(self) -> str:
        """获取格式化的创建日期"""
        dt = datetime.fromtimestamp(self.created_at)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def __str__(self) -> str:
        return f"ClipItem(id={self.id}, type={self.content_type.value}, preview={self.get_display_text(50)})"
    
    def __repr__(self) -> str:
        return self.__str__()
