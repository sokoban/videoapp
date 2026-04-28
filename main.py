"""
VideoVault Android
Kivy + KivyMD 기반 안드로이드 동영상 파일 관리자
"""

import os
import sys
import json
import threading
from datetime import datetime
from pathlib import Path

# ── Kivy 설정 (import 전에 반드시 먼저) ──────────
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.slider import Slider
from kivy.uix.video import Video
from kivy.clock import Clock, mainthread
from kivy.metrics import dp, sp
from kivy.properties import (
    StringProperty, NumericProperty,
    BooleanProperty, ListProperty, ObjectProperty
)
from kivy.utils import get_color_from_hex
from kivy.core.window import Window

try:
    from kivymd.app import MDApp
    from kivymd.uix.screen import MDScreen
    from kivymd.uix.toolbar import MDTopAppBar
    from kivymd.uix.navigationdrawer import (
        MDNavigationDrawer, MDNavigationDrawerItem
    )
    from kivymd.uix.card import MDCard
    from kivymd.uix.button import (
        MDRaisedButton, MDFlatButton, MDIconButton,
        MDFloatingActionButton
    )
    from kivymd.uix.dialog import MDDialog
    from kivymd.uix.list import (
        MDList, OneLineListItem, TwoLineListItem,
        ThreeLineListItem, IconLeftWidget
    )
    from kivymd.uix.tab import MDTabsBase, MDTabs
    from kivymd.uix.label import MDLabel
    from kivymd.uix.progressbar import MDProgressBar
    from kivymd.uix.snackbar import Snackbar
    from kivymd.uix.selectioncontrol import MDCheckbox
    from kivymd.uix.chip import MDChip
    HAS_KIVYMD = True
except ImportError:
    HAS_KIVYMD = False
    MDApp = App

# ── Android 전용 임포트 ───────────────────────────
try:
    from android.permissions import (
        request_permissions, Permission, check_permission
    )
    from android.storage import primary_external_storage_path
    from jnius import autoclass
    IS_ANDROID = True
except ImportError:
    IS_ANDROID = False


# ─────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────

VIDEO_EXTENSIONS = {
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv',
    '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.ts'
}

