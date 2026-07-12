from __future__ import annotations

import unittest
from unittest.mock import patch

from appearance import (
    AppearanceMode,
    CANDY_LIGHT,
    CANDY_NIGHT,
    appearance_from_value,
    resolve_palette,
    windows_apps_use_light_theme,
)


class AppearanceTests(unittest.TestCase):
    def test_explicit_modes_select_expected_palettes(self) -> None:
        self.assertIs(resolve_palette(AppearanceMode.LIGHT), CANDY_LIGHT)
        self.assertIs(resolve_palette(AppearanceMode.DARK), CANDY_NIGHT)

    def test_system_mode_uses_windows_preference(self) -> None:
        with patch("appearance.windows_apps_use_light_theme", return_value=True):
            self.assertIs(resolve_palette(AppearanceMode.SYSTEM), CANDY_LIGHT)
        with patch("appearance.windows_apps_use_light_theme", return_value=False):
            self.assertIs(resolve_palette(AppearanceMode.SYSTEM), CANDY_NIGHT)

    def test_non_windows_detection_falls_back_to_light(self) -> None:
        with patch("appearance.sys.platform", "linux"):
            self.assertTrue(windows_apps_use_light_theme())

    def test_invalid_saved_value_falls_back_to_light(self) -> None:
        self.assertIs(appearance_from_value("unknown"), AppearanceMode.LIGHT)

    def test_palette_tokens_match_preview_contract(self) -> None:
        self.assertEqual(CANDY_LIGHT.background, "#FBF7EE")
        self.assertEqual(CANDY_LIGHT.primary, "#E8B6C2")
        self.assertEqual(CANDY_NIGHT.background, "#252822")
        self.assertEqual(CANDY_NIGHT.grape, "#A999BD")

    def test_button_and_annotation_pairs_meet_normal_text_contrast(self) -> None:
        for palette in (CANDY_LIGHT, CANDY_NIGHT):
            pairs = (
                (palette.primary, palette.on_primary),
                (palette.soda, palette.on_soda),
                (palette.grape, palette.on_grape),
                (palette.canvas, palette.annotation),
            )
            for background, foreground in pairs:
                self.assertGreaterEqual(self._contrast_ratio(background, foreground), 4.5)

    @staticmethod
    def _contrast_ratio(first: str, second: str) -> float:
        def luminance(color: str) -> float:
            channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [
                channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
                for channel in channels
            ]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
        return (lighter + 0.05) / (darker + 0.05)


if __name__ == "__main__":
    unittest.main()
