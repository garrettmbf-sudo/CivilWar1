"""Deterministic mapping: historical ratings + OOB -> Hex of Steel unit-editor fields.

Only real Hex of Steel fields are emitted (docs/hos-unit-mechanics.md): soft/hard/air
damage, armor, HP, ammo, fuel, movement points, attack range, visibility, starting rank;
commanders: range (= command radius) and soft/hard/air damage (= % bonus).
Formula is documented in docs/hos-stats-mapping.md. No faction modifiers: identical
inputs give identical stats on both sides (no scripted outcome).

Run: python -m src.hos_stats  -> writes historical_data/hos_unit_stats_1862.csv
"""
from __future__ import annotations

import csv
import os
from datetime import date

from src.oob import OOB, DATA_DIR, _d, _rows

OUT = os.path.join(DATA_DIR, "hos_unit_stats_1862.csv")
FIELDS = ["row_type", "unit_id", "name", "faction", "unit_class", "as_of_date", "rating_id",
          "rating_from", "experience", "cohesion_morale", "training", "initiative", "reliability",
          "tactical_skill", "administration", "echelon", "soft_damage", "hard_damage",
          "air_damage", "armor", "hp", "ammo", "fuel", "movement_points", "range",
          "visibility", "rank", "confidence", "flags", "sources"]

# --- class baselines (500 yd/hex; MP per docs/valley-map-build-plan.md section 1.3) ---
BASE = {
    #            soft hard  ammo fuel  mp  range vis
    "infantry":  (20,  4,    6,   45,   9,  1,    1),
    "cavalry":   (14,  2,    5,   70,  14,  1,    2),   # recon class in editor: moves twice
    "artillery": (24,  6,    5,   45,   7,  3,    1),   # range 3 = smoothbore; rifled = 4
}
HP_PER_REGIMENT = 20     # strength proxy: no brigade-level returns in repo
HP_MIN, HP_MAX = 20, 100
ECHELON_RANGE = {"brigade": (1, 2), "division": (3, 4), "department": (5, 6), "army": (6, 7)}
LEVEL_TO_ECHELON = {"brigade": "brigade", "detachment": "brigade", "battalion": "brigade",
                    "battalion_group": "brigade", "division": "division",
                    "department": "department", "army": "army"}
