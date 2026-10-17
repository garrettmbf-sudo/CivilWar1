# Arrival and departure schedule, Feb to Jun 1862

Generated from `historical_data/reinforcements_1862.csv`. Start-date positions (`start_position` rows E103 to E116) are in `campaign_start.md`. Citation tokens follow `historical_data/README.md`: SRC009 = OR 12/1, SRC010 = OR 12/3, SRC100 = OR Vol. 5, SRC007 = repo reference file. **date_certainty:** confirmed = the OR states the date; approximate = the OR brackets it or the repo's modelling date differs; unverified = no OR page found.

Map entry points use the project's place names. *East edge* means a Blue Ridge gap (Snicker's, Ashby's, Manassas Gap/Front Royal, Chester, Swift Run). *NW edge* means Romney/Moorefield. *West edge* means McDowell/Monterey/Franklin.

| date | id | type | unit | what happens | location / edge | certainty | sources |
|---|---|---|---|---|---|---|---|
| 1862-02-27 | E100 | context | FRM_US_BANKSDEPT | Banks' division crosses the Potomac at Harpers Ferry (McClellan directing from Sandy Hook Feb 27); Stanton asks Feb 28 'what do you propose to do with the troops that have crossed the Potomac'; McClellan proposes to occupy Charlestown and Bunker Hill | Harpers Ferry -> Charlestown | confirmed | SRC100 p.728-730 |
| 1862-03-05 | E130 | departure | FRM_US_BANKSDEPT | Sedgwick's division, at Harper's Ferry on the February return, is not part of the Fifth Corps organization of March; it left the Valley in early March. Exact departure date not found in OR | Harpers Ferry -> off-map east | unverified | SRC100 p.732 / SRC100 p.21 |
| 1862-03-12 | E101 | context | FRM_CS_VALLEY | Jackson evacuates Winchester 5 p.m. Mar 11; Hamilton's brigade of Banks' corps enters Winchester morning of Mar 12; Banks' corps concentrated near Winchester Mar 13 | Winchester | confirmed | SRC100 p.59 |
| 1862-03-19 | E102 | context | FRM_US_SHIELDSDIV_K | Shields occupies Strasburg, driving Jackson to Mount Jackson; Mar 20 Williams' (1st) division begins move toward Manassas; Shields falls back to Winchester | Strasburg -> Winchester | confirmed | SRC100 p.59 / SRC009 p.378 |
| 1862-03-23 | E020 | recall | FRM_US_WILLIAMSDIV | Williams' division, en route to Centreville, ordered back to Winchester after Kernstown | Winchester | approximate | SRC009 p.337 / SRC009 p.342 |
| 1862-03-23 | E117 | departure | FRM_US_WILLIAMSDIV | Williams' Second Brigade marches Snickersville -> Aldie Mar 23 and on to Manassas Junction, 'detached from the division' at month end (likely Abercrombie's; Abercrombie at Warrenton Apr 1 - brigade identity is an inference) | Snicker's Gap -> Aldie -> Manassas (east edge) | confirmed | SRC009 p.378 / SRC100 p.59 |
| 1862-03-23 | E118 | arrival | FRM_US_WILLIAMSDIV | Williams' First Brigade marches from Berryville to the Kernstown field (36 miles in 10 hours), pursues to Strasburg Mar 24-25; Third Brigade back from Snickersville to Winchester Mar 24, Middletown Mar 25, Strasburg Mar 26 | Berryville -> Winchester -> Strasburg | confirmed | SRC009 p.378 |
| 1862-03-29 | E119 | arrival | FRM_US_GEARY | Geary marches Aldie (Mar 24) -> Snickersville -> Philomont -> Middleburg (Mar 27) -> White Plains on the Manassas Gap RR (Mar 29) to repair the line toward Strasburg | White Plains (Manassas Gap RR, east edge) | confirmed | SRC100 p.514 / SRC009 p.410-411 |
| 1862-04-01 | E001 | command_change | FRM_CS_STONEWALL | Garnett removed; Winder succeeds | Valley District (near Mount Jackson) | unverified | SRC007 |
| 1862-04-01 | E022 | modelled_entry | FRM_US_MCDOWELLDEPT | Department of the Rappahannock (McDowell) exists as receiving HQ for Shields | Fredericksburg / Manassas | unverified | SRC007 |
| 1862-04-06 | E013 | command_change | CMD_TALIAFERRO | Brig. Gen. W. B. Taliaferro assigned to Valley District (S.O. 98, Dept. of Northern Virginia) | Valley District | confirmed | SRC007 / SRC010 p.844 |
| 1862-04-06 | E120 | departure | FRM_CS_NW | Milroy's advance occupies Fort Alleghany; Johnson retiring toward Shenandoah Mountain | Allegheny -> Shenandoah Mountain (west of Staunton) | confirmed | SRC010 p.52 |
| 1862-04-10 | E121 | arrival | FRM_US_MILROY_MCD | Milroy in possession of Monterey and Crab Bottom; Schenck still at Moorefield; Banks at Edenburg | Monterey | confirmed | SRC010 p.64 |
| 1862-04-16 | E122 | arrival | FRM_US_BLENKERDIV | Ewell reports Blenker 'had crossed the Blue Ridge, apparently to join Banks'; Geary near Rectortown on the Manassas railroad | Blue Ridge gaps (Ashby's/Snicker's) -> Winchester | approximate | SRC010 p.850 |
| 1862-04-19 | E123 | movement | FRM_CS_VALLEY | Jackson, after halting 'more than a fortnight in the vicinity of Mount Jackson', crosses the South Fork Apr 19 to Elk Run Valley near Swift Run Gap | Elk Run Valley (Conrad's Store / Swift Run Gap) | confirmed | SRC009 p.470 |
| 1862-04-21 | E002 | reinforcement | REG_VA10 | 10th Virginia Infantry joins Jackson's command; with Taliaferro's brigade by McDowell (May 8) | Valley District (Elk Run Valley area, UNVERIFIED) | unverified | SRC007 / SRC009 p.472 / SRC009 p.481 |
| 1862-04-30 | E124 | movement | FRM_CS_NW | Banks: 'Johnson is west of Staunton 6 miles; Milroy in his rear'. Fremont hopes to have Blenker at Moorefield by end of week | west of Staunton (Buffalo Gap); Moorefield | confirmed | SRC010 p.118-119 |
| 1862-05-01 | E003 | command_change | FRM_US_SHIELDSDIV_K | Shields' division begins transfer from Banks to McDowell (spring 1862) | Valley (departs Banks for McDowell) | approximate | SRC007 / SRC010 p.159 (Fremont to Cox, May 9: 'Shields' division ordered to General McDowell') |
| 1862-05-07 | E014 | junction | FRM_CS_NW | Edward Johnson's Army of the Northwest joins Jackson's advance west of Staunton; Johnson leads toward McDowell | west of Staunton (near Buffalo Gap) -> McDowell | confirmed | SRC007 / SRC009 p.470-471 |
| 1862-05-08 | E004 | commander_loss | CMD_JOHNSON_E | Edward Johnson wounded at McDowell | McDowell | confirmed | SRC007 / SRC009 p.464 (Union report: Johnson among rebel wounded) |
| 1862-05-08 | E015 | arrival | FRM_US_SCHENCK_MCD | Schenck's brigade reaches Milroy at McDowell 10 a.m. after 34-mile march from Franklin | McDowell | confirmed | SRC007 / SRC009 p.462 |
| 1862-05-08 | E023 | modelled_entry | FRM_US_FREMONTDEPT | Mountain Department (Fremont) enters the database window with the McDowell fight | Wheeling / Franklin | approximate | SRC007 / SRC009 p.22 |
| 1862-05-09 | E016 | arrival | FRM_US_BLENKERDIV | Advance of Blenker's division joins Fremont near Petersburg (whole command by May 11) | Petersburg (W. Va.) | confirmed | SRC009 p.8 |
| 1862-05-12 | E125 | departure | FRM_US_SHIELDSDIV_K | Shields' division leaves New Market (planned May 11, deferred to Monday May 12) via Luray and Front Royal, thence Chester Gap to Warrenton; Banks to reach Strasburg Tuesday May 13 | New Market -> Luray -> Front Royal -> Chester Gap (east edge) | approximate | SRC010 p.160-162 |
| 1862-05-13 | E126 | movement | FRM_US_WILLIAMSDIV | Banks' remaining force (Williams' division) falls back from New Market to Strasburg | New Market -> Strasburg | approximate | SRC010 p.162 |
| 1862-05-20 | E005 | reinforcement | FRM_CS_EWELLDIV | Ewell's Division (Elzey, Taylor, Trimble brigades; Maryland Line; Munford/Flournoy cavalry per repo) unites with Jackson near New Market | near New Market (junction); entered Valley via Swift Run Gap Apr 30 | approximate | SRC007 / SRC009 p.470 (arrived west of Blue Ridge Apr 30) / SRC009 p.701 (junction near New Market) |
| 1862-05-20 | E021 | modelled_entry | FRM_US_HATCH | Banks' cavalry (Hatch), Geary's independent command and Kenly's Front Royal garrison enter the database window for the First Winchester campaign | Strasburg / Front Royal / Manassas Gap RR | unverified | SRC007 / SRC009 p.552 |
| 1862-05-21 | E131 | arrival | FRM_CS_TAYLOR | Ewell's division (incl. Taylor's Louisiana Brigade) marches from Elk Run Valley and joins Jackson near New Market (refines E005; the Louisiana Brigade's own arrival day is not page-cited) | near New Market | approximate | SRC009 p.701 |
| 1862-05-22 | E127 | arrival | FRM_US_SHIELDSDIV_R | Shields at Catlett's night of May 18; 'Major-General Shields' command has arrived' opposite Fredericksburg May 22 | off-map east: Catlett's -> Fredericksburg | confirmed | SRC010 p.202 / SRC010 p.213 |
| 1862-05-23 | E006 | battle_result | FRM_US_KENLY | Front Royal stormed; garrison captured | Front Royal | confirmed | SRC007 / SRC009 p.702 |
| 1862-05-23 | E008 | command_change | FRM_CS_FULKERSON | Taliaferro absent/ill; Col. Fulkerson commanding Third Brigade (Jackson's report: 'the Third Brigade, Colonel Fulkerson commanding'; Fulkerson's report covers operations May 24-25) | Front Royal-Winchester | approximate | SRC007 / SRC009 p.701 / SRC009 p.772 |
| 1862-05-25 | E007 | command_change | FRM_CS_BURKS | Campbell wounded at First Winchester; Patton succeeds | Winchester | confirmed | SRC007 / SRC009 p.764 |
| 1862-05-30 | E017 | arrival | FRM_US_SHIELDSDIV_R | Shields' division returns to the Valley: Kimball's brigade drives Confederates out of Front Royal 11 a.m. May 30 | Front Royal | confirmed | SRC009 p.283 (Kimball's brigade and Shields' division drive enemy out of Front Royal 11 a.m. May 30; PR #12 cited p.282 - sentence is on p.283) |
| 1862-05-31 | E128 | arrival | FRM_US_MCDOWELLDEPT | Ord's division (McDowell) gets within a few miles of Front Royal night of May 31; McDowell reaches Front Royal that night; railroad found destroyed beyond Rectortown | Front Royal (via Manassas Gap RR, east edge) | confirmed | SRC009 p.283 |
| 1862-06-01 | E019 | reorganization | FRM_US_MILROY_CK | Fremont's command re-enters the Valley (Strasburg area) for the pursuit; Cross Keys organization | Strasburg -> Cross Keys | approximate | SRC007 / SRC009 p.14 / SRC009 p.664-665 |
| 1862-06-01 | E129 | movement | FRM_US_SHIELDSDIV_R | Shields moves up the Luray (Page) valley to intercept Jackson; Bayard's cavalry, 8 guns and a rifle battalion pushed to Strasburg | Front Royal -> Luray; Front Royal -> Strasburg | confirmed | SRC009 p.283 |
| 1862-06-02 | E018 | arrival | FRM_US_BAYARD | Bayard's cavalry (sent by McDowell) joins Fremont's pursuit passing Strasburg | Strasburg | confirmed | SRC009 p.14 |
| 1862-06-06 | E009 | commander_loss | FRM_CS_ASHBY | Turner Ashby killed near Harrisonburg | near Harrisonburg | confirmed | SRC007 / SRC009 p.712 |
| 1862-06-08 | E010 | commander_loss | FRM_CS_ELZEY | Elzey wounded at Cross Keys | Cross Keys | confirmed | SRC007 / SRC009 p.714 / SRC009 p.792 |
| 1862-06-08 | E011 | commander_loss | FRM_CS_STEUART | Steuart wounded at Cross Keys | Cross Keys | confirmed | SRC007 / SRC009 p.714 |
| 1862-06-08 | E024 | command_change | FRM_CS_FULKERSON | Taliaferro commanding his brigade again at Port Republic | Port Republic | approximate | SRC009 p.713 |
| 1862-06-09 | E012 | reorganization | FRM_CS_STEUART | Post-Cross Keys/Port Republic redistribution within Ewell's command | Port Republic | unverified | SRC007 / SRC003 |

## Units not present at the recommended start (1862-03-22) and how they enter

| unit | enters / leaves | when | where | certainty |
|---|---|---|---|---|
| Ewell's division (Elzey, Trimble, Taylor, Maryland Line, cavalry, artillery) | enters west of the Blue Ridge | Apr 30; junction with Jackson ~May 20-21 | Swift Run Gap / Elk Run Valley, then New Market | confirmed / approximate (E005, E131) |
| Johnson's Army of the Northwest | on the west edge at start; leaves Allegheny Apr 6; west of Staunton Apr 30; joins Jackson May 7 | | Allegheny, Shenandoah Mtn, Buffalo Gap, McDowell | confirmed (E120, E124, E014) |
| 10th VA | joins Taliaferro | by May 8 (4/21 unverified) | Valley District | unverified (E002) |
| Williams's division, 2nd bde | **leaves** | Mar 23 | Snicker's Gap, Aldie, Manassas | confirmed (E117) |
| Williams's 1st & 3rd bdes | turn back | Mar 23-26 | Berryville, Winchester, Strasburg | confirmed (E118) |
| Sedgwick's division | **left** before the start | early Mar | Harpers Ferry to east | unverified (E130) |
| Geary | east edge, then the Manassas Gap RR | White Plains Mar 29; Rectortown area Apr 16 | Manassas Gap RR | confirmed / approximate (E119, E122) |
| Blenker's division | crosses the Blue Ridge ~Apr 16; joins Frémont May 9-11 | | northern gaps, Winchester, Moorefield, Petersburg | approximate / confirmed (E122, E124, E016) |
| Milroy | Fort Allegheny Apr 6; Monterey Apr 10; McDowell May 8 | | west edge | confirmed (E120, E121, E015) |
| Schenck | Moorefield Apr 10; McDowell May 8 | | NW edge to west | confirmed (E121, E015) |
| Shields's division | **leaves** New Market May 12; Fredericksburg May 22; **returns** Front Royal May 30; Luray Jun 1 | | Front Royal / Chester Gap | approximate / confirmed (E125, E127, E017, E129) |
| Ord's division (McDowell) | arrives | May 31 | Front Royal via the Manassas Gap RR | confirmed (E128) |
| Bayard | arrives | Jun 1-2 | Front Royal to Strasburg | confirmed (E129, E018) |
| Frémont's main body | enters the Valley | ~Jun 1 | Strasburg | approximate (E019) |

Departures of Union units sent east after Front Royal and Winchester (e.g. McDowell's columns withdrawn after Port Republic) are outside the rows researched here, apart from McDowell's Jun 4 proposal (12/1 p.284, not yet a row).
