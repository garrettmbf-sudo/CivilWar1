#!/usr/bin/env python3
"""Campaign carry-over from a Sekigahara 1600: Must Attack! save.

Reads the save's Units, Eliminated and Exited lists and prints, for each side, every unit's
strength (CombatStrength) as surviving (still on the board), exited (marched off through an exit
hex) or eliminated, with side totals checked against BlueInitialCS / RedInitialCS.  Units still in
Reinforcements (not yet arrived) are listed apart.  See CAMPAIGN_CARRYOVER.md.

    python3 carryover.py SAVE.json [--json OUT.json]

--json writes the same figures as a small file for seeding the next scenario.
Side 0 is "first" (Union in Kernstown), side 1 "second" (Confederate).
"""
import json
import sys

SIDES = {0: "Union", 1: "Confederate"}


def load(path):
    with open(path, encoding="utf-8-sig") as f:      # saves and scenarios may carry a BOM
        return json.load(f)


def key(u):
    return (u.get("Side"), u.get("TemplateId"), u.get("Name"))


def classify(save):
    """One row per unit: status is exited, eliminated, surviving or not_arrived.
    The Exited list wins over Eliminated, which wins over Units (a unit in two lists is counted once);
    a unit in Units flagged HasExited / IsEliminated is classed by its flag."""
    rows = {}
    def put(u, status):
        k = key(u)
        if k not in rows:
            rows[k] = {"side": u.get("Side"), "name": u.get("Name"), "template": u.get("TemplateId"),
                       "cs": u.get("CombatStrength", 0), "status": status,
                       "turn": u.get("EliminatedTurn") or None, "exit_points": u.get("ExitPoints", 0),
                       "replacement": bool(u.get("IsReplacement")), "hex": (u.get("X"), u.get("Y"))}
    for u in save.get("Exited") or []:
        put(u, "exited")
    for u in save.get("Eliminated") or []:
        put(u, "eliminated")
    for u in save.get("Units") or []:
        if u.get("HasExited"):
            put(u, "exited")
        elif u.get("IsEliminated"):
            put(u, "eliminated")
        else:
            put(u, "surviving")
    for u in save.get("Reinforcements") or []:
        put(u, "not_arrived")
    return list(rows.values())


def report(save, rows, out=sys.stdout):
    p = lambda *a: print(*a, file=out)
    p(f"save: turn {save.get('Turn')}, side to move {save.get('CurrentSide')}; "
      f"BlueVP {save.get('BlueVP')} RedVP {save.get('RedVP')}")
    totals = {}
    for side in sorted({r["side"] for r in rows}):
        name = SIDES.get(side, f"side {side}")
        init = save.get("BlueInitialCS" if side == 0 else "RedInitialCS")
        p("")
        p(f"{name} (side {side})")
        p(f"  {'unit':34} {'CS':>3}  {'status':11} note")
        t = {"surviving": 0, "exited": 0, "eliminated": 0, "not_arrived": 0}
        order = {"surviving": 0, "exited": 1, "eliminated": 2, "not_arrived": 3}
        for r in sorted((r for r in rows if r["side"] == side), key=lambda r: (order[r["status"]], r["name"])):
            t[r["status"]] += r["cs"]
            note = []
            if r["status"] == "eliminated" and r["turn"]:
                note.append(f"turn {r['turn']} at {r['hex'][0]},{r['hex'][1]}")
            if r["status"] == "surviving":
                note.append(f"at {r['hex'][0]},{r['hex'][1]}")
            if r["exit_points"]:
                note.append(f"exit points {r['exit_points']}")
            if r["replacement"]:
                note.append("replacement")
            p(f"  {r['name']:34} {r['cs']:>3}  {r['status']:11} {'; '.join(note)}")
        carried = t["surviving"] + t["exited"]
        p(f"  totals: surviving {t['surviving']}, exited {t['exited']}, eliminated {t['eliminated']}"
          + (f", not arrived {t['not_arrived']}" if t["not_arrived"] else "")
          + f"; carried forward {carried}")
        if init is not None:
            seen = sum(t.values())
            p(f"  initial CS in save {init}; listed {seen}"
              + ("" if seen == init else f" (differs by {seen - init}: replacements or edits after the start)"))
        totals[name] = dict(t, carried_forward=carried, initial_cs=init)
    return totals


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    save = load(argv[1])
    rows = classify(save)
    totals = report(save, rows)
    if "--json" in argv:
        out = argv[argv.index("--json") + 1]
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"turn": save.get("Turn"), "totals": totals, "units": rows}, f, indent=1)
        print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
