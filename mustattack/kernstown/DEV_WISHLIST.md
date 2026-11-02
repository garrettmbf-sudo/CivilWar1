# Wishlist from a Civil War scenario maker

Hello, and thank you for *Must Attack!* and the Wargame Maker. We made a First Kernstown (1862) scenario with the Wargame Maker export format and have played it three times. The engine works well for this. The editor's help text now answers many of our earlier questions: replacements, the retreat and ZOC options, the standby fields (containment, main body %, opposing group), the fact that held units still fire, the list of AI personalities, elite and sudden-death units, and the activation cap. Thank you. This list keeps only what is still open.

Each item has three parts:
- **Want:** what we would like
- **Why:** why it matters for Civil War battles
- **Smallest version:** where we can, the smallest change that would be enough, written in the style of the current JSON

The field names are only suggestions.

## Must-have

**1. Retreat into enemy ZOC as a scenario option, or a replacement for a blocked retreat**
- **Want:** let the scenario choose whether a retreating unit may enter an enemy ZOC hex, perhaps at a cost. Or let replacements also cover a unit lost because it had no retreat path.
- **Why:** Most of our losses are units hemmed in, not units beaten by the die. Replacements, as the help describes them, do not apply to those losses. Civil War brigades usually fell back battered, not wiped out. Saves already carry `ZocToZocAllowed`, but scenario rules have no field for it.
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

**3. Fortress terrain and retreats**
- **Want:** an option for whether a defender in a fortress hex may retreat.
- **Why:** In our log, a DR and two ARs became "C" (no effect) when the fortress hex was involved. That is right for a fort, but for a stone wall or a sunken lane it means the only bad result is destruction. We used mountain terrain for our wall instead.
- **Smallest version:** a terrain flag such as `"holdsInPlace": true` on fortress, set to false on others. Or just document the current rule.

**4. Containment: per unit or per group?**
- **Want:** one line on whether containment adds up the enemy strength around each unit separately or around the group as a whole.
- **Why:** With per-unit counting, a group whose units stand far apart wakes as soon as one of them has no enemy nearby. We now give containment only to groups whose units share a hex.

## High value

**5. Unit facing, with flank and rear attacks**
- **Want:** counters have a facing. An attack from the flank or rear gets an odds shift, and the counter turns or flips on the map.
- **Why:** Flanking decided many Civil War battles. At Kernstown, Jackson tried to turn the Union right. Today the board cannot show which way a line faces.
- **Smallest version:** unit `"facing": 0..5`, using the same edge numbers as fences. Attacks across the two rear edges get +1 column. Templates get a `"rotateWithFacing": true` flag.

**6. Leader units that can be wounded or killed**
- **Want:** a leader unit, or a leader attached to a unit, that can be hit in combat, with an effect when it is.
- **Why:** At Kernstown, Shields was wounded the day before, Col. Murray of the 84th Pennsylvania was killed, and Jackson arrested Garnett for falling back. Leaders make the game personal.
- **Smallest version:** unit `"leader": {"name": "Garnett", "lossChance": 10, "effect": "cs-1" | "activation-1" | "none"}`.

**7. Morale, disorder and rally**
- **Want:** a unit can be disordered (weaker, cannot attack) instead of eliminated, and can rally later, perhaps near a leader.
- **Why:** Panic and rally are central to Civil War battles. At Kernstown the Confederate line broke when Garnett pulled back, and Jackson tried to rally it.
- **Smallest version:** a CRT result `"DD"` (defender disordered) and a unit flag `"disordered"` (half CS, no attack). The unit clears the flag after one turn without combat.

**8. Scripted turn events and messages**
- **Want:** at turn N, or when a hex changes hands, show a message and optionally change something (release a standby group, add activation, bring in reinforcements).
- **Why:** History lives in moments such as "4 PM, Tyler goes in" or "6 PM, Garnett's ammunition is gone". Today we can only write them in the description.
- **Smallest version:** `"events": [{"turn": 5, "text": {"en": "...", "ja": "..."}, "release": 1}]`, with `release` naming a standby group.

**9. Ranged bombardment and ammunition**
- **Want:** artillery can fire at range without being treated as an assault, and optionally has limited ammunition.
- **Why:** Civil War batteries dueled at long range for hours. In our first test the guns did almost nothing. Garnett's brigade retreated because it ran out of ammunition.
- **Smallest version:** a separate bombardment table (results "C", "DR" or "D"), or the rule "range > 1 can never cause AR/AE". For ammunition, a unit field such as `"ammo": 6` that drops by 1 per attack.

