# Campaign carry-over: reading a Kernstown save for the next scenario

Kernstown ended with Jackson falling back up the Valley Turnpike toward Newtown. From v3.7 the Confederates can withdraw off the south edge (see README, "Withdrawal (v3.7)"). What a side has at the end of the game, on the board plus what exited, is what it takes into the next fight. The game has no campaign link yet (DEV_WISHLIST 27), so we read the result from a save and enter it in the next scenario by hand.

## Where the numbers are in a save

A save is UTF-8 JSON, sometimes with a BOM. The fields we use:

| Field | What it holds |
|---|---|
| `Units` | Every unit still in play, one object per counter. Surviving units have `IsEliminated` false and `HasExited` false, plus their `X`, `Y`. |
| `Eliminated` | Units destroyed, the same object shape, with `EliminatedTurn` and the hex where they died. |
| `Exited` | Units that left through an exit hex (expected `HasExited` true, `ExitPoints` set). Empty in every save we have; v3.7 is the first version with exits. |
| `Reinforcements` | Units that have not arrived yet (none in Kernstown). |
| `BlueInitialCS`, `RedInitialCS` | Each side's starting strength. Side 0 (`first`, blue) is the Union, side 1 (`second`, red) the Confederates. |
| `BlueVP`, `RedVP` | Probably exit points. Both are 0 in playtest 5, which had no exits (unconfirmed, DEV_WISHLIST 23). |

Each unit object has `Side`, `Name`, `TemplateId` (`local_<id>`, the scenario's unit id), `CombatStrength` (the doubled file value), `IsReplacement` (a "Replacements" counter made after an AE or DE) and `StandbyGroup`. Units here keep their CS until they are eliminated; a replacement shows up as a new unit with `IsReplacement` true.

## The script

```
python3 carryover.py SAVE.json
python3 carryover.py SAVE.json --json result.json
```

The script prints each side's units as surviving, exited or eliminated, with their CS and where they ended, then the side totals ("carried forward" = surviving + exited). It checks the totals against `BlueInitialCS` / `RedInitialCS`. A unit is counted once: `Exited` takes precedence over `Eliminated`, and `Eliminated` over `Units`. `--json` writes the same figures for a builder to read.

## Seeding the next scenario

1. Run the script on the last save of the game, taken after turn 11 or when the game ends.
2. For each surviving or exited unit, put it in the next scenario's order of battle with its CS from the save, matched by `TemplateId` or by name. Halve a unit that exited under pressure if the next scenario should reflect straggling; that is a design choice, not something the save records.
3. Leave eliminated units out, or bring them back weaker as returning stragglers if the next battle is days later.
4. A replacement counter (`IsReplacement`) stands for the remnant of its parent unit, so add its CS to that unit.
5. Exited Confederate units start the next scenario together on the road they left by: the Valley Turnpike for (11-13,35), the Middle Road for (0-2,35).

## Playtest 5 (v3.5 save, turn 11)

`python3 carryover.py /workspace/mustattack/ref/playtest5_save.json` (the save is not in the repo) gives Union 64 surviving and 2 eliminated (Brodhead OH/MD Cav, turn 10), out of 66. The Confederates have 34 surviving and 10 eliminated (Burks 21 VA/1 Bn 4 and Burks 42 VA 2 on turn 9 at (17,20), Marye Hampden 4 on turn 10 at (16,21)), out of 44. Nothing exited. That save predates v3.6, so it uses v3.5 strengths and names (Marye, OH/MD Cav; its Lanier Danville is again the current name from v3.9, after v3.6-v3.8.1 called it Shumaker Danville).
