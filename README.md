# VideoDownloader

A YouTube video downloader with a **DaVinci Resolve-style dark GUI**, built with Python, PySide6 (Qt) and yt-dlp. Works on Windows and macOS with an identical look.

## Features

- 🎬 **DaVinci Resolve 风格界面** - 近黑深色主题、橙色强调色、图标栏页面、内嵌进度条、可折叠控制台、状态栏（Win / Mac 一致）
- 📋 **Clipboard paste** - Quickly add URLs from clipboard
- ➕ **Batch add URLs** - Add multiple URLs at once (one per line)
- 📃 **Playlist support** - Parse and download entire playlists
- 🎬 **HDR detection** - Automatically detect and badge HDR formats (DV, HDR10+, HDR10, HLG)
- ⚙️ **画质上限选择** - 8K / 4K / 1440p / 1080p / 720p，真实作用于 yt-dlp 格式选择
- 📁 **Auto organize** - Optionally create subfolders by uploader
- ⏳ **Non-blocking UI** - Download in background with per-item progress bars
- 🔄 **Auto retry** - Automatically retry failed downloads
- ⏹ **Stop** - Cancel the current download

## Requirements

- Python 3.10+
- FFmpeg (for video merging)
- yt-dlp
- pyperclip
- PySide6 (Qt 6)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/VideoDownloader.git
cd VideoDownloader
```

2. Install dependencies (recommended: use a virtual environment):
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

3. Make sure FFmpeg is installed and in your PATH.

## Usage

Run the application:
```bash
python video_downloader_qt.py     # 新界面（PySide6，达芬奇风格）
```

### Basic workflow:

1. **Set download path** - Choose where to save videos (顶部路径栏 / 设置页)
2. **Add videos** - Use one of these methods:
   - Click "📋 粘贴" to paste URLs from clipboard
   - Click "➕ 添加URL" to manually enter URLs
   - 添加播放列表链接会自动展开为单条视频
3. **Select videos** - Use Ctrl+A to select all, or click individual items
4. **Download** - Click the orange "开始下载" button; each row shows a live progress bar
5. **停止** - Abort the current download mid-flight

### Options (设置页):

- **画质上限** - Max resolution used by the format selector (8K / 4K / 1440p / 1080p / 720p)
- **优先 HDR** - HDR preference flag (persisted; HDR detection shown as badges in the list)
- **按上传者分文件夹** - Create a subfolder for each uploader

### 旧版界面（回退）

`video_downloader.py` 为旧版 tkinter 界面，功能等价、风格朴素；如需回退可直接运行它。新界面逻辑内核在 `downloader_core.py`。

## Building Executable

To create a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onedir --windowed --name VideoDownloader video_downloader_qt.py
```

或使用自动构建脚本（含 ZIP 打包）：
```bash
python build.py
```

> 注：引入 PySide6 后，打包体积约 120–150 MB，属正常。

## License

See [LICENSE](LICENSE) file.
