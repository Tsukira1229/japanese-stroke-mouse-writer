# V2.4.0 Test Results

## Local validation

- Command: `python -m unittest discover -s tests -v`
- Result: 77 tests passed.

- Command: `python mouse_writer_ui.pyw --self-test`
- Result: `Japanese Stroke Mouse Writer 2.4.0 self-test passed`.

- Command: `powershell -ExecutionPolicy Bypass -File scripts\build_portable.ps1`
- Result: PyInstaller onedir build passed, frozen self-test passed, ZIP was created, extracted ZIP self-test passed.

## Portable artifact

- Package: `JapaneseStrokeMouseWriter-v2.4.0-win-x64-portable.zip`
- SHA-256: `622160cbb5a572c32e22350abcf885b010254d9695234948fe29c381bbad3e15`

## Notes

- V2.4.0 is unsigned because the SignPath Foundation application was not approved at this time.
- The previous V2.4.0 special-symbol development folder was discarded and replaced by this kaomoji release folder.