DARK_BG     = get_color_from_hex("#0d1117")
CARD_BG     = get_color_from_hex("#161b22")
ACCENT      = get_color_from_hex("#1f6feb")
TEXT_MAIN   = get_color_from_hex("#e6edf3")
TEXT_DIM    = get_color_from_hex("#8b949e")
BORDER      = get_color_from_hex("#30363d")
SUCCESS     = get_color_from_hex("#238636")
DANGER      = get_color_from_hex("#da3633")


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def format_size(b: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def format_duration(sec: float) -> str:
    if sec <= 0:
        return "—"
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def get_video_files(root_dir: str) -> list:
    """재귀적으로 동영상 파일 탐색."""
    results = []
    try:
        for dirpath, _, files in os.walk(root_dir):
            for fname in files:
                if Path(fname).suffix.lower() in VIDEO_EXTENSIONS:
                    fpath = os.path.join(dirpath, fname)
                    try:
                        stat  = os.stat(fpath)
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        results.append({
                            'path':     fpath,
                            'name':     fname,
                            'size':     stat.st_size,
                            'size_str': format_size(stat.st_size),
                            'modified': mtime.strftime('%Y-%m-%d %H:%M'),
                            'ext':      Path(fname).suffix.lower(),
                            'dir':      dirpath,
                        })
                    except OSError:
                        pass
    except PermissionError:
        pass
    return sorted(results, key=lambda x: x['name'].lower())


# ─────────────────────────────────────────────
#  KV Layout String
# ─────────────────────────────────────────────

KV = """
#:import dp kivy.metrics.dp
#:import get_color_from_hex kivy.utils.get_color_from_hex

<RootLayout>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: get_color_from_hex("#0d1117")
        Rectangle:
            pos: self.pos
            size: self.size

<VideoListItem>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(72)
    padding: dp(12), dp(8)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: get_color_from_hex("#161b22") if self.index % 2 == 0 else get_color_from_hex("#0d1117")
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: get_color_from_hex("#21262d")
        Line:
            points: [self.x, self.y, self.x + self.width, self.y]
            width: 1

    # File icon
    Label:
        text: '🎬'
        font_size: sp(22)
        size_hint: None, None
        size: dp(36), dp(36)

    # File info
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(2)
        Label:
            text: root.filename
            font_size: sp(13)
            color: get_color_from_hex("#e6edf3")
            text_size: self.width, None
            shorten: True
            shorten_from: 'right'
            halign: 'left'
            valign: 'middle'
        Label:
            text: root.meta_text
            font_size: sp(11)
            color: get_color_from_hex("#8b949e")
            halign: 'left'
            valign: 'middle'
            text_size: self.width, None

    # Play button
    Button:
        text: '▶'
        font_size: sp(18)
        size_hint: None, None
        size: dp(44), dp(44)
        background_color: get_color_from_hex("#1f6feb")
        background_normal: ''
        border_radius: [dp(22)]
        on_press: root.on_play_pressed()

<SearchBar>:
    size_hint_y: None
    height: dp(48)
    orientation: 'horizontal'
    padding: dp(8), dp(6)
    spacing: dp(6)
    canvas.before:
        Color:
            rgba: get_color_from_hex("#161b22")
        Rectangle:
            pos: self.pos
            size: self.size

    TextInput:
        id: search_input
        hint_text: '🔍  파일 검색...'
        font_size: sp(14)
        foreground_color: get_color_from_hex("#e6edf3")
        hint_text_color: get_color_from_hex("#484f58")
        background_color: get_color_from_hex("#21262d")
        cursor_color: get_color_from_hex("#1f6feb")
        padding: [dp(12), dp(10)]
        multiline: False
        on_text: root.on_search(self.text)

<StatsCard>:
    size_hint_y: None
    height: dp(100)
    orientation: 'horizontal'
    padding: dp(12)
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: get_color_from_hex("#161b22")
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: get_color_from_hex("#30363d")
        Line:
            points: [self.x, self.y, self.x + self.width, self.y]
            width: 1

<PlayerControls>:
    size_hint_y: None
    height: dp(130)
    orientation: 'vertical'
    padding: dp(8)
    spacing: dp(4)
    canvas.before:
        Color:
            rgba: get_color_from_hex("#161b22")
        Rectangle:
            pos: self.pos
            size: self.size
"""


# ─────────────────────────────────────────────
#  UI Components
# ─────────────────────────────────────────────

class RootLayout(BoxLayout):
    pass


class VideoListItem(RecycleDataViewBehavior, BoxLayout):
    """RecycleView의 각 영상 항목."""
    index      = NumericProperty(0)
    filename   = StringProperty("")
    meta_text  = StringProperty("")
    path       = StringProperty("")
    _app       = None

    def refresh_view_attrs(self, rv, index, data):
        self.index     = index
        self.filename  = data.get('name', '')
        size_str  = data.get('size_str', '')
        modified  = data.get('modified', '')
        self.meta_text = f"{size_str}  •  {modified}"
        self.path      = data.get('path', '')
        return super().refresh_view_attrs(rv, index, data)

    def on_play_pressed(self):
        if self._app:
            self._app.open_player(self.path)


class SearchBar(BoxLayout):
    callback = ObjectProperty(None)

    def on_search(self, text):
        if self.callback:
            self.callback(text)


class StatsCard(BoxLayout):
    pass


class PlayerControls(BoxLayout):
    pass


class VideoRecycleView(RecycleView):
    pass


# ─────────────────────────────────────────────
#  Screens
# ─────────────────────────────────────────────

class LibraryScreen(Screen):
    """메인 라이브러리 화면."""

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self._app = app_ref
        self._all_videos = []
        self._filtered   = []
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', spacing=0)

        # ── Top bar ──────────────────────────
        topbar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(56),
            padding=[dp(12), dp(8)],
            spacing=dp(8)
        )
        topbar.canvas.before.add(
            self._color_rect(topbar, "#161b22")
        )

        title = Label(
            text="🎬 VideoVault",
            font_size=sp(18),
            bold=True,
            color=TEXT_MAIN,
            size_hint_x=1,
            halign='left',
            valign='middle'
        )
        title.bind(size=title.setter('text_size'))

        btn_scan = Button(
            text="📂 스캔",
            size_hint=(None, None),
            size=(dp(80), dp(38)),
            background_color=ACCENT,
            background_normal='',
            font_size=sp(13),
            bold=True,
            color=TEXT_MAIN
        )
        btn_scan.bind(on_press=lambda x: self._app.show_folder_picker())

        btn_refresh = Button(
            text="🔄",
            size_hint=(None, None),
            size=(dp(38), dp(38)),
            background_color=get_color_from_hex("#21262d"),
            background_normal='',
            font_size=sp(16),
            color=TEXT_MAIN
        )
        btn_refresh.bind(on_press=lambda x: self._app.rescan())

        topbar.add_widget(title)
        topbar.add_widget(btn_refresh)
        topbar.add_widget(btn_scan)
        root.add_widget(topbar)

        # ── Stats bar ─────────────────────────
        self.stats_lbl = Label(
            text="폴더를 선택하여 스캔하세요",
            size_hint_y=None,
            height=dp(32),
            font_size=sp(12),
            color=TEXT_DIM,
            halign='left',
            padding_x=dp(12)
        )
        self.stats_lbl.bind(size=self.stats_lbl.setter('text_size'))
        root.add_widget(self.stats_lbl)

        # ── Search bar ────────────────────────
        search_box = BoxLayout(
            size_hint_y=None,
            height=dp(46),
            padding=[dp(8), dp(4)],
            spacing=dp(6)
        )
        with search_box.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*get_color_from_hex("#161b22"))
            self._sb_rect = Rectangle(
                pos=search_box.pos, size=search_box.size
            )
        search_box.bind(
            pos=lambda w, v: setattr(self._sb_rect, 'pos', v),
            size=lambda w, v: setattr(self._sb_rect, 'size', v)
        )

        self.search_input = TextInput(
            hint_text='🔍  파일 검색...',
            font_size=sp(14),
            foreground_color=TEXT_MAIN,
            background_color=get_color_from_hex("#21262d"),
            cursor_color=ACCENT,
            padding=[dp(12), dp(10)],
            multiline=False
        )
        self.search_input.bind(text=lambda _, t: self._apply_filter(t))
        search_box.add_widget(self.search_input)
        root.add_widget(search_box)

        # ── Progress bar ──────────────────────
        self.progress = ProgressBar(
            max=100, value=0,
            size_hint_y=None, height=dp(4)
        )
        self.progress.opacity = 0
        root.add_widget(self.progress)

        # ── Video list (RecycleView) ───────────
        self.rv = RecycleView(
            viewclass='VideoListItem',
            bar_width=dp(4),
            bar_color=ACCENT,
            bar_inactive_color=BORDER
        )
        from kivy.uix.recycleboxlayout import RecycleBoxLayout
        self.rv_layout = RecycleBoxLayout(
            orientation='vertical',
            default_size=(None, dp(72)),
            default_size_hint=(1, None),
            size_hint_y=None
        )
        self.rv_layout.bind(minimum_height=self.rv_layout.setter('height'))
        self.rv.add_widget(self.rv_layout)
        root.add_widget(self.rv)

        # ── Empty state ───────────────────────
        self.empty_lbl = Label(
            text="동영상 파일이 없습니다.\n상단 [📂 스캔] 버튼을 눌러 폴더를 선택하세요.",
            color=TEXT_DIM,
            font_size=sp(14),
            halign='center',
            valign='middle'
        )
        self.empty_lbl.bind(size=self.empty_lbl.setter('text_size'))
        root.add_widget(self.empty_lbl)

        self.add_widget(root)

    def _color_rect(self, widget, hex_color):
        from kivy.graphics import Color, Rectangle
        c = Color(*get_color_from_hex(hex_color))
        r = Rectangle(pos=widget.pos, size=widget.size)
        widget.bind(
            pos=lambda w, v: setattr(r, 'pos', v),
            size=lambda w, v: setattr(r, 'size', v)
        )
        return c

    @mainthread
    def set_videos(self, videos: list):
        self._all_videos = videos
        self._apply_filter(self.search_input.text)
        total = len(videos)
        total_size = sum(v['size'] for v in videos)
        self.stats_lbl.text = (
            f"  {total:,}개 파일  •  총 {format_size(total_size)}"
        )
        self.empty_lbl.opacity = 0 if total else 1
        self.rv.opacity = 1 if total else 0

    def _apply_filter(self, text: str):
        q = text.lower().strip()
        if q:
            filtered = [v for v in self._all_videos
                        if q in v['name'].lower()]
        else:
            filtered = self._all_videos[:]
        data = []
        for v in filtered:
            d = dict(v)
            d['_app'] = self._app
            data.append(d)
        self.rv.data = data

    @mainthread
    def set_progress(self, val: int, visible: bool = True):
        self.progress.value  = val
        self.progress.opacity = 1 if visible else 0

    def refresh_item_app_refs(self):
        for child in self.rv_layout.children:
            if hasattr(child, '_app'):
                child._app = self._app


