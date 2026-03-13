#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ContentClassifier 内容分类器：自动识别内容类型与提取元数据
"""
import re
from typing import List
from clip_item import ContentType


class ContentClassifier:
    """内容分类与标签提取"""
    
    # URL 正则表达式
    URL_PATTERN = re.compile(
        r'https?://(?:[-\w.]|%[\da-fA-F]{2})+'
        r'(?:/[^\s]*)?'
    )
    
    # Email 正则表达式
    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    )
    
    # 代码片段特征
    CODE_PATTERNS = [
        r'def\s+\w+\s*\(',  # Python 函数
        r'class\s+\w+',     # 类定义
        r'function\s+\w+',  # JavaScript 函数
        r'const\s+\w+',     # JavaScript 常量
        r'var\s+\w+',       # JavaScript 变量
        r'import\s+\w+',    # 导入语句
        r'from\s+\w+\s+import',  # Python 导入
        r'print\s*\(',      # Python 打印
        r'console\.log\s*\(',  # JavaScript 打印
        r'^\s*#\s+\w+',     # Shell 注释
        r'^\s*//\s+\w+',    # C/Java 注释
        r'^\s*--\s+\w+',    # SQL 注释
    ]
    
    # 命令行特征
    COMMAND_PATTERNS = [
        r'^cd\s+',
        r'^ls\s*',
        r'^git\s+',
        r'^npm\s+',
        r'^pip\s+',
        r'^python\s+',
        r'^node\s+',
        r'^docker\s+',
        r'^kubectl\s+',
        r'^sudo\s+',
    ]
    
    def __init__(self):
        self.code_regex = [re.compile(pattern, re.MULTILINE) for pattern in self.CODE_PATTERNS]
        self.command_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.COMMAND_PATTERNS]
        
    def classify(self, text: str) -> ContentType:
        """自动识别内容类型"""
        if not text:
            return ContentType.TEXT
            
        # 检查是否是链接
        if self.URL_PATTERN.search(text):
            return ContentType.LINK
            
        # 检查是否是邮箱
        if self.EMAIL_PATTERN.search(text):
            return ContentType.EMAIL
            
        # 检查是否是命令行
        for regex in self.command_regex:
            if regex.search(text):
                return ContentType.COMMAND
                
        # 检查是否是代码
        for regex in self.code_regex:
            if regex.search(text):
                return ContentType.CODE
                
        # 默认是普通文本
        return ContentType.TEXT
        
    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词作为标签建议"""
        tags = []
        
        # 检查链接
        if self.URL_PATTERN.search(text):
            tags.append("链接")
            
        # 检查邮箱
        if self.EMAIL_PATTERN.search(text):
            tags.append("邮箱")
            
        # 检查代码
        for regex in self.code_regex:
            if regex.search(text):
                tags.append("代码")
                break
                
        # 检查命令
        for regex in self.command_regex:
            if regex.search(text):
                tags.append("命令")
                break
                
        # 去除重复标签
        return list(set(tags))
        
    def generate_preview(self, text: str, content_type: ContentType, max_length: int = 150) -> str:
        """生成内容预览"""
        if not text:
            return ""
            
        # 对于代码，保留缩进但限制长度
        if content_type == ContentType.CODE:
            lines = text.splitlines()
            preview_lines = lines[:5]  # 最多显示前5行
            preview = '\n'.join(preview_lines)
        else:
            # 对于其他类型，去除多余空白
            preview = ' '.join(text.split())
            
        # 限制长度
        if len(preview) > max_length:
            preview = preview[:max_length] + "..."
            
        return preview
        
    def is_sensitive_content(self, text: str) -> bool:
        """检测是否是敏感内容（密码、密钥等）"""
        sensitive_patterns = [
            r'password\s*=',
            r'passwd\s*=',
            r'secret\s*=',
            r'api[_-]key\s*=',
            r'token\s*=',
            r'private[_-]key',
            r'-----BEGIN.*PRIVATE KEY-----',
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
                
        return False
