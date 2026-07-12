# -*- coding: utf-8 -*-
"""Matcha sakura theme palettes and Windows appearance integration."""

from __future__ import annotations

import ctypes
import sys
from dataclasses import dataclass
from enum import Enum


class AppearanceMode(str, Enum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class ThemePalette:
    name: str
    dark: bool
    background: str
    surface: str
    surface_alt: str
    text: str
    muted: str
    border: str
    primary: str
    primary_active: str
    on_primary: str
    mint: str
    soda: str
    soda_active: str
    on_soda: str
    grape: str
    grape_active: str
    on_grape: str
    warning: str
    error: str
    success: str
    annotation: str
    disabled: str
    on_disabled: str
    canvas: str
    path: str


CANDY_LIGHT = ThemePalette(
    name="matcha-sakura-light",
    dark=False,
    background="#FBF7EE",
    surface="#FFFDF7",
    surface_alt="#EEF3EA",
    text="#3E373D",
    muted="#746C70",
    border="#D5CCC0",
    primary="#E8B6C2",
    primary_active="#DFA4B3",
    on_primary="#5B2E3B",
    mint="#6F946D",
    soda="#C4D9B5",
    soda_active="#B2CCA0",
    on_soda="#344B2E",
    grape="#D6C8E5",
    grape_active="#C7B5DA",
    on_grape="#4A3B5B",
    warning="#8A5E22",
    error="#A84759",
    success="#4F7A55",
    annotation="#B94C63",
    disabled="#E4DED4",
    on_disabled="#7B7475",
    canvas="#FFFCF4",
    path="#242125",
)

CANDY_NIGHT = ThemePalette(
    name="matcha-sakura-night",
    dark=True,
    background="#252822",
    surface="#2F332B",
    surface_alt="#3A4035",
    text="#F4F0E7",
    muted="#C4BDB2",
    border="#596052",
    primary="#C98E9E",
    primary_active="#D7A1AF",
    on_primary="#321A23",
    mint="#9AB29A",
    soda="#99B186",
    soda_active="#ADC19B",
    on_soda="#1D2A19",
    grape="#A999BD",
    grape_active="#BAACCC",
    on_grape="#292034",
    warning="#D4B16A",
    error="#DF8B98",
    success="#8FBE91",
    annotation="#E3A1AD",
    disabled="#484C43",
    on_disabled="#A6A99F",
    canvas="#171914",
    path="#F4F0E7",
)


def appearance_from_value(value: object) -> AppearanceMode:
    try:
        return AppearanceMode(str(value))
    except ValueError:
        return AppearanceMode.LIGHT


def windows_apps_use_light_theme() -> bool:
    if sys.platform != "win32":
        return True
    try:
        import winreg

        path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            value, _kind = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return bool(value)
    except OSError:
        return True


def resolve_palette(mode: AppearanceMode) -> ThemePalette:
    if mode is AppearanceMode.DARK:
        return CANDY_NIGHT
    if mode is AppearanceMode.LIGHT:
        return CANDY_LIGHT
    return CANDY_LIGHT if windows_apps_use_light_theme() else CANDY_NIGHT


def configure_windows_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            pass


def apply_windows_titlebar_theme(root: object, dark: bool) -> None:
    if sys.platform != "win32":
        return
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        value = ctypes.c_int(1 if dark else 0)
        for attribute in (20, 19):
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                attribute,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
            if result == 0:
                break
    except (AttributeError, OSError):
        pass
