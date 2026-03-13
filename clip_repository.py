#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClipRepository 数据仓库：数据持久化与查询
"""
import sqlite3
import os
from typing import List, Optional, Dict, Any
from clip_item import ClipItem, ContentType


class ClipRepository:
    """SQLite 数据仓库实现"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.db_path = config_manager.get('db_path', 'clipboard_history.db')
        self.storage_path = config_manager.get('storage_path', './clipboard_data')
        
        # 确保存储目录存在
        os.makedirs(self.storage_path, exist_ok=True)
        
        # 初始化数据库连接
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()
        
    def _create_tables(self):
        """创建数据库表"""
        cursor = self.conn.cursor()
        
        # 创建剪贴项表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clip_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,
            raw_data TEXT NOT NULL,
            text_preview TEXT,
            created_at INTEGER NOT NULL,
            access_count INTEGER DEFAULT 0,
            last_accessed INTEGER NOT NULL,
            is_pinned BOOLEAN DEFAULT 0,
            is_sensitive BOOLEAN DEFAULT 0,
            tags TEXT,
            source_app TEXT,
            content_hash TEXT UNIQUE NOT NULL
        )
        ''')
        
        # 创建索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_created_at ON clip_items(created_at DESC)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_content_hash ON clip_items(content_hash)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_is_pinned ON clip_items(is_pinned)
        ''')
        
        self.conn.commit()
        
    def save(self, item: ClipItem) -> ClipItem:
        """保存或更新剪贴项"""
        cursor = self.conn.cursor()
        
        if item.id is None:
            # 插入新记录
            cursor.execute('''
            INSERT INTO clip_items (
                content_type, raw_data, text_preview, created_at,
                access_count, last_accessed, is_pinned, is_sensitive,
                tags, source_app, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.content_type.value,
                str(item.raw_data),
                item.text_preview,
                item.created_at,
                item.access_count,
                item.last_accessed,
                item.is_pinned,
                item.is_sensitive,
                ','.join(item.tags),
                item.source_app,
                item.content_hash
            ))
            item.id = cursor.lastrowid
        else:
            # 更新现有记录
            cursor.execute('''
            UPDATE clip_items SET
                content_type = ?, raw_data = ?, text_preview = ?,
                created_at = ?, access_count = ?, last_accessed = ?,
                is_pinned = ?, is_sensitive = ?, tags = ?,
                source_app = ?, content_hash = ?
            WHERE id = ?
            ''', (
                item.content_type.value,
                str(item.raw_data),
                item.text_preview,
                item.created_at,
                item.access_count,
                item.last_accessed,
                item.is_pinned,
                item.is_sensitive,
                ','.join(item.tags),
                item.source_app,
                item.content_hash,
                item.id
            ))
            
        self.conn.commit()
        return item
        
    def get_by_id(self, item_id: int) -> Optional[ClipItem]:
        """根据ID获取剪贴项"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM clip_items WHERE id = ?', (item_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_item(row)
        return None
        
    def get_by_hash(self, content_hash: str) -> Optional[ClipItem]:
        """根据内容哈希获取剪贴项"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM clip_items WHERE content_hash = ?', (content_hash,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_item(row)
        return None
        
    def get_recent(self, limit: int = 50, offset: int = 0) -> List[ClipItem]:
        """获取最近的剪贴项，置顶优先"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM clip_items 
        ORDER BY is_pinned DESC, created_at DESC
        LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        return [self._row_to_item(row) for row in rows]
        
    def search(self, keyword: str, 
               content_type: Optional[str] = None,
               time_range: Optional[int] = None,
               limit: int = 100) -> List[ClipItem]:
        """搜索剪贴项"""
        query = '''
        SELECT * FROM clip_items 
        WHERE (raw_data LIKE ? OR text_preview LIKE ?)
        '''
        params = [f'%{keyword}%', f'%{keyword}%']
        
        if content_type:
            query += ' AND content_type = ?'
            params.append(content_type)
            
        if time_range:
            import time
            min_time = int(time.time()) - time_range
            query += ' AND created_at >= ?'
            params.append(min_time)
            
        query += ' ORDER BY is_pinned DESC, created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [self._row_to_item(row) for row in rows]
        
    def delete_by_id(self, item_id: int) -> bool:
        """根据ID删除剪贴项"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM clip_items WHERE id = ?', (item_id,))
        self.conn.commit()
        return cursor.rowcount > 0
        
    def batch_delete(self, item_ids: List[int]) -> int:
        """批量删除剪贴项"""
        if not item_ids:
            return 0
            
        placeholders = ','.join('?' for _ in item_ids)
        cursor = self.conn.cursor()
        cursor.execute(f'DELETE FROM clip_items WHERE id IN ({placeholders})', item_ids)
        self.conn.commit()
        return cursor.rowcount
        
    def toggle_pin(self, item_id: int) -> bool:
        """切换置顶状态"""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE clip_items 
        SET is_pinned = NOT is_pinned 
        WHERE id = ?
        ''', (item_id,))
        self.conn.commit()
        return cursor.rowcount > 0
        
    def get_stats(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        cursor = self.conn.cursor()
        
        # 总条数
        cursor.execute('SELECT COUNT(*) FROM clip_items')
        total_count = cursor.fetchone()[0]
        
        # 今日条数
        import time
        today_start = int(time.time() - (time.time() % 86400))
        cursor.execute('SELECT COUNT(*) FROM clip_items WHERE created_at >= ?', (today_start,))
        today_count = cursor.fetchone()[0]
        
        # 置顶条数
        cursor.execute('SELECT COUNT(*) FROM clip_items WHERE is_pinned = 1')
        pinned_count = cursor.fetchone()[0]
        
        return {
            'total_count': total_count,
            'today_count': today_count,
            'pinned_count': pinned_count
        }
        
    def _row_to_item(self, row) -> ClipItem:
        """将数据库行转换为ClipItem实例"""
        data = {
            'id': row[0],
            'content_type': row[1],
            'raw_data': row[2],
            'text_preview': row[3],
            'created_at': row[4],
            'access_count': row[5],
            'last_accessed': row[6],
            'is_pinned': bool(row[7]),
            'is_sensitive': bool(row[8]),
            'tags': row[9],
            'source_app': row[10],
            'content_hash': row[11]
        }
        return ClipItem.from_dict(data)
        
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
