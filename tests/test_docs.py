from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = (
    ROOT / "README.md",
    ROOT / "README.en.md",
    ROOT / "README.ja.md",
    ROOT / "complete-guide.md",
    ROOT / "complete-guide.en.md",
    ROOT / "complete-guide.ja.md",
)
HTML_GUIDES = (
    ROOT / "complete-guide.html",
    ROOT / "complete-guide.en.html",
    ROOT / "complete-guide.ja.html",
)
POLICY_DOCS = (
    ROOT / "LICENSE",
    ROOT / "CODE_SIGNING_POLICY.md",
    ROOT / "PRIVACY.md",
    ROOT / "SECURITY.md",
    ROOT / "THIRD_PARTY_NOTICES.md",
)


class DocumentationTests(unittest.TestCase):
    def test_trilingual_documents_exist_and_old_guide_is_removed(self) -> None:
        self.assertTrue(all(path.exists() for path in DOCS))
        self.assertTrue(all(path.exists() for path in HTML_GUIDES))
        self.assertTrue(all(path.exists() for path in POLICY_DOCS))
        self.assertFalse((ROOT / "圖文使用教學.md").exists())

    def test_markdown_document_links_resolve(self) -> None:
        for document in DOCS:
            text = document.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^]]+\]\(([^)]+\.md)\)", text):
                with self.subTest(document=document.name, target=target):
                    self.assertTrue((document.parent / target).exists())

    def test_html_guide_links_resolve(self) -> None:
        for document in HTML_GUIDES:
            text = document.read_text(encoding="utf-8")
            for target in re.findall(r'href="([^"#]+)"', text):
                if "://" not in target:
                    with self.subTest(document=document.name, target=target):
                        self.assertTrue((document.parent / target).exists())

    def test_readmes_have_installation_without_development_section(self) -> None:
        expectations = {
            "README.md": "## 安裝方式",
            "README.en.md": "## Installation",
            "README.ja.md": "## インストール方法",
        }
        for filename, heading in expectations.items():
            text = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn(heading, text)
            self.assertNotIn("開發與測試", text)
            self.assertNotIn("Development and Testing", text)
            self.assertNotIn("開発とテスト", text)
        self.assertNotIn("一般使用者", (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_all_languages_document_new_character_support(self) -> None:
        symbol_pairs = ("#＃", "(（", ")）", "[［", "]］", "@＠", "~～", "、､", "。｡", "・･", "ーｰ", "「」", "【】", "｢｣")
        for document in DOCS:
            text = document.read_text(encoding="utf-8")
            self.assertIn("A–Z", text)
            self.assertIn("0–9", text)
            self.assertIn("0.5", text)
            self.assertIn("ｶﾞ", text)
            self.assertTrue("顏文字" in text or "Kaomoji" in text or "顔文字" in text)
            self.assertTrue("中心線" in text or "centerline" in text)
            self.assertNotIn("輪廓", text)
            self.assertNotIn("outline", text.lower())
            self.assertNotIn("アウトライン", text)
            for pair in symbol_pairs:
                self.assertIn(pair, text)

    def test_all_documents_use_current_version(self) -> None:
        for document in (*DOCS, *HTML_GUIDES):
            text = document.read_text(encoding="utf-8")
            self.assertIn("V2.7.1", text)
            self.assertNotIn("2.6.0-preview", text.lower())
            self.assertNotIn("V2.4.1", text)
            self.assertNotIn("V2.4.0", text)
            self.assertNotIn("V2.3.1", text)

    def test_license_privacy_and_code_signing_policy_are_public(self) -> None:
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        policy = (ROOT / "CODE_SIGNING_POLICY.md").read_text(encoding="utf-8")
        privacy = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2026 Tsukira1229", license_text)
        self.assertIn("Code signing policy", policy)
        self.assertIn("was not approved", policy)
        self.assertIn("Current releases", policy)
        self.assertNotIn("Free code signing provided by", policy)
        self.assertNotIn("active Authenticode signing workflow", policy.split("does not currently have", 1)[0])
        self.assertIn("Tsukira1229", policy)
        self.assertIn("will not transfer any information", privacy)

    def test_signpath_status_is_not_pending_or_integrating(self) -> None:
        forbidden = (
            "正在申請",
            "申請中",
            "is applying",
            "after the application is approved",
            "Free code signing provided by",
            "核准後",
            "承認後",
            "font contours",
            "font outline",
            "built-in kaomoji categories",
        )
        for document in (*DOCS, *POLICY_DOCS):
            text = document.read_text(encoding="utf-8")
            for phrase in forbidden:
                with self.subTest(document=document.name, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_user_guides_describe_partial_symbol_support_without_removed_wording(self) -> None:
        forbidden = (
            "不再提供內建" + "顏文字分類",
            "彩色 emoji、keycap" + " 與 ZWJ 組合序列不支援",
            "no longer provides built-in " + "kaomoji categories",
            "内蔵の顔文字分類" + "は提供しません",
        )
        localization = (ROOT / "localization.py").read_text(encoding="utf-8")
        for text in [localization, *(path.read_text(encoding="utf-8") for path in DOCS), *(path.read_text(encoding="utf-8") for path in HTML_GUIDES)]:
            self.assertFalse(any(phrase in text for phrase in forbidden))
        for document in DOCS[3:]:
            text = document.read_text(encoding="utf-8")
            self.assertTrue(
                "一部分" in text or "some commonly used" in text or "一部" in text,
                document.name,
            )

    def test_readmes_document_current_stroke_styles_and_symbol_expansion(self) -> None:
        expectations = {
            "README.md": ("KanjiVG (預設)", "Yomogi", "Zen Kurenaido", "Hachi Maru Pop", "最佳努力", "特殊符號"),
            "README.en.md": ("KanjiVG (Default)", "Yomogi", "Zen Kurenaido", "Hachi Maru Pop", "best-effort", "special symbols"),
            "README.ja.md": ("KanjiVG (既定)", "Yomogi", "Zen Kurenaido", "Hachi Maru Pop", "ベストエフォート", "特殊記号"),
        }
        for filename, phrases in expectations.items():
            text = (ROOT / filename).read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text)
            self.assertTrue("自訂選項" in text or "presets" in text.lower() or "プリセット" in text)

    def test_ui_guidance_matches_bottom_status_bar_and_help_tab(self) -> None:
        old_descriptions = ("標題下方固定", "below the title", "タイトル下")
        for document in DOCS:
            text = document.read_text(encoding="utf-8")
            self.assertFalse(any(description in text for description in old_descriptions))

    def test_readmes_document_current_portable_folder(self) -> None:
        for document in DOCS[:3]:
            text = document.read_text(encoding="utf-8")
            self.assertIn("JapaneseStrokeMouseWriter-v2.7.1-development-win-x64-portable", text)
            self.assertNotIn("JapaneseStrokeMouseWriter-v2.4.1-win-x64-portable", text)

    def test_portable_build_includes_html_guides(self) -> None:
        build_script = (ROOT / "scripts" / "build_portable.ps1").read_text(encoding="utf-8")
        self.assertIn('-Filter "*.html"', build_script)
        self.assertIn("generate_html_guides.py", build_script)

    def test_v271_development_build_is_uncompressed_and_local(self) -> None:
        build_script = (ROOT / "scripts" / "build_development_portable.ps1").read_text(encoding="utf-8")
        self.assertIn("JapaneseStrokeMouseWriter-v2.7.1-development-win-x64-portable", build_script)
        self.assertIn("build\\development-v2.7.1", build_script)
        for style_id in ("yomogi", "zen-kurenaido", "hachi-maru-pop"):
            self.assertIn(style_id, build_script)
        self.assertNotIn("CreateFromDirectory", build_script)
        self.assertNotIn("Compress-Archive", build_script)
        self.assertNotIn("gh release", build_script.lower())


if __name__ == "__main__":
    unittest.main()

