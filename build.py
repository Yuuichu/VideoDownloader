#!/usr/bin/env python3
"""
Build script for VideoDownloader
Creates a standalone executable using PyInstaller
"""

import subprocess
import sys
import os
import shutil
import zipfile
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 配置
APP_NAME = "VideoDownloader"
MAIN_SCRIPT = "video_downloader.py"
VERSION = "1.0.0"

def install_pyinstaller():
    """确保 PyInstaller 已安装"""
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__} installed")
    except ImportError:
        print("[*] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller installed")

def clean_build():
    """清理之前的构建文件"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for d in dirs_to_clean:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"[*] Cleaned: {d}")
    
    # 清理 .spec 文件
    for f in os.listdir('.'):
        if f.endswith('.spec'):
            os.remove(f)
            print(f"[*] Cleaned: {f}")

def build_exe():
    """使用 PyInstaller 构建可执行文件"""
    print("\n[*] Building executable...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",           # 创建目录（比 onefile 启动更快）
        "--windowed",         # 不显示控制台窗口
        "--noconfirm",        # 覆盖已有文件
        "--clean",            # 清理缓存
        "--add-data", f"README.md{os.pathsep}.",  # 包含 README
        MAIN_SCRIPT
    ]
    
    subprocess.check_call(cmd)
    print("[OK] Build completed")

def create_zip():
    """创建发布用的 ZIP 文件"""
    dist_dir = os.path.join("dist", APP_NAME)
    if not os.path.exists(dist_dir):
        print("[ERROR] Build directory not found")
        return None
    
    zip_name = f"{APP_NAME}-v{VERSION}-windows-x64.zip"
    zip_path = os.path.join("dist", zip_name)
    
    print(f"\n[*] Creating {zip_name}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "dist")
                zipf.write(file_path, arcname)
    
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[OK] Created: {zip_path} ({size_mb:.1f} MB)")
    return zip_path

def main():
    print("""
========================================
     VideoDownloader Build Script
              v1.0.0
========================================
""")
    
    # 切换到脚本所在目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    install_pyinstaller()
    clean_build()
    build_exe()
    zip_path = create_zip()
    
    print(f"""
========================================
           BUILD COMPLETE!
========================================

[>] Executable: dist/{APP_NAME}/{APP_NAME}.exe
[>] Release ZIP: {zip_path}

Next: Upload the ZIP file to GitHub Release
""")

if __name__ == "__main__":
    main()

