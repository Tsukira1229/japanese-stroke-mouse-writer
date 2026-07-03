# -*- coding: utf-8 -*-
"""Tkinter interface for Japanese Stroke Mouse Writer V2.0 Portable."""

from __future__ import annotations

import argparse
import math
import queue
import re
import sys
import threading
import time
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from localization import (
    LANGUAGE_OPTIONS,
    Language,
    detect_system_language,
    exception_text,
    tr,
    validate_translation_catalogs,
)
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


NUMERIC_TRANSLATION = str.maketrans("０１２３４５６７８９。．，,", "0123456789....")


class NumericSpinbox:
    def __init__(
        self,
        app: "JapaneseWriterApp",
        parent: ttk.Frame,
        variable: tk.StringVar,
        label_key: str,
        minimum: float,
        maximum: float,
        increment: float,
        integer: bool = False,
    ) -> None:
        self.app = app
        self.variable = variable
        self.label_key = label_key
        self.minimum = minimum
        self.maximum = maximum
        self.integer = integer
        self.last_valid = variable.get()
        validate = (app.root.register(self._validate), "%P")
        self.widget = ttk.Spinbox(
            parent,
            textvariable=variable,
            from_=minimum,
            to=maximum,
            increment=increment,
            validate="key",
            validatecommand=validate,
        )
        self.widget.bind("<FocusOut>", self._commit, add="+")
        self.widget.bind("<Return>", self._commit, add="+")

    @staticmethod
    def normalize(value: str) -> str:
        return value.translate(NUMERIC_TRANSLATION).replace(" ", "")

    def _validate(self, proposed: str) -> bool:
        normalized = self.normalize(proposed)
        if normalized != proposed:
            self.app.root.after_idle(self.variable.set, normalized)
            return False
        return re.fullmatch(r"\d*(?:\.\d*)?", proposed) is not None

    def _commit(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        try:
            value = float(self.variable.get())
            valid = math.isfinite(value) and self.minimum <= value <= self.maximum
            valid = valid and (not self.integer or value.is_integer())
        except ValueError:
            valid = False
        if valid:
            self.last_valid = self.variable.get()
            return
        self.variable.set(self.last_valid)
        self.app._set_status(
            "invalid_number_reverted",
            label=self.app.t(self.label_key),
        )


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
        self.language = detect_system_language()
        self.busy = False
        self.closing = False
        self.stop_event = threading.Event()
        self.current_layout: LayoutResult | None = None
        self.current_general: GeneralSettings | None = None
        self.coordinate_buttons: list[ttk.Button] = []
        self.numeric_inputs: list[NumericSpinbox] = []
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

    def t(self, key: str, **values: object) -> str:
        return tr(key, self.language, **values)

    def _orientation_labels(self) -> dict[str, Orientation]:
        return {self.t("horizontal"): Orientation.HORIZONTAL, self.t("vertical"): Orientation.VERTICAL}

    def _flow_labels(self) -> dict[str, FlowDirection]:
        return {self.t("right"): FlowDirection.RIGHT, self.t("left"): FlowDirection.LEFT}

    def _set_status(self, key: str, **values: object) -> None:
        self.status.set(self.t(key, **values))

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
        style.configure("TSpinbox", padding=7, fieldbackground="#fbfcfd")
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
        self.orientation = tk.StringVar(value=self.t("horizontal"))
        self.flow = tk.StringVar(value=self.t("right"))
        self.countdown = tk.StringVar(value="5")
        self.sample_spacing = tk.StringVar(value="2.0")
        self.point_delay_ms = tk.StringVar(value="8")
        self.language_selection = tk.StringVar(value=dict(LANGUAGE_OPTIONS)[self.language])
        self.preset_selection = tk.StringVar(value="")
        self.status = tk.StringVar(value=self.t("ready"))
        self.summary = tk.StringVar(value="")

    def _build_layout(self) -> None:
        self.root.title(f"{self.t('app_title')} V{APP_VERSION}")
        self.outer = ttk.Frame(self.root, style="App.TFrame", padding=(22, 12, 22, 12))
        self.outer.pack(fill="both", expand=True)
        outer = self.outer
        header = ttk.Frame(outer, style="App.TFrame")
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text=self.t("app_title"), style="Title.TLabel").pack(side="left")
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
        self.notebook.add(self.content_tab, text=self.t("tab_content"))
        self.notebook.add(self.general_tab, text=self.t("tab_general"))
        self.notebook.add(self.environment_tab, text=self.t("tab_environment"))
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
            text=self.t("emergency_hint"),
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
        ttk.Label(left, text=self.t("writing_text"), style="Section.TLabel").grid(row=0, column=0, sticky="w")
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
        self.text_input.bind("<KeyRelease>", lambda _event: self.schedule_preview())

        ttk.Label(left, text=self.t("canvas_coordinates"), style="Section.TLabel").grid(row=2, column=0, sticky="w")
        coordinate_grid = ttk.Frame(left, style="Surface.TFrame")
        coordinate_grid.grid(row=3, column=0, sticky="ew", pady=(8, 12))
        coordinate_grid.columnconfigure((0, 1), weight=1)
        self._coordinate_group(
            coordinate_grid,
            column=0,
            title=self.t("start_coordinates"),
            x_variable=self.start_x,
            y_variable=self.start_y,
            command=lambda: self.detect_coordinate("start"),
        )
        self._coordinate_group(
            coordinate_grid,
            column=1,
            title=self.t("end_coordinates"),
            x_variable=self.end_x,
            y_variable=self.end_y,
            command=lambda: self.detect_coordinate("end"),
        )

        actions = ttk.Frame(left, style="Surface.TFrame")
        actions.grid(row=4, column=0, sticky="ew")
        actions.columnconfigure((0, 1), weight=1)
        self.preview_button = ttk.Button(
            actions,
            text=self.t("update_preview"),
            style="Secondary.TButton",
            command=lambda: self.refresh_preview(show_errors=True),
        )
        self.preview_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.execute_button = ttk.Button(
            actions,
            text=self.t("start_writing"),
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
        ttk.Label(preview_header, text=self.t("actual_preview"), style="Section.TLabel").pack(side="left")
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
            text=self.t("preview_hint"),
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
        button = ttk.Button(frame, text=self.t("detect", target=title), style="Secondary.TButton", command=command)
        button.pack(fill="x")
        self.coordinate_buttons.append(button)

    def _build_general_tab(self) -> None:
        tab = self.general_tab
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        settings = ttk.Frame(tab, style="Surface.TFrame", padding=(0, 0, 30, 0))
        settings.grid(row=0, column=0, sticky="nsew")
        settings.columnconfigure((0, 1), weight=1)
        ttk.Label(settings, text=self.t("text_layout"), style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        self._field(settings, 1, 0, self.t("font_size_px"), self.font_size)
        self._field(settings, 1, 1, self.t("char_gap_px"), self.char_gap)
        self._field(settings, 3, 0, self.t("line_gap_px"), self.line_gap)
        self._combo_field(settings, 3, 1, self.t("orientation"), self.orientation, list(self._orientation_labels()))
        self._combo_field(settings, 5, 0, self.t("flow"), self.flow, list(self._flow_labels()))

        presets = ttk.Frame(tab, style="Surface.TFrame", padding=(30, 0, 0, 0))
        presets.grid(row=0, column=1, sticky="nsew")
        presets.columnconfigure(0, weight=1)
        ttk.Label(presets, text=self.t("presets"), style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))
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
            (self.t("preset_add"), self.add_preset),
            (self.t("preset_overwrite"), self.overwrite_preset),
            (self.t("preset_rename"), self.rename_preset),
            (self.t("preset_delete"), self.delete_preset),
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
            text=self.t("preset_hint"),
            style="Field.TLabel",
            wraplength=390,
        ).grid(row=3, column=0, sticky="w", pady=(8, 0))

    def _build_environment_tab(self) -> None:
        tab = self.environment_tab
        tab.columnconfigure((0, 1), weight=1)
        ttk.Label(tab, text=self.t("writing_environment"), style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        self.language_combo = self._combo_field(
            tab,
            1,
            0,
            self.t("language"),
            self.language_selection,
            [label for _language, label in LANGUAGE_OPTIONS],
        )
        self.language_combo.bind("<<ComboboxSelected>>", self._language_selected)
        self._numeric_field(tab, 1, 1, "countdown_seconds", "countdown", self.countdown, 0, 30, 1, integer=True)
        self._numeric_field(tab, 3, 0, "curve_detail", "curve_detail", self.sample_spacing, 0.1, 20, 0.1)
        self._numeric_field(tab, 3, 1, "point_delay_ms", "point_delay", self.point_delay_ms, 1, 1000, 1)
        descriptions = (
            self.t("countdown_hint"),
            self.t("curve_hint"),
            self.t("delay_hint"),
        )
        for index, text in enumerate(descriptions):
            ttk.Label(tab, text=text, style="Field.TLabel").grid(
                row=5 + index,
                column=0,
                columnspan=2,
                sticky="w",
                pady=(3, 0),
            )

    def _numeric_field(
        self,
        parent: ttk.Frame,
        row: int,
        column: int,
        label_key: str,
        short_label_key: str,
        variable: tk.StringVar,
        minimum: float,
        maximum: float,
        increment: float,
        integer: bool = False,
    ) -> None:
        container = ttk.Frame(parent, style="Surface.TFrame")
        container.grid(row=row, column=column, sticky="ew", padx=(0 if column == 0 else 8, 8 if column == 0 else 0), pady=(0, 12))
        ttk.Label(container, text=self.t(label_key), style="Field.TLabel").pack(anchor="w", pady=(0, 4))
        control = NumericSpinbox(
            self,
            container,
            variable,
            short_label_key,
            minimum,
            maximum,
            increment,
            integer,
        )
        control.widget.pack(fill="x")
        self.numeric_inputs.append(control)

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
    ) -> ttk.Combobox:
        container = ttk.Frame(parent, style="Surface.TFrame")
        container.grid(row=row, column=column, sticky="ew", padx=(0 if column == 0 else 8, 8 if column == 0 else 0), pady=(0, 12))
        ttk.Label(container, text=label, style="Field.TLabel").pack(anchor="w", pady=(0, 4))
        combo = ttk.Combobox(container, textvariable=variable, values=values, state="readonly")
        combo.pack(fill="x")
        return combo

    def _bind_live_updates(self) -> None:
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
            messagebox.showerror(self.t("portable_write_error"), exception_text(exc, self.language), parent=self.root)
            self.root.after(0, self.root.destroy)
            return
        if state.language is not self.language:
            orientation = self._orientation_labels()[self.orientation.get()]
            flow = self._flow_labels()[self.flow.get()]
            self.language = state.language
            self.language_selection.set(dict(LANGUAGE_OPTIONS)[self.language])
            self.orientation.set(next(label for label, value in self._orientation_labels().items() if value is orientation))
            self.flow.set(next(label for label, value in self._flow_labels().items() if value is flow))
            self._rebuild_layout()
        self._apply_environment(state.environment)
        self.refresh_preset_list()
        if state.last_preset_id:
            try:
                self._apply_general(self.store.select_preset(state.last_preset_id).general)
            except (KeyError, ValueError):
                self.store.state.last_preset_id = None

    def _language_selected(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        selected = next(
            (language for language, label in LANGUAGE_OPTIONS if label == self.language_selection.get()),
            self.language,
        )
        if selected is self.language:
            return
        orientation = self._orientation_labels()[self.orientation.get()]
        flow = self._flow_labels()[self.flow.get()]
        self.language = selected
        self.orientation.set(next(label for label, value in self._orientation_labels().items() if value is orientation))
        self.flow.set(next(label for label, value in self._flow_labels().items() if value is flow))
        try:
            self.store.set_language(selected)
        except PermissionError as exc:
            messagebox.showerror(self.t("portable_write_error"), exception_text(exc, self.language), parent=self.root)
        self._rebuild_layout()
        self._set_status("language_changed")

    def _rebuild_layout(self) -> None:
        text = self.text_input.get("1.0", "end-1c") if hasattr(self, "text_input") else "こんにちは日本語"
        selected_tab = self.notebook.index(self.notebook.select()) if hasattr(self, "notebook") else 0
        if hasattr(self, "outer"):
            self.outer.destroy()
        self.coordinate_buttons = []
        self.numeric_inputs = []
        self._build_layout()
        self.text_input.delete("1.0", "end")
        self.text_input.insert("1.0", text)
        self.refresh_preset_list()
        self.notebook.select(min(selected_tab, self.notebook.index("end") - 1))
        if self.current_layout:
            self._update_summary(self.current_layout)
            self._draw_current_layout()

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
            raise ValueError(self.t("number_required", label=label)) from exc
        if not math.isfinite(value):
            raise ValueError(self.t("finite_required", label=label))
        if minimum is not None and value < minimum:
            raise ValueError(self.t("minimum", label=label, value=minimum))
        if maximum is not None and value > maximum:
            raise ValueError(self.t("maximum", label=label, value=maximum))
        return value

    def _integer(self, variable: tk.StringVar, label: str, minimum: int, maximum: int) -> int:
        value = self._float(variable, label, minimum, maximum)
        if not value.is_integer():
            raise ValueError(self.t("integer_required", label=label))
        return int(value)

    def read_general(self) -> GeneralSettings:
        return GeneralSettings(
            font_size=self._float(self.font_size, self.t("font_size"), 10, 1000),
            char_gap=self._float(self.char_gap, self.t("char_gap"), 0, 1000),
            line_gap=self._float(self.line_gap, self.t("line_gap"), 0, 1000),
            orientation=self._orientation_labels()[self.orientation.get()],
            flow=self._flow_labels()[self.flow.get()],
        )

    def read_environment(self) -> EnvironmentSettings:
        return EnvironmentSettings(
            countdown=self._integer(self.countdown, self.t("countdown"), 0, 30),
            sample_spacing=self._float(self.sample_spacing, self.t("curve_detail"), 0.1, 20),
            point_delay=self._float(self.point_delay_ms, self.t("point_delay"), 1, 1000) / 1000,
            move_duration=0.0,
            stroke_delay=0.03,
        )

    def read_layout(self) -> tuple[str, LayoutSettings, EnvironmentSettings]:
        text = self.text_input.get("1.0", "end-1c")
        general = self.read_general()
        environment = self.read_environment()
        layout = LayoutSettings(
            start_x=self._float(self.start_x, self.t("start_x")),
            start_y=self._float(self.start_y, self.t("start_y")),
            end_x=self._float(self.end_x, self.t("end_x")),
            end_y=self._float(self.end_y, self.t("end_y")),
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
            self.status.set(exception_text(exc, self.language))
            if show_errors:
                messagebox.showerror(self.t("settings_error"), exception_text(exc, self.language), parent=self.root)
            return
        self.preview_request += 1
        request_id = self.preview_request
        self._set_status("preview_updating")

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
        self._update_summary(result)
        self._set_status("preview_updated")
        self._draw_current_layout()

    def _update_summary(self, result: LayoutResult) -> None:
        stroke_count, point_count = path_stats(result.paths)
        self.summary.set(
            self.t(
                "preview_summary",
                cells=len(result.placements),
                strokes=stroke_count,
                points=point_count,
            )
        )

    def _preview_failed(self, request_id: int, error: BaseException, show_errors: bool) -> None:
        if request_id != self.preview_request:
            return
        self.current_layout = None
        self.current_general = None
        self.preview_canvas.delete("all")
        self.status.set(exception_text(error, self.language))
        if show_errors:
            messagebox.showerror(self.t("preview_error"), exception_text(error, self.language), parent=self.root)

    def _draw_current_layout(self) -> None:
        canvas = self.preview_canvas
        canvas.delete("all")
        result = self.current_layout
        general = self.current_general
        if not result or not general:
            canvas.create_text(
                max(1, canvas.winfo_width()) / 2,
                max(1, canvas.winfo_height()) / 2,
                text=self.t("preview_empty"),
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
            self.status.set(exception_text(exc, self.language))
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
        self.orientation.set(next(label for label, value in self._orientation_labels().items() if value is general.orientation))
        self.flow.set(next(label for label, value in self._flow_labels().items() if value is general.flow))

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
            raise ValueError(self.t("preset_select_first"))
        return self.store.select_preset(preset_id)

    def load_selected_preset(self) -> None:
        try:
            preset = self.selected_preset()
            self._apply_general(preset.general)
            self._set_status("preset_loaded", name=preset.name)
        except (ValueError, KeyError) as exc:
            messagebox.showerror(self.t("preset_title"), exception_text(exc, self.language), parent=self.root)

    def add_preset(self) -> None:
        name = simpledialog.askstring(self.t("preset_add_title"), self.t("preset_name_prompt"), parent=self.root)
        if name is None:
            return
        try:
            preset = self.store.add_preset(name, self.read_general())
            self.refresh_preset_list(preset.id)
            self._set_status("preset_added", name=preset.name)
        except (ValueError, PermissionError) as exc:
            messagebox.showerror(self.t("cannot_add"), exception_text(exc, self.language), parent=self.root)

    def overwrite_preset(self) -> None:
        try:
            preset = self.selected_preset()
            if not messagebox.askyesno(self.t("preset_overwrite_title"), self.t("preset_overwrite_prompt", name=preset.name), parent=self.root):
                return
            updated = self.store.overwrite_preset(preset.id, self.read_general())
            self.refresh_preset_list(updated.id)
            self._set_status("preset_overwritten", name=updated.name)
        except (ValueError, KeyError, PermissionError) as exc:
            messagebox.showerror(self.t("cannot_overwrite"), exception_text(exc, self.language), parent=self.root)

    def rename_preset(self) -> None:
        try:
            preset = self.selected_preset()
            name = simpledialog.askstring(self.t("preset_rename_title"), self.t("preset_new_name"), initialvalue=preset.name, parent=self.root)
            if name is None:
                return
            updated = self.store.rename_preset(preset.id, name)
            self.refresh_preset_list(updated.id)
            self._set_status("preset_renamed", name=updated.name)
        except (ValueError, KeyError, PermissionError) as exc:
            messagebox.showerror(self.t("cannot_rename"), exception_text(exc, self.language), parent=self.root)

    def delete_preset(self) -> None:
        try:
            preset = self.selected_preset()
            if not messagebox.askyesno(self.t("preset_delete_title"), self.t("preset_delete_prompt", name=preset.name), parent=self.root):
                return
            self.store.delete_preset(preset.id)
            self.refresh_preset_list()
            self._set_status("preset_deleted", name=preset.name)
        except (ValueError, KeyError, PermissionError) as exc:
            messagebox.showerror(self.t("cannot_delete"), exception_text(exc, self.language), parent=self.root)

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
        target_label = self.t("start_coordinates") if target == "start" else self.t("end_coordinates")
        title = self.t("detect", target=target_label)
        self.set_busy(True, "detecting", target=target_label)
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
            label = self.t("start_short")
        else:
            self.end_x.set(str(x))
            self.end_y.set(str(y))
            label = self.t("end_short")
        self._close_detection_overlay()
        self.root.deiconify()
        self.root.lift()
        self.set_busy(False, "coordinate_detected", target=label, x=x, y=y)
        self.refresh_preview()

    def start_writing(self) -> None:
        if self.busy:
            return
        try:
            result, environment = self.build_result()
            self.store.set_environment(environment)
        except BaseException as exc:
            messagebox.showerror(self.t("cannot_start"), exception_text(exc, self.language), parent=self.root)
            return
        self.current_layout = result
        self.current_general = self.read_general()
        self.set_busy(True, "preparing_write")
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
        self.set_busy(False, "writing_complete")
        messagebox.showinfo(self.t("complete"), self.t("complete_message"), parent=self.root)

    def _restore_after_operation(self, error: BaseException) -> None:
        self._close_detection_overlay()
        self.root.deiconify()
        self.root.lift()
        if isinstance(error, WritingCancelled):
            status_key = "cancelled_failsafe" if error.message_key == "failsafe_stop" else "cancelled_esc"
            self.set_busy(False, status_key)
            return
        self.set_busy(False, "operation_failed")
        messagebox.showerror(self.t("operation_failed"), exception_text(error, self.language), parent=self.root)

    def set_busy(self, busy: bool, status_key: str, **values: object) -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.preview_button.configure(state=state)
        self.execute_button.configure(state=state)
        for button in self.coordinate_buttons:
            button.configure(state=state)
        self.language_combo.configure(state="disabled" if busy else "readonly")
        self._set_status(status_key, **values)
        self.status_mark.configure(foreground=self.ACCENT if busy else self.PRIMARY)

    def on_close(self) -> None:
        if self.busy:
            self.stop_event.set()
            messagebox.showwarning(self.t("operation_running"), self.t("stop_requested"), parent=self.root)
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
    validate_translation_catalogs()
    sample = DEFAULT_KANJIVG_DIR / "065e5.svg"
    if not sample.exists():
        raise RuntimeError(f"找不到 KanjiVG 測試檔：{sample}")
    settings = LayoutSettings(
        start_x=10,
        start_y=10,
        end_x=500,
        end_y=1100,
        general=GeneralSettings(font_size=100),
    )
    result = build_layout("あょっA0,，.．!！?？:：;；@＠~～、､。｡・･ーｰ", DEFAULT_KANJIVG_DIR, settings)
    if len(result.kanjivg_chars) != 29 or not result.paths:
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
