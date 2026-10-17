# Facing mod: in-game test checklist

Results come in two kinds:
- **[Box]** was compiled and tested on the box.
- **[Game]** can only be proven in Hex of Steel. Tick each [Game] item and paste the `Player.log` lines into the PR.

**Done on the box:**
- [Box] `dotnet build -c Release`: 0 warnings, 0 errors (net48, against template DLLs at commit 5fd716b).
- [Box] 39 unit tests pass:
  - direction math matches `src/hex_utils.py` (288 neighbour cases);
  - the game's grid geometry;
  - front/flank/rear arcs, rounding and enum mapping;
  - every patched method and field exists with the exact signature in `Assembly-CSharp.dll`.

## 0. Load
- [ ] [Game] With HarmonyCore and Facing enabled, `Player.log` shows the three lines listed in INSTALL.md.
- [ ] [Game] The log shows no `[Facing]` errors.

## 1. Test scenario setup (map editor)
1. Turn on **Show tile info** in the main-menu settings. The manual says it shows tile coordinates (x, y).
2. Turn **Random damage modifier** off (0) in the settings. Real hits use `PlayerSettings.RandomDamageModifier`; the preview does not.
3. Create a new map, **12 × 12**, all **plains**.
   - Player 1: country A. Player 2: country B. Set them at war.
   - Make **both players human** (hotseat), so the AI re-face doesn't move anything.
4. Place one **infantry for Player 2 at (6,6)**. This is the defender.
5. Place three identical **Player 1 infantry** (same type, full HP) at:
   - **(5,7)**, the defender's **NW** neighbour. Column 6 is even, and even columns sit half a row north (MapGO).
   - **(6,7)**, its **N** neighbour.
   - **(6,5)**, its **S** neighbour.
6. Save it as `facing_test` and start it as Player 1.

**Expected chevrons:**
- The defender's chevron points **NW** (upper-left). It was placed with the editor default WEST, which the mod reads as `legacyWestFacing` = 5 (NW).
- [ ] [Game] The chevron is visible on every ground counter, and the figure sprite is **not** rotated (only flipped east/west).

## 2. Combat preview numbers
For each attacker: select it, hover the defender, and read the damage the preview shows for the attacker's hit.
- [ ] [Game] Attacker at (5,7), NW of the defender = **front**. Write the number down as **D**.
- [ ] [Game] Attacker at (6,7), N of the defender = **flank**. Expect **round_half_even(1.25 × D)**.
- [ ] [Game] Attacker at (6,5), S of the defender = **rear**. Expect **round_half_even(1.5 × D)**.
- [ ] [Game] The retaliation number (the defender hitting back) is the **same** for all three attackers. Retaliation is always frontal, because the attacker turns to face its target before resolving.
- [ ] [Game] With the mod disabled, all three preview numbers equal D.

Expected values. The rounding is the game's own (`Math.Round`, `MidpointRounding.ToEven`):

| Front D | Flank (×1.25) | Rear (×1.5) |
| --- | --- | --- |
| 1 | 1 | 2 |
| 2 | 2 | 3 |
| 3 | 4 | 4 |
| 4 | 5 | 6 |
| 5 | 6 | 8 |
| 6 | 8 | 9 |
| 7 | 9 | 10 |
| 8 | 10 | 12 |
| 9 | 11 | 14 |
| 10 | 12 | 15 |
| 11 | 14 | 16 |
| 12 | 15 | 18 |
| 13 | 16 | 20 |
| 14 | 18 | 21 |
| 15 | 19 | 22 |
| 16 | 20 | 24 |
| 17 | 21 | 26 |
| 18 | 22 | 27 |
| 19 | 24 | 28 |
| 20 | 25 | 30 |
| 21 | 26 | 32 |
| 22 | 28 | 33 |
| 23 | 29 | 34 |
| 24 | 30 | 36 |
| 25 | 31 | 38 |
| 26 | 32 | 39 |
| 27 | 34 | 40 |
| 28 | 35 | 42 |
| 29 | 36 | 44 |
| 30 | 38 | 45 |

## 3. Real resolution
- [ ] [Game] With random damage at 0, attack from (6,5) (rear). The defender loses exactly the rear preview number. Check its HP before and after.
- [ ] [Game] After the attack, the defender's chevron still points NW (no auto-turn). The attacker now faces N, toward the defender.
- [ ] [Game] End turn as Player 1 and start Player 2. Move the defender one hex into any free neighbour (e.g. SW to (5,6)). The chevron points in the direction of the last step.

## 4. Turn in place
- [ ] [Game] As Player 2, select a unit with MP left and press `.`: the chevron moves one hexside clockwise and MP drops by 1. `,` turns it back.
- [ ] [Game] With 0 MP left, nothing happens.
- [ ] [Game] During the other player's turn, pressing `.` on an enemy unit does nothing.

## 5. AI re-face
- [ ] [Game] Make Player 2 an AI and end Player 1's turn. When the AI ends its turn, each of its ground units within 6 hexes of a Player 1 unit points at the nearest one (ties go to the lower unit ID).

## 6. Save and reload
- [ ] [Game] Turn the defender to face SE with `.`/`,`, save, quit to the main menu and load the save. The chevron still points SE, and the preview numbers from step 2 are relative to SE:
  - an attacker at SE is front;
  - attackers at NE and S are flank;
  - attackers at N, NW and SW are rear.

## 7. PBEM replay
- [ ] [Game] Start a PBEM game with this map. Both "players" need the mod.
- [ ] [Game] Player 1 moves an infantry two hexes north-east and attacks a Player 2 unit from its rear. Then save or send the turn.
- [ ] [Game] Load it as Player 2:
  - the attacker's chevron shows its final facing;
  - the defender's facing is unchanged;
  - the defender's HP matches the rear damage.

## 8. Not covered (known gaps)
- Real-time multiplayer: should stay in sync for moves and attacks; turn in place is disabled. **Untested.**
- Units on boats, planes and static units (bunkers, mines, MaxMP 0) are excluded on purpose.
- The AI does not plan around facing when it moves. It only re-faces at the end of its turn, and its attack choice already prefers flank and rear because it ranks targets with the patched damage.
- The chevron's size and offset depend on how the counter prefab is scaled in game (UNVERIFIED). Adjust `chevronDistance` and `chevronScale` if needed.
- Does `ShowPotentialPaths()` refresh the move highlight after turning in place? UNVERIFIED. If not, reselect the unit.
