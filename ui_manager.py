#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UIManager 界面控制器：Tkinter 视图管理与交互协调
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pyperclip
from typing import List, Optional
from clip_item import ClipItem, ContentType
from clip_repository import ClipRepository
from config_manager import ConfigManager


class UIManager:
    """Tkinter 界面管理器"""
    
    def __init__(self, root: tk.Tk, repository: ClipRepository, config_manager: ConfigManager):
        self.root = root
        self.repository = repository
        self.config_manager = config_manager
        
        self.root.title("智能剪贴板管理器")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.current_items: List[ClipItem] = []
        self.selected_item: Optional[ClipItem] = None
        
        self._setup_ui()
        self._load_recent_items()
        
    def _setup_ui(self):
        """设置主界面UI"""
        # 顶部搜索栏
        self.search_frame = ttk.Frame(self.root)
        self.search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.insert(0, "搜索剪贴内容...")
        
        # 类型过滤下拉框
        self.type_var = tk.StringVar(value="全部")
        self.type_combo = ttk.Combobox(self.search_frame, textvariable=self.type_var, 
                                       values=["全部", "文本", "代码", "链接", "命令", "邮箱"],
                                       state="readonly", width=10)
        self.type_combo.pack(side=tk.LEFT, padx=5)
        self.type_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # 主内容区域
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧列表区域
        self.list_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.list_frame, weight=2)
        
        # 列表标题
        self.list_header = ttk.Frame(self.list_frame)
        self.list_header.pack(fill=tk.X)
        
        ttk.Label(self.list_header, text="剪贴板历史", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.stats_label = ttk.Label(self.list_header, text="")
        self.stats_label.pack(side=tk.RIGHT, padx=5)
        
        # 剪贴项列表
        self.listbox_frame = ttk.Frame(self.list_frame)
        self.listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.listbox_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.item_listbox = tk.Listbox(self.listbox_frame, 
                                       yscrollcommand=self.scrollbar.set,
                                       font=('Microsoft YaHei', 10),
                                       selectmode=tk.SINGLE)
        self.item_listbox.pack(fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.item_listbox.yview)
        
        self.item_listbox.bind('<<ListboxSelect>>', self.on_item_select)
        self.item_listbox.bind('<Double-Button-1>', self.on_item_double_click)
        self.item_listbox.bind('<Return>', self.on_item_double_click)
        
        # 右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="复制到剪贴板", command=self.copy_selected)
        self.context_menu.add_command(label="置顶/取消置顶", command=self.toggle_pin)
        self.context_menu.add_command(label="删除", command=self.delete_selected)
        self.item_listbox.bind('<Button-3>', self.show_context_menu)
        
        # 右侧预览区域
        self.preview_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.preview_frame, weight=3)
        
        ttk.Label(self.preview_frame, text="内容预览", font=('Arial', 12, 'bold')).pack(anchor=tk.W, padx=5, pady=5)
        
        self.preview_text = scrolledtext.ScrolledText(self.preview_frame, 
                                                      wrap=tk.WORD,
                                                      font=('Microsoft YaHei', 10))
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 底部状态栏
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 更新统计信息
        self._update_stats()
        
    def _load_recent_items(self):
        """加载最近的剪贴项"""
        self.current_items = self.repository.get_recent(limit=100)
        self._update_listbox()
        
    def _update_listbox(self):
        """更新列表显示"""
        self.item_listbox.delete(0, tk.END)
        
        for item in self.current_items:
            prefix = "📌 " if item.is_pinned else ""
            type_icon = self._get_type_icon(item.content_type)
            display_text = f"{prefix}{type_icon} {item.get_display_text(60)}"
            self.item_listbox.insert(tk.END, display_text)
            
        # 更新统计
        self._update_stats()
        
    def _get_type_icon(self, content_type: ContentType) -> str:
        """获取内容类型图标"""
        icons = {
            ContentType.TEXT: "📝",
            ContentType.CODE: "💻",
            ContentType.LINK: "🔗",
            ContentType.COMMAND: "⌨️",
            ContentType.EMAIL: "📧",
            ContentType.IMAGE: "🖼️",
            ContentType.FILES: "📁",
        }
        return icons.get(content_type, "📝")
        
    def _update_stats(self):
        """更新统计信息"""
        stats = self.repository.get_stats()
        self.stats_label.config(text=f"总计: {stats['total_count']} | 今日: {stats['today_count']} | 置顶: {stats['pinned_count']}")
        
    def on_search_change(self, *args):
        """搜索内容变化回调"""
        keyword = self.search_var.get().strip()
        if keyword and keyword != "搜索剪贴内容...":
            self.current_items = self.repository.search(keyword)
        else:
            self.current_items = self.repository.get_recent(limit=100)
        self._update_listbox()
        
    def on_filter_change(self, event):
        """类型过滤变化回调"""
        type_filter = self.type_var.get()
        type_map = {
            "全部": None,
            "文本": "text",
            "代码": "code",
            "链接": "link",
            "命令": "command",
            "邮箱": "email"
        }
        
        content_type = type_map.get(type_filter)
        keyword = self.search_var.get().strip()
        
        if keyword:
            self.current_items = self.repository.search(keyword, content_type=content_type)
        else:
            if content_type:
                self.current_items = self.repository.search("", content_type=content_type)
            else:
                self.current_items = self.repository.get_recent(limit=100)
        self._update_listbox()
        
    def on_item_select(self, event):
        """选中项变化回调"""
        selection = self.item_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if 0 <= index < len(self.current_items):
            self.selected_item = self.current_items[index]
            self._show_preview(self.selected_item)
            
    def _show_preview(self, item: ClipItem):
        """显示内容预览"""
        self.preview_text.delete(1.0, tk.END)
        
        # 显示元信息
        info = f"类型: {item.content_type.value}\n"
        info += f"创建时间: {item.get_formatted_date()}\n"
        info += f"访问次数: {item.access_count}\n"
        if item.tags:
            info += f"标签: {', '.join(item.tags)}\n"
        info += "-" * 50 + "\n\n"
        
        self.preview_text.insert(tk.END, info)
        
        # 显示内容
        content = str(item.raw_data)
        self.preview_text.insert(tk.END, content)
        
    def on_item_double_click(self, event):
        """双击项回调：复制到剪贴板"""
        self.copy_selected()
        
    def copy_selected(self):
        """复制选中项到剪贴板"""
        if self.selected_item:
            pyperclip.copy(str(self.selected_item.raw_data))
            self.selected_item.mark_accessed()
            self.repository.save(self.selected_item)
            self.status_bar.config(text=f"已复制: {self.selected_item.get_display_text(40)}")
            
            # 如果启用了自动粘贴，模拟Ctrl+V
            if self.config_manager.get('auto_paste', True):
                self._simulate_paste()
                
    def _simulate_paste(self):
        """模拟Ctrl+V粘贴"""
        try:
            import keyboard
            keyboard.press_and_release('ctrl+v')
        except Exception as e:
            print(f"模拟粘贴失败: {e}")
            
    def toggle_pin(self):
        """切换置顶状态"""
        if self.selected_item:
            self.repository.toggle_pin(self.selected_item.id)
            self._load_recent_items()
            self.status_bar.config(text="已切换置顶状态")
            
    def delete_selected(self):
        """删除选中项"""
        if self.selected_item:
            if messagebox.askyesno("确认删除", "确定要删除这条记录吗？"):
                self.repository.delete_by_id(self.selected_item.id)
                self._load_recent_items()
                self.preview_text.delete(1.0, tk.END)
                self.selected_item = None
                self.status_bar.config(text="已删除记录")
                
    def show_context_menu(self, event):
        """显示右键菜单"""
        selection = self.item_listbox.curselection()
        if selection:
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
                
    def on_new_item(self, item: ClipItem):
        """新内容捕获回调"""
        # 在主线程中更新UI
        self.root.after(0, self._add_new_item, item)
        
    def _add_new_item(self, item: ClipItem):
        """添加新项到列表顶部"""
        self.current_items.insert(0, item)
        # 限制显示数量
        if len(self.current_items) > 100:
            self.current_items.pop()
        self._update_listbox()
        self.status_bar.config(text=f"新内容: {item.get_display_text(40)}")
        
    def show_quick_panel(self):
        """显示快速选择面板"""
        # 创建浮动面板
        self.quick_panel = tk.Toplevel(self.root)
        self.quick_panel.title("快速粘贴")
        self.quick_panel.geometry("500x400")
        self.quick_panel.attributes('-topmost', True)
        
        # 让面板居中显示
        self.quick_panel.update_idletasks()
        x = (self.quick_panel.winfo_screenwidth() // 2) - 250
        y = (self.quick_panel.winfo_screenheight() // 2) - 200
        self.quick_panel.geometry(f"+{x}+{y}")
        
        # 快速搜索框
        quick_search_var = tk.StringVar()
        quick_search = ttk.Entry(self.quick_panel, textvariable=quick_search_var)
        quick_search.pack(fill=tk.X, padx=5, pady=5)
        quick_search.focus_set()
        
        # 列表框
        quick_listbox = tk.Listbox(self.quick_panel, font=('Microsoft YaHei', 10))
        quick_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 加载最近15条
        recent_items = self.repository.get_recent(limit=15)
        
        def update_quick_list():
            keyword = quick_search_var.get().strip()
            quick_listbox.delete(0, tk.END)
            
            if keyword:
                items = self.repository.search(keyword, limit=15)
            else:
                items = recent_items
                
            for i, item in enumerate(items):
                prefix = "📌 " if item.is_pinned else ""
                display_text = f"{prefix}{self._get_type_icon(item.content_type)} {item.get_display_text(50)}"
                quick_listbox.insert(tk.END, display_text)
                
            # 选中第一项
            if quick_listbox.size() > 0:
                quick_listbox.selection_set(0)
                
        def on_quick_select(event=None):
            selection = quick_listbox.curselection()
            if selection:
                index = selection[0]
                if keyword:
                    items = self.repository.search(keyword, limit=15)
                else:
                    items = recent_items
                    
                if 0 <= index < len(items):
                    item = items[index]
                    pyperclip.copy(str(item.raw_data))
                    item.mark_accessed()
                    self.repository.save(item)
                    self.quick_panel.destroy()
                    
                    # 模拟粘贴
                    if self.config_manager.get('auto_paste', True):
                        self._simulate_paste()
                        
        # 绑定事件
        quick_search_var.trace('w', lambda *args: update_quick_list())
        quick_listbox.bind('<Return>', on_quick_select)
        quick_listbox.bind('<Double-Button-1>', on_quick_select)
        quick_search.bind('<Return>', on_quick_select)
        
        # ESC 关闭面板
        def close_panel(event):
            self.quick_panel.destroy()
            
        self.quick_panel.bind('<Escape>', close_panel)
        quick_search.bind('<Escape>', close_panel)
        
        # 方向键导航
        def navigate_up(event):
            selection = quick_listbox.curselection()
            if selection:
                index = selection[0]
                if index > 0:
                    quick_listbox.selection_clear(0, tk.END)
                    quick_listbox.selection_set(index - 1)
                    quick_listbox.see(index - 1)
            return "break"
            
        def navigate_down(event):
            selection = quick_listbox.curselection()
            if selection:
                index = selection[0]
                if index < quick_listbox.size() - 1:
                    quick_listbox.selection_clear(0, tk.END)
                    quick_listbox.selection_set(index + 1)
                    quick_listbox.see(index + 1)
            return "break"
            
        quick_search.bind('<Up>', navigate_up)
        quick_search.bind('<Down>', navigate_down)
        quick_listbox.bind('<Up>', navigate_up)
        quick_listbox.bind('<Down>', navigate_down)
        
        # 初始化列表
        update_quick_list()
        
    def on_close(self):
        """窗口关闭回调"""
        if messagebox.askokcancel("退出", "确定要退出智能剪贴板管理器吗？\n\n提示：程序将继续在后台运行监听剪贴板"):
            self.root.withdraw()
            # 最小化到系统托盘（简单实现）
            self.status_bar.config(text="程序已最小化到后台")
            
    def run(self):
        """运行主UI循环"""
        self.root.mainloop()
