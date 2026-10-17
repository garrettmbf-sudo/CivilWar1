# Campaign start date, start-date positions, and strengths

Status: **decided.** On 2026-10-17 the user chose **1862-03-22 at dawn** as the campaign start date. Code is not changed in this PR: `OPENING_DATE` in `src/oob.py` is still `1862-03-23` and formation `active_from` dates are unchanged; the code change belongs to Quartermaster.
`OPENING_DATE` in `src/oob.py` is still `1862-03-23`, and formation `active_from` dates are as before.

## Sources and how pages were checked

| id | source | how it was read |
|---|---|---|
| SRC100 (new) | OR Ser. I **Vol. 5** (to Mar 17, 1862) | archive.org `warofrebellion05unit` djvu text, page = running head. Tables at **p.732 and p.1086 were checked against the page images** |
| SRC009 | OR Ser. I **Vol. 12 Pt. 1** | archive.org `warofrebellion121unit` djvu text, page = running head (as in PR #12) |
| SRC010 | OR Ser. I **Vol. 12 Pt. 3** | archive.org `warofrebellion123unit` djvu text, page = running head |
| SRC101 (new) | Vol. 12 Pt. 3 page **images** | pp.37 and 120 return tables checked digit by digit |

**Note on the reading surface:** the brief named Cornell Making of America, eHistory OSU or HathiTrust. From this box, eHistory and HathiTrust return a Cloudflare challenge, and I could not reach Cornell's page viewer. So every page here comes from the archive.org scan of the same 1880s GPO edition, the scan PR #12 already used. I took no numbers or pages from secondary works. **No scholarly estimate (Cozzens 2008, Tanner 1976, Robertson, Krick) was checked.** Wherever the OR has no figure, the cell says *no return found, scholarly estimate p. UNVERIFIED, PROVISIONAL*. I did not fill in a number.

## 1. Candidate start dates

| # | date | event | OR evidence | what it means for the game |
|---|---|---|---|---|
| A | 1862-02-26/28 | Banks's division crosses the Potomac at Harpers Ferry and occupies Charlestown | Vol. 5 p.728-730 (McClellan at Sandy Hook Feb 27; Stanton Feb 28: "the troops that have crossed the Potomac"; McClellan proposes to occupy Charlestown and Bunker Hill). Feb return: Banks's division at Charlestown, Sedgwick at Harpers Ferry, Lander at Paw Paw (p.732) | Falls before the project window (Mar to Jun). Jackson still holds Winchester. Needs Sedgwick's division, which left early, and a long static opening with no OR position for each CS unit. Big, early, and mostly winter-quarters play |
| B | 1862-03-11/12 | Jackson evacuates Winchester | Vol. 5 p.59: enemy left Winchester 5 p.m. on the 11th; Hamilton's brigade entered the morning of the 12th; Banks's corps concentrated near Winchester on the 13th; Shields at Strasburg on the 19th | Both Union divisions (Shields and Williams) are in the Valley, about 20,000 men (cf. Vol. 5 p.61). The CS player starts with a retreat. Kernstown becomes optional. Williams's eastward departure (Mar 20 to 23) would have to be scripted as a forced exit |
| **C** | **1862-03-22 (dawn)** | Shields has pulled back to Winchester; Ashby reports Strasburg evacuated (Fri. evening Mar 21); Williams marches east | Jackson's report, Vol. 12/1 p.380-381 (positions of every CS brigade and battery on Mar 21 evening); Williams's record of events p.378; Ashby p.385; Mountain Dept dispositions Mar 22, 12/3 p.9-10; Johnson's statement Mar 18, 12/3 p.828-829 | **Chosen (user decision, 2026-10-17).** Every Valley District brigade has an OR-stated position. Union positions are dated to the day. Kernstown (Mar 23) comes out of play instead of being the opening setup. It is one day before the existing `OPENING_DATE`, so almost all data rows carry over |
| D | 1862-03-23 | Battle of Kernstown | 12/1 p.335-410 (returns p.346, p.384; strengths p.342, p.383) | The current repo choice. It opens in the middle of a battle with forces already committed, so it suits a separate Kernstown scenario better than the campaign opening. The Kernstown files and branches are not touched by this PR |

**Decision (user, 2026-10-17): 1862-03-22, dawn.** The reasons it was recommended: (1) it is the earliest date where the OR gives the position of every Confederate brigade and battery, from Jackson p.380-381. (2) The Union positions are dated the same day: Williams's division p.378, the Mountain Dept statement of Mar 22 at p.9-10, and Johnson's Mar 18 statement. (3) Kernstown happens in play rather than being imposed. (4) It needs only a one-day shift of `OPENING_DATE` and of the `active_from` of formations that now start 03-23.

Option B was not chosen. Had it been, the same tables would apply, but Williams's division sits at Winchester and Jackson at Strasburg/Woodstock. Those mid-March positions are not page-cited here.

**What implementing the decision requires (code change owned by Quartermaster, not done in this PR):** set `OPENING_DATE = date(1862, 3, 22)` and the validator's first day `first = date(1862, 3, 22)`. Change `active_from` 1862-03-23 to 1862-03-22 for the rows that start 03-23 in formations, assignments, brigade_commands, artillery `attached_to_from` and commanders `first_mentioned`. Then re-run `python src/oob.py` and `pytest`.

## 2. Positions on 1862-03-22 (dawn) and map places

Map places use the project names: Mount Jackson/Rude's Hill, Woodstock, Strasburg, Winchester, Front Royal, Staunton, McDowell/Monterey area, Franklin, Romney, Harpers Ferry, Manassas/Warrenton, plus off-map edges.

### Confederate

| formation (repo id) | units (OR names) | position, Mar 21 evening to Mar 22 dawn | map place | cite |
|---|---|---|---|---|
| Valley District HQ, Jackson (FRM_CS_VALLEY) | | with the main body near Mount Jackson; marched at dawn Mar 22 | Mount Jackson | 12/1 p.380-381 |
| Garnett's (Stonewall) Bde (FRM_CS_STONEWALL) | 2nd, 4th, 5th, 27th, 33rd VA | "near 2 miles below Mount Jackson" | Mount Jackson (N side) | p.380-381 |
| batteries with Garnett (FRM_CS_ARTY_JACKSON) | McLaughlin's (Rockbridge), Carpenter's, Waters' (West Augusta) | with Garnett | Mount Jackson | p.380-381 |
| Burks's Bde (FRM_CS_BURKS) | 21st, 42nd, 48th VA, 1st VA Bn (PACS) | "near 2 miles above Mount Jackson" (48th VA was rear guard Mar 23) | Rude's Hill / Mount Jackson (S side) | p.381 |
| battery with Burks | Marye's battery (repo ART_HAMPDEN; identification UNVERIFIED) | with Burks | Rude's Hill | p.381 |
| Fulkerson's Bde (FRM_CS_FULKERSON) | 23rd, 37th VA | "near Woodstock" | Woodstock | p.380 |
| battery with Fulkerson | Shumaker's battery (repo ART_DANVILLE) | with Fulkerson | Woodstock | p.380 |
| Ashby's cavalry (FRM_CS_ASHBY) | 7th VA Cav (Ashby), incl. Funsten's companies | "already in front": followed the Federal retreat from Strasburg on Saturday evening to within a mile of Winchester | Strasburg to Kernstown | p.380, p.385 |
| Chew's battery (ART_CHEWS) | 3 guns | with Ashby | Strasburg to Kernstown | p.380, p.385 |
| Army of the Northwest, E. Johnson (FRM_CS_NW; repo brigades CONNER, SCOTTBRA) | 12th GA, 25th, 31st, 44th, 52nd, 58th VA, Hansbrough's Bn; Rice's, Miller's, Raine's batteries (4 guns each); Churchville, Rockbridge, Charlotte, Pittsylvania cav, Alexander's TN cav | Mar 18: 1,834 men + 10 guns on top of Allegheny; 500 + 2 guns at Huntersville; 350 at Crab Bottom; 40 at Franklin; 60 at Monterey | McDowell/Monterey area, west edge (Allegheny); Franklin detachment | 12/3 p.828-829 |
| Ewell's division (FRM_CS_EWELLDIV: Elzey, Trimble, Taylor bdes) | | east of the Blue Ridge on the Rappahannock line. Letter of Apr 16 is headed "Rappahannock"; Ewell later "left the vicinity of Gordonsville". **Mar 22 camp not found in OR** | off-map east: Brandy Station / Rappahannock Station; Gordonsville | 12/3 p.850-851; 12/1 p.470 |

When Ewell came over the Blue Ridge: he arrived west of it on **Apr 30** via Swift Run Gap into Elk Run Valley (12/1 p.470). He joined Jackson near **New Market, about May 20-21** (12/1 p.701). See arrival_schedule.md.

### Union

| formation | units | position Mar 22 | map place | cite |
|---|---|---|---|---|
| Fifth Corps / Banks (FRM_US_BANKSDEPT) | corps cavalry: 1st ME, 1st VT, 1st MI, 1st RI, 5th & 8th NY, Keys's PA Bn, 18 cos MD, 1 sqdn VA; unattached 28th PA, 4th PHB | posts at Martinsburg, Harpers Ferry, Berryville, Charlestown (ordered forward Mar 23). Posts for each cavalry regiment not itemized | Harpers Ferry / Charlestown | 12/1 p.335; Vol. 5 p.21 |
| Shields's division (FRM_US_SHIELDSDIV_K) | Kimball (14th IN, 4th, 8th, 67th OH, 7th (W.)Va., 84th PA); Sullivan (5th, 62nd, 66th OH, 13th IN, 39th IL); Tyler (7th, 29th OH, 7th IN, 1st (W.)Va., 110th PA); batteries Clark E/4th US, Jenks A/1st (W.)Va., Davey B/1st (W.)Va., Huntington's 1st OH, Robinson L/1st OH; Brodhead's cavalry | back at **Winchester** after withdrawing from Strasburg; skirmish Mar 22 (Shields wounded) | Winchester | Vol. 5 p.22 (organization; brigade names are blank in the OCR and matched to the repo's p.346 roster), p.59; 12/1 p.335, 342 |
| Williams's division (FRM_US_WILLIAMSDIV; repo DONNELLY, GORDON) | Vol. 5 p.22 lists Abercrombie's brigade (12th MA, 16th IN, 1st PHB MD, Zouaves d'Afrique; OCR also puts 2nd MA here), a brigade of 9th NYSM, 29th PA, 27th IN, 3rd WI, and a brigade of 28th NY, 5th CT, 46th PA, 1st MD, 12th IN, 13th MA. Batteries: Best F/4th US, Hampton MD, Thompson MD, Matthews F PA, Cothran M/1st NY, Knap PA, McMahon NY | ordered Mar 20 to Centreville. **Mar 22:** First Bde Winchester to Castleman's Ferry, then countermarched to Berryville; Second Bde at Berryville (since Mar 21) to Snickersville; Third Bde Winchester to Castleman's Ferry | Winchester / Berryville / Snicker's Gap (east edge) | 12/1 p.378 |
| Kenly, 1st MD (FRM_US_KENLY) | 1st MD | with Williams's division (p.22 brigade); the Front Royal garrison came later (repo models it from 05-20) | as Williams | Vol. 5 p.22 |
| Geary (FRM_US_GEARY) | 28th PA + attachments | east of the Blue Ridge: Upperville from Mar 15, Piedmont area Mar 19, detachment at Leesburg | off-map east, Manassas Gap RR | Vol. 5 p.514 |
| Mountain Dept (FRM_US_FREMONTDEPT) | HQ Wheeling. The Mar 22 statement predates Frémont's arrival; his assumption date is not page-cited here | | off-map NW | 12/3 p.9 |
| Schenck, District of Cumberland (FRM_US_SCHENCK_MCD) | PHB, 5th (W.)Va., 82nd OH, 1 co. cav (Mar 22). Mar 28: Moorefield 82nd OH + 1st CT Cav cos + section (1,321); Romney 4 cos PHB + 12 cos Va. inf.; Cumberland PHB 573 | HQ Cumberland, Md.; Romney; Moorefield | Romney (NW edge) | 12/3 p.9, p.25 |
| Milroy, Cheat Mountain District (FRM_US_MILROY_MCD) | 2nd (W.)Va., 75th OH, Rigby's IN battery at Cheat Mtn Summit; 3rd (W.)Va. at Huttonsville/Elkwater; 25th, 32nd OH at Beverly; 73rd OH at Weston; detachments at Buckhannon and Sutton | Cheat Mountain to Beverly | off-map west (toward Monterey) | 12/3 p.9-10 |
| Blenker's division (FRM_US_BLENKERDIV) | Stahel, Koltes, Bohlen | Army of the Potomac. Feb station Hunter's Chapel; Apr 1 "push Blenker's division from Warrenton upon Strasburg". **Mar 22 camp not found** | off-map east: Manassas / Warrenton | Vol. 5 p.732, p.61 |
| McDowell (FRM_US_MCDOWELLDEPT) | First Corps divisions | Feb station Arlington. The Dept of the Rappahannock did not exist yet (repo models it from 04-01; creation page still UNVERIFIED) | off-map east | Vol. 5 p.732 |

## 3. Strengths ("exact" means the return figure, with its type)

| formation | date | figure | type | cite | note |
|---|---|---|---|---|---|
| Valley District | 1862-02-28 | **5,394** effective total present; PFD inf 362 off./3,935 men, cav 41/560, art 14/355; aggregate present 6,404; aggregate present & absent 13,759 | departmental return | Vol. 5 p.1086 (image checked) | nearest return before the start |
| Valley District | 1862-03-23 | **3,087** infantry present, 2,742 engaged; 27 guns (18 engaged); 290 cavalry present | commander's report | 12/1 p.383 | many stragglers after the 35-40 mile march |
| 2nd VA / 4th VA / 33rd VA / 23rd VA | 1862-03-23 | ≤320 r&f / 203 r&f / 275 / 17 off. + 160 r&f fit for duty | engaged / engaged / engaged / morning report | 12/1 p.389 / p.391 / p.396 / p.410 | |
| Ashby's cavalry | 1862-03-23 | 290 present | report | 12/1 p.383 | Feb 28 PFD cavalry 601 (Valley District, p.1086) |
| Army of the Northwest | 1862-03-18 | **2,425** PFD (175 + 2,250); aggregate present 2,784; aggregate present & absent 3,963 | statement in lieu of return | 12/3 p.828-829 | |
| Ewell's division | 1862-04-16 | "something over 8,000", 14 guns, plus cavalry "over 500 effective" | commander's letter (not a return) | 12/3 p.851 | PROVISIONAL for March. No March return found; scholarly estimate p. UNVERIFIED |
| Banks's division (became Williams's) | 1862-02 | 565 off./**13,671** PFD; aggregate present & absent 16,801; 32 guns | AoP monthly return | Vol. 5 p.732 (image checked) | pre-reorganization; PROVISIONAL for Mar 22. One brigade left east Mar 23 |
| Lander's division (became Shields's) | 1862-02 | 482 off./**11,387** PFD; aggregate present & absent 15,731; 26 guns | AoP monthly return | Vol. 5 p.732 | pre-reorganization; PROVISIONAL |
| Shields's division | 1862-03-23 | "did not exceed **7,000**": 6,000 inf, 750 cav, 24 guns | commander's report | 12/1 p.342 | **CONFLICT:** "not over 8,000" (p.335), "between 7,000 and 8,000" (p.336); Jackson estimated Federal infantry "over 11,000", over 8,000 engaged (p.383). Repo R002 (NPS ~8,500) is a secondary figure |
| Fifth Corps incl. Shields | 1862-04-01 | 19,687 + 41 guns; plus ~3,652 cavalry and ~2,100 railroad guards | army commander's estimate | Vol. 5 p.61 | |
| Williams's division bdes | 1862-04 | Donnelly 108/2,639 PFD; Gordon 116/2,889; artillery 21/471, 26 guns (Abercrombie row blank) | brigade returns ("incomplete") | 12/3 p.120 (image) | |
| Hatch's cavalry | 1862-04 | 142/2,792 PFD; aggregate present 3,273 | brigade returns | 12/3 p.120 (image) | |
| Geary | Mar 1862 | **no return found** | — | — | scholarly estimate p. UNVERIFIED, PROVISIONAL. Vol. 5 p.61 gives Abercrombie + Geary + cavalry at about 7,780 (aggregate only) |
| Blenker's division | 1862-02 | 411 off./**7,985** PFD; aggregate present & absent 10,455; 18 guns | AoP monthly return | Vol. 5 p.732 | McClellan Apr 1: 10,028 with 24 guns (p.61). **Conflict, both shown** |
| Mountain Dept: Cheat Mountain (Milroy) | 1862-03-22 | inf 5,586, cav 322, art 176 | departmental statement | 12/3 p.9-10 | **CONFLICT** with the March return: PFD 171/3,994, aggregate present 4,887, aggregate present & absent 5,691 (p.37, image) |
| Mountain Dept: Cumberland (Schenck) | 1862-03-22 | inf 2,753 + cav 63 | departmental statement | 12/3 p.9 | March return: PFD 93/2,090, aggregate present 2,506, aggregate present & absent 3,075 (p.37) |
| Mountain Dept (whole) | 1862-03 | aggregate present 21,884 (PFD 751/17,547) | dept return | 12/3 p.37 | includes the Kanawha District, outside the map |

All of these are now rows R100 to R118 in `historical_data/strength_returns_1862.csv`. The start-date positions are `start_position` events E103 to E116 in `reinforcements_1862.csv`.

## 4. Audit of PR #12 (corrections made here)

- **E017**: the Front Royal "11 a.m. May 30" sentence is on **12/1 p.283**, not p.282. Corrected.
- **A008, 48th VA**: Jackson lists it in Burks's brigade as the rear guard that did not reach the field (p.381). That explains why it is missing from the casualty return (p.384). The flag is resolved.
- **ART_HAMPDEN**: Jackson names "Marye's battery" with Burks (p.381). That it is the Hampden Artillery is my identification and is marked UNVERIFIED.
- **ART_DANVILLE**: "Shumaker's battery" with Fulkerson near Woodstock (p.380) was added.
- Williams's division "OPENING GAP" (E020) is refined by brigade-level movements (E110, E117, E118). The formation's `active_from` was not changed, because that would cascade into the assignment and command tables.

## 5. Still provisional or conflicting

- Ewell's Mar 22 camp; Blenker's Mar 22 camp; Sedgwick's departure date in early March; the creation date of the Department of the Rappahannock.
- Brigade numbering of Williams's division. The OCR blanks the brigade names on Vol. 5 p.22. That the "Second Brigade" sent to Manassas was Abercrombie's is an inference.
- Union strengths for Mar 22 rest on February returns (before reorganization) and Shields's own conflicting statements.
- No scholarly estimates checked (Cozzens, Tanner, Robertson, Krick: p. UNVERIFIED).
- The Louisiana Brigade's own arrival day; Ewell's junction date is approximate (May 20-21).
