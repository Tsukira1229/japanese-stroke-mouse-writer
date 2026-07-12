from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localization import Language
from appearance import AppearanceMode
from mouse_writer_pro import EnvironmentSettings, FlowDirection, GeneralSettings, Orientation
from settings_store import SettingsStore


class SettingsStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "user_data/settings.json"
        self.store = SettingsStore(self.path)
        self.store.load()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_named_preset_crud(self) -> None:
        general = GeneralSettings(
            font_size=120,
            char_gap=8,
            line_gap=16,
            orientation=Orientation.VERTICAL,
            flow=FlowDirection.LEFT,
        )
        preset = self.store.add_preset("直書", general)
        self.assertEqual(self.store.select_preset(preset.id).general, general)
        renamed = self.store.rename_preset(preset.id, "直書向左")
        self.assertEqual(renamed.name, "直書向左")
        updated = self.store.overwrite_preset(preset.id, GeneralSettings(font_size=90))
        self.assertEqual(updated.general.font_size, 90)
        self.store.delete_preset(preset.id)
        self.assertEqual(self.store.state.presets, [])

    def test_duplicate_names_are_case_insensitive(self) -> None:
        self.store.add_preset("Sample", GeneralSettings())
        with self.assertRaises(ValueError):
            self.store.add_preset("sample", GeneralSettings())

    def test_environment_persists(self) -> None:
        expected = EnvironmentSettings(countdown=8, sample_spacing=1.5, point_delay=0.02, move_duration=0.0)
        self.store.set_environment(expected)
        loaded = SettingsStore(self.path).load().environment
        self.assertEqual(loaded, expected)
        self.assertNotIn("move_duration", json.loads(self.path.read_text(encoding="utf-8"))["environment"])

    def test_language_persists(self) -> None:
        self.store.set_language(Language.JAPANESE)
        loaded = SettingsStore(self.path).load()
        self.assertIs(loaded.language, Language.JAPANESE)
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["language"], "ja")

    def test_appearance_mode_persists_without_schema_change(self) -> None:
        self.store.set_appearance_mode(AppearanceMode.DARK)
        loaded = SettingsStore(self.path).load()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertIs(loaded.appearance_mode, AppearanceMode.DARK)
        self.assertEqual(payload["appearance_mode"], "dark")
        self.assertEqual(payload["schema_version"], 1)

    def test_explicit_system_appearance_remains_supported(self) -> None:
        self.store.set_appearance_mode(AppearanceMode.SYSTEM)
        self.assertIs(SettingsStore(self.path).load().appearance_mode, AppearanceMode.SYSTEM)

    def test_legacy_settings_default_to_light_appearance(self) -> None:
        self.path.write_text(
            json.dumps({"schema_version": 1, "environment": {}, "presets": []}),
            encoding="utf-8",
        )
        self.assertIs(SettingsStore(self.path).load().appearance_mode, AppearanceMode.LIGHT)

    def test_legacy_settings_use_system_language(self) -> None:
        self.path.write_text(
            json.dumps({"schema_version": 1, "environment": {}, "presets": []}),
            encoding="utf-8",
        )
        with patch("localization._system_locale_name", return_value="zh-CN"):
            loaded = SettingsStore(self.path).load()
        self.assertIs(loaded.language, Language.SIMPLIFIED_CHINESE)

    def test_legacy_move_duration_is_ignored_and_removed_on_save(self) -> None:
        self.path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "environment": {
                        "countdown": 6,
                        "sample_spacing": 1.25,
                        "point_delay": 0.012,
                        "move_duration": 0.5,
                    },
                    "last_preset_id": None,
                    "presets": [],
                }
            ),
            encoding="utf-8",
        )
        loaded = SettingsStore(self.path)
        environment = loaded.load().environment
        self.assertEqual(environment.point_delay, 0.012)
        self.assertEqual(environment.move_duration, 0.0)
        loaded.set_environment(environment)
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertNotIn("move_duration", payload["environment"])

    def test_corrupt_json_is_backed_up(self) -> None:
        self.path.write_text("{invalid", encoding="utf-8")
        state = SettingsStore(self.path).load()
        self.assertEqual(state.presets, [])
        self.assertTrue(self.path.with_suffix(".json.broken").exists())
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
