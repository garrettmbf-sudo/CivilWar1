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
  * VP / CP hexes: boxes mirror vp/pp/name/initialControl (neutral VP: boxes[15] = 0, as
    secondbullrun1862 / chancellorsville1863); named non-VP hexes: boxes[9] = name (antietam)
  * meta.boardArt (v2): same geometry fields/values as antietam1862's, image decodes to the size the
    grid implies, transparent outside the board, hash = SHA-1 of the PNG (our assumption)
  * victory thresholds (v3.5): winLine is the status quo, thresholds are 5/40/80% of the scarcer
    side's room past the line, and each side can reach each threshold; elite units even per side
  * v3.3: standby trigger fields are sane (<= 5 groups a side, containment groups really are
    contained at the start, enemyGroup names an existing opposing group); with replacements on,
    every unit not on the BELOW_3_OK list has CS >= 3; doctrine words are stock words
  * v3.7: exits in secondbullrun1862's form (edge hexes, no VP/CP, per-CS points for that side,
    sudden death 0, unit exitPoints 0); brigade counters share one standby group
  * v3.4: no hex uses terrain the engine never retreats into ("mountain"; "fortress" never retreats),
    and the rear-room test ignores such hexes; crt prints C / retreat / eliminated odds per column,
    1:3-1:1 have >= 4 stand-offs of 6, no AE above a 1, and 1:1 keeps a DR
