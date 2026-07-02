# -*- coding: utf-8 -*-
"""Tkinter interface for Japanese Stroke Mouse Writer V2.0 Portable."""

from __future__ import annotations

import argparse
import math
import queue
import sys
import threading
import time
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from mouse_writer_pro import (
    APP_VERSION,
    DEFAULT_KANJIVG_DIR,
    EnvironmentSettings,
    FlowDirection,
    GeneralSettings,
    LayoutResult,
    LayoutSettings,
    Orientation,
    WritingCancelled,
    build_layout,
    draw_with_mouse,
    escape_pressed,
    interruptible_sleep,
    path_stats,
)
from settings_store import DEFAULT_SETTINGS_PATH, Preset, SettingsStore

ORIENTATION_LABELS = {"水平": Orientation.HORIZONTAL, "垂直": Orientation.VERTICAL}
FLOW_LABELS = {"向右": FlowDirection.RIGHT, "向左": FlowDirection.LEFT}


class JapaneseWriterApp:
    BACKGROUND = "#f3f5f7"
    SURFACE = "#ffffff"
    TEXT = "#17212b"
    MUTED = "#5d6875"
    BORDER = "#d8dee5"
    PRIMARY = "#176b87"
    PRIMARY_ACTIVE = "#12566d"
    ACCENT = "#b4512f"

    def __init__(self, root: tk.Tk, settings_path: Path = DEFAULT_SETTINGS_PATH) -> None:
        self.root = root
        self.store = SettingsStore(settings_path)
        self.busy = False
        self.closing = False
        self.stop_event = threading.Event()
        self.current_layout: LayoutResult | None = None
        self.current_general: GeneralSettings | None = None
        self.coordinate_buttons: list[ttk.Button] = []
        self.preview_request = 0
        self.preview_after_id: str | None = None
        self.environment_after_id: str | None = None
        self.ui_poll_after_id: str | None = None
        self.initial_preview_after_id: str | None = None
        self.countdown_overlay: tk.Toplevel | None = None
        self.countdown_label: ttk.Label | None = None
        self.ui_events: queue.Queue[
            tuple[Callable[..., None], tuple[object, ...]]
        ] = queue.Queue()
        self.preset_name_to_id: dict[str, str] = {}

        root.title(f"Japanese Stroke Mouse Writer V{APP_VERSION}")
        root.geometry("1200x820")
        root.minsize(1000, 700)
        root.configure(background=self.BACKGROUND)
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind("<Escape>", lambda _event: self.stop_event.set())

        self._configure_styles()
        self._create_variables()
        self._build_layout()
        self._load_portable_settings()
        self._bind_live_updates()
        self.ui_poll_after_id = self.root.after(40, self._drain_ui_events)
        self.initial_preview_after_id = self.root.after(200, self.refresh_preview)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("App.TFrame", background=self.BACKGROUND)
        style.configure("Surface.TFrame", background=self.SURFACE)
        style.configure("TNotebook", background=self.BACKGROUND, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 9), font=("Microsoft JhengHei UI", 10))
        style.configure(
            "Title.TLabel",
            background=self.BACKGROUND,
            foreground=self.TEXT,
            font=("Microsoft JhengHei UI", 19, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=self.BACKGROUND,
            foreground=self.MUTED,
            font=("Microsoft JhengHei UI", 10),
        )
        style.configure(
            "Section.TLabel",
            background=self.SURFACE,
            foreground=self.TEXT,
            font=("Microsoft JhengHei UI", 11, "bold"),
        )
        style.configure(
            "Field.TLabel",
            background=self.SURFACE,
            foreground=self.MUTED,
            font=("Microsoft JhengHei UI", 9),
        )
        style.configure(
            "Primary.TButton",
            background=self.PRIMARY,
            foreground="white",
            borderwidth=0,
            padding=(18, 10),
            font=("Microsoft JhengHei UI", 10, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.PRIMARY_ACTIVE), ("disabled", "#9caab2")],
        )
        style.configure(
            "Secondary.TButton",
            background="#e9eef1",
            foreground=self.TEXT,
            borderwidth=0,
            padding=(12, 8),
            font=("Microsoft JhengHei UI", 9),
        )
        style.map("Secondary.TButton", background=[("active", "#dce5e9")])
        style.configure("TEntry", padding=7, fieldbackground="#fbfcfd")
        style.configure("TCombobox", padding=7, fieldbackground="#fbfcfd")

    def _create_variables(self) -> None:
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.start_x = tk.StringVar(value="100")
        self.start_y = tk.StringVar(value="100")
        self.end_x = tk.StringVar(value=str(max(300, screen_width - 100)))
        self.end_y = tk.StringVar(value=str(max(300, screen_height - 140)))
        self.font_size = tk.StringVar(value="150")
        self.char_gap = tk.StringVar(value="12")
        self.line_gap = tk.StringVar(value="24")
        self.orientation = tk.StringVar(value="水平")
        self.flow = tk.StringVar(value="向右")
        self.countdown = tk.StringVar(value="5")
        self.sample_spacing = tk.StringVar(value="2.0")
        self.point_delay_ms = tk.StringVar(value="8")
        self.preset_selection = tk.StringVar(value="")
        self.status = tk.StringVar(value="準備就緒")
        self.summary = tk.StringVar(value="")

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, style="App.TFrame", padding=(22, 12, 22, 12))
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer, style="App.TFrame")
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="日文筆順滑鼠書寫工具", style="Title.TLabel").pack(side="left")
        ttk.Label(
            header,
            text=f"V{APP_VERSION} Portable  ·  KanjiVG",
            style="Subtitle.TLabel",
        ).pack(side="left", padx=(14, 0), pady=(8, 0))

        self.notebook = ttk.Notebook(outer)
        self.notebook.pack(fill="both", expand=True)
        self.content_tab = ttk.Frame(self.notebook, style="Surface.TFrame", padding=16)
        self.general_tab = ttk.Frame(self.notebook, style="Surface.TFrame", padding=22)
        self.environment_tab = ttk.Frame(self.notebook, style="Surface.TFrame", padding=22)
        self.notebook.add(self.content_tab, text="內容與預覽")
        self.notebook.add(self.general_tab, text="一般設定")
        self.notebook.add(self.environment_tab, text="環境設定")
        self._build_content_tab()
        self._build_general_tab()
        self._build_environment_tab()

        status_bar = ttk.Frame(outer, style="App.TFrame")
        status_bar.pack(fill="x", pady=(10, 0))
        self.status_mark = tk.Label(
            status_bar,
            text="●",
            background=self.BACKGROUND,
            foreground=self.PRIMARY,
            font=("Microsoft JhengHei UI", 9),
        )
        self.status_mark.pack(side="left", padx=(0, 7))
        ttk.Label(status_bar, textvariable=self.status, style="Subtitle.TLabel").pack(side="left")
        ttk.Label(
            status_bar,
            text="緊急停止：按 ESC 或將滑鼠移到螢幕角落",
            style="Subtitle.TLabel",
        ).pack(side="right")

    def _build_content_tab(self) -> None:
        tab = self.content_tab
        tab.columnconfigure(0, minsize=410)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)

        left = ttk.Frame(tab, style="Surface.TFrame", padding=(0, 0, 16, 0))
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        ttk.Label(left, text="書寫文字", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        text_frame = tk.Frame(left, background=self.BORDER, padx=1, pady=1)
        text_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 16))
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        self.text_input = tk.Text(
            text_frame,
            wrap="none",
            undo=True,
            relief="flat",
            borderwidth=0,
            font=("Yu Gothic UI", 15),
            foreground=self.TEXT,
            background="#fbfcfd",
            insertbackground=self.TEXT,
            padx=10,
            pady=8,
        )
        self.text_input.insert("1.0", "こんにちは日本語")
        self.text_input.grid(row=0, column=0, sticky="nsew")
        text_y = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_input.yview)
        text_x = ttk.Scrollbar(text_frame, orient="horizontal", command=self.text_input.xview)
        text_y.grid(row=0, column=1, sticky="ns")
        text_x.grid(row=1, column=0, sticky="ew")
        self.text_input.configure(yscrollcommand=text_y.set, xscrollcommand=text_x.set)

        ttk.Label(left, text="畫布座標", style="Section.TLabel").grid(row=2, column=0, sticky="w")
        coordinate_grid = ttk.Frame(left, style="Surface.TFrame")
        coordinate_grid.grid(row=3, column=0, sticky="ew", pady=(8, 12))
        coordinate_grid.columnconfigure((0, 1), weight=1)
        self._coordinate_group(
            coordinate_grid,
            column=0,
            title="起始座標",
            x_variable=self.start_x,
            y_variable=self.start_y,
            command=lambda: self.detect_coordinate("start"),
        )
        self._coordinate_group(
            coordinate_grid,
            column=1,
            title="末端座標",
            x_variable=self.end_x,
            y_variable=self.end_y,
            command=lambda: self.detect_coordinate("end"),
        )

        actions = ttk.Frame(left, style="Surface.TFrame")
        actions.grid(row=4, column=0, sticky="ew")
        actions.columnconfigure((0, 1), weight=1)
        self.preview_button = ttk.Button(
            actions,
            text="更新預覽",
            style="Secondary.TButton",
            command=lambda: self.refresh_preview(show_errors=True),
        )
        self.preview_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.execute_button = ttk.Button(
            actions,
            text="開始書寫",
            style="Primary.TButton",
            command=self.start_writing,
        )
        self.execute_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        right = ttk.Frame(tab, style="Surface.TFrame")
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        preview_header = ttk.Frame(right, style="Surface.TFrame")
        preview_header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(preview_header, text="實際排版預覽", style="Section.TLabel").pack(side="left")
        ttk.Label(preview_header, textvariable=self.summary, style="Field.TLabel").pack(side="right")
        canvas_frame = tk.Frame(right, background=self.BORDER, padx=1, pady=1)
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        self.preview_canvas = tk.Canvas(
            canvas_frame,
            background="white",
            highlightthickness=0,
            borderwidth=0,
        )
        self.preview_canvas.pack(fill="both", expand=True)
        self.preview_canvas.bind("<Configure>", lambda _event: self._draw_current_layout())
        ttk.Label(
            right,
            text="淡色字格僅供定位；實際輸出為黑色筆順路徑。",
            style="Field.TLabel",
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))

    def _coordinate_group(
        self,
        parent: ttk.Frame,
        column: int,
        title: str,
        x_variable: tk.StringVar,
        y_variable: tk.StringVar,
        command: Callable[[], None],
    ) -> None:
        frame = ttk.Frame(parent, style="Surface.TFrame", padding=(0 if column == 0 else 8, 0, 8 if column == 0 else 0, 0))
        frame.grid(row=0, column=column, sticky="nsew")
        ttk.Label(frame, text=title, style="Field.TLabel").pack(anchor="w")
        entries = ttk.Frame(frame, style="Surface.TFrame")
        entries.pack(fill="x", pady=(4, 6))
        entries.columnconfigure((0, 1), weight=1)
        ttk.Entry(entries, textvariable=x_variable, width=9).grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ttk.Entry(entries, textvariable=y_variable, width=9).grid(row=0, column=1, sticky="ew", padx=(3, 0))
        button = ttk.Button(frame, text=f"偵測{title}", style="Secondary.TButton", command=command)
        button.pack(fill="x")
        self.coordinate_buttons.append(button)

    def _build_general_tab(self) -> None:
        tab = self.general_tab
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        settings = ttk.Frame(tab, style="Surface.TFrame", padding=(0, 0, 30, 0))
        settings.grid(row=0, column=0, sticky="nsew")
        settings.columnconfigure((0, 1), weight=1)
        ttk.Label(settings, text="文字與排版", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        self._field(settings, 1, 0, "字體大小（px）", self.font_size)
        self._field(settings, 1, 1, "字距（px）", self.char_gap)
        self._field(settings, 3, 0, "行距（px）", self.line_gap)
        self._combo_field(settings, 3, 1, "排列方向", self.orientation, list(ORIENTATION_LABELS))
        self._combo_field(settings, 5, 0, "流向", self.flow, list(FLOW_LABELS))

        presets = ttk.Frame(tab, style="Surface.TFrame", padding=(30, 0, 0, 0))
        presets.grid(row=0, column=1, sticky="nsew")
        presets.columnconfigure(0, weight=1)
        ttk.Label(presets, text="自訂選項", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))
        self.preset_combo = ttk.Combobox(
            presets,
            textvariable=self.preset_selection,
            state="readonly",
            values=[],
        )
        self.preset_combo.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.preset_combo.bind("<<ComboboxSelected>>", lambda _event: self.load_selected_preset())
        preset_actions = ttk.Frame(presets, style="Surface.TFrame")
        preset_actions.grid(row=2, column=0, sticky="ew")
        preset_actions.columnconfigure((0, 1), weight=1)
        actions = (
            ("新增", self.add_preset),
            ("覆寫", self.overwrite_preset),
            ("重新命名", self.rename_preset),
            ("刪除", self.delete_preset),
        )
        for index, (label, command) in enumerate(actions):
            ttk.Button(preset_actions, text=label, style="Secondary.TButton", command=command).grid(
                row=index // 2,
                column=index % 2,
                sticky="ew",
                padx=(0 if index % 2 == 0 else 5, 5 if index % 2 == 0 else 0),
                pady=(0, 6),
            )
        ttk.Label(
            presets,
            text="自訂選項只保存字體大小、字距、行距、排列方向與流向。",
            style="Field.TLabel",
            wraplength=390,
        ).grid(row=3, column=0, sticky="w", pady=(8, 0))

    def _build_environment_tab(self) -> None:
        tab = self.environment_tab
        tab.columnconfigure((0, 1), weight=1)
        ttk.Label(tab, text="書寫環境", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        self._field(tab, 1, 0, "開始倒數（秒）", self.countdown)
        self._field(tab, 1, 1, "曲線精細度", self.sample_spacing)
        self._field(tab, 3, 0, "取樣點停頓（毫秒）", self.point_delay_ms)
        descriptions = (
            "倒數：按下開始後保留的視窗切換時間。",
            "曲線精細度：範圍 0.1–20；數字越小越細緻，但書寫時間越長。",
            "取樣點停頓：範圍 1–1000 毫秒；若筆畫斷線可適度提高。",
        )
        for index, text in enumerate(descriptions):
            ttk.Label(tab, text=text, style="Field.TLabel").grid(
                row=5 + index,
                column=0,
                columnspan=2,
                sticky="w",
                pady=(3, 0),
            )

    def _field(self, parent: ttk.Frame, row: int, column: int, label: str, variable: tk.StringVar) -> None:
        container = ttk.Frame(parent, style="Surface.TFrame")
        container.grid(row=row, column=column, sticky="ew", padx=(0 if column == 0 else 8, 8 if column == 0 else 0), pady=(0, 12))
        ttk.Label(container, text=label, style="Field.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Entry(container, textvariable=variable).pack(fill="x")

    def _combo_field(
        self,
        parent: ttk.Frame,
        row: int,
        column: int,
        label: str,
        variable: tk.StringVar,
        values: list[str],
    ) -> None:
        container = ttk.Frame(parent, style="Surface.TFrame")
        container.grid(row=row, column=column, sticky="ew", padx=(0 if column == 0 else 8, 8 if column == 0 else 0), pady=(0, 12))
        ttk.Label(container, text=label, style="Field.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Combobox(container, textvariable=variable, values=values, state="readonly").pack(fill="x")

    def _bind_live_updates(self) -> None:
        self.text_input.bind("<KeyRelease>", lambda _event: self.schedule_preview())
        preview_variables = (
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            self.font_size,
            self.char_gap,
            self.line_gap,
            self.orientation,
            self.flow,
            self.sample_spacing,
        )
        for variable in preview_variables:
            variable.trace_add("write", lambda *_args: self.schedule_preview())
        for variable in (self.countdown, self.sample_spacing, self.point_delay_ms):
            variable.trace_add("write", lambda *_args: self.schedule_environment_save())

    def _load_portable_settings(self) -> None:
        try:
            state = self.store.load()
        except PermissionError as exc:
            messagebox.showerror("Portable 資料夾無法寫入", str(exc), parent=self.root)
            self.root.after(0, self.root.destroy)
            return
        self._apply_environment(state.environment)
        self.refresh_preset_list()
        if state.last_preset_id:
            try:
                self._apply_general(self.store.select_preset(state.last_preset_id).general)
            except KeyError:
                self.store.state.last_preset_id = None

    def _post_ui(self, callback: Callable[..., None], *args: object) -> None:
        self.ui_events.put((callback, args))

    def _drain_ui_events(self) -> None:
        if self.closing:
            return
        while True:
            try:
                callback, args = self.ui_events.get_nowait()
            except queue.Empty:
                break
            callback(*args)
        self.ui_poll_after_id = self.root.after(40, self._drain_ui_events)

    def _float(self, variable: tk.StringVar, label: str, minimum: float | None = None, maximum: float | None = None) -> float:
        try:
            value = float(variable.get().strip())
        except ValueError as exc:
            raise ValueError(f"「{label}」必須是數字。") from exc
        if not math.isfinite(value):
            raise ValueError(f"「{label}」必須是有限數字。")
        if minimum is not None and value < minimum:
            raise ValueError(f"「{label}」不可小於 {minimum}。")
        if maximum is not None and value > maximum:
            raise ValueError(f"「{label}」不可大於 {maximum}。")
        return value

    def _integer(self, variable: tk.StringVar, label: str, minimum: int, maximum: int) -> int:
        value = self._float(variable, label, minimum, maximum)
        if not value.is_integer():
            raise ValueError(f"「{label}」必須是整數。")
        return int(value)

    def read_general(self) -> GeneralSettings:
        return GeneralSettings(
            font_size=self._float(self.font_size, "字體大小", 10, 1000),
            char_gap=self._float(self.char_gap, "字距", 0, 1000),
            line_gap=self._float(self.line_gap, "行距", 0, 1000),
            orientation=ORIENTATION_LABELS[self.orientation.get()],
            flow=FLOW_LABELS[self.flow.get()],
        )

    def read_environment(self) -> EnvironmentSettings:
        return EnvironmentSettings(
            countdown=self._integer(self.countdown, "開始倒數", 0, 30),
            sample_spacing=self._float(self.sample_spacing, "曲線精細度", 0.1, 20),
            point_delay=self._float(self.point_delay_ms, "取樣點停頓", 1, 1000) / 1000,
            move_duration=0.0,
            stroke_delay=0.03,
        )

    def read_layout(self) -> tuple[str, LayoutSettings, EnvironmentSettings]:
        text = self.text_input.get("1.0", "end-1c")
        general = self.read_general()
        environment = self.read_environment()
        layout = LayoutSettings(
            start_x=self._float(self.start_x, "起始 X"),
            start_y=self._float(self.start_y, "起始 Y"),
            end_x=self._float(self.end_x, "末端 X"),
            end_y=self._float(self.end_y, "末端 Y"),
            general=general,
        )
        return text, layout, environment

    def build_result(self) -> tuple[LayoutResult, EnvironmentSettings]:
        text, layout, environment = self.read_layout()
        return build_layout(text, DEFAULT_KANJIVG_DIR, layout, environment), environment

    def schedule_preview(self) -> None:
        if self.preview_after_id:
            self.root.after_cancel(self.preview_after_id)
        self.preview_after_id = self.root.after(350, self.refresh_preview)

    def refresh_preview(self, show_errors: bool = False) -> None:
        for pending in (self.initial_preview_after_id, self.preview_after_id):
            if pending:
                try:
                    self.root.after_cancel(pending)
                except tk.TclError:
                    pass
        self.initial_preview_after_id = None
        self.preview_after_id = None
        if self.busy or self.closing:
            return
        try:
            text, layout, environment = self.read_layout()
        except (ValueError, KeyError) as exc:
            self.status.set(str(exc))
            if show_errors:
                messagebox.showerror("設定錯誤", str(exc), parent=self.root)
            return
        self.preview_request += 1
        request_id = self.preview_request
        self.status.set("正在更新排版預覽…")

        def worker() -> None:
            try:
                result = build_layout(text, DEFAULT_KANJIVG_DIR, layout, environment)
                self._post_ui(self._preview_ready, request_id, result, layout.general)
            except BaseException as exc:
                self._post_ui(self._preview_failed, request_id, exc, show_errors)

        threading.Thread(target=worker, daemon=True).start()

    def _preview_ready(
        self,
        request_id: int,
        result: LayoutResult,
        general: GeneralSettings,
    ) -> None:
        if request_id != self.preview_request:
            return
        self.current_layout = result
        self.current_general = general
        stroke_count, point_count = path_stats(result.paths)
        self.summary.set(f"{len(result.placements)} 格 · {stroke_count} 筆 · {point_count} 點")
        self.status.set("預覽已更新")
        self._draw_current_layout()

    def _preview_failed(self, request_id: int, error: BaseException, show_errors: bool) -> None:
        if request_id != self.preview_request:
            return
        self.current_layout = None
        self.current_general = None
        self.preview_canvas.delete("all")
        self.status.set(str(error))
        if show_errors:
            messagebox.showerror("無法建立預覽", str(error), parent=self.root)

    def _draw_current_layout(self) -> None:
        canvas = self.preview_canvas
        canvas.delete("all")
        result = self.current_layout
        general = self.current_general
        if not result or not general:
            canvas.create_text(
                max(1, canvas.winfo_width()) / 2,
                max(1, canvas.winfo_height()) / 2,
                text="請確認文字、座標與排版設定",
                fill=self.MUTED,
                font=("Microsoft JhengHei UI", 11),
            )
            return
        min_x, min_y, max_x, max_y = result.canvas_bounds
        source_width = max(1, max_x - min_x)
        source_height = max(1, max_y - min_y)
        width = max(100, canvas.winfo_width())
        height = max(100, canvas.winfo_height())
        padding = 24
        scale = min((width - padding * 2) / source_width, (height - padding * 2) / source_height)
        offset_x = (width - source_width * scale) / 2
        offset_y = (height - source_height * scale) / 2

        def transform(point: Point) -> Point:
            return (
                offset_x + (point[0] - min_x) * scale,
                offset_y + (point[1] - min_y) * scale,
            )

        left, top = transform((min_x, min_y))
        right, bottom = transform((max_x, max_y))
        canvas.create_rectangle(left, top, right, bottom, outline="#97a6af", dash=(6, 4), width=1)
        primary_step = general.font_size + general.char_gap
        for placement in result.placements:
            for offset in range(placement.span):
                cell_x = placement.x
                cell_y = placement.y
                if general.orientation is Orientation.HORIZONTAL:
                    cell_x += offset * primary_step if general.flow is FlowDirection.RIGHT else -offset * primary_step
                else:
                    cell_y += offset * primary_step
                x1, y1 = transform((cell_x, cell_y))
                x2, y2 = transform((cell_x + general.font_size, cell_y + general.font_size))
                canvas.create_rectangle(x1, y1, x2, y2, outline="#e1e7ea", dash=(2, 3))
        for index, path in enumerate(result.paths, start=1):
            coordinates: list[float] = []
            for point in path:
                x, y = transform(point)
                coordinates.extend((x, y))
            canvas.create_line(*coordinates, fill="#17212b", width=max(1, min(3, round(scale * 1.2))), smooth=False)
            start_x, start_y = transform(path[0])
            canvas.create_text(start_x, start_y, text=str(index), fill="#b00020", anchor="se", font=("Segoe UI", 7))

    def schedule_environment_save(self) -> None:
        if self.environment_after_id:
            self.root.after_cancel(self.environment_after_id)
        self.environment_after_id = self.root.after(600, self.save_environment)

    def save_environment(self) -> None:
        self.environment_after_id = None
        try:
            self.store.set_environment(self.read_environment())
        except ValueError as exc:
            self.status.set(str(exc))
            return
        except PermissionError:
            return

    def _apply_environment(self, environment: EnvironmentSettings) -> None:
        self.countdown.set(str(environment.countdown))
        self.sample_spacing.set(str(environment.sample_spacing))
        self.point_delay_ms.set(f"{environment.point_delay * 1000:g}")

    def _apply_general(self, general: GeneralSettings) -> None:
        self.font_size.set(str(general.font_size))
        self.char_gap.set(str(general.char_gap))
        self.line_gap.set(str(general.line_gap))
        self.orientation.set(next(label for label, value in ORIENTATION_LABELS.items() if value is general.orientation))
        self.flow.set(next(label for label, value in FLOW_LABELS.items() if value is general.flow))

    def refresh_preset_list(self, selected_id: str | None = None) -> None:
        self.preset_name_to_id = {preset.name: preset.id for preset in self.store.state.presets}
        names = list(self.preset_name_to_id)
        self.preset_combo.configure(values=names)
        target_id = selected_id or self.store.state.last_preset_id
        target = next((preset.name for preset in self.store.state.presets if preset.id == target_id), "")
        self.preset_selection.set(target)

    def selected_preset(self) -> Preset:
        name = self.preset_selection.get()
        preset_id = self.preset_name_to_id.get(name)
        if not preset_id:
            raise ValueError("請先選擇自訂選項。")
        return self.store.select_preset(preset_id)

    def load_selected_preset(self) -> None:
        try:
            preset = self.selected_preset()
            self._apply_general(preset.general)
            self.status.set(f"已載入自訂選項：{preset.name}")
        except (ValueError, KeyError) as exc:
            messagebox.showerror("自訂選項", str(exc), parent=self.root)

    def add_preset(self) -> None:
        name = simpledialog.askstring("新增自訂選項", "名稱（1–40 個字元）：", parent=self.root)
        if name is None:
            return
        try:
            preset = self.store.add_preset(name, self.read_general())
            self.refresh_preset_list(preset.id)
            self.status.set(f"已新增自訂選項：{preset.name}")
        except (ValueError, PermissionError) as exc:
            messagebox.showerror("無法新增", str(exc), parent=self.root)

    def overwrite_preset(self) -> None:
        try:
            preset = self.selected_preset()
            if not messagebox.askyesno("覆寫自訂選項", f"以目前設定覆寫「{preset.name}」？", parent=self.root):
                return
            updated = self.store.overwrite_preset(preset.id, self.read_general())
            self.refresh_preset_list(updated.id)
            self.status.set(f"已覆寫自訂選項：{updated.name}")
        except (ValueError, KeyError, PermissionError) as exc:
            messagebox.showerror("無法覆寫", str(exc), parent=self.root)

    def rename_preset(self) -> None:
        try:
            preset = self.selected_preset()
            name = simpledialog.askstring("重新命名", "新名稱：", initialvalue=preset.name, parent=self.root)
            if name is None:
                return
            updated = self.store.rename_preset(preset.id, name)
            self.refresh_preset_list(updated.id)
            self.status.set(f"已重新命名為：{updated.name}")
        except (ValueError, KeyError, PermissionError) as exc:
            messagebox.showerror("無法重新命名", str(exc), parent=self.root)

    def delete_preset(self) -> None:
        try:
            preset = self.selected_preset()
            if not messagebox.askyesno("刪除自訂選項", f"確定刪除「{preset.name}」？", parent=self.root):
                return
            self.store.delete_preset(preset.id)
            self.refresh_preset_list()
            self.status.set(f"已刪除自訂選項：{preset.name}")
        except (ValueError, KeyError, PermissionError) as exc:
            messagebox.showerror("無法刪除", str(exc), parent=self.root)

    def _show_detection_overlay(self, title: str) -> None:
        overlay = tk.Toplevel(self.root)
        overlay.title(title)
        overlay.attributes("-topmost", True)
        overlay.resizable(False, False)
        overlay.configure(background="#17212b")
        self.countdown_label = ttk.Label(
            overlay,
            text=f"{title}\n3",
            foreground="white",
            background="#17212b",
            font=("Microsoft JhengHei UI", 16, "bold"),
            anchor="center",
            padding=20,
        )
        self.countdown_label.pack(fill="both", expand=True)
        overlay.geometry("260x120+30+30")
        self.countdown_overlay = overlay

    def _update_detection_overlay(self, title: str, remaining: int) -> None:
        if self.countdown_label:
            self.countdown_label.configure(text=f"{title}\n{remaining}")

    def _close_detection_overlay(self) -> None:
        if self.countdown_overlay:
            self.countdown_overlay.destroy()
        self.countdown_overlay = None
        self.countdown_label = None

    def detect_coordinate(self, target: str) -> None:
        if self.busy:
            return
        title = "偵測起始座標" if target == "start" else "偵測末端座標"
        self.set_busy(True, f"{title}進行中…")
        self.stop_event.clear()
        self._show_detection_overlay(title)
        self.root.iconify()

        def should_stop() -> bool:
            return self.stop_event.is_set() or escape_pressed()

        def worker() -> None:
            try:
                import pyautogui

                for remaining in range(3, 0, -1):
                    self._post_ui(self._update_detection_overlay, title, remaining)
                    interruptible_sleep(1, should_stop)
                x, y = pyautogui.position()
                self._post_ui(self._coordinate_detected, target, x, y)
            except BaseException as exc:
                self._post_ui(self._restore_after_operation, exc)

        threading.Thread(target=worker, daemon=True).start()

    def _coordinate_detected(self, target: str, x: int, y: int) -> None:
        if target == "start":
            self.start_x.set(str(x))
            self.start_y.set(str(y))
            label = "起始"
        else:
            self.end_x.set(str(x))
            self.end_y.set(str(y))
            label = "末端"
        self._close_detection_overlay()
        self.root.deiconify()
        self.root.lift()
        self.set_busy(False, f"已偵測{label}座標：X={x}，Y={y}")
        self.refresh_preview()

    def start_writing(self) -> None:
        if self.busy:
            return
        try:
            result, environment = self.build_result()
            self.store.set_environment(environment)
        except BaseException as exc:
            messagebox.showerror("無法開始書寫", str(exc), parent=self.root)
            return
        self.current_layout = result
        self.current_general = self.read_general()
        self.set_busy(True, "準備開始書寫…")
        self.stop_event.clear()
        self.root.iconify()

        def should_stop() -> bool:
            return self.stop_event.is_set() or escape_pressed()

        def worker() -> None:
            try:
                draw_with_mouse(
                    result.paths,
                    countdown=environment.countdown,
                    move_duration=0.0,
                    point_delay=environment.point_delay,
                    stroke_delay=environment.stroke_delay,
                    allow_offscreen=False,
                    stop_requested=should_stop,
                )
                self._post_ui(self._writing_complete)
            except BaseException as exc:
                self._post_ui(self._restore_after_operation, exc)

        threading.Thread(target=worker, daemon=True).start()

    def _writing_complete(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.set_busy(False, "書寫完成")
        messagebox.showinfo("完成", "文字已依預覽排版完成書寫。", parent=self.root)

    def _restore_after_operation(self, error: BaseException) -> None:
        self._close_detection_overlay()
        self.root.deiconify()
        self.root.lift()
        if isinstance(error, WritingCancelled):
            self.set_busy(False, "操作已由 ESC 取消")
            return
        self.set_busy(False, "操作未完成")
        messagebox.showerror("操作未完成", str(error), parent=self.root)

    def set_busy(self, busy: bool, status: str) -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.preview_button.configure(state=state)
        self.execute_button.configure(state=state)
        for button in self.coordinate_buttons:
            button.configure(state=state)
        self.status.set(status)
        self.status_mark.configure(foreground=self.ACCENT if busy else self.PRIMARY)

    def on_close(self) -> None:
        if self.busy:
            self.stop_event.set()
            messagebox.showwarning("操作進行中", "已送出停止要求，請等待操作結束。", parent=self.root)
            return
        self.save_environment()
        self.closing = True
        self.cancel_scheduled_callbacks()
        self.root.destroy()

    def cancel_scheduled_callbacks(self) -> None:
        for after_id in (
            self.ui_poll_after_id,
            self.initial_preview_after_id,
            self.preview_after_id,
            self.environment_after_id,
        ):
            if after_id:
                try:
                    self.root.after_cancel(after_id)
                except tk.TclError:
                    pass
        self.ui_poll_after_id = None
        self.initial_preview_after_id = None
        self.preview_after_id = None
        self.environment_after_id = None


def run_self_test(settings_path: Path = DEFAULT_SETTINGS_PATH) -> int:
    sample = DEFAULT_KANJIVG_DIR / "065e5.svg"
    if not sample.exists():
        raise RuntimeError(f"找不到 KanjiVG 測試檔：{sample}")
    settings = LayoutSettings(
        start_x=10,
        start_y=10,
        end_x=500,
        end_y=500,
        general=GeneralSettings(font_size=100),
    )
    result = build_layout("あア日", DEFAULT_KANJIVG_DIR, settings)
    if len(result.kanjivg_chars) != 3 or not result.paths:
        raise RuntimeError("基本筆順排版測試失敗。")
    SettingsStore(settings_path).ensure_writable()
    print(f"Japanese Stroke Mouse Writer {APP_VERSION} self-test passed")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--settings-path", type=Path, default=DEFAULT_SETTINGS_PATH)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        return run_self_test(args.settings_path)
    root = tk.Tk()
    JapaneseWriterApp(root, settings_path=args.settings_path)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
