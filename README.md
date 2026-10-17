# xstitch-b621

A browser viewer for the cross-stitch chart **Luca-S B621** (420×280 stitches, 64 colours, 16 count Aida), turned from 16 scanned A3 paper sheets into one digital chart. Also includes the Python pipeline that did the conversion.

Live site (GitHub Pages): `index.html` (viewer), `review.html` (check the cells the classifier was unsure about), `compare.html` (cover picture vs. redraw).

## Licence and credits
- The **code** (HTML/JS/CSS and `scripts/`) is released under the MIT licence; see `LICENSE`.
- The **chart design, symbol key and cover picture belong to Luca-S** (© Luca-S, pattern B621). The derived data in `data/` (symbol grid, key transcription, small cell crops, cover crop) is published here only as a personal stitching aid. It is **not** covered by the MIT licence. Please buy the kit from Luca-S. No full-page scans are included.

## Using the site
- The published chart in `data/bundle.json` loads by default.
- **Viewer:** scroll to zoom, drag to pan, and hover a cell to see its row, column, symbol number and name. Click a colour in the legend to highlight it. "Colours + symbols" draws each cell in its key colour with the symbol on top. Every colour is always named by number and symbol, so you never need to tell colours apart by eye. Highlights use blue and orange outlines.
- **Review:** 621 low-confidence cells. Pick the right symbol for each one. Your choices are saved in your browser (IndexedDB), the viewer uses them, and you can export them as JSON.
- **Other charts:** "Open chart bundle…" (or drag and drop) loads any bundle `.zip` or `.json`. The last one you opened is remembered, and "Back to default chart" returns to the published one. If `data-private/bundle.json` exists (it is git-ignored), it loads first. `demo/bundle.json` is a small made-up 60×40 example.

## Accuracy checks (from the conversion)
- Stitch counts match the printed key for 58 of 64 symbols. The total difference is 40 stitches, mostly #34 (−15) and #39 (+17).
- 700 cells were scanned twice where page halves overlap: all agree. The page 1 right half was rescanned: all 3,850 cells agree.
- Thread codes are not in the key photos yet, and the swatch colours are approximate (taken from a phone photo).

## Pipeline (`scripts/`)
Run from a private working folder that holds `raw/*.bmp`. Install with `pip install -r requirements.txt`.
1. `extract.py`: turns the right halves upright, straightens the scans and finds the grid lines (bold every 10).
2. `cells.py`: places every cell using the printed numbers and the page layout (4×4 pages, 112/84 columns × 70 rows), joins half-cells cut at the scan edge, and records overlaps.
3. `feat.py`, `classify.py`: group the cells by shape (k-means) into a first labelling. `run_tm.py` and `tmatch.py` then do template matching with shift search. `partial.py` handles cells cut at a scan edge.
4. `outputs.py`, `validate.py`, `diffs.py`: grid CSV, chart PNGs, count comparison, review sheets, seam and overlap checks.
5. `make_bundle.py`: writes a bundle (`real` or `demo`).
`mkkey.py` and `keysw.py` transcribe the key swatches. Set `KEY_PHOTOS_DIR`.

### Bundle format
One JSON file (optionally zipped): `{format:"xstitch-bundle", version:1, meta, key:[{nr,symbol,count,hex,code}], glyphs:{nr:dataURL}, grid:{rows,cols,nr[],conf[],low[]}, review:[{row,col,guess,second,conf,crop}], cover?, reference?[]}`. See `scripts/make_bundle.py`.
