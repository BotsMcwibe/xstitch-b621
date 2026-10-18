# Deer chart

A browser tool for **analysing and checking** a digitised cross-stitch chart (420×280 stitches, 64 colours, 16 count Aida). The chart was made from 16 scanned A3 paper sheets.

Pages (served by GitHub Pages; all of them load `data/bundle.json`):
- `index.html`, **Viewer:** scroll to zoom, drag to pan, and hover a cell to see its row, column, symbol number and name, and the confidence. Click a colour in the legend to highlight it. "Colours + symbols" fills each cell with its key colour. Each colour is always named by number and symbol, and highlights use blue and orange outlines (colour-blind friendly). The legend shows the key's stitch count next to the chart's count.
- `review.html`, **Review:** the cells the classifier was least sure about, with the scan crop, the best guess and the second guess. Choices are saved in your browser (localStorage), applied by the viewer, and can be exported or imported as JSON.
- `compare.html`, **Compare:** the cover picture next to a colour redraw of the chart data.

## Viewer (`index.html`)

The top bar holds only the page arrows (‹ N/16 ›), the zoom presets (Fit, 12, 24, 40 px per stitch) and the light/dark toggle. The legend is the floating pill at the bottom right. Page focus is on by default (page 10).

Keyboard: `+`/`−` page (or zoom outside focus), `[` `]` zoom, `0` fit, `P` page focus, `T` theme, `L` legend, `F` fullscreen, `O` low-confidence outline, `G` row/col jump, `?` help, `Esc` clear selection.

**Dev mode** adds a ☰ menu to the top bar with the extra controls (focus toggle, low-confidence outline, row/col jump, fullscreen, help, links to review/compare/symbols). Turn it on with `index.html?dev`, `?dev=1` or `#dev`; it is remembered in localStorage until you open `index.html?dev=0`.

## Editing the symbols

`symbols.html` has an editor section:

1. **Download all SVGs** gives `chart-symbols.zip`: `symbols/01.svg` … `64.svg` (viewBox `0 0 100 100`, plain paths, no transforms) plus `README.txt` with the canvas, safe area and stroke guidelines.
2. Edit them in any vector editor, then drop the edited `.svg` files or a `.zip` on the upload zone. Files are matched by name (`01.svg`, `1.svg`, `01-anything.svg`), sanitised (scripts, event handlers and external references removed) and rescaled to the expected viewBox, with a warning if it differed.
3. Each upload shows current vs uploaded, the scan crops with an overlay, the match score against the scan average (current → new, Δ) and a 12/24 px chart patch. Uploads stay in this browser until **Discard uploads**. Open `index.html?localsymbols` to preview them in the viewer.
4. **Download my set** zips the current set with your uploads applied. Import it with `python3 scripts/import_symbols.py my-chart-symbols.zip`, which validates the files, copies them into `symbols/`, rebuilds `sprite.svg` and `symbols.json`, and prints the scores.

## Licence
- The code (HTML/JS/CSS and `scripts/`) is MIT licensed; see `LICENSE`.
- The chart design, symbol key and cover picture belong to the original pattern publisher. The derived data in `data/` is shared only as a personal stitching aid and is **not** covered by the MIT licence. No full-page scans are included.

## Validation results
- Stitch counts match the printed key for 61 of 64 symbols. The total difference is 34 stitches: #34 −15, #39 +17, #58 −2. Every "m" (#39) cell matches its template very strongly, and none looks like #34 or #58, so this is probably a mismatch between the printed key and the chart rather than a reading error. Please check it on paper.
- 700 cells were scanned on both halves of a sheet: all agree. One half-sheet was rescanned: all 3,850 cells agree.
- 476 cells are flagged low confidence, including 280 cells only partly visible at a scan edge.
- Thread codes are not transcribed yet, and the swatch colours are approximate (taken from a photo).

## Pipeline (`scripts/`)
Run from a private working folder that holds `raw/*.bmp`. Install with `pip install -r requirements.txt`.
1. `extract.py`: turns the right halves upright, straightens the scans and finds the grid lines (bold every 10).
2. `cells.py`: places every cell using the printed numbers (4×4 pages, 112/84 columns × 70 rows) and records half-cells cut at a scan edge, plus overlaps.
3. `feat.py`, `classify.py`: group cells by shape for a first labelling. `run_tm.py` and `tmatch.py` do template matching with shift search.
4. `partial2.py` and `apply_partial.py`: for cells cut at a scan edge, rebuild the cell from both scan pieces (each aligned to its own grid line), mask the scanner's white margin, and match templates only on the visible part.
5. `outputs.py`, `validate.py`, `diffs.py`: grid CSV, chart PNGs, count comparison, review sheets, seam and overlap checks.
6. `make_bundle.py`: writes `data/bundle.json`.
`mkkey.py` and `keysw.py` transcribe the key swatches. Set `KEY_PHOTOS_DIR`.
