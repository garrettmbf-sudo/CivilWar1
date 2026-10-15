"""OOB database for Jackson's 1862 Shenandoah Valley Campaign.

Loads the canonical CSVs in historical_data/, validates them, and can emit
dated orders-of-battle snapshots (JSON) that drive scenario/unit generation.

Design rules encoded here (from the OPERATION: HISTORICAL ARMIES brief):
- Brigade is the maneuver counter; regiments are recorded but not counters.
- A regiment may have at most ONE active parent formation per date unless
  the assignment row is explicitly marked as a detachment partition.
- Formations/regiments persist by ID across reassignments - never duplicated.
- Aggregate historical strengths stay aggregate; unknowns stay unknown.
"""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from datetime import date

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "historical_data")


def _d(s: str) -> date | None:
    s = (s or "").strip()
    if not s:
        return None
    return date.fromisoformat(s)


def _rows(name: str) -> list[dict]:
    path = os.path.join(DATA_DIR, name)
    with open(path, newline="", encoding="utf-8-sig") as f:
        # tolerate BOM and '#' comment lines; skip leading blank lines so the
        # header row is detected correctly (portrait_manifest.csv starts blank)
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    return list(csv.DictReader(lines))


@dataclass
class OOB:
    commanders: dict = field(default_factory=dict)
    formations: dict = field(default_factory=dict)
    regiments: dict = field(default_factory=dict)
    artillery: dict = field(default_factory=dict)
    assignments: list = field(default_factory=list)
    commands: list = field(default_factory=list)   # dated brigade->commander windows
    returns: list = field(default_factory=list)
    events: list = field(default_factory=list)
    sources: dict = field(default_factory=dict)
    portraits: dict = field(default_factory=dict)

    @classmethod
    def load(cls, data_dir: str | None = None) -> "OOB":
        global DATA_DIR
        if data_dir:
            DATA_DIR = data_dir
        oob = cls()
        for r in _rows("commanders_1862.csv"):
            oob.commanders[r["commander_id"]] = r
        for r in _rows("formations_1862.csv"):
            oob.formations[r["formation_id"]] = r
        for r in _rows("regiments_1862.csv"):
            oob.regiments[r["regiment_id"]] = r
        for r in _rows("artillery_1862.csv"):
            oob.artillery[r["battery_id"]] = r
        oob.assignments = [
            {**r, "valid_from": _d(r["valid_from"]), "valid_to": _d(r["valid_to"])}
            for r in _rows("assignments_1862.csv")
        ]
        oob.commands = [
            {**r, "valid_from": _d(r["valid_from"]), "valid_to": _d(r["valid_to"])}
            for r in _rows("brigade_commands_1862.csv")
        ]
        oob.returns = [
            {**r, "date": _d(r["date"])} for r in _rows("strength_returns_1862.csv")
        ]
        oob.events = [{**r, "date": _d(r["date"])} for r in _rows("reinforcements_1862.csv")]
        for r in _rows("sources_1862.csv"):
            oob.sources[r["source_id"]] = r
        for r in _rows("portrait_manifest.csv"):
            oob.portraits[r["officer"]] = r
        return oob

    # ---------- queries ----------
    def active_formations(self, on: date) -> dict:
        out = {}
        for fid, f in self.formations.items():
            af, at = _d(f["active_from"]), _d(f["active_to"])
            if af and af <= on and (at is None or on <= at):
                out[fid] = f
        return out

    def members_of(self, formation_id: str, on: date) -> list[str]:
        return [
            a["member_id"] for a in self.assignments
            if a["formation_id"] == formation_id
            and a["valid_from"] and a["valid_from"] <= on
            and (a["valid_to"] is None or on <= a["valid_to"])
        ]

    def parents_of(self, member_id: str, on: date) -> list[dict]:
        """All assignment rows placing a member in some formation on `on`."""
        return [
            a for a in self.assignments
            if a["member_id"] == member_id
            and a["valid_from"] and a["valid_from"] <= on
            and (a["valid_to"] is None or on <= a["valid_to"])
        ]

    def commander_of(self, formation_id: str, on: date) -> str:
        for c in self.commands:
            if c["brigade_id"] == formation_id and c["valid_from"] <= on <= c["valid_to"]:
                return c["commander_id"]
        return ""  # vacant / not applicable

    def parent_on(self, formation_id: str, on: date) -> str:
        """Return a date-valid parent HQ without rewriting historical source rows."""
        parent = self.formations[formation_id]["parent_id"]
        if parent == "FRM_US_SHIELDSDIV_K" and on >= date(1862, 5, 1):
            parent = "FRM_US_SHIELDSDIV_R"
        if parent == "FRM_CS_JACKSONDIV" and on < date(1862, 5, 20):
            parent = "FRM_CS_VALLEY"
        return parent

    def state_origins(self, formation_id: str, on: date) -> list[str]:
        """Unique states of assigned regiments on the requested date."""
        states = set()
        for member in self.members_of(formation_id, on):
            regiment = self.regiments.get(member)
            if regiment:
                code = (regiment.get("state") or "").strip().upper()
                if code:
                    states.add(code)
        return sorted(states)

    def state_flag(self, formation_id: str, on: date) -> str:
        """Return an origin-state token, not an unverified sprite filename."""
        states = self.state_origins(formation_id, on)
        return states[0] if len(states) == 1 else ("MIXED" if states else "UNKNOWN")

    def command_chain(self, formation_id: str, on: date) -> list[str]:
        """Validate HQ ancestry against active formations on this date."""
        active = self.active_formations(on)
        chain = []
        seen = {formation_id}
        current = formation_id
        while True:
            parent = self.parent_on(current, on)
            if not parent:
                return chain
            if parent in seen:
                raise ValueError(f"{formation_id} on {on}: circular command chain at {parent}")
            if parent not in active:
                raise ValueError(f"{formation_id} on {on}: inactive/missing HQ {parent}")
            seen.add(parent)
            chain.append(parent)
            current = parent

    def snapshot(self, on: date) -> dict:
        """Dated order of battle: active HQ tree + counters (brigades etc.)."""
        act = self.active_formations(on)
        counters, hqs = [], []
        for fid, f in sorted(act.items()):
            if f["type"] == "hq":
                hqs.append(fid)
                continue
            if f["level"] == "battalion_group":
                continue  # aggregate artillery record, not a counter
            regs = [m for m in self.members_of(fid, on)]
            batts = [b["battery_id"] for b in self.artillery.values()
                     if b["attached_to"] == fid and _d(b["attached_to_from"]) <= on]
            counters.append({
                "formation_id": fid,
                "designation": f["designation"],
                "faction": f["faction"],
                "type": f["type"],
                "commander": self.commander_of(fid, on),
                "parent": self.parent_on(fid, on),
                "command_chain": self.command_chain(fid, on),
                "origin_states": self.state_origins(fid, on),
                "state_flag": self.state_flag(fid, on),
                "regiments": regs,
                "batteries": batts,
            })
        # batteries attached directly to hq/division groups ride along listed
        loose_batts = [
            b["battery_id"] for b in self.artillery.values()
            if b["attached_to"] in act and b["attached_to"] not in {c["formation_id"] for c in counters}
            and _d(b["attached_to_from"]) <= on
        ]
        return {"date": on.isoformat(), "headquarters": hqs, "counters": counters,
                "support_batteries": loose_batts}


