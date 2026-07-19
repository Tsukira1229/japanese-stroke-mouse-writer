from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import markdown


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Guide:
    source: str
    target: str
    language: str
    title: str
    contents_label: str


GUIDES = (
    Guide("complete-guide.md", "complete-guide.html", "zh-Hant", "完整說明", "本頁目錄"),
    Guide("complete-guide.en.md", "complete-guide.en.html", "en", "Complete Guide", "On this page"),
    Guide("complete-guide.ja.md", "complete-guide.ja.html", "ja", "完全ガイド", "ページ目次"),
)

STYLE = """
:root {
  color-scheme: light;
  --background: #fff8fb;
  --surface: #ffffff;
  --surface-alt: #f4faff;
  --text: #3a3342;
  --muted: #746b7c;
  --border: #e8dde8;
  --accent: #c83f75;
  --accent-soft: #fde8f0;
  --link: #306f9f;
  --code: #f5eff6;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--background);
  color: var(--text);
  font-family: "Segoe UI", "Microsoft JhengHei", "Yu Gothic UI", sans-serif;
  font-size: 16px;
  line-height: 1.75;
}
a { color: var(--link); }
a:hover { text-decoration-thickness: 2px; }
.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  min-height: 58px;
  padding: 10px clamp(18px, 4vw, 48px);
  background: rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid var(--border);
}
.brand { color: var(--text); font-weight: 700; text-decoration: none; }
.languages { display: flex; flex-wrap: wrap; gap: 14px; font-size: 14px; }
.languages a[aria-current="page"] { color: var(--accent); font-weight: 700; }
.layout {
  display: grid;
  grid-template-columns: minmax(180px, 230px) minmax(0, 820px);
  justify-content: center;
  gap: clamp(28px, 5vw, 64px);
  padding: 38px clamp(18px, 5vw, 64px) 80px;
}
.toc {
  position: sticky;
  top: 88px;
  align-self: start;
  max-height: calc(100vh - 110px);
  overflow: auto;
  padding: 18px;
  background: var(--surface-alt);
  border: 1px solid var(--border);
  border-radius: 8px;
}
.toc-title { margin: 0 0 8px; color: var(--muted); font-size: 13px; font-weight: 700; }
.toc ul { margin: 0; padding-left: 18px; }
.toc li { margin: 5px 0; }
.toc a { color: var(--text); font-size: 14px; text-decoration: none; }
main {
  min-width: 0;
  padding: clamp(24px, 5vw, 52px);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 12px 36px rgba(72, 48, 77, 0.08);
}
h1, h2 { line-height: 1.35; }
h1 { margin-top: 0; font-size: clamp(28px, 4vw, 40px); }
h2 { margin-top: 2.2em; padding-bottom: 8px; border-bottom: 2px solid var(--accent-soft); font-size: 23px; }
li + li { margin-top: 6px; }
code {
  padding: 2px 6px;
  background: var(--code);
  border-radius: 4px;
  font-family: Consolas, "Cascadia Mono", monospace;
  overflow-wrap: anywhere;
}
.headerlink { margin-left: 8px; color: var(--border); text-decoration: none; }
h1:hover .headerlink, h2:hover .headerlink { color: var(--accent); }
.footer { margin-top: 44px; padding-top: 20px; color: var(--muted); border-top: 1px solid var(--border); font-size: 14px; }
@media (max-width: 820px) {
  .topbar { position: static; align-items: flex-start; flex-direction: column; gap: 4px; }
  .layout { display: block; padding-top: 20px; }
  .toc { position: static; max-height: none; margin-bottom: 20px; }
  main { padding: 24px 20px; }
}
@media print {
  .topbar, .toc { display: none; }
  body { background: #fff; }
  .layout { display: block; padding: 0; }
  main { border: 0; box-shadow: none; padding: 0; }
}
""".strip()


def language_links(current_target: str) -> str:
    links = (
        ("complete-guide.html", "繁體中文"),
        ("complete-guide.en.html", "English"),
        ("complete-guide.ja.html", "日本語"),
    )
    rendered = []
    for target, label in links:
        current = ' aria-current="page"' if target == current_target else ""
        rendered.append(f'<a href="{target}"{current}>{label}</a>')
    return "\n".join(rendered)


def render(guide: Guide) -> str:
    source = (ROOT / guide.source).read_text(encoding="utf-8")
    converter = markdown.Markdown(
        extensions=["sane_lists", "toc"],
        extension_configs={"toc": {"toc_depth": "2-2"}},
        output_format="html5",
    )
    body = converter.convert(source)
    return f"""<!doctype html>
<html lang="{guide.language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>Japanese Stroke Mouse Writer V2.7.1 Development - {guide.title}</title>
  <style>{STYLE}</style>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="#content">Japanese Stroke Mouse Writer V2.7.1 Development</a>
    <nav class="languages" aria-label="Languages">
      {language_links(guide.target)}
    </nav>
  </header>
  <div class="layout">
    <nav class="toc" aria-label="{guide.contents_label}">
      <p class="toc-title">{guide.contents_label}</p>
      {converter.toc}
    </nav>
    <main id="content">
      {body}
      <p class="footer">Japanese Stroke Mouse Writer V2.7.1 Development - Offline documentation</p>
    </main>
  </div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate standalone HTML guides from Markdown.")
    parser.add_argument("--check", action="store_true", help="Fail when generated files are out of date.")
    args = parser.parse_args()

    stale: list[str] = []
    for guide in GUIDES:
        output = render(guide)
        target = ROOT / guide.target
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != output:
                stale.append(guide.target)
        else:
            target.write_text(output, encoding="utf-8", newline="\n")

    if stale:
        parser.error("out-of-date HTML guides: " + ", ".join(stale))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
