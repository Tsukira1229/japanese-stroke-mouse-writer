# -*- coding: utf-8 -*-
"""Portable JSON settings and named general-layout presets."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from uuid import uuid4

from mouse_writer_pro import (
    EXECUTABLE_DIR,
    EnvironmentSettings,
    FlowDirection,
    GeneralSettings,
    Orientation,
)

SCHEMA_VERSION = 1
DEFAULT_SETTINGS_PATH = EXECUTABLE_DIR / "user_data/settings.json"


@dataclass(frozen=True)
class Preset:
    id: str
    name: str
    general: GeneralSettings


@dataclass
class SettingsState:
    environment: EnvironmentSettings = field(default_factory=EnvironmentSettings)
    presets: list[Preset] = field(default_factory=list)
    last_preset_id: str | None = None


def general_to_dict(settings: GeneralSettings) -> dict[str, object]:
    return {
        "font_size": settings.font_size,
        "char_gap": settings.char_gap,
        "line_gap": settings.line_gap,
        "orientation": settings.orientation.value,
        "flow": settings.flow.value,
    }


def general_from_dict(data: dict[str, object]) -> GeneralSettings:
    return GeneralSettings(
        font_size=float(data.get("font_size", 150)),
        char_gap=float(data.get("char_gap", 12)),
        line_gap=float(data.get("line_gap", 24)),
        orientation=Orientation(str(data.get("orientation", "horizontal"))),
        flow=FlowDirection(str(data.get("flow", "right"))),
    )


def environment_to_dict(settings: EnvironmentSettings) -> dict[str, object]:
    data = asdict(settings)
    data.pop("stroke_delay", None)
    return data


def environment_from_dict(data: dict[str, object]) -> EnvironmentSettings:
    return EnvironmentSettings(
        countdown=int(data.get("countdown", 5)),
        sample_spacing=float(data.get("sample_spacing", 2.0)),
        point_delay=float(data.get("point_delay", 0.008)),
        move_duration=float(data.get("move_duration", 0.0)),
        stroke_delay=0.03,
    )


class SettingsStore:
    def __init__(self, path: Path = DEFAULT_SETTINGS_PATH) -> None:
        self.path = path
        self.state = SettingsState()

    def ensure_writable(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        probe = self.path.parent / ".write-test"
        try:
            probe.write_text("ok", encoding="ascii")
        except OSError as exc:
            raise PermissionError(
                f"Portable 資料夾無法寫入：{self.path.parent}\n"
                "請將整個程式資料夾移到文件、桌面或其他可寫入位置。"
            ) from exc
        finally:
            probe.unlink(missing_ok=True)

    def load(self) -> SettingsState:
        self.ensure_writable()
        if not self.path.exists():
            self.state = SettingsState()
            return self.state
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if raw.get("schema_version") != SCHEMA_VERSION:
                raise ValueError("不支援的設定檔版本。")
            presets = [
                Preset(
                    id=str(item["id"]),
                    name=str(item["name"]),
                    general=general_from_dict(dict(item["general"])),
                )
                for item in raw.get("presets", [])
            ]
            self.state = SettingsState(
                environment=environment_from_dict(dict(raw.get("environment", {}))),
                presets=presets,
                last_preset_id=raw.get("last_preset_id"),
            )
            return self.state
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            self._backup_broken_file()
            self.state = SettingsState()
            self.save()
            return self.state

    def save(self) -> None:
        self.ensure_writable()
        payload = {
            "schema_version": SCHEMA_VERSION,
            "environment": environment_to_dict(self.state.environment),
            "last_preset_id": self.state.last_preset_id,
            "presets": [
                {"id": preset.id, "name": preset.name, "general": general_to_dict(preset.general)}
                for preset in self.state.presets
            ],
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, self.path)

    def set_environment(self, environment: EnvironmentSettings) -> None:
        self.state.environment = environment
        self.save()

    def add_preset(self, name: str, general: GeneralSettings) -> Preset:
        validated = self._validate_name(name)
        self._ensure_unique(validated)
        preset = Preset(id=uuid4().hex, name=validated, general=general)
        self.state.presets.append(preset)
        self.state.last_preset_id = preset.id
        self.save()
        return preset

    def overwrite_preset(self, preset_id: str, general: GeneralSettings) -> Preset:
        index = self._preset_index(preset_id)
        current = self.state.presets[index]
        updated = Preset(id=current.id, name=current.name, general=general)
        self.state.presets[index] = updated
        self.state.last_preset_id = preset_id
        self.save()
        return updated

    def rename_preset(self, preset_id: str, name: str) -> Preset:
        index = self._preset_index(preset_id)
        validated = self._validate_name(name)
        self._ensure_unique(validated, excluding_id=preset_id)
        current = self.state.presets[index]
        updated = Preset(id=current.id, name=validated, general=current.general)
        self.state.presets[index] = updated
        self.save()
        return updated

    def delete_preset(self, preset_id: str) -> None:
        index = self._preset_index(preset_id)
        del self.state.presets[index]
        if self.state.last_preset_id == preset_id:
            self.state.last_preset_id = None
        self.save()

    def select_preset(self, preset_id: str) -> Preset:
        preset = self.state.presets[self._preset_index(preset_id)]
        self.state.last_preset_id = preset_id
        self.save()
        return preset

    def _backup_broken_file(self) -> None:
        if not self.path.exists():
            return
        backup = self.path.with_suffix(self.path.suffix + ".broken")
        counter = 1
        while backup.exists():
            backup = self.path.with_suffix(self.path.suffix + f".broken.{counter}")
            counter += 1
        shutil.move(self.path, backup)

    def _preset_index(self, preset_id: str) -> int:
        for index, preset in enumerate(self.state.presets):
            if preset.id == preset_id:
                return index
        raise KeyError("找不到指定的自訂選項。")

    @staticmethod
    def _validate_name(name: str) -> str:
        validated = name.strip()
        if not 1 <= len(validated) <= 40:
            raise ValueError("自訂選項名稱必須為 1 至 40 個字元。")
        return validated

    def _ensure_unique(self, name: str, excluding_id: str | None = None) -> None:
        normalized = name.casefold()
        if any(
            preset.id != excluding_id and preset.name.casefold() == normalized
            for preset in self.state.presets
        ):
            raise ValueError("已有相同名稱的自訂選項。")
