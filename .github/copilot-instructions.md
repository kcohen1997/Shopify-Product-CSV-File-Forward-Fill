## Purpose

This repository is a small, single-purpose Python GUI app that forward-fills Shopify product CSV exports so every variant row inherits product-level metadata.
The goal of these instructions is to help an AI coding agent become immediately productive by documenting the architecture, key files, workflows, and repository-specific conventions.

## Big picture (architecture & data flow)

- Single-file GUI app: `Shopify_Product_Forward_Fill.py` (Tkinter + pandas).
- Data flow: CSV input -> pandas DataFrame -> validation (`is_shopify_csv`) -> column selection -> forward-fill grouped by `Handle` (`groupby('Handle').ffill()`) -> create `Full Title` -> drop empty columns -> fill non-selected columns with `"N/A"` -> save CSV (UTF-8-sig, quoting all).
- Packaging artifacts: `build/` and the spec file `Shopify Product Forward Fill.spec` indicate PyInstaller was used to bundle the app.

## Key files to read first

- `Shopify_Product_Forward_Fill.py` — main application (functions of interest: `is_shopify_csv`, `create_full_title`, `upload_file`, `forward_fill_by_handle`, `save_file`).
- `README.md` — user-facing intent, examples, and expected columns.
- `product_template.csv` / `product_template_result.csv` — sample input/output useful for tests or reproducing flows.

## Project-specific patterns & conventions

- Column preselection logic is encoded in `DEFAULT_FORWARD_FILL_COLS` (set of Shopify-default column names). Update this constant if Shopify changes column names.
- Metafields detection: any column containing the substring `metafield` (case-insensitive) and not all-empty is auto-selected.
- Required columns for a valid Shopify file: `Handle`, `Title`, `Body (HTML)`, `Vendor`, `Image Src` — enforced by `is_shopify_csv`.
- `Full Title` is constructed by `create_full_title()` using `Title` + `Option1/2/3 Value` columns; the function ensures missing Option columns are created as empty strings and reinserts `Full Title` as the second column.
- Forward-fill semantics: only forward-fill on the selected columns and only within a `Handle` group to avoid cross-product leakage.
- Non-selected columns are filled with the literal string `N/A` before saving; completely empty columns are removed.

## Developer workflows (how to run & package)

- Run locally (dev): ensure Python 3.x and pandas are installed (tkinter is part of standard library on many platforms).

  Example (macOS / zsh):

  python3 Shopify_Product_Forward_Fill.py

- Packaging: repository contains `Shopify Product Forward Fill.spec` and a `build/` directory with PyInstaller outputs. To rebuild the bundle use PyInstaller with the spec file:

  pyinstaller "Shopify Product Forward Fill.spec"

  (Be conservative: PyInstaller can change behavior across versions; test the produced bundle on target OS.)

## Integration points & dependencies

- Dependencies: `pandas` (external). `tkinter`, `csv` are stdlib.
- No network APIs, no database; CSV file I/O only. Unit/integration tests are not present — use `product_template.csv` to create test cases.

## Small edits that are safe / common change patterns

- Add or remove default columns by editing `DEFAULT_FORWARD_FILL_COLS`.
- If adding headless or CLI usage, extract the forward-fill logic into a function that accepts a DataFrame and a list of columns (the existing `forward_fill_by_handle` logic is a good starting point).
- If adding automated tests, assert the grouping and forward-fill behavior using `product_template.csv` as fixture and `product_template_result.csv` as expected output.

## Things agents should NOT change without careful review

- Do not change the GUI event loop (`app.mainloop()`) unless converting to a CLI or refactoring into importable functions.
- Do not change the save encoding/quoting behavior lightly — `utf-8-sig` and `csv.QUOTE_ALL` are deliberate for Shopify compatibility.

## Quick examples (copy-pasteable pointers)

- How the app forward-fills columns by handle (in code):

  df[selected_cols] = df.groupby("Handle")[selected_cols].ffill()

- How `Full Title` is built (in code): `df.insert(1, "Full Title", df.apply(combine_row, axis=1))`

## If something is unclear

- Ask the repo owner for sample Shopify exports (if more edge cases are needed).
- Confirm target OS for packaging; the current `build/` artifacts imply cross-platform builds were attempted.

---
Please review and tell me if you'd like the doc to be more prescriptive (for example: required unit tests to add, or a small refactor that exposes the forward-fill logic for CLI usage). 
