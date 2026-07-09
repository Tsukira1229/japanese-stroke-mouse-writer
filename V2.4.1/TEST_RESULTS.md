# V2.4.1 Test Results

Status: passed local verification.

Executed checks:

- `python -m unittest discover -s tests -v`: 79 tests passed.
- `python mouse_writer_ui.pyw --self-test --settings-path V2.4.1\self-test-settings.json`: passed.
- `python mouse_writer_pro.py --text "(^O^) (≧▽≦) m(_ _)m (/ω＼) ¯\_(ツ)_/¯ (╯°□°)╯︵ ┻━┻ ฅ^•ﻌ•^ฅ" --preview V2.4.1\emoticon-centerline-preview.png`: generated preview successfully.
- `powershell -ExecutionPolicy Bypass -File scripts\build_internal_v2_4_1.ps1`: PyInstaller onedir build completed and frozen self-test passed.
- `V2.4.1\JapaneseStrokeMouseWriter-v2.4.1-win-x64-portable\JapaneseStrokeMouseWriter.exe --self-test`: passed.
- `git tag --list "v2.4.1"`: no tag exists.
- No V2.4.1 release ZIP was created. PyInstaller's required runtime `_internal\base_library.zip` remains inside the onedir folder.
