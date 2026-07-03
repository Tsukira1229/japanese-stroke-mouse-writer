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


class DocumentationTests(unittest.TestCase):
    def test_trilingual_documents_exist_and_old_guide_is_removed(self) -> None:
        self.assertTrue(all(path.exists() for path in DOCS))
        self.assertFalse((ROOT / "圖文使用教學.md").exists())

    def test_markdown_document_links_resolve(self) -> None:
        for document in DOCS:
            text = document.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^]]+\]\(([^)]+\.md)\)", text):
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
        symbol_pairs = (",，", ".．", "!！", "?？", ":：", ";；", "@＠", "~～", "、､", "。｡", "・･", "ーｰ")
        for document in DOCS:
            text = document.read_text(encoding="utf-8")
            self.assertIn("A–Z", text)
            self.assertIn("0–9", text)
            for pair in symbol_pairs:
                self.assertIn(pair, text)

    def test_all_documents_use_current_version(self) -> None:
        for document in DOCS:
            text = document.read_text(encoding="utf-8")
            self.assertIn("V2.1.3", text)
            self.assertNotIn("V2.1.2", text)


if __name__ == "__main__":
    unittest.main()
