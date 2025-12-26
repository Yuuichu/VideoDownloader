# VideoDownloader

A YouTube video downloader with GUI, built with Python and yt-dlp.

## Features

- 📋 **Clipboard paste** - Quickly add URLs from clipboard
- ➕ **Batch add URLs** - Add multiple URLs at once (one per line)
- 📃 **Playlist support** - Parse and download entire playlists
- 🎬 **HDR detection** - Automatically detect and prioritize HDR formats (DV, HDR10+, HDR10, HLG)
- 📁 **Auto organize** - Optionally create subfolders by uploader
- ⏳ **Non-blocking UI** - Download in background with progress display
- 🔄 **Auto retry** - Automatically retry failed downloads

## Requirements

- Python 3.8+
- FFmpeg (for video merging)
- yt-dlp
- pyperclip

## Installation

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/VideoDownloader.git
cd VideoDownloader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure FFmpeg is installed and in your PATH.

## Usage

Run the application:
```bash
python video_downloader.py
```

### Basic workflow:

1. **Set download path** - Choose where to save videos
2. **Add videos** - Use one of these methods:
   - Click "📋 从剪贴板粘贴" to paste URLs from clipboard
   - Click "➕ 添加URL" to manually enter URLs
   - Click "📃 添加播放列表" to add a playlist URL
3. **Select videos** - Use Ctrl+A to select all, or click individual items
4. **Download** - Click "⬇️ 开始下载" to start downloading

### Options:

- **按上传者分文件夹** - Create a subfolder for each uploader

## Building Executable

To create a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onedir --windowed --name VideoDownloader video_downloader.py
```

## License

See [LICENSE](LICENSE) file.
