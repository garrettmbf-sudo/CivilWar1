#!/usr/bin/env python3
"""Validate a Must Attack scenario JSON against the stock scenarios.

Checks (exit 1 on any ERROR):
  * file parses, no UTF-8 BOM, size < 20 MB
  * schema key-for-key: every key we write was seen at the same path in a stock file, every key
    present in all Antietam-schema stock files is present, and value types match stock types
  * grid convention probe on the stock files (odd-r, edges 0=E clockwise: roads/rivers symmetric)
  * hex list: count = width*height, row-major order, id "q-r", q/r in range
  * roads / rivers / trails symmetric across shared edges; hasRoad/hasRiver flags consistent;
    fences one-sided (as stock) and pointing at an on-board neighbour
  * units: on board, on a non-impassable terrain, <= stacking_limit per hex, unique ids,
    boxes mirror the unit fields, standbyGroup indexes rules.standby_groups (1-based)
  * every templateId, imageRef and terrainId resolves
  * VP / CP hexes: boxes mirror vp/pp/name/initialControl
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIRS_EVEN = [(1, 0), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1)]
DIRS_ODD = [(1, 0), (1, 1), (0, 1), (-1, 0), (0, -1), (1, -1)]
# dicts whose keys are data (ids / language codes), not schema
MAPPINGS = {"assets.images", "meta.description", "meta.regionMap.labels[].text", "meta.battleMap.labels[].text",
            "scenario.sideNamesByLang"}

errors, warns = [], []


def err(m):
    errors.append(m)


def warn(m):
    warns.append(m)


def nb(q, r, e):
    dq, dr = (DIRS_ODD if r & 1 else DIRS_EVEN)[e]
    return q + dq, r + dr


def tname(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "num"
    return type(v).__name__


def walk(v, path, out):
    """out[path] = (set of key-sets seen, set of types seen)"""
    ks, ts = out.setdefault(path, (set(), set()))
    ts.add(tname(v))
    if isinstance(v, dict):
        if path in MAPPINGS:
            for x in v.values():
                walk(x, path + ".*", out)
        else:
            ks.add(frozenset(v))
            for k, x in v.items():
                walk(x, f"{path}.{k}" if path else k, out)
    elif isinstance(v, list):
        for x in v:
            walk(x, path + "[]", out)


def load(p):
    raw = open(p, "rb").read()
    return raw, json.loads(raw.decode("utf-8"))


def _alt_dirs():
    """Candidate conventions: (name, fn(q, r, e) -> neighbour). Ours first."""
    ev_r = [(1, 0), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1)]      # even-r rows, clockwise from E
    od_r = [(1, 0), (1, 1), (0, 1), (-1, 0), (0, -1), (1, -1)]
    def rows(odd_shift):
        return lambda q, r, e: tuple(map(sum, zip((q, r), ((od_r if r & 1 else ev_r) if odd_shift else (ev_r if r & 1 else od_r))[e])))
    def ccw(f):
        return lambda q, r, e: f(q, r, (6 - e) % 6)
    return [("odd-r, cw from E (ours)", rows(True)), ("even-r, cw from E", rows(False)),
            ("odd-r, ccw from E", ccw(rows(True))), ("even-r, ccw from E", ccw(rows(False)))]


def check_stock_grid(stock):
    """Probe: under the right convention stock roads/rivers are (almost) all mirrored on the neighbour.
    Edges that run off the board are excluded; the few left are stock authoring slips."""
    for name, d in stock.items():
        if name == "user_kernstown1862":
            continue  # hand-made, roads asymmetric by construction
        H = {(h["q"], h["r"]): h for h in d["scenario"]["map"]["hexes"]}
        rates = []
        for cname, f in _alt_dirs():
            tot = bad = 0
            for (q, r), h in H.items():
                for key in ("roads", "rivers"):
                    for e in h.get(key) or []:
                        n = H.get(f(q, r, e))
                        if n is None:
                            continue
                        tot += 1
                        bad += (e + 3) % 6 not in (n.get(key) or [])
            rates.append((bad / max(tot, 1), cname, bad, tot))
        best = min(rates)
        print(f"  grid probe {name}: " + "; ".join(f"{c} {b}/{t}" for _, c, b, t in rates))
        if best[1] != rates[0][1] or rates[0][0] > 0.05:
            err(f"stock grid probe on {name}: our convention is not the best fit")


def main(path, refdir):
    raw, d = load(path)
    if raw.startswith(b"\xef\xbb\xbf"):
        err("file has a UTF-8 BOM; no stock file does")
    if len(raw) > 20 * 1024 * 1024:
        err(f"file is {len(raw)/1e6:.1f} MB (> 20 MB)")
    stock = {}
    for f in ("antietam1862", "gainesmill1862", "gettysburg1863", "user_kernstown1862"):
        sraw, sd = load(os.path.join(refdir, f + ".json"))
        if sraw.startswith(b"\xef\xbb\xbf"):
            print(f"  note: stock {f} has a BOM")
        stock[f] = sd
    print("grid convention:")
    check_stock_grid(stock)

    # ---- schema
    allowed, required = {}, None
    for f, sd in stock.items():
        o = {}
        walk(sd, "", o)
        for p, (ks, ts) in o.items():
            a = allowed.setdefault(p, [set(), set()])
            for k in ks:
                a[0] |= k
            a[1] |= ts
        if f in ("antietam1862", "gainesmill1862", "user_kernstown1862"):  # same schema as ours
            req = {p: set.intersection(*[set(k) for k in ks]) if ks else set() for p, (ks, ts) in o.items()}
            required = req if required is None else {p: required[p] & req[p] for p in required if p in req}
    ours = {}
    walk(d, "", ours)
    for p, (ks, ts) in ours.items():
        if p not in allowed:
            err(f"schema: path {p!r} not present in any stock file")
            continue
        okeys = set().union(*ks) if ks else set()
        extra = okeys - allowed[p][0]
        if extra:
            err(f"schema: {p!r} has keys not in stock: {sorted(extra)}")
        miss = set().union(*[required.get(p, set()) - k for k in ks]) if ks else set()
        if miss:
            err(f"schema: {p!r} missing keys present in every stock file: {sorted(miss)}")
        badt = ts - allowed[p][1]
        if badt:
            err(f"schema: {p!r} has types {sorted(badt)}, stock has {sorted(allowed[p][1])}")
    for p in required:
        if p and p not in ours and "[]" not in p and ".*" not in p and required.get(p.rsplit(".", 1)[0] if "." in p else "", None) is not None:
            parent = p.rsplit(".", 1)[0] if "." in p else ""
            if parent in ours and p.rsplit(".", 1)[-1] in required.get(parent, set()):
                err(f"schema: missing required path {p!r}")
    # list-element shapes that only one stock file shows: say so
    for p in ("scenario.rules.activation_steps.first[]", "scenario.rules.night_turns[]"):
        if p in ours:
            who = [f for f, sd in stock.items() if p in (lambda o: (walk(sd, "", o), o)[1])({})]
            print(f"  note: {p} has stock examples only in {who}")

    # ---- map
    sc = d["scenario"]
    m = sc["map"]
    W, Hh = m["width"], m["height"]
    hexes = m["hexes"]
    if len(hexes) != W * Hh:
        err(f"hex count {len(hexes)} != {W}x{Hh}")
    H = {}
    for i, h in enumerate(hexes):
        q, r = h["q"], h["r"]
        if (q, r) != (i % W, i // W):
            err(f"hex #{i} is {q},{r}; expected row-major {i % W},{i // W}")
        if h["id"] != f"{q}-{r}":
            err(f"hex id {h['id']} != {q}-{r}")
        if (q, r) in H:
            err(f"duplicate hex {q},{r}")
        H[(q, r)] = h
    terr = {t["id"]: t for t in d["assets"]["terrains"]}
    nsym = 0
    for (q, r), h in H.items():
        if h["terrainId"] not in terr:
            err(f"hex {q},{r}: terrainId {h['terrainId']} unresolved")
        for key in ("roads", "rivers", "trails"):
            for e in h[key]:
                if not 0 <= e <= 5:
                    err(f"hex {q},{r} {key} edge {e} out of range")
                    continue
                n = H.get(nb(q, r, e))
                if n is None:
                    err(f"hex {q},{r} {key} edge {e} leads off board")
                elif (e + 3) % 6 not in n[key]:
                    err(f"hex {q},{r} {key} edge {e} not mirrored on {n['id']}")
                else:
                    nsym += 1
            if len(set(h[key])) != len(h[key]):
                err(f"hex {q},{r} duplicate {key} edges")
        if h["hasRoad"] != bool(h["roads"] or h["trails"]) and h["hasRoad"] != bool(h["roads"]):
            err(f"hex {q},{r} hasRoad flag inconsistent")
        if h["hasRiver"] != bool(h["rivers"]):
            err(f"hex {q},{r} hasRiver flag inconsistent")
        for e in h["fences"]:
            if H.get(nb(q, r, e)) is None:
                err(f"hex {q},{r} fence edge {e} faces off board")
            elif (e + 3) % 6 in H[nb(q, r, e)]["fences"]:
                warn(f"hex {q},{r} fence edge {e} is two-sided (stock fences are one-sided)")
        b = h["boxes"]
        if len(b) != 20:
            err(f"hex {q},{r} boxes length {len(b)}")
        if h["isVPLocation"]:
            if b[9] != h["name"] or b[10] != h["vp"]["first"] or b[11] != h["vp"]["second"]:
                err(f"VP hex {q},{r} boxes 9-11 do not mirror name/vp")
            if b[15] != h["initialControl"] + 1:
                err(f"VP hex {q},{r} boxes[15] != initialControl+1")
        elif h["pp"]["first"] or h["pp"]["second"]:
            if b[16] != f"+{h['pp']['first']}" or b[17] != f"+{h['pp']['second']}":
                err(f"CP hex {q},{r} boxes 16/17 do not mirror pp")
    print(f"  {len(H)} hexes, {nsym} symmetric road/river/trail edge pairs (counted per side)")

    # ---- assets
    imgs = d["assets"]["images"]
    tmpl = {t["id"]: t for t in d["assets"]["unitTemplates"]}
    for t in tmpl.values():
        for s in t["visuals"]["shapes"]:
            if s["type"] == "image" and s["imageRef"] not in imgs:
                err(f"template {t['id']}: imageRef {s['imageRef']} unresolved")
    for k, v in imgs.items():
        if not (isinstance(v, str) and v.startswith("data:image/png;base64,")):
            err(f"image {k} is not a PNG data URL")

    # ---- units
    rules = sc["rules"]
    lim = rules["stacking_limit"]
    groups = rules["standby_groups"]
    stack, ids = {}, set()
    for u in sc["units"]:
        q, r = u["q"], u["r"]
        if u["id"] in ids:
            err(f"duplicate unit id {u['id']}")
        ids.add(u["id"])
        if (q, r) not in H:
            err(f"unit {u['id']} {u['name']} off board at {q},{r}")
            continue
        t = terr[H[(q, r)]["terrainId"]]
        if t.get("moveCost", 1) >= 99:
            err(f"unit {u['id']} on impassable terrain")
        stack[(q, r)] = stack.get((q, r), 0) + 1
        if u["templateId"] not in tmpl:
            err(f"unit {u['id']} templateId {u['templateId']} unresolved")
        if u["side"] not in (0, 1):
            err(f"unit {u['id']} side {u['side']}")
        b = u["boxes"]
        if [b[0], b[2], b[5], b[6], b[7]] != [u["side"], u["id"], u["combatStrength"], u["movePoints"], u["range"]]:
            err(f"unit {u['id']} boxes do not mirror side/id/CS/MP/range")
        sg = u["standbyGroup"]
        if sg:
            if not 1 <= sg <= len(groups):
                err(f"unit {u['id']} standbyGroup {sg} has no rules.standby_groups entry")
            elif groups[sg - 1]["side"] != u["side"]:
                err(f"unit {u['id']} standbyGroup {sg} belongs to the other side")
        if u["entryHex"] or u["entryTurn"]:
            warn(f"unit {u['id']} uses entryHex/entryTurn")
    for h, n in stack.items():
        if n > lim:
            err(f"{n} units on hex {h} (stacking_limit {lim})")
    vc = d["victoryCondition"]
    if not vc["tacticalThreshold"] < vc["operationalThreshold"] < vc["strategicThreshold"]:
        err("victory thresholds not increasing")
    if sc["turnClock"] and sc["turnClock"][0]["turn"] != 1:
        err("turnClock does not start at turn 1")
    for n in rules["night_turns"]:
        if not 1 <= n <= sc["maxTurns"]:
            err(f"night turn {n} outside 1..maxTurns")

    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{'FAIL' if errors else 'PASS'}: {len(errors)} errors, {len(warns)} warnings ({path}, {len(raw)/1e6:.2f} MB)")
    return 1 if errors else 0


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "mKernstown1862_CW1.json")
    ref = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "ref")
    sys.exit(main(p, ref))