class PlayerScreen(Screen):
    """단일 동영상 재생 화면."""

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self._app = app_ref
        self._video_path = None
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', spacing=0)

        # Top bar
        topbar = BoxLayout(
            size_hint_y=None, height=dp(52),
            padding=[dp(8), dp(6)], spacing=dp(6)
        )
        with topbar.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*get_color_from_hex("#161b22"))
            r = Rectangle(pos=topbar.pos, size=topbar.size)
            topbar.bind(pos=lambda w, v: setattr(r, 'pos', v),
                        size=lambda w, v: setattr(r, 'size', v))

        btn_back = Button(
            text="← 뒤로",
            size_hint=(None, 1),
            width=dp(80),
            background_color=get_color_from_hex("#21262d"),
            background_normal='',
            color=TEXT_MAIN,
            font_size=sp(13)
        )
        btn_back.bind(on_press=lambda x: self._app.go_back())

        self.title_lbl = Label(
            text="",
            font_size=sp(13),
            color=TEXT_MAIN,
            halign='left',
            valign='middle',
            shorten=True,
            shorten_from='right',
            size_hint_x=1
        )
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))

        topbar.add_widget(btn_back)
        topbar.add_widget(self.title_lbl)
        root.add_widget(topbar)

        # Video
        self.video = Video(
            allow_stretch=True,
            keep_ratio=True,
            options={'eos': 'loop'}
        )
        root.add_widget(self.video, 1)

        # Controls
        ctrl = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
            padding=[dp(12), dp(8)],
            spacing=dp(6)
        )
        with ctrl.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*get_color_from_hex("#161b22"))
            r2 = Rectangle(pos=ctrl.pos, size=ctrl.size)
            ctrl.bind(pos=lambda w, v: setattr(r2, 'pos', v),
                      size=lambda w, v: setattr(r2, 'size', v))

        # Seek slider
        self.seek_slider = Slider(
            min=0, max=1, value=0,
            cursor_size=(dp(20), dp(20))
        )
        self.seek_slider.bind(
            on_touch_up=self._on_seek
        )
        ctrl.add_widget(self.seek_slider)

        # Time row
        time_row = BoxLayout(
            size_hint_y=None, height=dp(24), spacing=dp(8)
        )
        self.pos_lbl = Label(
            text="00:00",
            font_size=sp(12),
            color=ACCENT,
            size_hint_x=None, width=dp(50),
            halign='left'
        )
        self.dur_lbl = Label(
            text="/ 00:00",
            font_size=sp(12),
            color=TEXT_DIM,
            size_hint_x=1,
            halign='left'
        )
        time_row.add_widget(self.pos_lbl)
        time_row.add_widget(self.dur_lbl)
        ctrl.add_widget(time_row)

        # Buttons row
        btn_row = BoxLayout(
            size_hint_y=None, height=dp(52), spacing=dp(8)
        )

        def mk_btn(text, color=None, size=dp(48)):
            b = Button(
                text=text,
                font_size=sp(20),
                size_hint=(None, None),
                size=(size, dp(48)),
                background_color=color or get_color_from_hex("#21262d"),
                background_normal='',
                color=TEXT_MAIN
            )
            return b

        self.btn_prev  = mk_btn("⏮")
        self.btn_play  = mk_btn("▶", ACCENT, dp(56))
        self.btn_next  = mk_btn("⏭")
        self.btn_vol   = mk_btn("🔊")

        self.vol_slider = Slider(
            min=0, max=1, value=0.8,
            size_hint_x=1
        )
        self.vol_slider.bind(value=self._on_volume)

        self.btn_prev.bind(on_press=lambda x: self._seek_rel(-10))
        self.btn_play.bind(on_press=lambda x: self._toggle_play())
        self.btn_next.bind(on_press=lambda x: self._seek_rel(10))

        btn_row.add_widget(self.btn_prev)
        btn_row.add_widget(self.btn_play)
        btn_row.add_widget(self.btn_next)
        btn_row.add_widget(self.btn_vol)
        btn_row.add_widget(self.vol_slider)
        ctrl.add_widget(btn_row)

        root.add_widget(ctrl)
        self.add_widget(root)

        # Update timer
        Clock.schedule_interval(self._update_ui, 0.5)

    def load(self, path: str):
        self._video_path = path
        self.title_lbl.text = Path(path).name
        self.video.source = path
        self.video.play()
        self.btn_play.text = "⏸"

    def _toggle_play(self):
        if self.video.state == 'play':
            self.video.pause()
            self.btn_play.text = "▶"
        else:
            self.video.play()
            self.btn_play.text = "⏸"

    def _seek_rel(self, secs: float):
        dur = self.video.duration
        if dur and dur > 0:
            pos = max(0, min(dur, self.video.position + secs))
            self.video.seek(pos / dur)

    def _on_seek(self, slider, touch):
        if slider.collide_point(*touch.pos):
            dur = self.video.duration
            if dur and dur > 0:
                self.video.seek(slider.value)

    def _on_volume(self, slider, val):
        self.video.volume = val

    def _update_ui(self, dt):
        dur = self.video.duration
        pos = self.video.position
        if dur and dur > 0:
            self.seek_slider.value = pos / dur
            self.pos_lbl.text = format_duration(pos)
            self.dur_lbl.text = f"/ {format_duration(dur)}"

    def unload(self):
        self.video.source = ""


