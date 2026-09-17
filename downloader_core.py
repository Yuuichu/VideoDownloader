#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoDownloader 核心逻辑模块（无 GUI 依赖，供 PySide6 UI 使用）

从 video_downloader.py（tkinter 旧版）提取并保持等价行为：
- 配置读写（config.json，frozen 兼容路径）
- yt-dlp 辅助（JS 运行时探测、播放列表展开、HDR 检测、格式选择）
- 后台下载线程（QThread + 信号），支持进度数值回调与取消
- 视频信息抓取线程（QThread + 信号）
"""

import os
import sys
import json
import time
import shutil
import threading

import yt_dlp
from PySide6.QtCore import QThread, Signal

__version__ = "2.0.0"

# ---------------------------------------------------------------- 配置

def get_script_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


SCRIPT_DIR = get_script_directory()
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

DEFAULT_CONFIG = {
    "default_path": "",
    "history_paths": [],
    "use_subfolders": False,
    "prefer_hdr": True,
    "max_resolution": "4320",   # 8K
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            merged = dict(DEFAULT_CONFIG)
            merged.update(data or {})
            return merged
        except (json.JSONDecodeError, IOError):
            pass
    save_config(DEFAULT_CONFIG)
    return dict(DEFAULT_CONFIG)


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4, ensure_ascii=False)
    except OSError:
        pass


# ---------------------------------------------------------------- yt-dlp 辅助

def with_js_runtimes(ydl_opts):
    """为 yt-dlp 配置可用的 JS 运行时（node/deno）。

    新版 yt-dlp 提取 YouTube 完整格式需要 JS 运行时 + yt-dlp-ejs；
    探测 PATH 中可用的运行时并写入 ydl_opts，找不到则保持原样。
    注意：js_runtimes 的取值必须是配置字典（无额外配置时传空字典），传 None 会崩溃。
    """
    for runtime in ('node', 'deno'):
        if shutil.which(runtime):
            ydl_opts.setdefault('js_runtimes', {})[runtime] = {}
    return ydl_opts


def get_playlist_video_links(playlist_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'ignoreerrors': True,
    }
    with_js_runtimes(ydl_opts)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(playlist_url, download=False)
        video_entries = info_dict.get('entries', [])
        video_links = []
        for entry in video_entries:
            if entry and entry.get('id'):
                # 构造纯视频链接（不带 list 参数），确保后续只下载单条视频
                video_links.append(f"https://www.youtube.com/watch?v={entry.get('id')}")
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


# ---------------------------------------------------------------- 格式选择

# config.json 中 max_resolution 取值 -> 展示标签
RESOLUTION_VALUES = ["4320", "2160", "1440", "1080", "720"]
RESOLUTION_LABELS = {
    "4320": "8K  (4320p)",
    "2160": "4K  (2160p)",
    "1440": "1440p",
    "1080": "1080p",
    "720":  "720p",
}


def build_format_selector(max_resolution):
    """根据画质上限构造 yt-dlp 格式选择串。

    4320（8K/自动）保持原版行为 bestvideo+bestaudio/best；
    其余档位附加 height 过滤，并保留 /best 兜底。
    """
    max_resolution = str(max_resolution or "4320")
    if max_resolution == "4320":
        return 'bestvideo+bestaudio/best'
    try:
        height = int(max_resolution)
    except (TypeError, ValueError):
        return 'bestvideo+bestaudio/best'
    return f'bestvideo[height<={height}]+bestaudio/best'


def format_speed(bps):
    if not bps:
        return 'N/A'
    if bps >= 1e9:
        return f"{bps / 1e9:.1f} GB/s"
    if bps >= 1e6:
        return f"{bps / 1e6:.1f} MB/s"
    if bps >= 1e3:
        return f"{bps / 1e3:.0f} KB/s"
    return f"{bps:.0f} B/s"


def format_eta(seconds):
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return '--'
    if seconds < 0:
        return '--'
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


# ---------------------------------------------------------------- 数据模型

class TaskItem:
    """队列中的一项任务"""
    __slots__ = ("item_id", "url", "title", "uploader", "hdr",
                 "status", "pct", "speed", "eta", "phase")

    def __init__(self, item_id, url, title="", uploader="", hdr="", status="待下载"):
        self.item_id = item_id
        self.url = url
        self.title = title
        self.uploader = uploader
        self.hdr = hdr
        self.status = status
        self.pct = 0.0
        self.speed = ""
        self.eta = ""
        self.phase = "idle"   # idle | downloading | processing

    def display_status(self):
        """状态列的展示文本"""
        if self.phase == "processing":
            return "处理中…"
        if self.phase == "downloading":
            parts = [f"{self.pct:.0f}%"]
            if self.speed:
                parts.append(self.speed)
            if self.eta and self.eta != "--":
                parts.append(f"ETA {self.eta}")
            return "  ".join(parts)
        return self.status


# ---------------------------------------------------------------- 下载线程

class DownloadWorker(QThread):
    """单个下载任务的后台线程（QThread + 信号，跨线程安全）"""

    log = Signal(str)                                  # 日志行
    progress = Signal(str, float, str, str, str)       # item_id, pct(0-100), speed, eta, phase
    succeeded = Signal(str, str, str)                  # item_id, filename, hdr
    failed = Signal(str, str)                          # item_id, error

    def __init__(self, video_url, output_directory, uploader_name, item_id,
                 format_selector='bestvideo+bestaudio/best', use_subfolders=False,
                 parent=None):
        super().__init__(parent)
        self.video_url = video_url
        self.output_directory = output_directory
        self.uploader_name = uploader_name or ''
        self.item_id = item_id
        self.format_selector = format_selector
        self.use_subfolders = use_subfolders
        self._cancelled = False
        self._cancel_lock = threading.Lock()

    def cancel(self):
        with self._cancel_lock:
            self._cancelled = True

    def is_cancelled(self):
        with self._cancel_lock:
            return self._cancelled

    def run(self):
        try:
            filename, hdr_format = self.download_and_merge()
            if filename:
                self.succeeded.emit(self.item_id, filename, hdr_format)
        except Exception as e:
            self.failed.emit(self.item_id, str(e))

    def download_and_merge(self):
        if self.use_subfolders and self.uploader_name:
            output_directory = os.path.join(self.output_directory, self.uploader_name)
            os.makedirs(output_directory, exist_ok=True)
        else:
            output_directory = self.output_directory

        output_template = os.path.join(output_directory, '%(title)s.%(ext)s')

        ydl_opts = {
            'format': self.format_selector,
            'outtmpl': output_template,
            'merge_output_format': 'mkv',
            'noplaylist': True,      # 单视频下载：忽略 URL 中的 list 参数，只下载该视频
            'retries': 5,
            'fragment_retries': 5,
            'progress_hooks': [self.progress_hook],
            'postprocessor_hooks': [self.postprocessor_hook],
            'quiet': False,
            'no_warnings': False,
        }
        with_js_runtimes(ydl_opts)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.video_url)
            if info.get('_type') == 'playlist':
                raise Exception("检测到播放列表：请使用「添加URL」添加（会自动展开整个列表）")
            hdr_format = detect_hdr_format(info)
            filename = ydl.prepare_filename(info)

            self.log.emit(f"已下载: {filename}")

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
                    temp_filename,
                ]

                result = subprocess_run(ffmpeg_command)

                if result and result.returncode == 0:
                    if os.path.exists(merged_filename):
                        os.remove(merged_filename)
                    os.rename(temp_filename, merged_filename)

                    # 清理原始文件
                    if os.path.exists(filename) and filename != merged_filename:
                        try:
                            os.remove(filename)
                        except OSError:
                            pass

                    self.log.emit(f"已合并: {merged_filename}")
                else:
                    # ffmpeg 失败，使用原文件
                    self.log.emit(f"合并失败，使用原文件: {filename}")
                    merged_filename = filename

            return merged_filename, hdr_format

    def progress_hook(self, d):
        if self.is_cancelled():
            raise Exception("下载已取消")

        status = d.get('status')
        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            pct = (downloaded / total * 100.0) if total else 0.0
            speed = format_speed(d.get('speed'))
            eta = format_eta(d.get('eta'))
            self.progress.emit(self.item_id, pct, speed, eta, 'downloading')
        elif status == 'finished':
            self.progress.emit(self.item_id, 100.0, "", "", 'processing')

    def postprocessor_hook(self, d):
        if d.get('status') == 'started':
            self.log.emit(f"后处理: {d.get('postprocessor', 'unknown')}")


def subprocess_run(ffmpeg_command):
    """运行外部命令并捕获输出（隔离 subprocess 导入，便于测试/无窗口场景）"""
    import subprocess
    try:
        return subprocess.run(ffmpeg_command, capture_output=True, text=True, timeout=3600)
    except Exception:
        return None


# ---------------------------------------------------------------- 信息抓取线程

class FetchInfoWorker(QThread):
    """抓取单个 URL 的视频信息（标题/上传者/HDR），检测播放列表并展开"""

    fetched = Signal(str, str, str, str)     # url, title, uploader, hdr
    playlist_detected = Signal(str, list)    # playlist_url, [video urls]
    log = Signal(str)
    error = Signal(str)

    def __init__(self, video_url, parent=None):
        super().__init__(parent)
        self.video_url = video_url

    def run(self):
        try:
            ydl_opts = {
                'quiet': True,
                'extract_flat': False,
                'noplaylist': True,   # 只提取该视频的信息，不展开播放列表
            }
            with_js_runtimes(ydl_opts)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.video_url, download=False)
                if info_dict.get('_type') == 'playlist':
                    # 智能展开：检测到播放列表，自动解析并逐条返回视频链接
                    video_links = get_playlist_video_links(self.video_url)
                    self.playlist_detected.emit(self.video_url, video_links)
                    return
                video_title = info_dict.get('title', 'No title')
                uploader_name = info_dict.get('uploader') or info_dict.get('channel') or 'Unknown'
                hdr_format = detect_hdr_format(info_dict)
                self.fetched.emit(self.video_url, video_title, uploader_name, hdr_format)
        except Exception as e:
            self.error.emit(str(e))


def now_timestamp():
    return time.strftime("%H:%M:%S")
