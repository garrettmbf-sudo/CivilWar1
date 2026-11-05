# Wishlist from a Civil War scenario maker

Hello, and thank you for *Must Attack!* and the Wargame Maker. We made a First Kernstown (1862) scenario with the Wargame Maker export format and have played it five times (v3.6 and v3.7 are not yet played). The engine works well for this. The editor's help text now answers many of our earlier questions: replacements, the retreat and ZOC options, the standby fields (containment, main body %, opposing group), the fact that held units still fire, the list of AI personalities, elite and sudden-death units, and the activation cap. Thank you. This list keeps only what is still open.

Each item has three parts:
- **Want:** what we would like
- **Why:** why it matters for Civil War battles
- **Smallest version:** where we can, the smallest change that would be enough, written in the style of the current JSON

The field names are only suggestions.

## Must-have

**1. Retreat into enemy ZOC as a scenario option, or a replacement for a blocked retreat**
- **Want:** let the scenario choose whether a retreating unit may enter an enemy ZOC hex, perhaps at a cost. Or let replacements also cover a unit lost because it had no retreat path.
- **Why:** Most of our losses are units hemmed in, not units beaten by the die. Replacements, as the help describes them, do not apply to those losses. Civil War brigades usually fell back battered, not wiped out. Saves carry `ZocToZocAllowed`, but scenario rules have no field for it, and we cannot tell whether the editor's "Exit from ZOC" also covers retreats.
- **Smallest version:** `rules.retreat_into_zoc: "forbid" | "allow" | "allow_with_loss"`, where `allow_with_loss` halves the unit as a replacement does.

**2. A short list of JSON keys and values for the editor's fields**
- **Want:** a table that maps each editor field to its JSON key and values.
- **Why:** We build scenarios with a script, and we match fields to keys by reading stock files. Some are still guesses:
  - the doctrine word for Auto, Incompetent, Delay and Maneuver (we have seen `ber`, `off`, `def`, `ultra`, `std`, `sei`, `brk`, `line` and `dyn`);
  - whether `enemyGroup` n means the opposing side's n-th group;
  - the key for the per-side counter coaster;
  - the key for the cap on exit points;
  - whether `retreat_control` 1 is Attacker and 2 Automatic;
  - whether negative `pp` values are allowed for minus CP.
- **Smallest version:** one help line per field naming its key.

**3. Mountain terrain and retreats**
- **Want:** document whether a retreating unit may enter a mountain hex, or let the scenario choose.
- **Why:** We replayed three playtests. Of 33 retreats, none ended in a mountain hex. Nine units were destroyed because mountain was the only open hex behind them, even though they moved onto mountain normally. We had used mountain (at 2 MP) for a gentle ridge, and it quietly turned the ridge into a trap. We now use rough.
- **Smallest version:** one help line ("units cannot retreat into mountain"), or a terrain flag such as `"noRetreatInto": true`.

**4. Replacements keep the parent unit's name**
- **Want:** a replacement takes its parent's name, for example "Marye Hampden (remnant)".
- **Why:** Our first replacement was called "Replacements ①". It kept Marye's counter art, but the log and the unit list lose who it was. Civil War players follow particular regiments.
- **Smallest version:** name the remnant "<parent name> ①", or add a scenario option for the suffix.

**5. Fortress terrain and retreats**
- **Want:** an option for whether a defender in a fortress hex may retreat.
- **Why:** In our log, a DR and two ARs became "C" (no effect) when the fortress hex was involved. That is right for a fort, but for a stone wall or a sunken lane it means the only bad result is destruction. We used mountain terrain for our wall instead.
- **Smallest version:** a terrain flag such as `"holdsInPlace": true` on fortress, set to false on others. Or just document the current rule.

**6. Containment: per unit or per group?**
- **Want:** one line on whether containment adds up the enemy strength around each unit separately or around the group as a whole.
- **Why:** With per-unit counting, a group whose units stand far apart wakes as soon as one of them has no enemy nearby. We now give containment only to groups whose units share a hex.

