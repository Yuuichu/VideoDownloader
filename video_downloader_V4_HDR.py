import sys
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import yt_dlp
import pyperclip
import subprocess

def get_script_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

SCRIPT_DIR = get_script_directory()
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    else:
        default_config = {"default_path": "G:\\Compony\\@Recordings\\MiaoVideos\\WebDL\\test2", "history_paths": [], "use_subfolders": False}
        save_config(default_config)
        return default_config

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

config = load_config()
default_download_path = config.get("default_path", "G:\\Compony\\@Recordings\\MiaoVideos\\WebDL\\test2")
history_paths = config.get("history_paths", [])
use_subfolders = config.get("use_subfolders", False)

def get_playlist_video_links(playlist_url):
    ydl_opts = {'quiet': True, 'extract_flat': 'yes'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(playlist_url, download=False)
        video_entries = info_dict.get('entries', [])
        video_links = [f"https://www.youtube.com/watch?v={entry.get('id', '')}" for entry in video_entries if entry.get('id', '')]
        return video_links

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader")
        self.root.geometry("800x600")
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.use_subfolders_var = tk.BooleanVar(value=use_subfolders)

        path_frame = tk.Frame(root)
        path_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        path_frame.columnconfigure(1, weight=1)

        tk.Label(path_frame, text="Download Path:").grid(row=0, column=0, sticky="w", pady=5)
        self.path_combobox = ttk.Combobox(path_frame, values=history_paths, width=50)
        self.path_combobox.set(default_download_path)
        self.path_combobox.grid(row=0, column=1, sticky="ew", padx=5)
        path_button = tk.Button(path_frame, text="Browse...", command=self.select_directory)
        path_button.grid(row=0, column=2, padx=5)

        url_list_frame = tk.LabelFrame(root, text="Video URLs", padx=5, pady=5)
        url_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        url_list_frame.grid_rowconfigure(0, weight=1)
        url_list_frame.grid_columnconfigure(0, weight=1)

        self.treeview = ttk.Treeview(url_list_frame, columns=("index", "url", "title", "uploader", "hdr_format"), show="headings", selectmode="extended")
        self.treeview.heading("index", text="Index")
        self.treeview.column("index", width=60, anchor="center")
        self.treeview.heading("url", text="URL")
        self.treeview.column("url", anchor="w")
        self.treeview.heading("title", text="Title")
        self.treeview.column("title", anchor="w")
        self.treeview.heading("uploader", text="Uploader")
        self.treeview.column("uploader", width=100, anchor="center")
        self.treeview.heading("hdr_format", text="HDR Format")
        self.treeview.column("hdr_format", width=100, anchor="center")
        self.treeview.grid(row=0, column=0, sticky="nsew")

        treeview_scrollbar = ttk.Scrollbar(url_list_frame, orient="vertical", command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=treeview_scrollbar.set)
        treeview_scrollbar.grid(row=0, column=1, sticky="ns")
        self.treeview.bind('<Control-a>', self.select_all)

        button_edit_delete_frame = tk.Frame(url_list_frame)
        button_edit_delete_frame.grid(row=1, column=0, sticky="ew", pady=5)
        button_edit = tk.Button(button_edit_delete_frame, text="Edit", command=self.on_edit)
        button_edit.pack(side=tk.LEFT, padx=5)
        button_delete = tk.Button(button_edit_delete_frame, text="Delete", command=self.on_delete)
        button_delete.pack(side=tk.LEFT, padx=5)

        button_frame = tk.Frame(root)
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        button_copy = tk.Button(button_frame, text="Copy from Clipboard", command=self.on_copy_from_clipboard)
        button_copy.pack(side=tk.LEFT, padx=5)
        button_add = tk.Button(button_frame, text="Add URL", command=self.on_add_url)
        button_add.pack(side=tk.LEFT, padx=5)
        button_add_playlist = tk.Button(button_frame, text="Add Playlist", command=self.on_add_playlist_url)
        button_add_playlist.pack(side=tk.LEFT, padx=5)
        button_download = tk.Button(button_frame, text="Download", command=self.on_download)
        button_download.pack(side=tk.LEFT, padx=5)
        button_clear = tk.Button(button_frame, text="Clear List", command=self.clear_list)
        button_clear.pack(side=tk.LEFT, padx=5)
        subfolder_checkbutton = tk.Checkbutton(button_frame, text="Use subfolder per uploader", variable=self.use_subfolders_var)
        subfolder_checkbutton.pack(side=tk.LEFT, padx=5)

        log_frame = tk.LabelFrame(root, text="Task Logs", padx=5, pady=5)
        log_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, state=tk.NORMAL)
        log_scroll = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        log_scroll.grid(row=0, column=1, sticky="ns")

        self.tasks = []

    def download_and_merge(self, video_url, output_directory, uploader_name=None):
        if self.use_subfolders_var.get() and uploader_name:
            output_directory = os.path.join(output_directory, uploader_name)
            os.makedirs(output_directory, exist_ok=True)

        output_template = os.path.join(output_directory, '%(title)s.%(ext)s')
        ydl_opts = {
            'format': 'bestvideo+bestaudio',
            'outtmpl': output_template,
            'merge_output_format': 'mkv'
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url)
                formats = info.get('formats', [])
                best_video = next((f for f in formats if f.get('vcodec') != 'none'), None)
                video_dynamic_range = (info.get('dynamic_range') or (best_video.get('dynamic_range') if best_video else '非HDR'))
                filename = ydl.prepare_filename(info)
                self.log_message(f"Downloaded: {filename}")

                merged_filename = filename.rsplit('.', 1)[0] + '.mkv'
                temp_filename = merged_filename + ".tmp.mkv"

                ffmpeg_command = [
                    'ffmpeg', '-y', '-i', filename, '-c', 'copy', temp_filename
                ]
                subprocess.run(ffmpeg_command, check=True)

                if os.path.exists(merged_filename):
                    os.remove(merged_filename)

                os.rename(temp_filename, merged_filename)
                self.log_message(f"Merged to: {merged_filename}")

                return merged_filename, video_dynamic_range
        except Exception as e:
            self.log_message(f"Error: {e}")
            return None, None

    def on_download(self):
        output_directory = self.path_combobox.get()
        if not output_directory:
            messagebox.showwarning("Directory Error", "Please select or enter a download directory")
            return

        if output_directory not in history_paths:
            history_paths.append(output_directory)
            self.path_combobox['values'] = history_paths

        config["default_path"] = output_directory
        config["history_paths"] = history_paths
        config["use_subfolders"] = self.use_subfolders_var.get()
        save_config(config)

        selected_items = self.treeview.selection()
        self.download_videos(selected_items, output_directory)

    def download_videos(self, items, output_directory):
        if items:
            item_id = items[0]
            video_url = self.treeview.item(item_id, 'values')[1]
            uploader_name = self.treeview.item(item_id, 'values')[3]
            output_file, hdr_format = self.download_and_merge(video_url, output_directory, uploader_name)
            if output_file:
                self.treeview.delete(item_id)
                self.log_message(f"Download and merge completed: {output_file}")
                self.update_task_hdr_format(item_id, hdr_format)
            else:
                self.log_message(f"Failed to download: {video_url}")
            self.root.after(100, self.download_videos, items[1:], output_directory)

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path_combobox.set(directory)

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def select_all(self, event):
        self.treeview.selection_set(self.treeview.get_children())

    def on_copy_from_clipboard(self):
        clipboard = pyperclip.paste()
        urls = clipboard.split()
        for url in urls:
            self.add_task(url)

    def on_add_url(self):
        self.prompt_for_urls("Add URLs")

    def on_add_playlist_url(self):
        self.prompt_for_playlist_urls("Add Playlist URL")

    def on_edit(self):
        selected_items = self.treeview.selection()
        if selected_items:
            item_id = selected_items[0]
            current_url = self.treeview.item(item_id, 'values')[1]
            self.prompt_for_urls("Edit URL", item_id=item_id, initialtext=current_url)

    def prompt_for_urls(self, title, item_id=None, initialtext=""):
        url_input_box = tk.Toplevel(self.root)
        url_input_box.title(title)

        url_input = tk.Text(url_input_box, height=10, width=100)
        url_input.pack(padx=10, pady=10)
        if initialtext:
            url_input.insert(tk.END, initialtext)
        url_input.focus_set()

        def submit():
            text = url_input.get("1.0", tk.END).strip()
            urls = text.split()
            if item_id:
                self.update_task(item_id, urls[0])
            else:
                for url in urls:
                    self.add_task(url)
            url_input_box.destroy()

        submit_button = tk.Button(url_input_box, text="Submit", command=submit)
        submit_button.pack(pady=10)

        url_input_box.transient(self.root)
        url_input_box.grab_set()
        self.root.wait_window(url_input_box)

    def prompt_for_playlist_urls(self, title, item_id=None, initialtext=""):
        url_input_box = tk.Toplevel(self.root)
        url_input_box.title(title)

        url_input = tk.Text(url_input_box, height=10, width=100)
        url_input.pack(padx=10, pady=10)
        if initialtext:
            url_input.insert(tk.END, initialtext)
        url_input.focus_set()

        def submit():
            text = url_input.get("1.0", tk.END).strip()
            if item_id:
                self.update_task(item_id, get_playlist_video_links(text)[0])
            else:
                video_urls = get_playlist_video_links(text)
                for url in video_urls:
                    self.add_task(url)
            url_input_box.destroy()

        submit_button = tk.Button(url_input_box, text="Submit", command=submit)
        submit_button.pack(pady=10)

        url_input_box.transient(self.root)
        url_input_box.grab_set()
        self.root.wait_window(url_input_box)

    def add_task(self, video_url):
        if video_url:
            try:
                with yt_dlp.YoutubeDL() as ydl:
                    info_dict = ydl.extract_info(video_url, download=False)
                    video_title = info_dict.get('title', 'No title')
                    uploader_name = info_dict.get('uploader', 'Unknown uploader')
                    formats = info_dict.get('formats', [])
                    best_video = next((f for f in formats if f.get('vcodec') != 'none'), None)
                    hdr_format = info_dict.get('dynamic_range') or (best_video.get('dynamic_range') if best_video else '非HDR')
            except Exception as e:
                self.log_message(f"Error: {e}")
                return

            index = len(self.tasks) + 1
            new_task = (index, video_url, video_title, uploader_name, hdr_format)
            self.tasks.append(new_task)
            self.treeview.insert("", tk.END, values=new_task)

    def update_task(self, item_id, video_url):
        if video_url:
            try:
                with yt_dlp.YoutubeDL() as ydl:
                    info_dict = ydl.extract_info(video_url, download=False)
                    video_title = info_dict.get('title', 'No title')
                    uploader_name = info_dict.get('uploader', 'Unknown uploader')
                    formats = info_dict.get('formats', [])
                    best_video = next((f for f in formats if f.get('vcodec') != 'none'), None)
                    hdr_format = info_dict.get('dynamic_range') or (best_video.get('dynamic_range') if best_video else '非HDR')
            except Exception as e:
                self.log_message(f"Error: {e}")
                return

            for task in self.tasks:
                if task[0] == int(item_id):
                    task[1] = video_url
                    task[2] = video_title
                    task[3] = uploader_name
                    task[4] = hdr_format

            self.update_treeview()

    def update_treeview(self):
        self.treeview.delete(*self.treeview.get_children())
        for task in self.tasks:
            self.treeview.insert("", tk.END, values=task)

    def clear_list(self):
        self.tasks.clear()
        self.update_treeview()

    def on_delete(self):
        selected_items = self.treeview.selection()
        for item_id in selected_items:
            item_index = int(self.treeview.item(item_id, 'values')[0])
            self.tasks = [task for task in self.tasks if task[0] != item_index]
            self.treeview.delete(item_id)
        self.update_task_indices()
        self.update_treeview()

    def update_task_indices(self):
        for index, task in enumerate(self.tasks, start=1):
            task[0] = index

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.configure("Treeview.Heading", anchor="center")
    style.configure("Treeview", rowheight=25)
    app = YouTubeDownloader(root)
    root.mainloop()