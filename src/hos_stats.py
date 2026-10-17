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
OUT_EXCLUDED = os.path.join(DATA_DIR, "hos_unit_stats_excluded_1862.csv")
# Unrated / doubtful items: kept flagged in the OOB, never given stats.
EXCLUDED = {
    "REG_OH13C": "UNRATED: likely spurious - no 13th Ohio Cavalry in OR 12/1 full-text search",
    "ART_PLEASANTS": "UNRATED: no battery-specific evidence in unit_ratings_1862.csv",
    "ART_US_WVB": "UNRATED: no battery-specific evidence in unit_ratings_1862.csv",
    "ART_US_ADDHOW": "UNRATED: organization UNCONFIRMED (Blenker additional howitzers)",
    "ART_US_PAE": "UNRATED: no battery-specific evidence in unit_ratings_1862.csv",
}
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


RANK_CAP = 4  # rank 5 assigns a random WW2 medal-winner "hero" (manual 8.4.15 p.18-19)
TRAINING_SOFT_PCT = 0.05     # crosswalk: training 1..5 -> -10%..+10% soft attack
COHESION_HP = {1: 0.70, 2: 0.85}  # crosswalk option (b): straggling/desertion; 3-5 full
TACTICAL_BRIGADE_PCT = {1: 1, 2: 3, 3: 5, 4: 7, 5: 9}
ECHELON_MULT = {"brigade": 1.0, "division": 1.3, "department": 1.5, "army": 1.6}
RANGE_BASE = {"brigade": 2, "division": 4, "department": 5, "army": 6}
CMD_MP = 14


def unit_stats(unit_class: str, exp: int, coh: int, trn: int, n_regiments: int) -> dict:
    soft, hard, ammo, fuel, mp, rng, vis = BASE[unit_class]
    t = 1 + TRAINING_SOFT_PCT * (trn - 3)   # experience is NOT here: rank already adds +4%/rank
    hp = clamp(HP_PER_REGIMENT * max(n_regiments, 1), HP_MIN, HP_MAX)
    hp = max(1, round(hp * COHESION_HP.get(coh, 1.0)))
    return {
        "soft_damage": round(soft * t),
        "hard_damage": max(1, round(hard * t)),
        "air_damage": 0,
        "armor": 0,
        "hp": hp,
        "ammo": ammo,
        "fuel": fuel,
        "movement_points": mp,
        "range": rng,
        "visibility": vis,
        "rank": clamp(round((2 * exp + coh) / 3), 1, RANK_CAP),
    }


def commander_stats(echelon: str, ini: int, rel: int, tac: int, adm: int) -> dict:
    """tactical -> bonus %, administration -> radius, initiative -> MP.
    reliability is deliberately unused (no engine parameter; scenario design only)."""
    lo, hi = ECHELON_RANGE[echelon]
    adj = 1 if adm >= 4 else (-1 if adm <= 2 else 0)
    soft = clamp(round(TACTICAL_BRIGADE_PCT[tac] * ECHELON_MULT[echelon]), 1, BONUS_MAX)
    mp = CMD_MP + (1 if ini == 5 else (-1 if ini <= 2 else 0))
    return {
        "range": clamp(RANGE_BASE[echelon] + adj, lo, hi),
        "soft_damage": soft,
        "hard_damage": 0,            # no armoured targets in 1862 (crosswalk)
        "air_damage": 0,
        "armor": 0, "hp": 20, "ammo": 0, "fuel": 70, "movement_points": mp, "visibility": 2,
        "rank": clamp(round((ini + tac + adm) / 3), 1, RANK_CAP),
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

    oob_units = set(oob.regiments) | set(oob.artillery)
    # direct regiment/battery ratings; rows whose basis says "inherits" are not direct evidence
    direct = [r for r in urs if r["unit_id"] in oob_units and "inherits" not in r["basis"].lower()]

    def own_rating(uid: str, on: date) -> dict | None:
        past = [r for r in direct if r["unit_id"] == uid and _d(r["as_of_date"]) <= on]
        return max(past, key=lambda r: r["as_of_date"]) if past else None

    def child(row_type, uid, name, cls, parent, extra):
        own = own_rating(uid, _d(parent["as_of_date"]))
        if own:
            src, how = own, ["OWN_RATING"]
        else:
            src, how = None, ["INHERITED_FROM_PARENT"]
        e, c, t = ((int(src["experience"]), int(src["cohesion_morale"]), int(src["training"]))
                   if src else (parent["experience"], parent["cohesion_morale"], parent["training"]))
        conf = src["confidence"] if src else parent["confidence"]
        return {**parent, "row_type": row_type, "unit_id": uid, "name": name, "unit_class": cls,
                "experience": e, "cohesion_morale": c, "training": t, "confidence": conf,
                "rating_id": src["rating_id"] if src else parent["rating_id"],
                "rating_from": uid if src else parent["rating_from"],
                "sources": src["sources"] if src else parent["sources"],
                **unit_stats(cls, e, c, t, 1), "flags": _flags(conf, how + extra)}

    for r in sorted((r for r in urs if r["unit_id"] in oob.formations),
                    key=lambda r: (r["unit_id"], r["as_of_date"])):
        fid, on = r["unit_id"], _d(r["as_of_date"])
        f = oob.formations[fid]
        cls = f["type"] if f["type"] in BASE else "infantry"
        regs = [x for x in oob.members_of(fid, on) if x not in EXCLUDED]
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
        for rid in regs:
            reg = oob.regiments[rid]
            rc = reg["type"] if reg.get("type") in BASE else "infantry"
            out.append(child("regiment", rid, reg["designation"], rc, base, []))
        for b in oob.artillery.values():
            if (b["battery_id"] not in EXCLUDED and b["attached_to"] == fid
                    and _d(b["attached_to_from"]) and _d(b["attached_to_from"]) <= on):
                out.append(child("battery", b["battery_id"], b["designation"], "artillery", base,
                                 ["GUN_TYPE_UNVERIFIED_RANGE_3"]))

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
    with open(OUT_EXCLUDED, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["unit_id", "excluded_reason"])
        for k in sorted(EXCLUDED):
            w.writerow([k, EXCLUDED[k]])
    return len(rows)


if __name__ == "__main__":
    print(f"wrote {write()} rows -> {OUT}")