## High value

**7. Unit facing, with flank and rear attacks**
- **Want:** counters have a facing. An attack from the flank or rear gets an odds shift, and the counter turns or flips on the map.
- **Why:** Flanking decided many Civil War battles. At Kernstown, Jackson tried to turn the Union right. Today the board cannot show which way a line faces.
- **Smallest version:** unit `"facing": 0..5`, using the same edge numbers as fences. Attacks across the two rear edges get +1 column. Templates get a `"rotateWithFacing": true` flag.

**8. Leader units that can be wounded or killed**
- **Want:** a leader unit, or a leader attached to a unit, that can be hit in combat, with an effect when it is.
- **Why:** At Kernstown, Shields was wounded the day before, Col. Murray of the 84th Pennsylvania was killed, and Jackson arrested Garnett for falling back. Leaders make the game personal.
- **Smallest version:** unit `"leader": {"name": "Garnett", "lossChance": 10, "effect": "cs-1" | "activation-1" | "none"}`.

**9. Morale, disorder and rally**
- **Want:** a unit can be disordered (weaker, cannot attack) instead of eliminated, and can rally later, perhaps near a leader.
- **Why:** Panic and rally are central to Civil War battles. At Kernstown the Confederate line broke when Garnett pulled back, and Jackson tried to rally it.
- **Smallest version:** a CRT result `"DD"` (defender disordered) and a unit flag `"disordered"` (half CS, no attack). The unit clears the flag after one turn without combat.

**10. Scripted turn events and messages**
- **Want:** at turn N, or when a hex changes hands, show a message and optionally change something (release a standby group, add activation, bring in reinforcements).
- **Why:** History lives in moments such as "4 PM, Tyler goes in" or "6 PM, Garnett's ammunition is gone". Today we can only write them in the description.
- **Smallest version:** `"events": [{"turn": 5, "text": {"en": "...", "ja": "..."}, "release": 1}]`, with `release` naming a standby group.

**11. Ranged bombardment and ammunition**
- **Want:** artillery can fire at range without being treated as an assault, and optionally has limited ammunition.
- **Why:** Civil War batteries dueled at long range for hours. In our first test the guns did almost nothing. Garnett's brigade retreated because it ran out of ammunition.
- **Smallest version:** a separate bombardment table (results "C", "DR" or "D"), or the rule "range > 1 can never cause AR/AE". For ammunition, a unit field such as `"ammo": 6` that drops by 1 per attack.

**12. Line of sight for artillery**
- **Want:** if the game does not have it already, high ground and woods should block fire at range.
- **Why:** Pritchard's Hill and Sandy Ridge matter because guns on them could see. Without line of sight, a battery fires through a forest as easily as across a field.
- **Smallest version:** terrain `"blocksLOS": true` (forest, city, mountain), checked on hexes between the firer and the target.

**13. Text for each unit (tooltip or description)**
- **Want:** a short text on each unit, shown on hover.
- **Why:** We want to show the colonel, the regiments and the men present, for example "33rd Virginia, Col. Cummings". Today the tooltip is only the name, and `boxes` 8–19 are always 0.
- **Smallest version:** unit `"description": {"en": "...", "ja": "..."}`.

## Nice-to-have

**14. Separate briefings and images for each side**
- **Want:** a separate description and briefing image for each side, plus a name for each turn.
- **Why:** Kimball and Jackson knew very different things. Jackson believed he faced four regiments, not a division. Turn names such as "4:00 PM, Tyler attacks" help players feel the clock.
- **Smallest version:** `meta.descriptionBySide: {"first": {...}, "second": {...}}`, `briefingImageBySide`, and an optional `"label"` on each `turnClock` entry. A short note on what `briefingImage` accepts would also help, because every stock file has it as "".

