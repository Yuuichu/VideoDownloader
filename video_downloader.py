#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoDownloader - A YouTube video downloader with GUI
Supports HDR video detection and multi-threaded downloading
"""

import sys
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import pyperclip
import subprocess
import time
import threading
from queue import Queue

__version__ = "1.0.0"

def get_script_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

SCRIPT_DIR = get_script_directory()
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError):
            pass
    default_config = {
        "default_path": "",
        "history_paths": [],
        "use_subfolders": False,
        "prefer_hdr": True,
        "max_resolution": "4320"  # 8K
    }
    save_config(default_config)
    return default_config

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4, ensure_ascii=False)

config = load_config()
default_download_path = config.get("default_path", "")
history_paths = config.get("history_paths", [])
use_subfolders = config.get("use_subfolders", False)

def get_playlist_video_links(playlist_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'no_check_certificate': True,
        'ignoreerrors': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(playlist_url, download=False)
        video_entries = info_dict.get('entries', [])
        video_links = []
        for entry in video_entries:
            if entry and entry.get('id'):
                url = entry.get('url') or entry.get('webpage_url')
                if not url:
                    url = f"https://www.youtube.com/watch?v={entry.get('id')}"
                video_links.append(url)
        return video_links

def detect_hdr_format(info_dict):
    """检测视频的 HDR 格式"""
    formats = info_dict.get('formats', [])
    
    # HDR 格式优先级
    hdr_priority = ['DV', 'HDR10+', 'HDR10', 'HLG', 'HDR', 'SDR']
    detected_formats = set()
    
    for fmt in formats:
        if fmt.get('vcodec') == 'none':
            continue
        dynamic_range = fmt.get('dynamic_range', '')
        if dynamic_range:
            detected_formats.add(dynamic_range)
    
    # 返回最高优先级的格式
    for hdr_type in hdr_priority:
        if hdr_type in detected_formats:
            return hdr_type
    
    # 检查视频级别的 dynamic_range
    video_dr = info_dict.get('dynamic_range', '')
    if video_dr:
        return video_dr
    
    return 'SDR'

class DownloadThread(threading.Thread):
    """后台下载线程"""
    def __init__(self, app, video_url, output_directory, uploader_name, item_id, callback_queue):
        super().__init__(daemon=True)
        self.app = app
        self.video_url = video_url
        self.output_directory = output_directory
        self.uploader_name = uploader_name
        self.item_id = item_id
        self.callback_queue = callback_queue
        self.cancelled = False
    
    def run(self):
        try:
            result = self.download_and_merge()
            self.callback_queue.put(('success', self.item_id, result))
        except Exception as e:
            self.callback_queue.put(('error', self.item_id, str(e)))
    
    def download_and_merge(self):
        if self.app.use_subfolders_var.get() and self.uploader_name:
            output_directory = os.path.join(self.output_directory, self.uploader_name)
            os.makedirs(output_directory, exist_ok=True)
        else:
            output_directory = self.output_directory

        output_template = os.path.join(output_directory, '%(title)s.%(ext)s')
        
        # 优化格式选择：优先选择高质量视频（让 yt-dlp 自动选择最佳格式）
        format_selector = 'bestvideo+bestaudio/best'
        
        ydl_opts = {
            'format': format_selector,
            'outtmpl': output_template,
            'merge_output_format': 'mkv',
            'no_check_certificate': True,
            'retries': 5,
            'fragment_retries': 5,
            'progress_hooks': [self.progress_hook],
            'postprocessor_hooks': [self.postprocessor_hook],
            'quiet': False,
            'no_warnings': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.video_url)
            hdr_format = detect_hdr_format(info)
            filename = ydl.prepare_filename(info)
            
            self.callback_queue.put(('log', None, f"已下载: {filename}"))

            merged_filename = filename.rsplit('.', 1)[0] + '.mkv'
            
            # 检查是否需要重新封装
            if os.path.exists(merged_filename):
                return merged_filename, hdr_format
            
            # 使用 ffmpeg 重新封装确保兼容性
            if os.path.exists(filename) and filename != merged_filename:
                temp_filename = merged_filename + ".tmp.mkv"

                ffmpeg_command = [
                    'ffmpeg', '-y', '-i', filename, 
                    '-c', 'copy',
                    '-movflags', '+faststart',
                    temp_filename
                ]
                
                result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
                
                if result.returncode == 0:
                    if os.path.exists(merged_filename):
                        os.remove(merged_filename)
                    os.rename(temp_filename, merged_filename)
                    
                    # 清理原始文件
                    if os.path.exists(filename) and filename != merged_filename:
                        try:
                            os.remove(filename)
                        except:
                            pass
                    
                    self.callback_queue.put(('log', None, f"已合并: {merged_filename}"))
                else:
                    # ffmpeg 失败，使用原文件
                    self.callback_queue.put(('log', None, f"合并失败，使用原文件: {filename}"))
                    merged_filename = filename
            
            return merged_filename, hdr_format
    
    def progress_hook(self, d):
        if self.cancelled:
            raise Exception("下载已取消")
        
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', 'N/A').strip()
            eta = d.get('_eta_str', 'N/A').strip()
            self.callback_queue.put(('progress', self.item_id, f"{percent} | {speed} | ETA: {eta}"))
        elif d['status'] == 'finished':
            self.callback_queue.put(('progress', self.item_id, "下载完成，正在处理..."))
    
    def postprocessor_hook(self, d):
        if d['status'] == 'started':
            self.callback_queue.put(('progress', self.item_id, f"后处理: {d.get('postprocessor', 'unknown')}"))


class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Video Downloader v{__version__}")
        self.root.geometry("900x700")
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.use_subfolders_var = tk.BooleanVar(value=use_subfolders)
        self.callback_queue = Queue()
        self.download_threads = {}
        self.is_downloading = False

        self._create_ui()
        self._start_queue_processor()
        
        self.tasks = []

    def _create_ui(self):
        # 路径选择区域
        path_frame = tk.Frame(self.root)
        path_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        path_frame.columnconfigure(1, weight=1)

        tk.Label(path_frame, text="下载路径:").grid(row=0, column=0, sticky="w", pady=5)
        self.path_combobox = ttk.Combobox(path_frame, values=history_paths, width=50)
        self.path_combobox.set(default_download_path)
        self.path_combobox.grid(row=0, column=1, sticky="ew", padx=5)
        path_button = tk.Button(path_frame, text="浏览...", command=self.select_directory)
        path_button.grid(row=0, column=2, padx=5)

        # 视频列表区域
        url_list_frame = tk.LabelFrame(self.root, text="视频列表", padx=5, pady=5)
        url_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        url_list_frame.grid_rowconfigure(0, weight=1)
        url_list_frame.grid_columnconfigure(0, weight=1)

        # 添加状态列
        columns = ("index", "url", "title", "uploader", "hdr_format", "status")
        self.treeview = ttk.Treeview(url_list_frame, columns=columns, show="headings", selectmode="extended")
        
        self.treeview.heading("index", text="#")
        self.treeview.column("index", width=40, anchor="center")
        self.treeview.heading("url", text="URL")
        self.treeview.column("url", width=200, anchor="w")
        self.treeview.heading("title", text="标题")
        self.treeview.column("title", width=250, anchor="w")
        self.treeview.heading("uploader", text="上传者")
        self.treeview.column("uploader", width=100, anchor="center")
        self.treeview.heading("hdr_format", text="HDR格式")
        self.treeview.column("hdr_format", width=80, anchor="center")
        self.treeview.heading("status", text="状态")
        self.treeview.column("status", width=150, anchor="center")
        
        self.treeview.grid(row=0, column=0, sticky="nsew")

        treeview_scrollbar = ttk.Scrollbar(url_list_frame, orient="vertical", command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=treeview_scrollbar.set)
        treeview_scrollbar.grid(row=0, column=1, sticky="ns")
        self.treeview.bind('<Control-a>', self.select_all)
        self.treeview.bind('<Delete>', lambda e: self.on_delete())

        # 编辑删除按钮
        button_edit_delete_frame = tk.Frame(url_list_frame)
        button_edit_delete_frame.grid(row=1, column=0, sticky="ew", pady=5)
        button_edit = tk.Button(button_edit_delete_frame, text="编辑", command=self.on_edit)
        button_edit.pack(side=tk.LEFT, padx=5)
        button_delete = tk.Button(button_edit_delete_frame, text="删除", command=self.on_delete)
        button_delete.pack(side=tk.LEFT, padx=5)

        # 功能按钮区域
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        button_copy = tk.Button(button_frame, text="📋 从剪贴板粘贴", command=self.on_copy_from_clipboard)
        button_copy.pack(side=tk.LEFT, padx=5)
        button_add = tk.Button(button_frame, text="➕ 添加URL", command=self.on_add_url)
        button_add.pack(side=tk.LEFT, padx=5)
        button_add_playlist = tk.Button(button_frame, text="📃 添加播放列表", command=self.on_add_playlist_url)
        button_add_playlist.pack(side=tk.LEFT, padx=5)
        
        self.download_button = tk.Button(button_frame, text="⬇️ 开始下载", command=self.on_download, bg="#4CAF50", fg="white")
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        button_clear = tk.Button(button_frame, text="🗑️ 清空列表", command=self.clear_list)
        button_clear.pack(side=tk.LEFT, padx=5)
        
        subfolder_checkbutton = tk.Checkbutton(button_frame, text="按上传者分文件夹", variable=self.use_subfolders_var)
        subfolder_checkbutton.pack(side=tk.LEFT, padx=5)

        # 日志区域
        log_frame = tk.LabelFrame(self.root, text="任务日志", padx=5, pady=5)
        log_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, state=tk.NORMAL, height=10)
        log_scroll = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        log_scroll.grid(row=0, column=1, sticky="ns")

    def _start_queue_processor(self):
        """处理后台线程的回调消息"""
        self._process_queue()
    
    def _process_queue(self):
        try:
            while not self.callback_queue.empty():
                msg_type, item_id, data = self.callback_queue.get_nowait()
                
                if msg_type == 'log':
                    self.log_message(data)
                elif msg_type == 'progress':
                    self._update_item_status(item_id, data)
                elif msg_type == 'success':
                    filename, hdr_format = data
                    self._on_download_success(item_id, filename, hdr_format)
                elif msg_type == 'error':
                    self._on_download_error(item_id, data)
        except:
            pass
        
        self.root.after(100, self._process_queue)
    
    def _update_item_status(self, item_id, status):
        """更新列表项的状态"""
        try:
            for child in self.treeview.get_children():
                values = self.treeview.item(child, 'values')
                if str(values[0]) == str(item_id):
                    new_values = list(values)
                    new_values[5] = status
                    self.treeview.item(child, values=new_values)
                    break
        except:
            pass
    
    def _on_download_success(self, item_id, filename, hdr_format):
        """下载成功的回调"""
        self.log_message(f"✅ 下载完成: {filename}")
        
        for child in self.treeview.get_children():
            values = self.treeview.item(child, 'values')
            if str(values[0]) == str(item_id):
                self.treeview.delete(child)
                break
        
        self.tasks = [t for t in self.tasks if t[0] != item_id]
        
        if item_id in self.download_threads:
            del self.download_threads[item_id]
        
        self._continue_download_queue()
    
    def _on_download_error(self, item_id, error):
        """下载失败的回调"""
        self.log_message(f"❌ 下载失败: {error}")
        self._update_item_status(item_id, f"失败: {error[:30]}...")
        
        if item_id in self.download_threads:
            del self.download_threads[item_id]
        
        self._continue_download_queue()
    
    def _continue_download_queue(self):
        """继续处理下载队列"""
        if not hasattr(self, 'download_queue') or not self.download_queue:
            self.is_downloading = False
            self.download_button.config(text="⬇️ 开始下载", bg="#4CAF50")
            self.log_message("📦 所有下载任务完成")
            return
        
        next_item = self.download_queue.pop(0)
        self._start_download_item(next_item)

    def on_download(self):
        if self.is_downloading:
            self.log_message("⚠️ 已有下载任务正在进行中...")
            return
        
        output_directory = self.path_combobox.get()
        if not output_directory:
            messagebox.showwarning("路径错误", "请选择或输入下载目录")
            return

        if output_directory not in history_paths:
            history_paths.append(output_directory)
            self.path_combobox['values'] = history_paths

        config["default_path"] = output_directory
        config["history_paths"] = history_paths
        config["use_subfolders"] = self.use_subfolders_var.get()
        save_config(config)

        selected_items = self.treeview.selection()
        if not selected_items:
            messagebox.showwarning("未选择", "请先选择要下载的视频")
            return
        
        self.download_queue = []
        self.output_directory = output_directory
        
        for item in selected_items:
            values = self.treeview.item(item, 'values')
            self.download_queue.append({
                'item_id': values[0],
                'tree_item': item,
                'url': values[1],
                'uploader': values[3]
            })
        
        self.is_downloading = True
        self.download_button.config(text="⏳ 下载中...", bg="#FFA500")
        
        if self.download_queue:
            first_item = self.download_queue.pop(0)
            self._start_download_item(first_item)
    
    def _start_download_item(self, item_info):
        """启动单个下载任务"""
        item_id = item_info['item_id']
        video_url = item_info['url']
        uploader = item_info['uploader']
        
        self._update_item_status(item_id, "下载中...")
        self.log_message(f"🚀 开始下载: {video_url}")
        
        thread = DownloadThread(
            self,
            video_url,
            self.output_directory,
            uploader,
            item_id,
            self.callback_queue
        )
        self.download_threads[item_id] = thread
        thread.start()

    def update_task_hdr_format(self, item_id, hdr_format):
        """更新任务的 HDR 格式信息"""
        for task in self.tasks:
            if task[0] == item_id:
                task[4] = hdr_format
                break
        self.update_treeview()

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path_combobox.set(directory)

    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def select_all(self, event):
        self.treeview.selection_set(self.treeview.get_children())

    def on_copy_from_clipboard(self):
        clipboard = pyperclip.paste()
        urls = clipboard.split()
        count = 0
        for url in urls:
            if url.startswith('http'):
                self.add_task(url)
                count += 1
        self.log_message(f"📋 从剪贴板添加了 {count} 个URL")

    def on_add_url(self):
        self.prompt_for_urls("添加URLs")

    def on_add_playlist_url(self):
        self.prompt_for_playlist_urls("添加播放列表URL")

    def on_edit(self):
        selected_items = self.treeview.selection()
        if selected_items:
            item_id = selected_items[0]
            current_url = self.treeview.item(item_id, 'values')[1]
            self.prompt_for_urls("编辑URL", item_id=item_id, initialtext=current_url)

    def prompt_for_urls(self, title, item_id=None, initialtext=""):
        url_input_box = tk.Toplevel(self.root)
        url_input_box.title(title)
        url_input_box.geometry("600x300")

        tk.Label(url_input_box, text="输入URL（每行一个）:").pack(padx=10, pady=5, anchor="w")
        
        url_input = tk.Text(url_input_box, height=10, width=80)
        url_input.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        if initialtext:
            url_input.insert(tk.END, initialtext)
        url_input.focus_set()

        def submit():
            text = url_input.get("1.0", tk.END).strip()
            urls = [u.strip() for u in text.split('\n') if u.strip().startswith('http')]
            if item_id:
                if urls:
                    self.update_task(item_id, urls[0])
            else:
                for url in urls:
                    self.add_task(url)
            url_input_box.destroy()

        button_frame = tk.Frame(url_input_box)
        button_frame.pack(pady=10)
        
        submit_button = tk.Button(button_frame, text="确定", command=submit, width=10)
        submit_button.pack(side=tk.LEFT, padx=5)
        cancel_button = tk.Button(button_frame, text="取消", command=url_input_box.destroy, width=10)
        cancel_button.pack(side=tk.LEFT, padx=5)

        url_input_box.transient(self.root)
        url_input_box.grab_set()
        self.root.wait_window(url_input_box)

    def prompt_for_playlist_urls(self, title, item_id=None, initialtext=""):
        url_input_box = tk.Toplevel(self.root)
        url_input_box.title(title)
        url_input_box.geometry("600x200")

        tk.Label(url_input_box, text="输入播放列表URL:").pack(padx=10, pady=5, anchor="w")
        
        url_input = tk.Text(url_input_box, height=5, width=80)
        url_input.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        if initialtext:
            url_input.insert(tk.END, initialtext)
        url_input.focus_set()

        def submit():
            text = url_input.get("1.0", tk.END).strip()
            url_input_box.destroy()
            
            self.log_message("🔍 正在解析播放列表...")
            
            def fetch_playlist():
                try:
                    video_urls = get_playlist_video_links(text)
                    self.callback_queue.put(('log', None, f"📃 找到 {len(video_urls)} 个视频"))
                    for url in video_urls:
                        self.root.after(0, lambda u=url: self.add_task(u))
                except Exception as e:
                    self.callback_queue.put(('log', None, f"❌ 解析播放列表失败: {e}"))
            
            threading.Thread(target=fetch_playlist, daemon=True).start()

        button_frame = tk.Frame(url_input_box)
        button_frame.pack(pady=10)
        
        submit_button = tk.Button(button_frame, text="确定", command=submit, width=10)
        submit_button.pack(side=tk.LEFT, padx=5)
        cancel_button = tk.Button(button_frame, text="取消", command=url_input_box.destroy, width=10)
        cancel_button.pack(side=tk.LEFT, padx=5)

        url_input_box.transient(self.root)
        url_input_box.grab_set()
        self.root.wait_window(url_input_box)

    def add_task(self, video_url):
        if not video_url or not video_url.startswith('http'):
            return
        
        # 检查是否已存在
        for task in self.tasks:
            if task[1] == video_url:
                self.log_message(f"⚠️ URL已存在: {video_url[:50]}...")
                return
        
        self.log_message("🔍 正在获取视频信息...")
        
        def fetch_info():
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_check_certificate': True,
                    'extract_flat': False
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video_url, download=False)
                    video_title = info_dict.get('title', 'No title')
                    uploader_name = info_dict.get('uploader') or info_dict.get('channel') or 'Unknown'
                    hdr_format = detect_hdr_format(info_dict)
                    
                    self.root.after(0, lambda: self._add_task_to_list(
                        video_url, video_title, uploader_name, hdr_format
                    ))
            except Exception as e:
                self.callback_queue.put(('log', None, f"❌ 获取视频信息失败: {e}"))
        
        threading.Thread(target=fetch_info, daemon=True).start()
    
    def _add_task_to_list(self, video_url, video_title, uploader_name, hdr_format):
        """将任务添加到列表（在主线程执行）"""
        index = len(self.tasks) + 1
        new_task = [index, video_url, video_title, uploader_name, hdr_format, "待下载"]
        self.tasks.append(new_task)
        self.treeview.insert("", tk.END, values=new_task)
        self.log_message(f"✅ 已添加: {video_title[:50]}...")

    def update_task(self, item_id, video_url):
        if not video_url:
            return
        
        def fetch_info():
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_check_certificate': True
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video_url, download=False)
                    video_title = info_dict.get('title', 'No title')
                    uploader_name = info_dict.get('uploader') or info_dict.get('channel') or 'Unknown'
                    hdr_format = detect_hdr_format(info_dict)
                    
                    self.root.after(0, lambda: self._update_task_in_list(
                        item_id, video_url, video_title, uploader_name, hdr_format
                    ))
            except Exception as e:
                self.callback_queue.put(('log', None, f"❌ 更新视频信息失败: {e}"))
        
        threading.Thread(target=fetch_info, daemon=True).start()
    
    def _update_task_in_list(self, item_id, video_url, video_title, uploader_name, hdr_format):
        """更新列表中的任务"""
        for child in self.treeview.get_children():
            values = self.treeview.item(child, 'values')
            if values[1] == item_id or child == item_id:
                current_index = values[0]
                new_values = [current_index, video_url, video_title, uploader_name, hdr_format, "待下载"]
                self.treeview.item(child, values=new_values)
                break
        
        for task in self.tasks:
            if task[1] == item_id:
                task[1] = video_url
                task[2] = video_title
                task[3] = uploader_name
                task[4] = hdr_format
                break
        
        self.log_message(f"✏️ 已更新: {video_title[:50]}...")

    def update_treeview(self):
        self.treeview.delete(*self.treeview.get_children())
        for task in self.tasks:
            self.treeview.insert("", tk.END, values=task)

    def clear_list(self):
        if self.is_downloading:
            messagebox.showwarning("无法清空", "下载进行中，请等待下载完成")
            return
        self.tasks.clear()
        self.update_treeview()
        self.log_message("🗑️ 列表已清空")

    def on_delete(self):
        if self.is_downloading:
            messagebox.showwarning("无法删除", "下载进行中，请等待下载完成")
            return
        
        selected_items = self.treeview.selection()
        for item_id in selected_items:
            item_index = int(self.treeview.item(item_id, 'values')[0])
            self.tasks = [task for task in self.tasks if task[0] != item_index]
            self.treeview.delete(item_id)
        
        self.update_task_indices()
        self.update_treeview()
        self.log_message(f"🗑️ 已删除 {len(selected_items)} 个项目")

    def update_task_indices(self):
        for index, task in enumerate(self.tasks, start=1):
            task[0] = index


if __name__ == "__main__":
    # 设置 DPI 感知（Windows）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    root = tk.Tk()
    style = ttk.Style()
    style.configure("Treeview.Heading", anchor="center")
    style.configure("Treeview", rowheight=25)
    
    app = YouTubeDownloader(root)
    root.mainloop()

