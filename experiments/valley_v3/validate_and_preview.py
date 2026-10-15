#!/usr/bin/env python3
"""Portable geometry audit/preview for build_valley_map_v3.ps1.
No game assemblies, BinaryFormatter, third-party files, or write to workshop.
The script reads the PS waypoint data (single source of truth) and mirrors
its even-q interpolation/terrain precedence; PNG is a schematic preview.
"""
import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H = 125, 130
TERRAIN_COLORS = {
    0: '#c6c4b9', 1: '#9f8173', 2: '#d7a97d', 3: '#6d936b',
    4: '#e9ddb0', 5: '#3c8dc1', 6: '#c69a63', 7: '#fff2d2',
    8: '#79716c', 9: '#b9bf88', 10: '#dfe1b9', 11: '#d7b15e',
}


def parse_script(path):
    src = Path(path).read_text(encoding='utf-8-sig')
    src = re.sub(r'(?m)#.*$', '', src)
    arrays = {}
    for key, body in re.findall(r'(?ms)^\$(\w+)\s*=\s*@\((.*?)\)', src):
        if '@{' in body:
            continue
        body = re.sub(r'#.*', '', body)
        if re.fullmatch(r'[\d,\s-]*', body):
            nums = [int(n) for n in re.findall(r'-?\d+', body)]
            if nums and len(nums) % 2 == 0:
                arrays[key] = list(zip(nums[::2], nums[1::2]))
    array_of_tables = {}
    for key, body in re.findall(r'(?ms)^\$(\w+)\s*=\s*@\((.*?)\)', src):
        if '@{' not in body:
            continue
        entries = []
        for m in re.findall(r'@\{(.*?)\}', body, flags=re.S):
            d = {}
            for k, v in re.findall(r'(\w+)\s*=\s*("[^"]*"|\$true|\$false|-?\d+)', m):
                if v.startswith('"'):
                    d[k] = v[1:-1]
                elif v == '$true':
                    d[k] = True
                elif v == '$false':
                    d[k] = False
                else:
                    d[k] = int(v)
            if 'X' in d and 'Y' in d:
                entries.append(d)
        if entries:
            array_of_tables[key] = entries
    return arrays, array_of_tables


def offset_to_cube(p):
    x, y = p
    q = x
    r = y - math.floor((x + 1) / 2)
    return q, r, -q-r


def cube_to_offset(q, r):
    return int(q), int(r + math.floor((q + 1) / 2))


def cube_round(a, b, c):
    qa, rb, sc = round(a), round(b), round(c)
    diffs = (abs(qa-a), abs(rb-b), abs(sc-c))
    if diffs[0] > diffs[1] and diffs[0] > diffs[2]:
        qa = -rb-sc
    elif diffs[1] > diffs[2]:
        rb = -qa-sc
    else:
        sc = -qa-rb
    return qa, rb, sc


def line(p1, p2):
    a, b = offset_to_cube(p1), offset_to_cube(p2)
    n = max(abs(b[k] - a[k]) for k in range(3))
    if n == 0:
        return [p1]
    route = []
    for i in range(n+1):
        t = i/n
        curr = cube_to_offset(*cube_round(*[a[k]+t*(b[k]-a[k]) for k in range(3)])[:2])
        if not route or route[-1] != curr:
            route.append(curr)
    return route


def trace(waypoints):
    coords = []
    for a, b in zip(waypoints, waypoints[1:]):
        coords.extend(line(a, b))
    return {(x, y) for x, y in coords if 0 <= x < W and 0 <= y < H}


def interp(ridge, y):
    if y < ridge[0][1] or y > ridge[-1][1]:
        return None
    for (x1,y1),(x2,y2) in zip(ridge, ridge[1:]):
        if y1 <= y <= y2:
            if y2 == y1:
                return x1
            # .NET [int] casts ties to even
            return round(x1+(y-y1)/(y2-y1)*(x2-x1))
    return None


def near_gap(x, y, gaps):
    return any(abs(x-g['X']) <= g['R'] and abs(y-g['Y']) <= g['R'] for g in gaps)


def neighbors(p):
    x,y = p
    odd = x % 2
    offsets = ((0,-1),(1,-1 if odd else 0),(1,0 if odd else 1),(0,1),(-1,0 if odd else 1),(-1,-1 if odd else 0))
    return {(x+dx, y+dy) for dx,dy in offsets}


def path_gaps(points, traversable):
    return sum(not (neighbors(p) & (points & traversable)) for p in points)  # isolated tiles, not graph fragmentation