**15. Standby holds for human players (optional)**
- **Want:** an option so that standby groups also bind a human player until they are released.
- **Why:** Historical reserves were held back by orders. The help says a standby unit "cannot move on its own", but not whether that binds a human player. If it does not, a human can move every unit on turn 1, which breaks the timing.
- **Smallest version:** `standby_groups[n].bindsHuman: true`.

**16. Mod or scripting hooks**
- **Want:** a small hook for scripts, for example a Lua or JavaScript function called at the start of each turn and after each combat, with read and write access to units and hexes.
- **Why:** Scenario makers could add the rules above without asking you for each one.
- **Smallest version:** even read-only hooks that can show messages would help.

**17. Hex-name size and placement**
- **Want:** a smaller font, or an optional offset, for hex names.
- **Why:** Civil War fields have many named farms close together. Neighbouring names run into each other, so we had to drop some.
- **Smallest version:** hex `"nameOffset": [dx, dy]`, or `"nameSize": "small"`.

**18. A command-point label without a hex name**
- **Want:** a CP hex that shows its value without needing a name.
- **Why:** All stock CP hexes have names, so we gave ours a name too. That adds another label to a crowded row.

**19. Step losses beyond one replacement**
- **Want:** more than one step: for example 6 → 3 → 1, or a CRT result that costs a step without a retreat.
- **Why:** Replacements give a brigade one second life at half strength, which helps a lot. A replacement that is destroyed is gone, and AR/DR never cost strength, so a long fight still wears nothing down.
- **Smallest version:** a CRT result `"DL"` (defender loses half, stays in place).

## Questions from v3.5 (only the engine can answer these)

