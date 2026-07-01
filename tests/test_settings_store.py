from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

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
        expected = EnvironmentSettings(countdown=8, sample_spacing=1.5, point_delay=0.02, move_duration=0.01)
        self.store.set_environment(expected)
        loaded = SettingsStore(self.path).load().environment
        self.assertEqual(loaded, expected)

    def test_corrupt_json_is_backed_up(self) -> None:
        self.path.write_text("{invalid", encoding="utf-8")
        state = SettingsStore(self.path).load()
        self.assertEqual(state.presets, [])
        self.assertTrue(self.path.with_suffix(".json.broken").exists())
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
