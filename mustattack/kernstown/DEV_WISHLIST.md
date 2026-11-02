# Wishlist from a Civil War scenario maker

Hello, and thank you for *Must Attack!* and the Wargame Maker. We made a First Kernstown (1862) scenario with the Wargame Maker export format and played it twice. The engine works well for this. Below is what would help Civil War scenarios most. Each item has three parts:
- **Want:** what we would like
- **Why:** why it matters for Civil War battles
- **Smallest version:** where we can, the smallest change that would be enough, written in the style of the current JSON

The field names are only suggestions.

## Must-have

**1. Document the CRT and the AI doctrine values**
- **Want:** a short note on what `rules.crt` rows and columns mean, and what each doctrine word does (`def`, `off`, `line`, `brk` and the others).
- **Why:** We had to work out the CRT layout from 40 combats in save logs. We still guess what the doctrine words do, and the wrong word sent our AI into hopeless 1:2 attacks.
- **Smallest version:** a few lines in the editor help. Our reading of the CRT is `crt[odds][die-1]`, with rows 1:3, 1:2, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1 and a high die good for the attacker. Is that right?

**2. Retreat into enemy ZOC as a scenario option**
- **Want:** let the scenario choose whether a retreating unit may enter an enemy ZOC hex, perhaps at a cost.
- **Why:** In our tests, units were often destroyed only because every hex behind them was in enemy ZOC. Civil War brigades usually fell back battered, not wiped out. Saves already have `ZocToZocAllowed`, but scenario rules have no field for it.
- **Smallest version:** `rules.retreat_into_zoc: true | false`, or `"retreat_into_zoc": "allow" | "forbid" | "allow_with_loss"`.

**3. Documentation for `replacement`, `retreat_control` and `retreat_distance`**
- **Want:** what each value does.
- **Why:** These are the main levers for "units should not vanish". Every stock file uses the same value for each (0, 1, false), so we cannot tell what the others do. Saves have `IsReplacement` and `EliminatedTurn`. Do eliminated units come back?
- **Smallest version:** one help line for each field.

**4. Fortress terrain and retreats**
- **Want:** an option for whether a defender in a fortress hex may retreat.
- **Why:** In our log, a DR and two ARs became "C" (no effect) when the fortress hex was involved. That is right for a fort, but for a stone wall or a sunken lane it means the only bad result is destruction. We had to use mountain terrain for our wall instead.
- **Smallest version:** a terrain flag such as `"holdsInPlace": true` on fortress, set to false on others. Or just document the current rule.

**5. Step losses or remnant units**
- **Want:** a unit can lose strength (for example 3 → 2 → 1) instead of only surviving or dying.
- **Why:** A Civil War brigade that lost a fight was usually weakened, not wiped out, and stayed on the field. Without steps, even a gentle CRT gives "all or nothing".
- **Smallest version:** unit `"steps": [3, 2, 1]` (the CS for each step), plus a CRT result such as `"DL"` (defender loses a step). Or `replacement` could bring a unit back weaker.

## High value

**6. Unit facing, with flank and rear attacks**
- **Want:** counters have a facing. An attack from the flank or rear gets an odds shift, and the counter turns or flips on the map.
- **Why:** Flanking decided many Civil War battles. At Kernstown, Jackson tried to turn the Union right. Today the board cannot show which way a line faces.
- **Smallest version:** unit `"facing": 0..5`, using the same edge numbers as fences. Attacks across the two rear edges get +1 column. Templates get a `"rotateWithFacing": true` flag.

**7. Leader units that can be wounded or killed**
- **Want:** a leader unit, or a leader attached to a unit, that can be hit in combat, with an effect when it is.
- **Why:** At Kernstown, Shields was wounded the day before, Col. Murray of the 84th Pennsylvania was killed, and Jackson arrested Garnett for falling back. Leaders make the game personal.
- **Smallest version:** unit `"leader": {"name": "Garnett", "lossChance": 10, "effect": "cs-1" | "activation-1" | "none"}`.

**8. Morale, disorder and rally**
- **Want:** a unit can be disordered (weaker, cannot attack) instead of eliminated, and can rally later, perhaps near a leader.
- **Why:** Panic and rally are central to Civil War battles. At Kernstown the Confederate line broke when Garnett pulled back, and Jackson tried to rally it.
- **Smallest version:** a CRT result `"DD"` (defender disordered) and a unit flag `"disordered"` (half CS, no attack). The unit clears the flag after one turn without combat.

**9. Scripted turn events and messages**
- **Want:** at turn N, or when a hex changes hands, show a message and optionally change something (release a standby group, add activation, bring in reinforcements).
- **Why:** History lives in moments such as "4 PM, Tyler goes in" or "6 PM, Garnett's ammunition is gone". Today we can only write them in the description.
- **Smallest version:** `"events": [{"turn": 5, "text": {"en": "...", "ja": "..."}, "release": 1}]`, with `release` naming a standby group.