**20. Elite (surprise) units: the exact rules**
- **Want:** a few help lines on the elite round: does it fire when an elite unit is attacked during the enemy's elite round; can an elite unit still on standby take part (or does the round wake it); does the AI plan its elite move, or just move those units as in a normal phase; and is the round spent if the first elite combat is a ranged artillery shot?
- **Why:** v3.6 marks two counters a side elite (two of Tyler's for the Union; Fulkerson's and Garnett's 2nd/4th/27th for Jackson). Tyler's brigade starts on standby. If a standby elite unit is skipped, the Union round may be wasted; if it is woken, the reserve timing breaks. We also cannot tell whether the Steady AI will use its round to leave the stone wall.
- **Smallest version:** document the current behaviour, or add `standby_groups[n].eliteWakes: true|false`.

**21. Victory thresholds when the line is not in the middle**
- **Want:** say what the 5/40/80% threshold guidance assumes, or let the editor show each side's best possible margin.
- **Why:** Our winLine is the status quo (the Union starts holding most objectives), so the guidance's strategic level (5/40/80% of objectives + average CS) was out of the Union's reach. We now use 5/40/80% of the smaller side's best possible margin past the line, which we worked out ourselves. A line in the editor ("Union best +99, Confederate best +211") would let makers see this at once.
- **Smallest version:** show the two best margins next to the threshold fields, and warn when a threshold is above one of them. Or allow separate thresholds per side: `victoryCondition.thresholdsBySide: {"first": [...], "second": [...]}`.

**22. Board-art layers the game can hide**
- **Want:** an option for decorations on the board art (title cartouche, compass, scale bar) that the game draws above or beside the board, or a flag that marks a rectangle of the art as "no hexes".
- **Why:** v3.5 puts a period title block with yard and meter scale bars in an empty corner of the art, on hexes nothing uses. Units can still move there and be hidden under it in a player's eye.
- **Smallest version:** `meta.boardArt.decorations: [{"image": "data:...", "anchor": "se"}]`, drawn outside the hex grid.

## From playtest 5 (v3.7)

The owner's notes after playtest 5: artillery should limber and unlimber, line of sight should be visible, brigades should stay together, and Jackson needs a way to withdraw and fight again. v3.7 does the withdrawal with your exit keys; the rest needs the engine. Naming replacements after their parent unit is already item 4.

**23. Exits: how they score (question)**
- **Want:** a few help lines on exits: does `exit_points_per_cs` add to the exiting side's score, and is the exited CS then also counted as "strength lost"; what does `exit_sudden_death_cs` do (end the game when that much CS has exited?); is there a key that caps exit points; does the AI ever exit on its own, and when; and are the save's `BlueVP`/`RedVP` the exit points?
- **Why:** v3.7 gives Jackson exits at 1 point per CS (as Second Bull Run); whether a full early walk-off can win depends on these answers.
- **Smallest version:** document the current behaviour; if exited CS counts as lost, say so in the help.

**24. Limbered and unlimbered artillery**
- **Want:** a battery has two states: limbered (moves, cannot fire) and unlimbered (fires, moves 1 or not at all), switching costs its move or half of it.
- **Why:** Guns that march and fire in the same turn make batteries roving assault units, which is how playtest 5 lost Marye's battery alone at the front.
- **Smallest version:** unit `"limber": true`; a unit that fires may not move that turn and one that moves more than 1 hex may not fire.

**25. Showing line of sight**
- **Want:** when a unit is selected, shade the hexes it can see or fire at (with item 12's blocking terrain).
- **Why:** Players cannot judge what the guns on Pritchard's Hill or Sandy Ridge can reach without seeing it.
- **Smallest version:** highlight valid ranged targets for the selected unit, even before full LOS rules exist.

**26. Brigade cohesion and command range**
- **Want:** a `brigade` id per unit, so the AI keeps a brigade's counters together, and an optional command range (a unit more than N hexes from its brigade or HQ moves or fights at a penalty).
- **Why:** In playtest 5 the AI marched Burks's brigade alone east of the pike and lost both counters to one blocked retreat; standby groups only keep units together until they wake.
- **Smallest version:** `units[].brigade` read by the AI to move a brigade toward its own centre; later `rules.command_range`.

**27. Campaign carry-over**
- **Want:** a way to start a scenario from another's result: surviving and exited strength per unit, carried into the next battle's order of battle.
- **Why:** Kernstown ended with Jackson's retreat up the Valley; the owner wants the strength he gets away with to fight the next battle.
- **Smallest version:** an "export result" that writes the save's Units / Eliminated / Exited lists by unit id (we read them today with `carryover.py`), and a scenario field such as `units[].carryFrom` matched by id.

## Workarounds we use today

What we already do in the data:

- **No step losses or rally.** Replacements are on and every strength is doubled. The CRT is gentler: no AE, DE in 3 cells, and at 1:3 to 1:1 most rolls are "C", because the must-attack rule forces units in contact to attack at poor odds every turn.
- **Units destroyed when the retreat is blocked.** Our validator checks that every stack starts with at least 2 open hexes behind it, that no two enemy flankers can close them all (v3.2), and that every battery starts stacked with infantry.
- **Fortress hexes never retreat, and nothing retreats into mountain.** We made the stone wall and ridges `rough` (x2 defence) and kept one-sided fences, as Antietam's Bloody Lane does.
- **Surprise used for initiative.** v3.6 marks two of Tyler's counters and Fulkerson's and Garnett's 2nd/4th/27th elite, about a fifth of each side's strength, and leaves the HQs out so that neither side can spend or keep its round for free.
- **No leaders.** We added HQ counters with portraits for Kimball and Jackson, held back by standby groups. Brigade counters show the commander's name and portrait.
- **No unit tooltips.** The commander and unit are printed on the counter, and the colonels are in the description.
- **No events or turn labels.** The description has an "afternoon" timeline, and standby groups wake units at historical times.
- **No side briefings.** One description has a section for each side.
- **AI behaviour.** We use a Cautious Union and a Steady Confederacy, and standby triggers (containment, opposing group, main body %) to time the reserves.
- **Artillery too weak.** Range 3 on our 300 m hexes, and CS 4 for a full battery (all strengths doubled).
- **No facing.** We use symmetric NATO marks, so nothing points the wrong way.

Thank you for reading. We are happy to test anything you add.