# ─────────────────────────────────────────────
#  Folder Picker (Android-aware)
# ─────────────────────────────────────────────

class FolderPickerPopup(Popup):
    """간단한 폴더 선택 팝업 (안드로이드 기본 경로 제공)."""

    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self._callback = callback
        self.title = "📂 스캔할 폴더 선택"
        self.size_hint = (0.92, 0.8)
        self._build()

    def _build(self):
        root = BoxLayout(orientation='vertical', spacing=dp(8),
                         padding=dp(12))

        lbl = Label(
            text="스캔할 폴더 경로를 선택하거나 직접 입력하세요:",
            color=TEXT_MAIN,
            size_hint_y=None,
            height=dp(32),
            font_size=sp(13)
        )
        root.add_widget(lbl)

        # 빠른 선택 버튼들
        quick_lbl = Label(
            text="빠른 선택:",
            color=TEXT_DIM,
            size_hint_y=None,
            height=dp(24),
            font_size=sp(12),
            halign='left'
        )
        quick_lbl.bind(size=quick_lbl.setter('text_size'))
        root.add_widget(quick_lbl)

        # 기본 경로 목록
        paths = self._get_default_paths()
        scroll = ScrollView(size_hint_y=0.5)
        path_list = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(4)
        )
        path_list.bind(minimum_height=path_list.setter('height'))

        for p in paths:
            btn = Button(
                text=p,
                size_hint_y=None,
                height=dp(44),
                background_color=get_color_from_hex("#21262d"),
                background_normal='',
                color=TEXT_MAIN,
                font_size=sp(12),
                halign='left',
                padding_x=dp(10)
            )
            btn.bind(on_press=lambda x, path=p: self._select(path))
            path_list.add_widget(btn)

        scroll.add_widget(path_list)
        root.add_widget(scroll)

        # 직접 입력
        input_lbl = Label(
            text="직접 입력:",
            color=TEXT_DIM,
            size_hint_y=None,
            height=dp(24),
            font_size=sp(12),
            halign='left'
        )
        input_lbl.bind(size=input_lbl.setter('text_size'))
        root.add_widget(input_lbl)

        self.path_input = TextInput(
            text=paths[0] if paths else "/sdcard",
            font_size=sp(13),
            size_hint_y=None,
            height=dp(44),
            background_color=get_color_from_hex("#21262d"),
            foreground_color=TEXT_MAIN,
            multiline=False
        )
        root.add_widget(self.path_input)

        btn_row = BoxLayout(
            size_hint_y=None, height=dp(48), spacing=dp(8)
        )
        btn_cancel = Button(
            text="취소",
            background_color=get_color_from_hex("#21262d"),
            background_normal='',
            color=TEXT_MAIN
        )
        btn_ok = Button(
            text="✅ 이 폴더 스캔",
            background_color=ACCENT,
            background_normal='',
            color=(1, 1, 1, 1),
            bold=True
        )
        btn_cancel.bind(on_press=lambda x: self.dismiss())
        btn_ok.bind(on_press=lambda x: self._select(self.path_input.text))
        btn_row.add_widget(btn_cancel)
        btn_row.add_widget(btn_ok)
        root.add_widget(btn_row)

        self.content = root

    def _get_default_paths(self) -> list:
        paths = []
        if IS_ANDROID:
            try:
                base = primary_external_storage_path()
                for sub in ['', 'DCIM', 'Movies', 'Download', 'Videos']:
                    p = os.path.join(base, sub) if sub else base
                    if os.path.isdir(p):
                        paths.append(p)
            except Exception:
                paths = ['/sdcard', '/sdcard/DCIM',
                         '/sdcard/Movies', '/sdcard/Download']
        else:
            home = os.path.expanduser('~')
            for sub in ['Videos', 'Movies', 'Downloads',
                        'Desktop', 'Documents']:
                p = os.path.join(home, sub)
                if os.path.isdir(p):
                    paths.append(p)
            if not paths:
                paths = [home]
        return paths

    def _select(self, path: str):
        self.dismiss()
        if self._callback:
            self._callback(path.strip())