# Documented overrides: data 'level' vs. command size
ECHELON_OVERRIDE = {"FRM_CS_NW": "division"}  # Army of the Northwest ~2 brigades at McDowell
BONUS_MAX = 15


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def unit_stats(unit_class: str, exp: int, coh: int, trn: int, n_regiments: int) -> dict:
    soft, hard, ammo, fuel, mp, rng, vis = BASE[unit_class]
    q = (trn - 3) + (exp - 3)            # -4..+4 quality offset
    hp = clamp(HP_PER_REGIMENT * max(n_regiments, 1), HP_MIN, HP_MAX)
    return {
        "soft_damage": soft + 2 * q,
        "hard_damage": max(1, hard + q // 2),
        "air_damage": 0,
        "armor": 0,
        "hp": hp,
        "ammo": ammo,
        "fuel": fuel,
        "movement_points": mp,
        "range": rng,
        "visibility": vis,
        # cohesion has no engine field (morale is a global option): it goes into rank only
        "rank": clamp(round(0.6 * exp + 0.4 * coh), 1, 5),
    }


def commander_stats(echelon: str, ini: int, rel: int, tac: int, adm: int) -> dict:
    lo, hi = ECHELON_RANGE[echelon]
    reach = (ini + adm) / 2
    soft = clamp(2 * tac + (ini - 3) + (rel - 3), 1, BONUS_MAX)
    return {
        "range": hi if reach >= 3.5 else lo,
        "soft_damage": soft,
        "hard_damage": soft // 2,
        "air_damage": 0,
        "armor": 0, "hp": 20, "ammo": 0, "fuel": 70, "movement_points": 14, "visibility": 2,
        "rank": clamp(round((ini + rel + tac + adm) / 4), 1, 5),
    }


def _rating_for(rows: list[dict], key: str, ident: str, on: date) -> dict | None:
    cand = [r for r in rows if r[key] == ident]
    if not cand:
        return None
    past = [r for r in cand if _d(r["as_of_date"]) <= on]
    return max(past, key=lambda r: r["as_of_date"]) if past else min(cand, key=lambda r: r["as_of_date"])


def _flags(conf: str, extra: list[str]) -> str:
    f = list(extra)
    if conf == "provisional":
        f.insert(0, "PROVISIONAL_RATING")
    return ";".join(f)


def build(oob: OOB | None = None) -> list[dict]:
    oob = oob or OOB.load()
    urs = _rows("unit_ratings_1862.csv")
    crs = _rows("command_ratings_1862.csv")
    out: list[dict] = []

    for r in sorted(urs, key=lambda r: (r["unit_id"], r["as_of_date"])):
        fid, on = r["unit_id"], _d(r["as_of_date"])
        f = oob.formations[fid]
        cls = f["type"] if f["type"] in BASE else "infantry"
        regs = oob.members_of(fid, on)
        exp, coh, trn = int(r["experience"]), int(r["cohesion_morale"]), int(r["training"])
        flags = ["HP_PROXY_REGIMENT_COUNT"]
        if not regs:
            flags.append("NO_REGIMENTS_ON_DATE")
        base = dict(rating_id=r["rating_id"], rating_from=fid, as_of_date=r["as_of_date"],
                    experience=exp, cohesion_morale=coh, training=trn, faction=f["faction"],
                    confidence=r["confidence"], sources=r["sources"])
        out.append({**base, "row_type": "formation", "unit_id": fid, "name": f["designation"],
                    "unit_class": cls, **unit_stats(cls, exp, coh, trn, len(regs)),
                    "flags": _flags(r["confidence"], flags)})
        # regiments and batteries inherit the parent brigade's rating on that date
        for rid in regs:
            reg = oob.regiments[rid]
            rc = reg["type"] if reg.get("type") in BASE else "infantry"
            out.append({**base, "row_type": "regiment", "unit_id": rid, "name": reg["designation"],
                        "unit_class": rc, **unit_stats(rc, exp, coh, trn, 1),
                        "flags": _flags(r["confidence"], ["INHERITED_FROM_PARENT"])})
        for b in oob.artillery.values():
            if b["attached_to"] == fid and _d(b["attached_to_from"]) and _d(b["attached_to_from"]) <= on:
                out.append({**base, "row_type": "battery", "unit_id": b["battery_id"],
                            "name": b["designation"], "unit_class": "artillery",
                            **unit_stats("artillery", exp, coh, trn, 1),
                            "flags": _flags(r["confidence"], ["INHERITED_FROM_PARENT",
                                                              "GUN_TYPE_UNVERIFIED_RANGE_3"])})

    for r in sorted(crs, key=lambda r: (r["commander_id"], r["as_of_date"])):
        cid, on = r["commander_id"], _d(r["as_of_date"])
        c = oob.commanders.get(cid, {})
        held = [x["brigade_id"] for x in oob.commands
                if x["commander_id"] == cid and x["valid_from"] <= on <= x["valid_to"]]
        if not held:  # rating date outside command windows: nearest command record
            near = sorted((abs((x["valid_from"] - on).days), x["brigade_id"])
                          for x in oob.commands if x["commander_id"] == cid)
            held = [near[0][1]] if near else []
        order = ["brigade", "division", "department", "army"]
        ech = "brigade"
        for fid in held:
            e = ECHELON_OVERRIDE.get(fid) or LEVEL_TO_ECHELON.get(oob.formations[fid]["level"], "brigade")
            if order.index(e) > order.index(ech):
                ech = e
        ini, rel, tac, adm = (int(r[k]) for k in ("initiative", "reliability", "tactical_skill", "administration"))
        extra = ["COMMANDER_UNIT"] + (["ECHELON_OVERRIDE"] if any(h in ECHELON_OVERRIDE for h in held) else [])
        out.append({"row_type": "commander", "unit_id": cid, "name": c.get("name", cid),
                    "faction": c.get("faction", ""), "unit_class": "commander",
                    "as_of_date": r["as_of_date"], "rating_id": r["rating_id"],
                    "rating_from": "|".join(held), "initiative": ini, "reliability": rel,
                    "tactical_skill": tac, "administration": adm, "echelon": ech,
                    **commander_stats(ech, ini, rel, tac, adm), "confidence": r["confidence"],
                    "flags": _flags(r["confidence"], extra), "sources": r["sources"]})
    return out


def write(path: str = OUT) -> int:
    rows = build()
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    return len(rows)


if __name__ == "__main__":
    print(f"wrote {write()} rows -> {OUT}")