**10. Ranged bombardment and ammunition**
- **Want:** artillery can fire at range without being treated as an assault, and optionally has limited ammunition.
- **Why:** Civil War batteries dueled at long range for hours. In our first test the guns did almost nothing. Garnett's brigade retreated because it ran out of ammunition.
- **Smallest version:** a separate bombardment table (results "C", "DR" or "D"), or the rule "range > 1 can never cause AR/AE". For ammunition, a unit field such as `"ammo": 6` that drops by 1 per attack.

**11. Line of sight for artillery**
- **Want:** if the game does not have it already, high ground and woods should block fire at range.
- **Why:** Pritchard's Hill and Sandy Ridge matter because guns on them could see. Without line of sight, a battery fires through a forest as easily as across a field.
- **Smallest version:** terrain `"blocksLOS": true` (forest, city, mountain), checked on hexes between the firer and the target.

**12. Text for each unit (tooltip or description)**
- **Want:** a short text on each unit, shown on hover.
- **Why:** We want to show the colonel, the regiments and the men present, for example "33rd Virginia, Col. Cummings". Today the tooltip is only the name, and `boxes` 8–19 are always 0.
- **Smallest version:** unit `"description": {"en": "...", "ja": "..."}`.

## Nice-to-have

**13. Separate briefings and images for each side**
- **Want:** a separate description and briefing image for each side, plus a name for each turn.
- **Why:** Kimball and Jackson knew very different things. Jackson believed he faced four regiments, not a division. Turn names such as "4:00 PM, Tyler attacks" help players feel the clock.
- **Smallest version:** `meta.descriptionBySide: {"first": {...}, "second": {...}}`, `briefingImageBySide`, and an optional `"label"` on each `turnClock` entry. A short note on what `briefingImage` accepts would also help, because every stock file has it as "".

**14. Standby holds for human players (optional)**
- **Want:** an option so that standby groups also bind a human player until they are released.
- **Why:** Historical reserves were held back by orders. A human can move every unit on turn 1, which breaks the timing.
- **Smallest version:** `standby_groups[n].bindsHuman: true`.

**15. Mod or scripting hooks**
- **Want:** a small hook for scripts, for example a Lua or JavaScript function called at the start of each turn and after each combat, with read and write access to units and hexes.
- **Why:** Scenario makers could add the rules above without asking you for each one.
- **Smallest version:** even read-only hooks that can show messages would help.

**16. Documentation for `eliteUnit` and `suddenDeathUnit`**
- **Want:** what elite does (saves have `EliteUnit` / `EliteTriggered`, which look like a one-shot trigger), and what sudden death does when a unit is lost.
- **Why:** We wanted to mark the Stonewall Brigade as elite and make Jackson's loss decisive, but no stock unit sets either to true, so we did not dare.
- **Smallest version:** one help line for each.

**17. Hex-name size and placement**
- **Want:** a smaller font, or an optional offset, for hex names.
- **Why:** Civil War fields have many named farms close together. Neighbouring names run into each other, so we had to drop some.
- **Smallest version:** hex `"nameOffset": [dx, dy]`, or `"nameSize": "small"`.

**18. A command-point label without a hex name**
- **Want:** a CP hex that shows its value without needing a name.
- **Why:** All stock CP hexes have names, so we gave ours a name too. That adds another label to a crowded row.

## Workarounds we use today

What we already do in the data:

- **No step losses or rally.** We made the CRT gentler. AE appears in 1 cell and DE in 3, against 3 and 15 in the default table, and many AR/DR results became "C".
- **Units destroyed when the retreat is blocked.** Our validator checks that every stack starts with at least 2 open hexes behind it, and we place units in depth.
- **Fortress hexes never retreat.** We made the stone wall `mountain` (x2 defence) and kept one-sided fences, as Antietam's Bloody Lane does.
- **No leaders.** We added 1-CS HQ counters with portraits for Kimball and Jackson, held back by standby groups. Brigade counters show the commander's name and portrait.
- **No unit tooltips.** The commander and unit are printed on the counter, and the colonels are in the description.
- **No events or turn labels.** The description has an "afternoon" timeline, and standby groups wake units at historical times.
- **No side briefings.** One description has a section for each side.
- **AI too aggressive.** We chose the doctrine pair by trial, put VPs and CPs on the ground to hold, and held some units with standby turn 0 / chance 0.
- **Artillery too weak.** Range 3 on our 300 m hexes, and CS 2 for a full battery.
- **No facing.** We use symmetric NATO marks, so nothing points the wrong way.

Thank you for reading. We are happy to test anything you add.