# ─────────────────────────────────────────────
#  Main Application
# ─────────────────────────────────────────────

class VideoVaultApp(MDApp if HAS_KIVYMD else App):
    """메인 앱 클래스."""

    def build(self):
        self.title = "VideoVault"
        if HAS_KIVYMD:
            self.theme_cls.theme_style  = "Dark"
            self.theme_cls.primary_palette = "Blue"

        Builder.load_string(KV)
        Window.clearcolor = DARK_BG

        # Screen Manager
        self.sm = ScreenManager(
            transition=SlideTransition(duration=0.2)
        )

        self.library_screen = LibraryScreen(
            app_ref=self, name='library'
        )
        self.player_screen  = PlayerScreen(
            app_ref=self, name='player'
        )

        self.sm.add_widget(self.library_screen)
        self.sm.add_widget(self.player_screen)

        # 저장된 스캔 데이터 복원
        self._scan_dir   = ""
        self._videos     = []
        self._load_saved()

        # Android 권한 요청
        if IS_ANDROID:
            Clock.schedule_once(self._request_permissions, 1)

        return self.sm

    # ── Android Permissions ───────────────────
    def _request_permissions(self, dt=None):
        perms = [
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
        ]
        try:
            perms.append(Permission.READ_MEDIA_VIDEO)
        except Exception:
            pass
        request_permissions(perms, self._on_permissions)

    def _on_permissions(self, permissions, grants):
        pass  # 권한 처리 완료

    # ── Navigation ────────────────────────────
    def open_player(self, path: str):
        self.player_screen.load(path)
        self.sm.current = 'player'

    def go_back(self):
        self.player_screen.unload()
        self.sm.current = 'library'

    # ── Folder scan ───────────────────────────
    def show_folder_picker(self):
        popup = FolderPickerPopup(callback=self._start_scan)
        popup.open()

    def _start_scan(self, folder: str):
        if not folder or not os.path.isdir(folder):
            self._toast(f"폴더를 찾을 수 없습니다: {folder}")
            return
        self._scan_dir = folder
        self.library_screen.set_progress(0, True)
        self._toast(f"스캔 중: {folder}")
        threading.Thread(
            target=self._scan_worker,
            args=(folder,),
            daemon=True
        ).start()

    def _scan_worker(self, folder: str):
        try:
            videos = get_video_files(folder)
            self._videos = videos
            self._save_data()
            Clock.schedule_once(
                lambda dt: self._scan_done(videos), 0
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._toast(f"스캔 오류: {e}"), 0
            )

    @mainthread
    def _scan_done(self, videos: list):
        self.library_screen.set_progress(100, False)
        self.library_screen.set_videos(videos)
        self._toast(f"✅ {len(videos):,}개 파일 발견")

    def rescan(self):
        if self._scan_dir:
            self._start_scan(self._scan_dir)
        else:
            self.show_folder_picker()

    # ── Persistence ───────────────────────────
    def _data_path(self) -> str:
        return os.path.join(
            self.user_data_dir, 'videovault_scan.json'
        )

    def _save_data(self):
        try:
            with open(self._data_path(), 'w', encoding='utf-8') as f:
                json.dump({
                    'scan_dir': self._scan_dir,
                    'videos': self._videos[:5000]  # 최대 5000개
                }, f, ensure_ascii=False)
        except Exception:
            pass

    def _load_saved(self):
        try:
            with open(self._data_path(), 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._scan_dir = data.get('scan_dir', '')
            videos = data.get('videos', [])
            if videos:
                # 파일 존재 여부 확인
                valid = [v for v in videos if os.path.exists(v['path'])]
                self._videos = valid
                Clock.schedule_once(
                    lambda dt: self.library_screen.set_videos(valid), 0.5
                )
        except Exception:
            pass

    # ── Toast / Snackbar ──────────────────────
    def _toast(self, msg: str):
        if HAS_KIVYMD:
            try:
                Snackbar(text=msg, snackbar_x="8dp",
                         snackbar_y="8dp").open()
                return
            except Exception:
                pass
        # Fallback: popup
        lbl = Label(text=msg, color=TEXT_MAIN)
        popup = Popup(
            title="", content=lbl,
            size_hint=(0.7, 0.15),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)


def main():
    VideoVaultApp().run()


if __name__ == "__main__":
    main()
