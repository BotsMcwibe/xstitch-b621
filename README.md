# Deer chart

A browser tool for **analysing and checking** a digitised cross-stitch chart (420×280 stitches, 64 colours, 16 count Aida). The chart was made from 16 scanned A3 paper sheets.

Pages (served by GitHub Pages; all of them load `data/bundle.json`):
- `index.html`, **Viewer:** scroll to zoom, drag to pan, and hover a cell to see its row, column, symbol number and name, and the confidence. Click a colour in the legend to highlight it. "Colours + symbols" fills each cell with its key colour. Each colour is always named by number and symbol, and highlights use blue and orange outlines (colour-blind friendly). The legend shows the key's stitch count next to the chart's count.
- `review.html`, **Review:** the cells the classifier was least sure about, with the scan crop, the best guess and the second guess. Choices are saved in your browser (localStorage), applied by the viewer, and can be exported or imported as JSON.
- `compare.html`, **Compare:** the cover picture next to a colour redraw of the chart data.

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