"""
import base64, hashlib, io, itertools, json, math, os, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
# v3.2: stacks this close to the enemy at the start (cavalry MP 6 + 2) must pass the two-flank test.
FLANK_REACH = 8
# v3.3: units allowed below CS 3 (no replacement on AE/DE): HQs, the cavalry, Chew's 3-gun horse
# battery and the two single regiments.  Everything else must be CS >= 3.
# v3.6: Brodhead's WV/OH/MD/PA Cav is now 3; Keeper's B 1 WV is one section (Daum, OR 12/1 p.359), 2
BELOW_3_OK = {"Kimball Shields' Div. HQ", "Jackson Valley District HQ", "Ashby 7 VA Cav", "Chew Horse Bty",
              "Brodhead 1 MI Cav", "Keeper B 1 WV Bty", "Sullivan 39 IL", "Burks 42 VA"}
DIRS_EVEN = [(1, 0), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1)]
DIRS_ODD = [(1, 0), (1, 1), (0, 1), (-1, 0), (0, -1), (1, -1)]
# dicts whose keys are data (ids / language codes), not schema
MAPPINGS = {"assets.images", "meta.description", "meta.regionMap.labels[].text", "meta.battleMap.labels[].text",
            "scenario.sideNamesByLang"}

errors, warns = [], []


def err(m):
    errors.append(m)


NO_RETREAT_TERRAIN = {"mountain", "fortress"}


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
    return raw, json.loads(raw.decode("utf-8-sig"))


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
        err("file has a UTF-8 BOM (the brief says no BOM)")
    if len(raw) > 20 * 1024 * 1024:
        err(f"file is {len(raw)/1e6:.1f} MB (> 20 MB)")
    stock = {}
    for f in ("antietam1862", "gainesmill1862", "gettysburg1863", "user_kernstown1862",
              "malvernhill1862", "sevenpines1862", "chancellorsville1863", "secondbullrun1862"):
        fp = os.path.join(refdir, f + ".json")
        if not os.path.exists(fp):
            print(f"  note: stock {f} not in {refdir}")
            continue
        sraw, sd = load(fp)
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
            if b[15] != (0 if h["initialControl"] is None else h["initialControl"] + 1):
                err(f"VP hex {q},{r} boxes[15] != initialControl+1 (0 if neutral)")
        elif h["pp"]["first"] or h["pp"]["second"]:
            if b[16] != f"+{h['pp']['first']}" or b[17] != f"+{h['pp']['second']}":
                err(f"CP hex {q},{r} boxes 16/17 do not mirror pp")
            if b[9] != h["name"]:
                err(f"CP hex {q},{r} boxes[9] != name")
            if h["initialControl"] is not None:
                warn(f"CP hex {q},{r} has initialControl")
        elif h["name"] and b[9] != h["name"]:
            err(f"named hex {q},{r} boxes[9] != name")
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
    stack, ids, sg_use = {}, set(), {}
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
        # v3.2: standbyGroup n is the n-th standby_groups entry OF THE UNIT'S OWN SIDE (malvernhill1862
        # lists [s0, s0, s1, s1, s1] and its side-1 units use 1-3; secondbullrun1862 lists [s1, s0] and
        # both sides use 1).  v3/v3.1 checked the global index and missed that Confederate groups 4/5
        # did not exist; the game loaded them as 0 (playtests 2 and 3).
        sg = u["standbyGroup"]
        own = [g for g in groups if g["side"] == u["side"]]
        if sg:
            if not 1 <= sg <= len(own):
                err(f"unit {u['id']} {u['name']}: standbyGroup {sg} but side {u['side']} has only {len(own)} standby_groups entries")
            else:
                g = own[sg - 1]
                sg_use.setdefault((u["side"], sg), []).append(u["name"])
        if u["entryHex"] or u["entryTurn"]:
            warn(f"unit {u['id']} uses entryHex/entryTurn")
    for h, n in stack.items():
        if n > lim:
            err(f"{n} units on hex {h} (stacking_limit {lim})")
    # v3.3: trigger fields (editor STANDBY FORCE panel): guardHexes = containment range, guardCs =
    # containment strength needed, mainForcePct = joins when main body falls to %, enemyGroup = joins
    # when opposing group n activates (0 = none; per-side numbering assumed).
    def _cube(q, r):
        x = q - (r - (r & 1)) // 2
        return x, -x - r, r
    def _hd(a, b):
        A, B = _cube(*a), _cube(*b)
        return max(abs(A[i] - B[i]) for i in range(3))
    for side in (0, 1):
        own = [g for g in groups if g["side"] == side]
        opp = [g for g in groups if g["side"] != side]
        if len(own) > 5:
            err(f"side {side} has {len(own)} standby groups (editor maximum 5)")
        for i, g in enumerate(own, 1):
            who = sg_use.get((side, i), [])
            if not who:
                warn(f"side {side} standby group {i} has no units")
            if not (0 <= g["chance"] <= 100 and 0 <= g["rise"] <= 100 and 0 <= g["turn"] <= sc["maxTurns"]):
                err(f"side {side} group {i}: turn/chance/rise out of range {g}")
            if g["turn"] == 0 and g["chance"] > 0 or g["turn"] > 0 and g["chance"] == 0 and g["rise"] == 0:
                warn(f"side {side} group {i}: join turn and chance disagree {g}")
            rng, need = g.get("guardHexes", 0), g.get("guardCs", 0)
            trig = []
            if (rng > 0) != (need > 0):
                err(f"side {side} group {i}: containment range {rng} and strength {need} must both be set or both 0")
            elif rng:
                gu = [u for u in sc["units"] if u["side"] == side and u["standbyGroup"] == i]
                en = [u for u in sc["units"] if u["side"] != side]
                per_unit = [sum(e["combatStrength"] for e in en if _hd((u["q"], u["r"]), (e["q"], e["r"])) <= rng) for u in gu]
                union = sum(e["combatStrength"] for e in en if any(_hd((u["q"], u["r"]), (e["q"], e["r"])) <= rng for u in gu))
                if min(per_unit) < need or union < need:
                    err(f"side {side} group {i}: containment {need} CS within {rng} hexes is already short at the "
                        f"start (per unit {per_unit}, group {union}) -- it would activate on turn 1")
                trig.append(f"containment {rng} hexes/{need} CS (start: {union})")
            mp = g.get("mainForcePct", 0)
            if not 0 <= mp < 100:
                err(f"side {side} group {i}: mainForcePct {mp} not in 0..99")
            elif mp:
                trig.append(f"main body <= {mp}%")
            eg = g.get("enemyGroup", 0)
            if eg:
                if not 1 <= eg <= len(opp):
                    err(f"side {side} group {i}: enemyGroup {eg} but the other side has {len(opp)} groups")
                elif not sg_use.get((1 - side, eg)):
                    err(f"side {side} group {i}: enemyGroup {eg} has no units")
                else:
                    trig.append(f"enemy group {eg} wakes")
            kind = "hold" if g["turn"] == 0 and g["chance"] == 0 else f"turn {g['turn']} {g['chance']}%+{g['rise']}"
            print(f"  standby side {side} group {i} ({kind}{'; ' + ', '.join(trig) if trig else ''}): {', '.join(who)}")
    # v3.3: replacements need CS >= 3
    if rules.get("replacement"):
        low = [u["name"] for u in sc["units"] if u["combatStrength"] < 3]
        bad = [n for n in low if n not in BELOW_3_OK]
        if bad:
            err(f"replacements on, but these units are below CS 3 and get no replacement: {bad}")
        ok = len(sc["units"]) - len(low)
        print(f"  replacements on: {ok} of {len(sc['units'])} units are CS >= 3; below 3 by design: {', '.join(low)}")
    # v3.7: withdrawal exits, in secondbullrun1862's format.  exit_points_per_cs and
    # exit_sudden_death_cs are {first, second} dicts; exit hexes lie on the board edge, are passable,
    # carry no VP/CP; every unit keeps exitPoints 0 (as every stock file); sudden death on exits is 0
    # (its meaning is undocumented); a side with exit hexes has exit points and vice versa.
    sbr = stock.get("secondbullrun1862", {}).get("scenario", {}).get("rules", {})
    for k in ("exit_points_per_cs", "exit_sudden_death_cs"):
        if k in rules:
            v = rules[k]
            if not (isinstance(v, dict) and set(v) == {"first", "second"}) or not isinstance(sbr.get(k), dict):
                err(f"rules.{k} = {v!r} is not in secondbullrun1862's {{first, second}} form")
    if any(rules.get("exit_sudden_death_cs", {}).values()):
        err("rules.exit_sudden_death_cs is not 0: its meaning is undocumented (DEV_WISHLIST)")
    exits = {k: [] for k in ("first", "second")}
    for (q, r), h in H.items():
        for k, on in h.get("exitHex", {}).items():
            if on:
                exits[k].append((q, r))
                if not (q in (0, W - 1) or r in (0, Hh - 1)):
                    err(f"exit hex {q},{r} ({k}) is not on the board edge")
                if h["isVPLocation"] or any(h["pp"].values()):
                    err(f"exit hex {q},{r} carries VP or CP")
                if terr[h["terrainId"]].get("moveCost", 1) >= 99:
                    err(f"exit hex {q},{r} is impassable")
    per = rules.get("exit_points_per_cs", {})
    per = per if isinstance(per, dict) else {}
    for k in ("first", "second"):
        if bool(exits[k]) != bool(per.get(k)):
            err(f"{k} side: {len(exits[k])} exit hexes but exit_points_per_cs {per.get(k)}")
    if any(u.get("exitPoints") for u in sc["units"]):
        err("units[].exitPoints is not 0 on every unit (no stock file sets it)")
    for k in ("first", "second"):
        if exits[k]:
            print(f"  exits {k} side ({sc['sideNames'][0 if k == 'first' else 1]}): {per.get(k)} point(s) per CS, "
                  f"hexes {sorted(exits[k])}")
    # v3.7: brigade cohesion.  Counters of one brigade (same commander, HQs and batteries aside, which
    # are held on purpose) share one standby group, so the AI moves the brigade as a body.
    brig = {}
    for u in sc["units"]:
        if "HQ" in u["name"] or u.get("range", 1) > 1:
            continue
        brig.setdefault((u["side"], u["boxes"][3]), set()).add(u.get("standbyGroup", 0))
    for (side, ldr), gs in sorted(brig.items()):
        if len(gs) > 1:
            err(f"side {side} brigade {ldr} is split across standby groups {sorted(gs)}")
    print(f"  cohesion: {len(brig)} brigades, each in one standby group")
    seen_doc = {st["doctrine"][k] for nm, st in stock.items() if not nm.startswith("user_") and "doctrine" in st for k in ("blue", "red")}
    for k in ("blue", "red"):
        if d["doctrine"][k] not in seen_doc:
            err(f"doctrine.{k} = {d['doctrine'][k]!r} is not a word any stock file uses ({sorted(seen_doc)})")
    # ---- boardArt
    ba = d["meta"].get("boardArt")
    if ba is not None:
        sba = stock["antietam1862"]["meta"]["boardArt"]
        for k in ("version", "style", "scale", "hexSize", "originX", "originY", "grid", "gridAlpha"):
            if ba.get(k) != sba.get(k):
                warn(f"boardArt.{k} = {ba.get(k)!r}, antietam has {sba.get(k)!r}")
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        png = base64.b64decode(ba["image"].split(",", 1)[1])
        im = Image.open(io.BytesIO(png))
        R, bsc = ba["hexSize"], ba["scale"]
        ew = round((math.sqrt(3) * R * (W + 0.5) - math.sqrt(3) * R / 2 - 2 * ba["originX"] - math.sqrt(3) * R / 2) * bsc)
        eh = round((1.5 * R * (Hh - 1) + R - 2 * ba["originY"] - R) * bsc)
        if abs(im.width - ew) > 2 or abs(im.height - eh) > 2:
            err(f"boardArt image {im.size} != expected ~({ew}, {eh}) for {W}x{Hh} hexes")
        a = im.convert("RGBA")
        if a.getpixel((0, 0))[3] != 0:
            warn("boardArt corner pixel is opaque (stock is transparent outside the board)")
        if ba["hash"] != hashlib.sha1(png).hexdigest():
            warn("boardArt.hash is not the SHA-1 of the image (meaning of stock hash unknown)")
        print(f"  boardArt {im.size} {im.mode}, {len(png)/1e6:.2f} MB PNG")
        # v3.6: the painted stone wall lies on every fenced hexside.  Sample t = 0.25/0.5/0.75 along
        # each fence edge (pixel = (world - origin) * scale, world centre (sqrt3*R*(q + (r&1)/2),
        # 1.5*R*r)); a wall colour (limestone 226,224,216 or mortar 150,146,136, +-14 per channel)
        # must lie within 12 px of each sample.
        import numpy as np
        arr = np.asarray(a)[..., :3].astype(int)
        WALL = [(226, 224, 216), (150, 146, 136)]
        def wall_near(x, y, rad=12):
            x0, y0 = int(x) - rad, int(y) - rad
            sub = arr[max(0, y0):y0 + 2 * rad + 1, max(0, x0):x0 + 2 * rad + 1]
            return any((np.abs(sub - np.array(c)).max(axis=2) <= 14).any() for c in WALL)
        nfe = nmiss = 0
        for (q, r), h in H.items():
            for e in h["fences"]:
                cx, cy = math.sqrt(3) * R * (q + 0.5 * (r & 1)), 1.5 * R * r
                c0 = (cx + R * math.cos(math.radians(60 * e - 30)), cy + R * math.sin(math.radians(60 * e - 30)))
                c1 = (cx + R * math.cos(math.radians(60 * e + 30)), cy + R * math.sin(math.radians(60 * e + 30)))
                nfe += 1
                for t in (0.25, 0.5, 0.75):
                    wx, wy = c0[0] + (c1[0] - c0[0]) * t, c0[1] + (c1[1] - c0[1]) * t
                    px, py = (wx - ba["originX"]) * bsc, (wy - ba["originY"]) * bsc
                    if not wall_near(px, py):
                        nmiss += 1
                        err(f"boardArt: no stone wall drawn near fenced hexside {q},{r} edge {e} at t={t} (px {px:.0f},{py:.0f})")
        print(f"  boardArt stone wall: {nfe} fenced hexsides x 3 samples, {nmiss} missing")
    # ---- v3: retreat rules use stock values only; crt shape/values/monotonic
    for k in ("retreat_control", "retreat_distance", "zoc_exit_allowed", "full_move_entry_allowed", "replacement"):
        seen = {json.dumps(st["scenario"]["rules"].get(k)) for nm, st in stock.items() if not nm.startswith("user_") if k in st["scenario"]["rules"]}
        if json.dumps(rules.get(k)) not in seen:
            err(f"rules.{k} = {rules.get(k)!r} is not a value any stock file uses ({sorted(seen)})")
    if "crt" in rules:
        crt = rules["crt"]
        stock_vals = {v for nm, st in stock.items() if not nm.startswith("user_") for row in st["scenario"]["rules"].get("crt", []) for v in row}
        rank = {"AE": 0, "AR": 1, "C": 2, "DR": 3, "DE": 4}
        if len(crt) != 8 or any(len(r) != 6 for r in crt):
            err("crt is not 8 rows x 6 columns (stock shape)")
        elif any(v not in stock_vals for r in crt for v in r):
            err(f"crt has values outside the stock set {sorted(stock_vals)}")
        else:
            for i in range(8):
                for j in range(6):
                    if j and rank[crt[i][j]] < rank[crt[i][j - 1]]:
                        err(f"crt row {i}: die {j + 1} worse for the attacker than die {j}")
                    if i and rank[crt[i][j]] < rank[crt[i - 1][j]]:
                        err(f"crt die {j + 1}: odds row {i} worse for the attacker than row {i - 1}")
            flat = [v for r in crt for v in r]
            print(f"  crt: AE {flat.count('AE')}, AR {flat.count('AR')}, C {flat.count('C')}, DR {flat.count('DR')}, DE {flat.count('DE')}")
            # v3.4: per-column outcome odds; a forced attack at 1:3-1:1 should usually stall
            names = ["1:3", "1:2", "1:1", "2:1", "3:1", "4:1", "5:1", "6:1"]
            for i, r in enumerate(crt):
                p = {k: r.count(k) / 6 for k in ("C", "AR", "DR", "AE", "DE")}
                print(f"    {names[i]}: C {p['C']:.0%}  retreat {p['AR'] + p['DR']:.0%} (AR {p['AR']:.0%}, DR {p['DR']:.0%})"
                      f"  eliminated {p['AE'] + p['DE']:.0%}")
                if i <= 2 and r.count("C") < 4:
                    err(f"crt {names[i]}: only {r.count('C')}/6 stand-offs; a forced attack at poor odds should usually stall")
                if i <= 2 and "AE" in r[1:]:
                    err(f"crt {names[i]}: AE on a roll above 1")
            if "DR" not in crt[2]:
                err("crt: no DR at 1:1, so a held wall could never be taken at even odds")
    # ---- v3.4: the engine never retreats a unit into "mountain".  Replaying playtests 2-4, 0 of 33
    # retreats ended in a mountain hex, and 9 units died whose only open retreat hexes were mountain.
    # (A unit in a "fortress" hex never retreats at all; playtest 2.)  Neither may appear on this board.
    terr_by_id = {t["id"]: t for t in d["assets"]["terrains"]}
    bad = Counter(h["terrainId"] for h in hexes if h["terrainId"] in NO_RETREAT_TERRAIN)
    if bad:
        err(f"hexes use terrain that blocks retreats: {dict(bad)}")
    # ---- v3: every starting stack has >= 2 open hexes to fall back into
    Hx = {(h["q"], h["r"]): h for h in hexes}
    def cube(q, r):
        x = q - (r - (r & 1)) // 2
        return x, -x - r, r
    def hd(a, b):
        A, B = cube(*a), cube(*b)
        return max(abs(A[i] - B[i]) for i in range(3))
    occ = {}
    for u in sc["units"]:
        occ.setdefault((u["q"], u["r"]), []).append(u)
    rooms, flank_ok, pairs_out = [], [], []
    for hx, us in sorted(occ.items()):
        side = us[0]["side"]
        enemy = [k for k, v in occ.items() if v[0]["side"] != side]
        ezoc = {nb(*e, k) for e in enemy for k in range(6)}
        d0 = min(hd(hx, e) for e in enemy)
        room = []
        for k in range(6):
            n = nb(*hx, k)
            if n not in Hx or terr_by_id.get(Hx[n]["terrainId"], {}).get("moveCost", 1) >= 99 \
                    or Hx[n]["terrainId"] in NO_RETREAT_TERRAIN:
                continue
            if n in ezoc or (n in occ and (occ[n][0]["side"] != side or len(occ[n]) >= lim)):
                continue
            if min(hd(n, e) for e in enemy) > d0:   # strictly farther from every enemy unit
                room.append(n)
        if len(room) < 2:
            err(f"stack at {hx} ({', '.join(u['name'] for u in us)}) has {len(room)} open rear hexes (< 2)")
        rooms.append(len(room))
        # v3.2 two-flank test, for stacks within FLANK_REACH hexes of the enemy at the start: an enemy
        # unit could stand on any ring hex that is on the board, passable, not friendly and not a rear
        # hex.  For every pair of such hexes, at least one rear hex must stay outside both their ZOCs
        # (and not be one of them), so two flankers cannot close the retreat by themselves.
        rear = {nb(*hx, k) for k in range(6)}
        rear = [n for n in rear if n in Hx and terr_by_id.get(Hx[n]["terrainId"], {}).get("moveCost", 1) < 99
                and Hx[n]["terrainId"] not in NO_RETREAT_TERRAIN
                and not (n in occ and (occ[n][0]["side"] != side or len(occ[n]) >= lim))
                and min(hd(n, e) for e in enemy) > d0]
        ring = [nb(*hx, k) for k in range(6)]
        cand = [n for n in ring if n in Hx and terr_by_id.get(Hx[n]["terrainId"], {}).get("moveCost", 1) < 99
                and n not in rear and not (n in occ and occ[n][0]["side"] == side)]
        if d0 <= FLANK_REACH:
            pairs = list(itertools.combinations(cand, 2)) or [(c, c) for c in cand]
            for a, b2 in pairs:
                z = {a, b2} | {nb(*a, k) for k in range(6)} | {nb(*b2, k) for k in range(6)}
                if not [n for n in room if n not in z]:
                    err(f"stack at {hx} ({', '.join(u['name'] for u in us)}): enemy units on {a} and {b2} "
                        f"would close every rear hex")
                    break
            else:
                flank_ok.append(hx)
        # v3.2: every battery (range > 1) starts with exactly one non-battery unit, never two guns alone
        guns = [u for u in us if u["range"] > 1]
        if guns:
            others = [u for u in us if u["range"] <= 1]
            if len(guns) > 1:
                err(f"stack at {hx}: {len(guns)} batteries together ({', '.join(u['name'] for u in guns)})")
            elif not others:
                err(f"battery {guns[0]['name']} at {hx} starts without a supporting unit")
            else:
                pairs_out.append(f"{guns[0]['name']} + {others[0]['name']}")
    print(f"  rear room: every stack has >= {min(rooms)} open rear hexes (on board, passable, not enemy ZOC, "
          f"stack space, strictly farther from the nearest enemy unit)")
    print(f"  two-flank test: {len(flank_ok)} stacks within {FLANK_REACH} hexes of the enemy pass")
    print(f"  batteries: " + "; ".join(pairs_out))
    # ---- thresholds: status-quo winLine, 5/40/80% of the scarcer side's room (v3.5)
    vc = d["victoryCondition"]
    vps = sum(h["vp"]["first"] for h in hexes)
    cs = [sum(u["combatStrength"] for u in sc["units"] if u["side"] == k) for k in (0, 1)]
    total = vps + sum(cs) / 2
    guide = (round(0.05 * total), round(0.4 * total), round(0.8 * total))
    got = (vc["tacticalThreshold"], vc["operationalThreshold"], vc["strategicThreshold"])
    # v3.5: winLine must be the status quo (Union-held VP minus Confederate-held VP at the start)
    held = [sum(h["vp"]["first"] for h in hexes if h["isVPLocation"] and h["initialControl"] == k) for k in (0, 1)]
    if vc["winLine"] != held[0] - held[1]:
        err(f"winLine {vc['winLine']} is not the status quo {held[0]} - {held[1]} = {held[0] - held[1]}")
    # best case for each side relative to winLine: every objective held, the enemy destroyed, no losses
    best = {0: vps + cs[1] - vc["winLine"], 1: vps + cs[0] + vc["winLine"]}
    # v3.5: 5/40/80% of the scarcer side's room past the line (the editor's guidance total assumes a
    # line near the middle; ours is the status quo, so the guidance strategic was out of the Union's reach)
    room = min(best.values())
    want = (round(0.05 * room), round(0.4 * room), round(0.8 * room))
    if got != want:
        err(f"thresholds {got} differ from 5/40/80% of the scarcer side's room {room} = {want}")
    for k, nm in ((0, "tactical"), (1, "operational"), (2, "strategic")):
        cant = [str(sd) for sd in (0, 1) if best[sd] < got[k]]
        if cant:
            err(f"side {'/'.join(cant)} cannot reach a {nm} victory ({got[k]}; best possible {[best[int(c)] for c in cant]})")
    print(f"  victory: winLine {vc['winLine']} (status quo U {held[0]} - C {held[1]}), thresholds {got} = 5/40/80% of "
          f"room {room}; best margin past the line U {best[0]} / C {best[1]}; editor-guidance total {total:g} "
          f"(VP {vps} + avg CS {sum(cs)/2:g}) would give {guide}")
    # v3.5: elite (surprise) units, one round per side: report and keep the two sides even
    el = {k: [u for u in sc["units"] if u["side"] == k and u["eliteUnit"]] for k in (0, 1)}
    share = {k: sum(u["combatStrength"] for u in el[k]) / cs[k] for k in (0, 1)}
    for k in (0, 1):
        print(f"  elite side {k}: {len(el[k])} units, CS {sum(u['combatStrength'] for u in el[k])} "
              f"({100 * share[k]:.0f}% of {cs[k]}): " + ", ".join(u["name"] for u in el[k]))
    if bool(el[0]) != bool(el[1]):
        err("eliteUnit set on one side only")
    if el[0] and (abs(len(el[0]) - len(el[1])) > 1 or abs(share[0] - share[1]) > 0.10):
        err("elite units uneven between the sides (unit count differs by > 1 or CS share by > 10 points)")
    # v3.9 counter style (opt-in): the elite frame and star sit on exactly the eliteUnit counters
    if any(k.startswith("img_v39_") for k in d["assets"]["images"]):
        refs = {t["id"]: {s.get("imageRef") for s in t["visuals"]["shapes"]} for t in d["assets"]["unitTemplates"]}
        frame = {k for k, v in refs.items() if "img_v39_elite_frame" in v}
        star = {k for k, v in refs.items() if "img_v39_star" in v}
        elite_t = {u["templateId"] for u in sc["units"] if u["eliteUnit"]}
        if not frame == star == elite_t:
            err(f"v3.9 elite marks {sorted(frame)} / {sorted(star)} != eliteUnit counters {sorted(elite_t)}")
        print(f"  v3.9 counters: elite frame + star on {len(frame)} counters, matching eliteUnit")
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