**10. Line of sight for artillery**
- **Want:** if the game does not have it already, high ground and woods should block fire at range.
- **Why:** Pritchard's Hill and Sandy Ridge matter because guns on them could see. Without line of sight, a battery fires through a forest as easily as across a field.
- **Smallest version:** terrain `"blocksLOS": true` (forest, city, mountain), checked on hexes between the firer and the target.

**11. Text for each unit (tooltip or description)**
- **Want:** a short text on each unit, shown on hover.
- **Why:** We want to show the colonel, the regiments and the men present, for example "33rd Virginia, Col. Cummings". Today the tooltip is only the name, and `boxes` 8–19 are always 0.
- **Smallest version:** unit `"description": {"en": "...", "ja": "..."}`.

## Nice-to-have

**12. Separate briefings and images for each side**
- **Want:** a separate description and briefing image for each side, plus a name for each turn.
- **Why:** Kimball and Jackson knew very different things. Jackson believed he faced four regiments, not a division. Turn names such as "4:00 PM, Tyler attacks" help players feel the clock.
- **Smallest version:** `meta.descriptionBySide: {"first": {...}, "second": {...}}`, `briefingImageBySide`, and an optional `"label"` on each `turnClock` entry. A short note on what `briefingImage` accepts would also help, because every stock file has it as "".

**13. Standby holds for human players (optional)**
- **Want:** an option so that standby groups also bind a human player until they are released.
- **Why:** Historical reserves were held back by orders. The help says a standby unit "cannot move on its own", but not whether that binds a human player. If it does not, a human can move every unit on turn 1, which breaks the timing.
- **Smallest version:** `standby_groups[n].bindsHuman: true`.

**14. Mod or scripting hooks**
- **Want:** a small hook for scripts, for example a Lua or JavaScript function called at the start of each turn and after each combat, with read and write access to units and hexes.
- **Why:** Scenario makers could add the rules above without asking you for each one.
- **Smallest version:** even read-only hooks that can show messages would help.

**15. Hex-name size and placement**
- **Want:** a smaller font, or an optional offset, for hex names.
- **Why:** Civil War fields have many named farms close together. Neighbouring names run into each other, so we had to drop some.
- **Smallest version:** hex `"nameOffset": [dx, dy]`, or `"nameSize": "small"`.

**16. A command-point label without a hex name**
- **Want:** a CP hex that shows its value without needing a name.
- **Why:** All stock CP hexes have names, so we gave ours a name too. That adds another label to a crowded row.

**17. Step losses beyond one replacement**
- **Want:** more than one step: for example 6 → 3 → 1, or a CRT result that costs a step without a retreat.
- **Why:** Replacements give a brigade one second life at half strength, which helps a lot. A replacement that is destroyed is gone, and AR/DR never cost strength, so a long fight still wears nothing down.
- **Smallest version:** a CRT result `"DL"` (defender loses half, stays in place).

## Workarounds we use today

What we already do in the data:

- **No step losses or rally.** Replacements are on and every strength is doubled, so brigades of CS 4-6 get a half-strength second life on an AE or DE. The CRT is also gentler: AE appears in 1 cell and DE in 3, and many AR/DR results became "C".
- **Units destroyed when the retreat is blocked.** Our validator checks that every stack starts with at least 2 open hexes behind it, that no two enemy flankers can close them all (v3.2), and that every battery starts stacked with infantry.
- **Fortress hexes never retreat.** We made the stone wall `mountain` (x2 defence) and kept one-sided fences, as Antietam's Bloody Lane does.
- **No leaders.** We added HQ counters with portraits for Kimball and Jackson, held back by standby groups. Brigade counters show the commander's name and portrait.
- **No unit tooltips.** The commander and unit are printed on the counter, and the colonels are in the description.
- **No events or turn labels.** The description has an "afternoon" timeline, and standby groups wake units at historical times.
- **No side briefings.** One description has a section for each side.
- **AI behaviour.** We use a Cautious Union and an Aggressive Confederacy, and standby triggers (containment, opposing group, main body %) to time the reserves.
- **Artillery too weak.** Range 3 on our 300 m hexes, and CS 4 for a full battery (all strengths doubled).
- **No facing.** We use symmetric NATO marks, so nothing points the wrong way.

Thank you for reading. We are happy to test anything you add.
