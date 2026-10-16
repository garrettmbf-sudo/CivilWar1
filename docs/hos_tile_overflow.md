# HoS tile sprite overflow & draw order

## Findings (from stock tiles + docs)
- Engine draws one sprite per hex; **transparent alpha is not shown**.
- Stock `Plain.png` opaque region ≈ flat-top hex inset in 2000×2000 (bbox y≈164–1835).
- `Village Union` / `Factory Confederacy` have **mildly taller** opaque bboxes (y≈135–1864) and
  some opaque pixels outside `Plain`’s alpha (~red in `previews/qa_village_overflow.png`).
  So **limited overflow past the terrain hex is used by stock building tiles**, but still
  inside the 2000×2000 canvas and still defined by that tile’s own alpha.
- **Pixels outside a tile’s alpha are never drawn.** True “overflow into neighbor hexes”
  only works if (a) this tile’s alpha covers those pixels, or (b) the art is baked into
  the neighbor tile’s pixels.

## Draw order
- Not documented in repo. Typical hex map engines paint **north→south** (top row first)
  so southern sprites sit on top — which matches “view from south / loom over hex to the north”
  **only if** the southern tile’s sprite alpha extends northward. Unverified for HoS.

## Our approach (unique SV_K_* slices)
- Draw tall objects on the **continuous basemap** with northward (up-screen) height and
  NW light. When sliced with the stock hex mask, crowns/roofs that cross the north edge
  land in the **northern neighbor tile** automatically — seamless overhang without relying
  on undocumented alpha overflow or draw order.
- Do **not** expand alpha beyond the stock mask (keeps tessellation compatible).

## Stock HoS look (user screenshot Agrigento / Jul 1943)
- Per-hex **stamped** tree clusters centered in hexes — avoid this.
- Unit counters = large opaque white circles (~70–80% of hex width) with icons/stats.
- Terrain under counters is mostly hidden → keep hex **centers relatively clear**; put
  unique landmarks toward edges / north; continuous basemap detail can still show in rims.
- Stock map is flat top-down; our continuous DEM slices + modest oblique props are intentional
  departure so ridges read raised and features flow across grid lines.
