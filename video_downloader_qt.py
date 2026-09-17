#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoDownloader v2 - 达芬奇 Resolve 风格深色界面（PySide6）

Win / Mac 通用：QSS + Fusion 风格保证两平台外观一致。
依赖：downloader_core.py（下载逻辑）、PySide6、yt-dlp、pyperclip。
"""

import sys
import os
import shutil
from collections import deque

import pyperclip
import yt_dlp
from PySide6 import __version__ as pyside6_version
from PySide6.QtCore import (Qt, QAbstractTableModel, QModelIndex, QPoint, QPointF,
                            QRect, QSize, QTimer)
from PySide6.QtGui import (QBrush, QColor, QFontMetrics, QIcon,
                           QKeySequence, QPainter, QPen, QPixmap, QShortcut)
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication,
                               QComboBox, QDialog, QFileDialog, QHBoxLayout,
                               QHeaderView, QLabel, QListWidget,
                               QListWidgetItem, QMainWindow, QMessageBox,
                               QPlainTextEdit, QPushButton, QStackedWidget,
                               QStyledItemDelegate, QStyle, QTableView,
                               QToolButton, QVBoxLayout, QWidget)

import downloader_core as core

__version__ = core.__version__

# ================================================================ 主题令牌

THEME = {
    "bg_main": "#1a1a1a",
    "bg_toolbar": "#0e0e0e",
    "bg_panel": "#1e1e1e",
    "bg_input": "#0e0e0e",
    "border": "#2a2a2a",
    "border_input": "#3a3a3a",
    "border_focus": "#5a5a5a",
    "text_primary": "#d0d0d0",
    "text_secondary": "#909090",
    "text_tertiary": "#707070",
    "accent": "#FF6E00",
    "accent_hover": "#FF7E10",
    "accent_pressed": "#E56300",
    "success": "#67C23A",
    "warning": "#FF9500",
    "danger": "#E5484D",
    "selection": "#33445f",
}

QSS = """
QMainWindow, QDialog { background: #1a1a1a; }
QWidget { color: #d0d0d0; font-size: 12px; }
QWidget#Toolbar { background: #0e0e0e; border-bottom: 1px solid #2a2a2a; }
QWidget#ActionBar { background: #0e0e0e; border-top: 1px solid #2a2a2a; }

QLabel#SectionTitle { color: #707070; font-size: 10px; font-weight: bold; }
QLabel#AppTitle { color: #FF6E00; font-size: 13px; font-weight: bold; }
QLabel#AppSubtitle { color: #707070; font-size: 10px; }
QLabel#ValueText { color: #d0d0d0; font-size: 12px; }
QLabel#FieldLabel { color: #909090; font-size: 11px; }

QPushButton {
    background: #1e1e1e; color: #d0d0d0;
    border: 1px solid #3a3a3a; border-radius: 3px;
    padding: 6px 14px; font-size: 12px;
}
QPushButton:hover { background: #262626; border-color: #5a5a5a; }
QPushButton:pressed { background: #161616; }
QPushButton:disabled { color: #555555; border-color: #2a2a2a; background: #161616; }
QPushButton#PrimaryButton {
    background: #FF6E00; color: #ffffff; border: 1px solid #FF6E00;
    font-weight: bold; padding: 8px 26px;
}
QPushButton#PrimaryButton:hover { background: #FF7E10; border-color: #FF7E10; }
QPushButton#PrimaryButton:pressed { background: #E56300; }
QPushButton#PrimaryButton:disabled { background: #5a3a20; color: #c0a08a; border-color: #5a3a20; }
QPushButton#DangerButton { color: #E5484D; border-color: #4a2a2e; }
QPushButton#DangerButton:hover { background: #2a1f22; border-color: #6a3a3e; }

QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {
    background: #0e0e0e; color: #d0d0d0;
    border: 1px solid #3a3a3a; border-radius: 3px;
    padding: 5px 8px;
    selection-background-color: #FF6E00; selection-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus { border-color: #5a5a5a; }
QLineEdit:disabled, QComboBox:disabled { color: #555555; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #161616; color: #d0d0d0; border: 1px solid #3a3a3a;
    selection-background-color: #FF6E00; selection-color: #ffffff; outline: 0;
}

QTableView {
    background: #1a1a1a; alternate-background-color: #1d1d1d;
    border: 1px solid #2a2a2a; gridline-color: #242424;
    selection-background-color: #33445f; selection-color: #ffffff;
}
QHeaderView::section {
    background: #161616; color: #707070; border: none;
    border-right: 1px solid #2a2a2a; border-bottom: 1px solid #2a2a2a;
    padding: 6px 8px; font-size: 10px; font-weight: bold;
}
QTableCornerButton::section { background: #161616; border: none; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #3a3a3a; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #4a4a4a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: #3a3a3a; border-radius: 5px; min-width: 24px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }

QListWidget#Rail { background: #0e0e0e; border: none; border-right: 1px solid #2a2a2a; outline: 0; }
QListWidget#Rail::item { color: #707070; font-size: 9px; padding: 10px 0; border: none; }
QListWidget#Rail::item:selected { color: #FF6E00; background: transparent; }
QListWidget#Rail::item:hover { color: #d0d0d0; }

QPlainTextEdit#Console {
    background: #0e0e0e; color: #9ab0c9; border: none; border-top: 1px solid #2a2a2a;
    font-family: Consolas, Menlo, "Courier New", monospace; font-size: 11px; padding: 6px;
}

QStatusBar { background: #0e0e0e; color: #909090; border-top: 1px solid #2a2a2a; font-size: 11px; }
QStatusBar::item { border: none; }

QToolButton {
    background: transparent; color: #909090; border: none; border-radius: 3px; padding: 4px 8px;
}
QToolButton:hover { background: #262626; color: #d0d0d0; }
QToolButton:pressed { background: #1a1a1a; }
QToolButton:checked { background: #262626; color: #FF6E00; }

QToolTip { background: #161616; color: #d0d0d0; border: 1px solid #3a3a3a; padding: 4px; }

QMessageBox { background: #1a1a1a; }
QMessageBox QLabel { color: #d0d0d0; }
"""


def apply_dark_palette(app):
    from PySide6.QtGui import QPalette
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(THEME["bg_main"]))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(THEME["text_primary"]))
    pal.setColor(QPalette.ColorRole.Base, QColor(THEME["bg_input"]))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#1d1d1d"))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor("#161616"))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(THEME["text_primary"]))
    pal.setColor(QPalette.ColorRole.Text, QColor(THEME["text_primary"]))
    pal.setColor(QPalette.ColorRole.Button, QColor(THEME["bg_panel"]))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(THEME["text_primary"]))
    pal.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(THEME["accent"]))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.Link, QColor(THEME["accent"]))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(THEME["text_tertiary"]))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#555555"))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#555555"))
    app.setPalette(pal)


# ================================================================ 图标（QPainter 内绘，无外部资源）

def make_icon(draw_fn, size=18):
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_fn(p, size)
    p.end()
    return QIcon(pm)


def pen_for(p, size, color="#d0d0d0", width=None):
    pen = QPen(QColor(color))
    pen.setWidthF(width if width else max(1.5, size / 11))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)


def icon_clipboard():
    def draw(p, s):
        pen_for(p, s)
        p.drawRoundedRect(s * 0.30, s * 0.22, s * 0.40, s * 0.66, s * 0.05, s * 0.05)
        p.drawRoundedRect(s * 0.40, s * 0.13, s * 0.20, s * 0.20, s * 0.04, s * 0.04)
        p.drawLine(QPointF(s * 0.40, s * 0.55), QPointF(s * 0.60, s * 0.55))
        p.drawLine(QPointF(s * 0.40, s * 0.68), QPointF(s * 0.60, s * 0.68))
    return make_icon(draw)


def icon_plus():
    def draw(p, s):
        pen_for(p, s, "#d0d0d0", max(1.6, s / 10))
        cx, cy = s * 0.5, s * 0.5
        p.drawLine(QPointF(s * 0.28, cy), QPointF(s * 0.72, cy))
        p.drawLine(QPointF(cx, s * 0.28), QPointF(cx, s * 0.72))
    return make_icon(draw)


def icon_pencil():
    def draw(p, s):
        pen_for(p, s, "#d0d0d0", max(1.4, s / 12))
        p.drawLine(QPointF(s * 0.22, s * 0.78), QPointF(s * 0.30, s * 0.62))
        p.drawLine(QPointF(s * 0.30, s * 0.62), QPointF(s * 0.72, s * 0.22))
        p.drawLine(QPointF(s * 0.72, s * 0.22), QPointF(s * 0.78, s * 0.28))
        p.drawLine(QPointF(s * 0.78, s * 0.28), QPointF(s * 0.38, s * 0.68))
        p.drawLine(QPointF(s * 0.22, s * 0.78), QPointF(s * 0.38, s * 0.68))
    return make_icon(draw)


def icon_trash():
    def draw(p, s):
        pen_for(p, s, "#E5484D", max(1.4, s / 12))
        p.drawLine(QPointF(s * 0.30, s * 0.30), QPointF(s * 0.32, s * 0.78))
        p.drawLine(QPointF(s * 0.70, s * 0.30), QPointF(s * 0.68, s * 0.78))
        p.drawLine(QPointF(s * 0.22, s * 0.30), QPointF(s * 0.78, s * 0.30))
        p.drawLine(QPointF(s * 0.40, s * 0.20), QPointF(s * 0.60, s * 0.20))
        p.drawLine(QPointF(s * 0.44, s * 0.44), QPointF(s * 0.46, s * 0.66))
        p.drawLine(QPointF(s * 0.56, s * 0.44), QPointF(s * 0.54, s * 0.66))
    return make_icon(draw)


def icon_clear():
    def draw(p, s):
        pen_for(p, s, "#d0d0d0", max(1.5, s / 11))
        m = s * 0.25
        p.drawLine(QPointF(m, m), QPointF(s - m, s - m))
        p.drawLine(QPointF(s - m, m), QPointF(m, s - m))
    return make_icon(draw)


def icon_folder():
    def draw(p, s):
        pen_for(p, s, "#d0d0d0", max(1.4, s / 12))
        p.drawRoundedRect(s * 0.12, s * 0.28, s * 0.76, s * 0.48, s * 0.04, s * 0.04)
        p.drawLine(QPointF(s * 0.12, s * 0.46), QPointF(s * 0.42, s * 0.46))
        p.drawLine(QPointF(s * 0.40, s * 0.46), QPointF(s * 0.52, s * 0.56))
        p.drawLine(QPointF(s * 0.52, s * 0.56), QPointF(s * 0.70, s * 0.56))
    return make_icon(draw)


def icon_stop():
    def draw(p, s):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#E5484D"))
        p.drawRoundedRect(s * 0.26, s * 0.26, s * 0.48, s * 0.48, s * 0.08, s * 0.08)
    return make_icon(draw)


def icon_download():
    def draw(p, s):
        pen_for(p, s, "#ffffff", max(1.6, s / 10))
        cx = s * 0.5
        p.drawLine(QPointF(cx, s * 0.16), QPointF(cx, s * 0.62))
        p.drawLine(QPointF(cx - s * 0.2, s * 0.46), QPointF(cx, s * 0.66))
        p.drawLine(QPointF(cx + s * 0.2, s * 0.46), QPointF(cx, s * 0.66))
        p.drawLine(QPointF(s * 0.2, s * 0.82), QPointF(s * 0.8, s * 0.82))
    return make_icon(draw)


def icon_queue():
    def draw(p, s):
        pen_for(p, s, "#d0d0d0", max(1.6, s / 10))
        p.drawLine(QPointF(s * 0.18, s * 0.28), QPointF(s * 0.82, s * 0.28))
        p.drawLine(QPointF(s * 0.18, s * 0.50), QPointF(s * 0.82, s * 0.50))
        p.drawLine(QPointF(s * 0.18, s * 0.72), QPointF(s * 0.82, s * 0.72))
    return make_icon(draw)


def icon_settings():
    def draw(p, s):
        pen_for(p, s, "#d0d0d0", max(1.6, s / 10))
        for y, x1, x2 in ((0.28, 0.20, 0.80), (0.50, 0.20, 0.80), (0.72, 0.20, 0.80)):
            p.drawLine(QPointF(s * x1, s * y), QPointF(s * x2, s * y))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#FF6E00"))
        for y in (0.28, 0.50, 0.72):
            p.drawEllipse(QPointF(s * 0.64, s * y), s * 0.075, s * 0.075)
    return make_icon(draw)


def brand_pixmap(size=22):
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(THEME["accent"]))
    p.drawRoundedRect(0, 0, size, size, 5, 5)
    pen = QPen(QColor("#ffffff"))
    pen.setWidthF(max(1.8, size / 11))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    cx = size / 2
    p.drawLine(QPointF(cx, size * 0.30), QPointF(cx, size * 0.62))
    p.drawLine(QPointF(cx - size * 0.18, size * 0.48), QPointF(cx, size * 0.66))
    p.drawLine(QPointF(cx + size * 0.18, size * 0.48), QPointF(cx, size * 0.66))
    p.drawLine(QPointF(size * 0.24, size * 0.76), QPointF(size * 0.76, size * 0.76))
    p.end()
    return pm


# ================================================================ 达芬奇风格开关

class Switch(QAbstractButton):
    """扁平拨动开关（达芬奇式）"""

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(36, 20)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        on = self.isChecked()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(THEME["accent"]) if on else QColor("#3a3a3a"))
        p.drawRoundedRect(self.rect(), 10, 10)
        p.setBrush(QColor("#ffffff") if on else QColor("#909090"))
        margin = 2
        d = self.height() - margin * 2
        x = self.width() - margin - d if on else margin
        p.drawEllipse(x, margin, d, d)
        p.end()


# ================================================================ 队列表格模型与委托

class TaskTableModel(QAbstractTableModel):
    HEADERS = ["#", "标题", "上传者", "HDR", "状态"]
    COL_INDEX, COL_TITLE, COL_UPLOADER, COL_HDR, COL_STATUS = range(5)
    RoleItem = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.items)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.items):
            return None
        item = self.items[index.row()]
        col = index.column()
        if role == self.RoleItem:
            return item
        if role == Qt.ItemDataRole.DisplayRole:
            if col == self.COL_INDEX:
                return item.item_id
            if col == self.COL_TITLE:
                return item.title or "获取中…"
            if col == self.COL_UPLOADER:
                return item.uploader
            if col == self.COL_HDR:
                return item.hdr or "SDR"
            if col == self.COL_STATUS:
                return item.display_status()
        if role == Qt.ItemDataRole.ForegroundRole:
            if col == self.COL_HDR:
                return QBrush(QColor(THEME["accent"]) if item.hdr and item.hdr != "SDR" else QColor(THEME["text_tertiary"]))
            if col == self.COL_STATUS and item.status == "失败":
                return QBrush(QColor(THEME["danger"]))
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (self.COL_INDEX, self.COL_UPLOADER, self.COL_HDR):
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if role == Qt.ItemDataRole.ToolTipRole:
            if col == self.COL_TITLE:
                return item.url
        return None

    # ---- 变更接口 ----

    def add_item(self, item):
        self.beginInsertRows(QModelIndex(), len(self.items), len(self.items))
        self.items.append(item)
        self.endInsertRows()

    def find_row(self, item_id):
        for i, it in enumerate(self.items):
            if it.item_id == item_id:
                return i
        return -1

    def get(self, item_id):
        row = self.find_row(item_id)
        return self.items[row] if row >= 0 else None

    def _touch(self, row):
        top = self.index(row, 0)
        bottom = self.index(row, self.columnCount() - 1)
        self.dataChanged.emit(top, bottom)

    def set_info(self, item_id, title, uploader, hdr):
        row = self.find_row(item_id)
        if row < 0:
            return
        it = self.items[row]
        it.title, it.uploader, it.hdr = title, uploader, hdr
        it.status = "待下载"
        self._touch(row)

    def set_status(self, item_id, status, phase="idle"):
        row = self.find_row(item_id)
        if row < 0:
            return
        it = self.items[row]
        it.status = status
        it.phase = phase
        if phase != "downloading":
            it.pct, it.speed, it.eta = 0.0, "", ""
        self._touch(row)

    def update_progress(self, item_id, pct, speed, eta, phase):
        row = self.find_row(item_id)
        if row < 0:
            return
        it = self.items[row]
        it.pct = max(0.0, min(100.0, pct))
        it.speed, it.eta, it.phase = speed, eta, phase
        it.status = "下载中" if phase == "downloading" else "处理中"
        self._touch(row)

    def remove_item(self, item_id):
        row = self.find_row(item_id)
        if row < 0:
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        self.items.pop(row)
        self.endRemoveRows()

    def clear(self):
        self.beginResetModel()
        self.items.clear()
        self.endResetModel()

    def renumber(self):
        for i, it in enumerate(self.items, start=1):
            it.item_id = str(i)


def _paint_row_background(painter, option, index):
    """自定义委托需自行绘制行背景（选中/隔行），与 QSS 一致"""
    if option.state & QStyle.StateFlag.State_Selected:
        color = QColor("#33445f")
    elif index.row() % 2 == 1:
        color = QColor("#1d1d1d")
    else:
        color = QColor("#1a1a1a")
    painter.fillRect(option.rect, color)


class StatusDelegate(QStyledItemDelegate):
    """状态列：状态圆点 + 内嵌进度条"""

    DOT_COLORS = {
        "待下载": QColor("#707070"),
        "解析中": QColor("#5B8DEF"),
        "下载中": QColor(THEME["accent"]),
        "处理中": QColor(THEME["warning"]),
        "失败": QColor(THEME["danger"]),
        "已取消": QColor("#909090"),
    }

    def paint(self, painter, option, index):
        item = index.data(TaskTableModel.RoleItem)
        if item is None:
            super().paint(painter, option, index)
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        _paint_row_background(painter, option, index)

        if selected:
            text_color = QColor("#ffffff")
        elif item.status == "失败":
            text_color = QColor(THEME["danger"])
        else:
            text_color = QColor(THEME["text_primary"])

        dot_color = self.DOT_COLORS.get(item.status, QColor("#707070"))
        fm = QFontMetrics(option.font)
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""

        margin = 10
        dot_r = 4
        dot_center = QPoint(rect.left() + margin + dot_r, rect.center().y())

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(dot_color)
        painter.drawEllipse(dot_center, dot_r, dot_r)

        text_rect = QRect(rect.left() + margin + dot_r * 2 + 8, rect.top(),
                          rect.width() - (margin + dot_r * 2 + 8) * 2, rect.height())

        if item.phase in ("downloading", "processing"):
            bar_rect = QRect(text_rect.left() + 2, rect.bottom() - 11, text_rect.width() - 4, 4)
            painter.setBrush(QColor("#2a2a2a"))
            painter.drawRoundedRect(bar_rect, 2, 2)
            if item.phase == "processing":
                fill = bar_rect
                bar_color = QColor(THEME["warning"])
            else:
                shrink = int(bar_rect.width() * (1.0 - item.pct / 100.0))
                fill = bar_rect.adjusted(0, 0, -shrink, 0)
                bar_color = QColor(THEME["accent"])
            painter.setBrush(bar_color)
            painter.drawRoundedRect(fill, 2, 2)
            painter.setPen(text_color)
            painter.drawText(text_rect.adjusted(0, -7, 0, -4),
                             int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), text)
        else:
            painter.setPen(text_color)
            painter.drawText(text_rect,
                             int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), text)
        painter.restore()


class HdrDelegate(QStyledItemDelegate):
    """HDR 列：圆角徽章"""

    def paint(self, painter, option, index):
        hdr = index.data(Qt.ItemDataRole.DisplayRole) or "SDR"
        is_hdr = hdr not in ("SDR", "")
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        _paint_row_background(painter, option, index)
        fm = QFontMetrics(option.font)
        text = hdr
        w = fm.horizontalAdvance(text) + 16
        h = fm.height() + 6
        rect = QRect(0, 0, w, h)
        rect.moveCenter(option.rect.center())
        painter.setPen(QPen(QColor(THEME["accent"]), 1) if is_hdr else QPen(QColor("#4a4a4a"), 1))
        painter.setBrush(QColor(255, 110, 0, 26) if is_hdr else QColor(90, 90, 90, 30))
        painter.drawRoundedRect(rect, 3, 3)
        painter.setPen(QColor(THEME["accent"]) if is_hdr else QColor(THEME["text_secondary"]))
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), text)
        painter.restore()


# ================================================================ 弹窗

class AddUrlDialog(QDialog):
    def __init__(self, title, initial="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(560, 320)
        self.setMinimumSize(420, 240)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 12)
        lay.setSpacing(10)

        tip = QLabel("输入 URL（每行一个，支持单视频 / 播放列表链接）：")
        tip.setObjectName("FieldLabel")
        lay.addWidget(tip)

        self.text = QPlainTextEdit()
        self.text.setPlainText(initial)
        self.text.setPlaceholderText("https://www.youtube.com/watch?v=...")
        lay.addWidget(self.text, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        ok = QPushButton("确定")
        ok.setObjectName("PrimaryButton")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(ok)
        btn_row.addWidget(cancel)
        lay.addLayout(btn_row)

        self.text.setFocus()

    def urls(self):
        return [u.strip() for u in self.text.toPlainText().splitlines()
                if u.strip().startswith('http')]


def warn(parent, title, message):
    box = QMessageBox(QMessageBox.Icon.Warning, title, message, QMessageBox.StandardButton.Ok, parent)
    box.exec()


# ================================================================ 队列页 / 设置页

class QueuePage(QWidget):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(8)

        # 路径行
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        label = QLabel("输出路径")
        label.setObjectName("SectionTitle")
        path_row.addWidget(label)
        path_row.addSpacing(6)

        self.path_combo = QComboBox()
        self.path_combo.setEditable(True)
        self.path_combo.setMinimumWidth(320)
        self.path_combo.setToolTip("下载保存目录（历史可下拉选择）")
        path_row.addWidget(self.path_combo, 1)

        self.browse_btn = QToolButton()
        self.browse_btn.setIcon(icon_folder())
        self.browse_btn.setToolTip("浏览…")
        self.browse_btn.setFixedSize(30, 28)
        path_row.addWidget(self.browse_btn)
        outer.addLayout(path_row)

        # 表格
        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.view.setAlternatingRowColors(True)
        self.view.setShowGrid(False)
        self.view.verticalHeader().setVisible(False)
        self.view.verticalHeader().setDefaultSectionSize(34)
        self.view.horizontalHeader().setHighlightSections(False)
        self.view.setItemDelegateForColumn(TaskTableModel.COL_STATUS, StatusDelegate(self.view))
        self.view.setItemDelegateForColumn(TaskTableModel.COL_HDR, HdrDelegate(self.view))

        header = self.view.horizontalHeader()
        header.setSectionResizeMode(TaskTableModel.COL_INDEX, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(TaskTableModel.COL_TITLE, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(TaskTableModel.COL_UPLOADER, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(TaskTableModel.COL_HDR, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(TaskTableModel.COL_STATUS, QHeaderView.ResizeMode.Fixed)
        self.view.setColumnWidth(TaskTableModel.COL_INDEX, 46)
        self.view.setColumnWidth(TaskTableModel.COL_UPLOADER, 130)
        self.view.setColumnWidth(TaskTableModel.COL_HDR, 84)
        self.view.setColumnWidth(TaskTableModel.COL_STATUS, 250)

        outer.addWidget(self.view, 1)

    def selected_item_ids(self):
        ids = []
        for idx in self.view.selectionModel().selectedRows():
            ids.append(self.model.items[idx.row()].item_id)
        return ids


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        # ---- 输出设置 ----
        outer.addWidget(self._section("输出设置"))

        self.quality_combo = QComboBox()
        for value in core.RESOLUTION_VALUES:
            self.quality_combo.addItem(core.RESOLUTION_LABELS[value], value)
        outer.addLayout(self._row("画质上限", self.quality_combo))

        self.hdr_switch = Switch(checked=True)
        outer.addLayout(self._switch_row("优先 HDR", self.hdr_switch,
                                         "检测并倾向 HDR 格式（DV / HDR10+ / HDR10 / HLG）"))

        self.subfolder_switch = Switch(checked=False)
        outer.addLayout(self._switch_row("按上传者分文件夹", self.subfolder_switch,
                                         "每个上传者保存到独立子目录"))

        # ---- 路径 ----
        outer.addSpacing(6)
        outer.addWidget(self._section("默认路径"))
        path_row = QHBoxLayout()
        self.path_label = QLabel("未设置")
        self.path_label.setObjectName("ValueText")
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        path_row.addWidget(self.path_label, 1)
        self.path_btn = QPushButton("更改…")
        path_row.addWidget(self.path_btn)
        outer.addLayout(path_row)

        # ---- 关于 ----
        outer.addSpacing(6)
        outer.addWidget(self._section("关于"))
        self.about_label = QLabel()
        self.about_label.setObjectName("FieldLabel")
        self.about_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        outer.addWidget(self.about_label)

        outer.addStretch(1)

    @staticmethod
    def _section(text):
        label = QLabel(text.upper())
        label.setObjectName("SectionTitle")
        return label

    @staticmethod
    def _row(text, widget):
        row = QHBoxLayout()
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        label.setFixedWidth(130)
        row.addWidget(label)
        row.addWidget(widget, 1)
        return row

    @staticmethod
    def _switch_row(text, switch, hint):
        row = QHBoxLayout()
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        label.setFixedWidth(130)
        row.addWidget(label)
        row.addWidget(switch)
        row.addSpacing(8)
        h = QLabel(hint)
        h.setObjectName("AppSubtitle")
        row.addWidget(h)
        row.addStretch(1)
        return row

    def set_about(self, text):
        self.about_label.setText(text)


# ================================================================ 主窗口

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Video Downloader")
        self.setMinimumSize(980, 640)
        self.resize(1160, 780)
        self.setWindowIcon(QIcon(brand_pixmap(32)))

        self.config = core.load_config()
        self.model = TaskTableModel(self)
        self.fetch_workers = set()
        self.download_workers = set()
        self.download_queue = deque()
        self.is_downloading = False
        self.current_worker = None
        self._closing = False

        self._build_ui()
        self._load_config_into_ui()
        self._check_environment()
        self.log_message(f"Video Downloader v{__version__} 已启动")
        self.set_status("就绪")

    # ------------------------------------------------------------ UI 构建

    def _build_ui(self):
        self.menuBar().setVisible(False)

        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_toolbar())
        outer.addWidget(self._build_body(), 1)
        outer.addWidget(self._build_console())
        outer.addWidget(self._build_action_bar())

        self.setCentralWidget(central)
        self._build_status_bar()

    def _build_toolbar(self):
        bar = QWidget()
        bar.setObjectName("Toolbar")
        bar.setFixedHeight(44)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(10)

        mark = QLabel()
        mark.setPixmap(brand_pixmap(24))
        lay.addWidget(mark)

        title = QLabel("VIDEO DOWNLOADER")
        title.setObjectName("AppTitle")
        lay.addWidget(title)

        version = QLabel(f"v{__version__}")
        version.setObjectName("AppSubtitle")
        version.setStyleSheet(f"border: 1px solid #3a3a3a; border-radius: 3px; padding: 1px 7px;")
        lay.addWidget(version)

        lay.addStretch(1)

        self.ffmpeg_dot = QLabel()
        self.ffmpeg_text = QLabel("FFmpeg")
        self.ffmpeg_text.setObjectName("AppSubtitle")
        lay.addWidget(self.ffmpeg_dot)
        lay.addWidget(self.ffmpeg_text)
        return bar

    def _build_body(self):
        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        # 左侧图标栏（达芬奇「页面」隐喻）
        self.rail = QListWidget()
        self.rail.setObjectName("Rail")
        self.rail.setFixedWidth(58)
        self.rail.setIconSize(QSize(20, 20))
        self.rail.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.rail.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        for text, icon in (("队列", icon_queue()), ("设置", icon_settings())):
            item = QListWidgetItem(icon, text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
            self.rail.addItem(item)
        self.rail.setCurrentRow(0)
        body_lay.addWidget(self.rail)

        # 页面
        self.queue_page = QueuePage(self.model)
        self.settings_page = SettingsPage()
        self.stack = QStackedWidget()
        self.stack.addWidget(self.queue_page)
        self.stack.addWidget(self.settings_page)
        body_lay.addWidget(self.stack, 1)

        self.rail.currentRowChanged.connect(self.stack.setCurrentIndex)
        return body

    def _build_console(self):
        self.console = QPlainTextEdit()
        self.console.setObjectName("Console")
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(2000)
        self.console.setFixedHeight(118)
        return self.console

    def _build_action_bar(self):
        bar = QWidget()
        bar.setObjectName("ActionBar")
        bar.setFixedHeight(52)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(6)

        self.console_btn = QToolButton()
        self.console_btn.setText("▤ 控制台")
        self.console_btn.setCheckable(True)
        self.console_btn.setChecked(True)
        self.console_btn.toggled.connect(self.console.setVisible)
        lay.addWidget(self.console_btn)
        lay.addSpacing(6)

        def make_action(text, icon, slot, obj=None):
            btn = QPushButton(text)
            btn.setIcon(icon)
            btn.clicked.connect(slot)
            if obj:
                btn.setObjectName(obj)
            lay.addWidget(btn)
            return btn

        make_action("粘贴", icon_clipboard(), self.on_copy_from_clipboard)
        make_action("添加URL", icon_plus(), self.on_add_url)
        self.edit_btn = make_action("编辑", icon_pencil(), self.on_edit)
        self.delete_btn = make_action("删除", icon_trash(), self.on_delete)
        self.clear_btn = make_action("清空", icon_clear(), self.clear_list)

        lay.addStretch(1)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setIcon(icon_stop())
        self.stop_btn.setObjectName("DangerButton")
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self.on_stop)
        lay.addWidget(self.stop_btn)

        self.download_btn = QPushButton("开始下载")
        self.download_btn.setIcon(icon_download())
        self.download_btn.setObjectName("PrimaryButton")
        self.download_btn.setMinimumWidth(150)
        self.download_btn.clicked.connect(self.on_download)
        lay.addWidget(self.download_btn)
        return bar

    def _build_status_bar(self):
        sb = self.statusBar()

        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("StatusText")
        sb.addWidget(self.status_label, 1)

        self.ytdlp_label = QLabel(f"yt-dlp {yt_dlp.version.__version__}")
        self.ytdlp_label.setObjectName("StatusText")
        sb.addPermanentWidget(self.ytdlp_label)

        platform = "macOS" if sys.platform == "darwin" else ("Windows" if sys.platform == "win32" else sys.platform)
        self.platform_label = QLabel(platform)
        self.platform_label.setObjectName("StatusText")
        sb.addPermanentWidget(self.platform_label)

    # ------------------------------------------------------------ 配置与环境

    def _load_config_into_ui(self):
        # 路径
        history = self.config.get("history_paths") or []
        if history:
            self.queue_page.path_combo.addItems(list(dict.fromkeys(history)))
        default_path = self.config.get("default_path", "")
        if default_path:
            self.queue_page.path_combo.setCurrentText(default_path)
            self.settings_page.path_label.setText(default_path)
        else:
            self.settings_page.path_label.setText("未设置")

        # 画质
        max_res = str(self.config.get("max_resolution", "4320"))
        idx = self.quality_index_for(max_res)
        self.settings_page.quality_combo.setCurrentIndex(idx)

        # 开关
        self.settings_page.hdr_switch.setChecked(bool(self.config.get("prefer_hdr", True)))
        self.settings_page.subfolder_switch.setChecked(bool(self.config.get("use_subfolders", False)))

        # 关于
        about = (f"VideoDownloader v{__version__}\n"
                 f"Python {sys.version.split()[0]}  ·  PySide6 {pyside6_version}  ·  yt-dlp {yt_dlp.version.__version__}\n"
                 f"逻辑内核: downloader_core.py")
        self.settings_page.set_about(about)

        # 信号接线
        self.settings_page.quality_combo.currentIndexChanged.connect(self.on_quality_changed)
        self.settings_page.hdr_switch.toggled.connect(self.on_prefer_hdr_changed)
        self.settings_page.subfolder_switch.toggled.connect(self.on_subfolders_changed)
        self.settings_page.path_btn.clicked.connect(self.on_change_default_path)
        self.queue_page.browse_btn.clicked.connect(self.select_directory)

        # 快捷键
        QShortcut(QKeySequence("Ctrl+A"), self.queue_page.view, self.select_all)
        QShortcut(QKeySequence(QKeySequence.StandardKey.Delete), self.queue_page.view, self.on_delete)

    def quality_index_for(self, value):
        try:
            return core.RESOLUTION_VALUES.index(str(value))
        except ValueError:
            return 0

    def _check_environment(self):
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            self.ffmpeg_dot.setText("●")
            self.ffmpeg_dot.setStyleSheet("color: #67C23A; font-size: 11px;")
            self.ffmpeg_text.setToolTip(ffmpeg)
        else:
            self.ffmpeg_dot.setText("●")
            self.ffmpeg_dot.setStyleSheet("color: #E5484D; font-size: 11px;")
            self.ffmpeg_text.setToolTip("未检测到 FFmpeg：多轨视频将无法合并")
        self.ffmpeg_text.setText(f"FFmpeg {'已就绪' if ffmpeg else '缺失'}")

    # ------------------------------------------------------------ 状态与日志

    def set_status(self, text):
        self.status_label.setText(text)

    def log_message(self, message):
        ts = core.now_timestamp()
        self.console.appendPlainText(f"[{ts}] {message}")

    def _set_downloading_ui(self, on):
        self.is_downloading = on
        self.download_btn.setEnabled(not on)
        self.download_btn.setText("下载中…" if on else "开始下载")
        self.stop_btn.setVisible(on)
        self.delete_btn.setEnabled(not on)
        self.clear_btn.setEnabled(not on)

    # ------------------------------------------------------------ 任务管理

    def on_copy_from_clipboard(self):
        try:
            clipboard = pyperclip.paste()
        except Exception as e:
            self.log_message(f"⚠️ 读取剪贴板失败: {e}")
            return
        urls = [u for u in clipboard.split() if u.startswith('http')]
        count = 0
        for url in urls:
            if self.add_task(url):
                count += 1
        self.log_message(f"📋 从剪贴板添加了 {count} 个 URL" if count else "剪贴板中没有找到 URL")

    def on_add_url(self):
        dlg = AddUrlDialog("添加 URL", parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            urls = dlg.urls()
            count = 0
            for url in urls:
                if self.add_task(url):
                    count += 1
            self.log_message(f"✅ 已添加 {count} 个 URL")

    def on_edit(self):
        ids = self.queue_page.selected_item_ids()
        if not ids:
            warn(self, "未选择", "请先选择要编辑的视频")
            return
        if self.is_downloading:
            warn(self, "无法编辑", "下载进行中，请等待下载完成")
            return
        item_id = ids[0]
        item = self.model.get(item_id)
        current_url = item.url if item else ""
        dlg = AddUrlDialog("编辑 URL", initial=current_url, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            urls = dlg.urls()
            if urls and urls[0] != current_url:
                self._start_fetch(urls[0], edit_item_id=item_id)

    def add_task(self, video_url):
        if not video_url or not video_url.startswith('http'):
            return False
        for it in self.model.items:
            if it.url == video_url:
                self.log_message(f"⚠️ URL 已存在: {video_url[:60]}...")
                return False
        self._start_fetch(video_url)
        return True

    def _start_fetch(self, video_url, edit_item_id=None):
        """启动信息抓取线程（单视频或编辑）"""
        if edit_item_id is None:
            item_id = str(len(self.model.items) + 1)
            self.model.add_item(core.TaskItem(item_id, video_url, status="解析中"))
            self.log_message(f"🔍 正在获取视频信息: {video_url[:60]}...")
        else:
            item_id = edit_item_id
            self.model.set_status(item_id, "解析中")
            self.log_message(f"🔍 正在更新视频信息: {video_url[:60]}...")

        worker = core.FetchInfoWorker(video_url)
        worker.fetched.connect(
            lambda url, t, u, h: self._on_fetched(url, t, u, h, edit_item_id, item_id))
        worker.playlist_detected.connect(self._on_playlist_detected)
        worker.log.connect(self.log_message)
        worker.error.connect(lambda err: self._on_fetch_error(err, item_id, edit_item_id))
        worker.finished.connect(lambda: self._discard_worker(self.fetch_workers, worker))
        self.fetch_workers.add(worker)
        worker.start()

    def _on_fetched(self, url, title, uploader, hdr, edit_item_id, item_id):
        if edit_item_id:
            self.model.set_info(edit_item_id, title, uploader, hdr)
            self.log_message(f"✏️ 已更新: {title[:50]}...")
        else:
            self.model.set_info(item_id, title, uploader, hdr)
            self.log_message(f"✅ 已添加: {title[:50]}...")

    def _on_playlist_detected(self, playlist_url, links):
        self.log_message(f"📃 检测到播放列表，找到 {len(links)} 个视频，正在添加...")
        for u in links:
            self.add_task(u)

    def _on_fetch_error(self, error, item_id, edit_item_id):
        if edit_item_id:
            self.model.set_status(edit_item_id, f"失败: {str(error)[:40]}")
        else:
            self.model.remove_item(item_id)
        self.log_message(f"❌ 获取视频信息失败: {error}")

    def _discard_worker(self, pool, worker):
        pool.discard(worker)

    # ------------------------------------------------------------ 下载流程

    def on_download(self):
        if self.is_downloading:
            return

        output_directory = self.queue_page.path_combo.currentText().strip()
        if not output_directory:
            warn(self, "路径错误", "请选择或输入下载目录")
            return

        # 记录历史路径
        history = list(dict.fromkeys(self.config.get("history_paths") or []))
        if output_directory not in history:
            history.insert(0, output_directory)
        if history:
            self.config["history_paths"] = history
            self.queue_page.path_combo.clear()
            self.queue_page.path_combo.addItems(history)
        self.config["default_path"] = output_directory
        self.save_config_now()

        selected = self.queue_page.selected_item_ids()
        if not selected:
            warn(self, "未选择", "请先选择要下载的视频")
            return

        self.download_queue = deque(selected)
        self.output_directory = output_directory
        self.set_status(f"准备下载 {len(selected)} 项…")
        self._set_downloading_ui(True)
        self._start_next_download()

    def _start_next_download(self):
        if not self.download_queue:
            self._finish_downloading()
            return
        item_id = self.download_queue.popleft()
        item = self.model.get(item_id)
        if item is None:
            self._start_next_download()
            return

        self.model.set_status(item_id, "下载中", phase="downloading")
        self.log_message(f"🚀 开始下载: {item.url}")

        format_selector = core.build_format_selector(self.config.get("max_resolution", "4320"))
        use_subfolders = bool(self.config.get("use_subfolders", False))

        worker = core.DownloadWorker(
            item.url, self.output_directory, item.uploader, item_id,
            format_selector=format_selector, use_subfolders=use_subfolders,
        )
        worker.progress.connect(self._on_progress)
        worker.succeeded.connect(self._on_success)
        worker.failed.connect(self._on_failure)
        worker.log.connect(self.log_message)
        worker.finished.connect(lambda: self._discard_worker(self.download_workers, worker))
        self.download_workers.add(worker)
        self.current_worker = worker
        self.set_status(f"正在下载…队列剩余 {len(self.download_queue)} 项")
        worker.start()

    def _on_progress(self, item_id, pct, speed, eta, phase):
        self.model.update_progress(item_id, pct, speed, eta, phase)

    def _on_success(self, item_id, filename, hdr):
        self.log_message(f"✅ 下载完成: {os.path.basename(filename)}")
        self.model.remove_item(item_id)
        self._start_next_download()

    def _on_failure(self, item_id, error):
        err = str(error)
        if "下载已取消" in err:
            self.model.set_status(item_id, "已取消")
            self.log_message("⏹ 下载已取消")
        else:
            self.model.set_status(item_id, f"失败: {err[:36]}")
            self.log_message(f"❌ 下载失败: {err}")
        self._start_next_download()

    def _finish_downloading(self):
        self._set_downloading_ui(False)
        self.set_status("就绪")
        self.log_message("📦 所有下载任务完成")

    def on_stop(self):
        worker = getattr(self, "current_worker", None)
        if worker and worker.isRunning():
            self.log_message("⏹ 正在停止当前任务…")
            worker.cancel()

    # ------------------------------------------------------------ 编辑/删除/清空

    def select_all(self):
        self.queue_page.view.selectAll()

    def on_delete(self):
        if self.is_downloading:
            warn(self, "无法删除", "下载进行中，请等待下载完成")
            return
        ids = self.queue_page.selected_item_ids()
        if not ids:
            return
        for item_id in ids:
            self.model.remove_item(item_id)
        self.model.renumber()
        self.log_message(f"🗑️ 已删除 {len(ids)} 个项目")

    def clear_list(self):
        if self.is_downloading:
            warn(self, "无法清空", "下载进行中，请等待下载完成")
            return
        self.model.clear()
        self.log_message("🗑️ 列表已清空")

    # ------------------------------------------------------------ 路径与设置

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择下载目录",
                                                     self.queue_page.path_combo.currentText())
        if directory:
            self.queue_page.path_combo.setCurrentText(directory)
            self.config["default_path"] = directory
            self.settings_page.path_label.setText(directory)
            self.save_config_now()

    def on_change_default_path(self):
        directory = QFileDialog.getExistingDirectory(self, "选择默认下载目录",
                                                     self.config.get("default_path", ""))
        if directory:
            self.config["default_path"] = directory
            self.settings_page.path_label.setText(directory)
            self.queue_page.path_combo.setCurrentText(directory)
            self.save_config_now()

    def on_quality_changed(self, index):
        value = self.settings_page.quality_combo.itemData(index)
        self.config["max_resolution"] = value
        self.save_config_now()
        self.log_message(f"⚙️ 画质上限: {core.RESOLUTION_LABELS[value]}")

    def on_prefer_hdr_changed(self, checked):
        self.config["prefer_hdr"] = checked
        self.save_config_now()

    def on_subfolders_changed(self, checked):
        self.config["use_subfolders"] = checked
        self.save_config_now()
        self.log_message(f"📁 按上传者分文件夹: {'开' if checked else '关'}")

    def save_config_now(self):
        core.save_config(self.config)

    # ------------------------------------------------------------ 关闭

    def closeEvent(self, event):
        if self._closing:
            event.accept()
            return
        self._closing = True
        event.ignore()   # 等待下载线程安全退出后再真正关闭
        for worker in list(self.download_workers):
            worker.cancel()
        QTimer.singleShot(0, self._finish_close)

    def _finish_close(self):
        for worker in list(self.download_workers):
            worker.wait(3000)
        self.close()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VideoDownloader")
    app.setApplicationDisplayName("Video Downloader")
    app.setStyle("Fusion")
    apply_dark_palette(app)
    app.setStyleSheet(QSS)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