def build(arrays, tabs):
    required = ['blueRidge','massanutten','northMtn','allegheny','valleyPike','rrVirginiaCentral']
    for key in required:
        if key not in arrays:
            raise ValueError(f'missing {key} in script')
    river_keys = [k for k in arrays if k.startswith('river')]
    roads = ['valleyPike'] + [k for k in arrays if k.startswith('rd')]
    rails = [k for k in arrays if k.startswith('rr')]
    river = set().union(*(trace(arrays[k]) for k in river_keys))
    road = set().union(*(trace(arrays[k]) for k in roads))
    rail = set().union(*(trace(arrays[k]) for k in rails))
    towns = {(t['X'], t['Y']):t for t in tabs['towns']}
    blues, mass = tabs['blueRidgeGaps'], tabs['massanuttenGaps']
    north_gaps, all_gaps = tabs['northMtnGaps'], tabs['alleghenyGaps']
    sites = tabs['crossingSites']
    # One permanent bridge per named site: the single nearest road/rail
    # intersection. Every other overlap stays a blocking river. Hex of Steel
    # only lets non-engineers cross a river on a bridge tile, and blowing
    # that one tile must re-seal the river.
    candidates = {}
    for x, y in river & (road | rail):
        site = next((s for s in sites if abs(x - s['X']) <= s['R'] and abs(y - s['Y']) <= s['R']), None)
        if site is None:
            continue
        dist = max(abs(x - site['X']), abs(y - site['Y']))
        candidates.setdefault(site['Name'], []).append((dist, x, y, site))
    approved = {}
    claimed = set()
    for name, group in candidates.items():
        group.sort()
        for dist, x, y, site in group:
            if (x, y) not in claimed:
                approved[(x, y)] = site
                claimed.add((x, y))
                break
    unresolved = (river & (road | rail)) - set(approved)
    terrain = [0] * (W * H)
    blocked = set()
    overlaps_mountain_town = set()
    for y in range(H):
        br, ms, nm, al = (interp(arrays[k],y) for k in ['blueRidge','massanutten','northMtn','allegheny'])
        for x in range(W):
            p=(x,y)
            i=y*W+x
            if x < 2 or x >= W-2 or y < 2 or y >= H-2:
                continue
            mt = ((al is not None and abs(x-al) <= 3 and not near_gap(x,y,all_gaps)) or
                  (nm is not None and abs(x-nm) <= 2 and not near_gap(x,y,north_gaps)) or
                  (br is not None and abs(x-br) <= 2 and not near_gap(x,y,blues)) or
                  (ms is not None and abs(x-ms) <= 2 and not near_gap(x,y,mass)))
            if mt and p in road|rail:
                blocked.add(p)
            if mt and p in towns:
                overlaps_mountain_town.add(p)
            if p in towns and not mt:
                terrain[i] = 7
                continue
            if p in river:
                # 11 = one FilterRoadBridge tile. 5 = FilterRiver, impassable
                # to every unit except engineers.
                if p in approved and not mt:
                    terrain[i] = 11
                else:
                    terrain[i] = 5
                continue
            if mt:
                terrain[i] = 1
                continue
            if p in rail:
                terrain[i] = 8
                continue
            if p in road:
                terrain[i] = 6
                continue
            if al is not None and x < al-3 or al is None and x < 5:
                continue
            if al is not None and nm is not None and al+3 < x < nm-2:
                terrain[i] = 3
                continue
            if ms is not None:
                is_valley = (nm is not None and nm+2 < x < ms-2) or (br is not None and ms+2 < x < br-2)
            else:
                wE = nm+2 if nm is not None else al+3 if al is not None else 5
                eE = br-2 if br is not None else W-5
                is_valley = wE < x < eE
            if is_valley:
                terrain[i] = 4
                continue
            if br is not None and x > br+2:
                dist = x-(br+2)
                terrain[i] = 2 if dist <= 4 else 9 if dist <= 8 else 10
                continue
            if any(v is not None and abs(x-v) <= wd+2 for v,wd in [(br,2),(nm,2),(ms,2),(al,3)]):
                terrain[i] = 2
                continue
            terrain[i] = 3
    return dict(arrays=arrays,tabs=tabs,river=river,road=road,rail=rail,towns=towns,
                approved=approved,unresolved=unresolved,blocked=blocked,terrain=terrain,
                town_mountain=overlaps_mountain_town)


