from __future__ import annotations

import unittest
from unittest.mock import patch

from localization import (
    Language,
    detect_system_language,
    exception_text,
    tr,
    validate_translation_catalogs,
)
from mouse_writer_pro import LayoutError


class LocalizationTests(unittest.TestCase):
    def test_translation_catalogs_are_complete(self) -> None:
        validate_translation_catalogs()

    def test_windows_locale_mapping(self) -> None:
        cases = {
            "ja-JP": Language.JAPANESE,
            "zh-TW": Language.TRADITIONAL_CHINESE,
            "zh-HK": Language.TRADITIONAL_CHINESE,
            "zh-Hans-CN": Language.SIMPLIFIED_CHINESE,
            "zh-CN": Language.SIMPLIFIED_CHINESE,
            "en-US": Language.ENGLISH,
            "fr-FR": Language.ENGLISH,
        }
        for locale_name, expected in cases.items():
            with self.subTest(locale_name=locale_name), patch(
                "localization._system_locale_name", return_value=locale_name
            ):
                self.assertIs(detect_system_language(), expected)

    def test_domain_error_can_be_localized(self) -> None:
        error = LayoutError("layout_text_empty")
        self.assertEqual(str(error), tr("layout_text_empty", Language.TRADITIONAL_CHINESE))
        self.assertEqual(exception_text(error, Language.ENGLISH), tr("layout_text_empty", Language.ENGLISH))
        self.assertEqual(exception_text(error, Language.JAPANESE), tr("layout_text_empty", Language.JAPANESE))


if __name__ == "__main__":
    unittest.main()
