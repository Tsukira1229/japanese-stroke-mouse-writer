# Special-symbol development workflow

`data/symbol_manifest.json` is the source of truth for the 430 additional centerline symbols. Runtime support groups, cell spans, vertical behavior, public documentation, review batches, and validation are derived from it.

## Prepare a batch

1. Add proposed single-code-point characters to `data/symbol_candidates.csv`.
2. Use one of these statuses: `candidate`, `accepted`, `in_progress`, `verified`, or `deferred`.
3. Select 12–20 related characters. Add mirrored, directional, hollow, and filled family members together.
4. Reject combining marks, ZWJ sequences, keycap sequences, variation-selector sequences, and color emoji that cannot be represented by a practical centerline.
5. Move accepted records into `data/symbol_manifest.json` and give the batch a stable lowercase id such as `kaomoji-eyes-01`.

Manifest records contain the literal symbol, uppercase code point, Unicode name, runtime group, display category, cell span, vertical behavior, drawing style, expected physical pen-down count, SVG path, review status, and batch id.

## Author and review

- Store each source at `data/custom_strokes/<five-digit-lowercase-codepoint>.svg`.
- Keep `viewBox="0 0 109 109"`, absolute path commands, continuous ids, and one physical pen-down per `<path>`.
- Put every disconnected dot or mark in its own path.
- Preserve natural stroke direction. Filled shapes use a recognizable boundary and sparse skeleton or hatching.
- Generate review artifacts without moving the mouse:

```powershell
python .\scripts\generate_symbol_comparisons.py --batch kaomoji-eyes-01
```

The command writes fixed-cell reference, actual `build_layout` path, and overlay cards plus an overview and checklist under `build/symbol-review/<batch>/`.

## Validate and publish

```powershell
python .\scripts\manage_symbol_catalog.py validate
python .\scripts\manage_symbol_catalog.py generate-docs
python -m unittest discover -s tests
git diff --check
```

Mark records `verified` only after the checklist confirms position, length, shape, direction, and all disconnected components. Rebuild the portable package once after the entire batch passes review:

```powershell
& .\scripts\build_portable.ps1 -Python python
```

Do not use `--execute` while producing or reviewing symbol paths.