def render(data, output):
    # Hex centers consistent with even-q axial/offset geometry (2-d preview only).
    scale=10
    r=6.4
    dx=1.5*r
    dy=math.sqrt(3)*r
    offx=90; offy=62
    iw=int(offx*2 + (W+1)*dx + 45)
    ih=int(offy*2 + (H+.7)*dy + 80)
    im = Image.new('RGB',(iw,ih),'#ece9df')
    draw=ImageDraw.Draw(im)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
    title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',21)
    def center(p):
        x,y=p
        return (offx+x*dx, offy+(H-1-y+(x%2)/2)*dy)
    for y in range(H):
        for x in range(W):
            k=data['terrain'][y*W+x]
            cx,cy=center((x,y))
            vertices = [(cx+r*math.cos(math.radians(deg)),cy+r*math.sin(math.radians(deg))) for deg in (0,60,120,180,240,300)]
            draw.polygon(vertices,fill=TERRAIN_COLORS[k])
    for pts, color, thick in [(data['road'],'#a2764e',2),(data['rail'],'#39393a',2)]:
        for p in pts:
            if data['terrain'][p[1]*W+p[0]] not in (6,7,8,11):
                continue
            cp=center(p)
            for n in neighbors(p) & pts:
                if data['terrain'][n[1]*W+n[0]] in (6,7,8,11):
                    draw.line([cp,center(n)], fill=color,width=thick)
    for p in data['approved']:
        cx,cy=center(p)
        draw.ellipse((cx-3,cy-3,cx+3,cy+3),fill='#f6e697',outline='#584210')
    for p in data['unresolved']:
        cx,cy=center(p)
        draw.line((cx-2,cy-2,cx+2,cy+2),fill='#c4423c',width=2)
        draw.line((cx+2,cy-2,cx-2,cy+2),fill='#c4423c',width=2)
    for p,t in data['towns'].items():
        x,y=center(p)
        draw.ellipse((x-4,y-4,x+4,y+4),fill='#292925',outline='#fffaf1',width=1)
        if t['S']==2 or t['N'] in ('Port Republic','McDowell','Luray','Strasburg','Front Royal'):
            draw.text((x+5,y-9),t['N'],font=font,fill='#171e22',stroke_width=2,stroke_fill='#f3edda')
    draw.text((24,13),'SHENANDOAH VALLEY CAMPAIGN • V3 SCHEMATIC HEX PREVIEW',font=title,fill='#303633')
    draw.text((24,43),'North ↑ • Town coordinates approximate • Red × unresolved crossing • Gold circle approved crossing',font=font,fill='#4b4b46')
    draw.text((24,ih-27),'NOT A GAME SCREENSHOT. NOT VERIFIED AGAINST A SURVEYED 1862 MAP.',font=font,fill='#7e2929')
    im.save(output,optimize=True)


def audit(data):
    arr=data['arrays']
    issues=[]
    # every consecutive path tile must be a true hex neighbor (source segment check).
    for name, wp in arr.items():
        if name not in ['valleyPike'] and not name.startswith(('rd','rr','river')):
            continue
        for a,b in zip(wp,wp[1:]):
            route=line(a,b)
            if any(v not in neighbors(u) for u,v in zip(route,route[1:])):
                issues.append(f'NONADJACENT: {name} segment {a} to {b}')
    towns = data['towns']
    for name in ['Staunton','Winchester','New Market','Front Royal','Harrisonburg','Strasburg']:
        matches = [p for p,v in towns.items() if v['N']==name]
        if len(matches)!=1:
            issues.append(f'MISSING IMPORTANT TOWN: {name}')
    for p in data['town_mountain']:
        issues.append(f'TOWN ON CLOSED RIDGE: {towns[p]["N"]} {p}')
    for p in towns:
        if data['terrain'][p[1]*W+p[0]] != 7:
            issues.append(f'TOWN NOT RENDERED: {towns[p]["N"]} {p}')
    return issues


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--script',default=str(ROOT/'build_valley_map_v3.ps1'))
    parser.add_argument('--output',default=str(ROOT/'Valley_Map_v3_preview.png'))
    parser.add_argument('--json',default=str(ROOT/'geometry_audit.json'))
    args=parser.parse_args()
    arrays,tabs=parse_script(args.script)
    data=build(arrays,tabs)
    issues=audit(data)
    report={
        'source':Path(args.script).name,'width':W,'height':H,'status':'schematic_unverified',
        'terrain_counts':dict(Counter(data['terrain'])),
        'towns':len(data['towns']),'river_hexes':len(data['river']),'road_hexes':len(data['road']),
        'rail_hexes':len(data['rail']),'approved_crossings':[
            {'x':x,'y':y,'site':s['Name']} for (x,y),s in sorted(data['approved'].items())],
        'unresolved_crossings':[{'x':x,'y':y} for x,y in sorted(data['unresolved'])],
        'blocked_ridge_paths':[{'x':x,'y':y} for x,y in sorted(data['blocked'])],
        'issues':issues,
    }
    Path(args.json).write_text(json.dumps(report,indent=2),encoding='utf-8')
    render(data,args.output)
    print(json.dumps({k:v for k,v in report.items() if k not in ('approved_crossings','unresolved_crossings','blocked_ridge_paths','terrain_counts')},indent=2))
    print('Crossings approved:',len(data['approved']),'unresolved:',len(data['unresolved']), 'blocked ridge path hexes:',len(data['blocked']))
    print('Output:',args.output)
    if issues:
        raise SystemExit('Geometry audit contains issues; see JSON report')

if __name__=='__main__':main()
