# 1862 OOB polish — portraits, command integrity, state flags

This document supplements the recovered historical OOB. It does **not** change any audited portrait filename, claim an image has been imported, or claim Hex of Steel supports a particular counter-overlay feature.

## Portrait acquisition queue

The recovered `commanders_1862.csv` contains **16 MISSING portrait entries** (ten Confederate, six Union), compared with the 51-officer master manifest, which is a broader inventory. Preserve the master manifest as the authority for filenames and actual repository paths. A source link is not a delivered portrait.

### Primary-source candidates located

| Commander | Approved filename | Historical image | Evidence | Action |
|---|---|---|---|---|
| George H. Steuart | `mdl_CSA_GHSteuart.png` | [National Park Service portrait](https://www.nps.gov/articles/000/george-h-steuart.htm) | NPS identifies a Confederate-uniform image and describes his June 8 Cross Keys wound | Obtain original image and check provenance/usage, crop into existing style |
| Bradley T. Johnson | `mdl_CSA_BTJohnson.png` | [Library of Congress identified carte de visite](https://www.loc.gov/item/2022630852/) | Identified photograph, dated Civil War period | Download original from LoC and check rights advisory |
| Henry Bohlen | `mdl_USA_HBohlen.png` | [Library of Congress glass negative](https://www.loc.gov/item/2018667600/) | Named photograph, 1860–62 | Download original from LoC and check rights advisory |

These are source candidates, **not yet converted PNGs**. Verify image subject against catalog metadata; do not use arbitrary web image search matches.

### Remaining missing portraits to research

| Faction | Commander | Approved filename |
|---|---|---|
| CSA | Jesse S. Burks | `mdl_CSA_JSBurks.png` |
| CSA | John A. Campbell | `mdl_CSA_JACampbell.png` |
| CSA | John M. Patton Jr. | `mdl_CSA_JMPatton.png` |
| CSA | Samuel V. Fulkerson | `mdl_CSA_SVFulkerson.png` |
| CSA | Zephaniah T. Conner | `mdl_CSA_ZTConner.png` |
| CSA | William C. Scott | `mdl_CSA_WCScott.png` |
| CSA | Thomas S. Flournoy | `mdl_CSA_TSFlournoy.png` |
| CSA | Stapleton Crutchfield | `mdl_CSA_SCrutchfield.png` |
| USA | Thornton F. Brodhead | `mdl_USA_TFBrodhead.png` |
| USA | Dudley Donnelly | `mdl_USA_DDonnelly.png` |
| USA | John A. Koltes | `mdl_USA_JAKoltes.png` |
| USA | Gustave P. Cluseret | `mdl_USA_GPCluseret.png` |
| USA | Orris S. Ferry | `mdl_USA_OSFerry.png` |

For each new portrait record catalog URL, image rights, confidence of identification, processing date, original image provenance, and target filename. If no authentic image can be found, mark **NO_VERIFIED_PORTRAIT** and use a clearly identified generic placeholder, never an invented likeness described as authentic.

## Small state flags on unit counters

The recovered `regiments_1862.csv` already has a `state` column. Keep this as the source of truth; do **not** derive state from the commanding officer's birthplace, brigade name, or army affiliation.

Suggested future rendering: a small state-origin flag in a consistent corner of each brigade counter, beneath or beside the unit designation; retain the main USA/CSA identity in the principal counter field. Avoid flags obscuring strength, status or selection indicators.

A brigade can include regiments from **more than one state**. The brigade's display flag must be computed from its **date-specific active regiment assignments**:
- all constituent regiments share one state: display that state's historical flag;
- mixed-state brigade: display a neutral `MIXED` marker or multiple small state indicators if legible;
- unknown/detached composition: `UNKNOWN`, not an invented state;
- independent cavalry and artillery: follow their actual unit origin, not the nearest brigade.
- distinguish historical flags (1862) from modern state flags, and track flag-art sources/licensing.

Implement flag overlays only after confirming how Hex of Steel renders modded counter sprites. If no overlay is supported, generate composited original counter art offline and preserve unmodified originals. This is a cosmetic feature, not a command or combat modifier.

## Validation polish required before game generation

1. Add active-parent validation: for every active brigade on date D, all non-root parent HQs must exist and be active on D.
2. Resolve date-specific commander succession, including killed/wounded/acting status, without respawning units.
3. Validate detachment manpower partitions, not just absence of overlapping parent IDs.
4. Reconcile formation-count terminology (all formations versus brigade counters versus artillery records).
5. Add date-specific state-origin tests for homogeneous and mixed-state brigades.
6. Add exact-path existence tests for all portrait entries marked PRESENT, using the audited canonical manifest.
7. Do not claim save compatibility or command-radius integration until a native Hex of Steel in-game test passes.

## Acceptance

This polish pass is a **research and implementation specification** only. No portraits or flags are claimed installed. The recovered OOB CSVs and existing audited artwork are unchanged.