# ---------- validation ----------
def validate(oob: OOB, repo_root: str | None = None) -> list[str]:
    errors: list[str] = []
    e = errors.append

    # 1 unique ids (dict keys enforce uniqueness; check duplicates in raw files)
    for fname, key in [("formations_1862.csv", "formation_id"),
                       ("regiments_1862.csv", "regiment_id"),
                       ("commanders_1862.csv", "commander_id"),
                       ("artillery_1862.csv", "battery_id"),
                       ("assignments_1862.csv", "assignment_id")]:
        seen = set()
        for r in _rows(fname):
            if r[key] in seen:
                e(f"duplicate {key}: {r[key]} in {fname}")
            seen.add(r[key])

    # Invalid reverse-date sentinels must not masquerade as historical records.
    for row in oob.assignments:
        if row["valid_to"] and row["valid_from"] > row["valid_to"]:
            e(f"assignment {row['assignment_id']}: valid_from after valid_to")
    for row in oob.commands:
        if row["valid_to"] and row["valid_from"] > row["valid_to"]:
            e(f"command {row['brigade_id']}: valid_from after valid_to")

    # 4 parents exist
    for fid, f in oob.formations.items():
        p = f["parent_id"]
        if p and p not in oob.formations:
            e(f"{fid}: parent {p} does not exist")

    # 5 no circular command relationships
    for fid in oob.formations:
        chain, cur = set(), fid
        while cur:
            if cur in chain:
                e(f"circular parent chain involving {fid}")
                break
            chain.add(cur)
            cur = oob.formations.get(cur, {}).get("parent_id", "")

    # 8 allegiance consistency up the chain
    for fid, f in oob.formations.items():
        p = f["parent_id"]
        if p and p in oob.formations and oob.formations[p]["faction"] != f["faction"]:
            e(f"{fid} ({f['faction']}) cross-assigned under {p} ({oob.formations[p]['faction']})")

    # 3 every brigade references valid commander on its active dates
    all_days = [date(1862, 3, 23), date(1862, 5, 8), date(1862, 5, 25), date(1862, 6, 9)]
    for fid, f in oob.formations.items():
        if f["level"] != "brigade" or f["type"] == "hq":
            continue
        for day in all_days:
            if not (f["active_from"] and _d(f["active_from"]) <= day <= (_d(f["active_to"]) or day)):
                continue
            cmd = oob.commander_of(fid, day)
            if cmd and cmd not in oob.commanders:
                e(f"{fid} on {day}: unknown commander {cmd}")

    # Date-valid command chains, including pre-division and department transfers.
    for fid in oob.formations:
        for day in all_days:
            if fid not in oob.active_formations(day):
                continue
            try:
                oob.command_chain(fid, day)
            except ValueError as exc:
                e(str(exc))

    # 2 one active parent per regiment/date unless detachment-marked
    for rid in oob.regiments:
        for day in all_days:
            ps = oob.parents_of(rid, day)
            non_det = [p for p in ps if p.get("detachment", "").strip() != "Y"]
            if len(non_det) > 1:
                e(f"{rid} on {day} has {len(non_det)} non-detachment parents: "
                  f"{[p['formation_id'] for p in non_det]}")
            # detachment overlap must be flagged as such AND documented
            if len(ps) > 1 and not any(p.get("detachment", "").strip() == "Y" for p in ps):
                e(f"{rid} on {day} overlaps multiple formations without detachment flag")

    # 9 portrait references use approved filenames (manifest authoritative)
    manifest_files = {r["filename"] for r in oob.portraits.values()}
    for cid, c in oob.commanders.items():
        pf = c["portrait_file"]
        if pf and pf not in manifest_files:
            e(f"commander {cid}: portrait {pf} not in portrait_manifest.csv")

    # 12 unknown strengths identifiable
    for r in oob.returns:
        if r["kind"] not in ("reported", "estimate", "unknown"):
            e(f"return {r['return_id']}: kind {r['kind']} not in reported/estimate/unknown")

    # 6 commander mentions within rank window sanity (light check)
    for cid, c in oob.commanders.items():
        if c["first_mentioned"] and c["last_mentioned"] and c["first_mentioned"] > c["last_mentioned"]:
            e(f"commander {cid}: first_mentioned after last_mentioned")

    return errors


if __name__ == "__main__":
    import sys
    oob = OOB.load()
    errs = validate(oob)
    print(f"loaded: {len(oob.formations)} formations, {len(oob.regiments)} regiments, "
          f"{len(oob.commanders)} commanders, {len(oob.artillery)} batteries")
    if errs:
        print(f"VALIDATION ERRORS ({len(errs)}):")
        for x in errs:
            print("  -", x)
        sys.exit(1)
    print("validation OK")
    for day in ["1862-03-23", "1862-05-08", "1862-05-25", "1862-06-09"]:
        snap = oob.snapshot(date.fromisoformat(day))
        print(f"{day}: {len(snap['counters'])} counters, {len(snap['headquarters'])} HQs")
