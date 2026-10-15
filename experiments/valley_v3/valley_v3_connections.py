"""Non-destructive, edge-exact topology audit for the 125x130 Valley v3 prototype.

Never execute the uploaded PowerShell, deserialize .sav data, fabricate crossings,
or claim native Hex of Steel sprite/game compatibility. This module preserves
route identity: adjacent hexes are not necessarily joined by the same route.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from validate_and_preview import W, H, parse_script, line, neighbors, build

# Flat-top even-q hex; 0=N, clockwise. Ports are opposite at (d+3)%6.
EVEN = ((0,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0))
ODD  = ((0,-1),(1,-1),(1,0),(0,1),(-1,0),(-1,-1))

# These asset-port assignments come from the physically audited civilhex tile
# inventory in repository PR #5, NOT the suffix fallback in v3 PowerShell.
# No road-port inventory has been verified against the installed game.
RIVER_VARIANTS = {
    (0,3): 'River1', (1,4): 'River2', (2,5): 'River3',
    (1,5): 'River4', (2,4): 'River5', (0,4): 'River6',
    (0,2): 'River7', (1,3): 'River8', (3,5): 'River9',
    (1,3,5): 'River10', (0,2,4): 'River11', (0,1,3): 'River12',
}
RAIL_VARIANTS = {
    (0,3): 'Railroad1', (1,4): 'Railroad2', (2,5): 'Railroad3',
    (1,5): 'Railroad4', (2,4): 'Railroad5', (0,2): 'Railroad6',
    (1,3): 'Railroad7', (3,5): 'Railroad8', (0,4): 'Railroad9',
}


def adjacent(cell: tuple[int, int], d: int) -> tuple[int, int]:
    x, y = cell
    dx, dy = (EVEN if not x % 2 else ODD)[d]
    return x + dx, y + dy


def port(a: tuple[int,int], b: tuple[int,int]) -> int:
    for d in range(6):
        if adjacent(a,d) == b:
            return d
    raise ValueError(f'Nonadjacent hexes {a} {b}')


def traced_line(waypoints: list[tuple[int,int]]) -> list[tuple[int,int]]:
    """Ordered polyline, unlike the old set-based trace that loses edge identity."""
    if not waypoints:
        return []
    out = [waypoints[0]]
    for a, b in zip(waypoints,waypoints[1:]):
        seg = line(a,b)
        out.extend(seg[1:])
    return [p for i,p in enumerate(out) if i == 0 or p != out[i-1]]


def source_routes(arrays: dict) -> dict[str,dict[str,list[tuple[int,int]]]]:
    return {
        'river': {k:v for k,v in arrays.items() if k.startswith('river')},
        'road': {k:v for k,v in arrays.items() if k == 'valleyPike' or k.startswith('rd')},
        'rail': {k:v for k,v in arrays.items() if k.startswith('rr')},
    }


def build_edges(routes: dict, width: int = W, height: int = H) -> dict:
    ports = {kind:defaultdict(set) for kind in routes}
    occupancy = {kind:defaultdict(set) for kind in routes}
    track_edges = {kind:defaultdict(set) for kind in routes}
    defects = []
    for kind, named in routes.items():
        for name, wp in named.items():
            if not wp:
                defects.append({'type':'empty_route','route':name})
                continue
            traced = traced_line(wp)
            for cell in traced:
                x,y = cell
                if not (0 <= x < width and 0 <= y < height):
                    defects.append({'type':'out_of_bounds','route':name,'hex':list(cell)})
                    continue
                occupancy[kind][cell].add(name)
            for a,b in zip(traced,traced[1:]):
                if a == b:
                    continue
                try:
                    d = port(a,b)
                except ValueError:
                    defects.append({'type':'nonadjacent','route':name,'from':list(a),'to':list(b)})
                    continue
                if (a not in occupancy[kind] or b not in occupancy[kind]):
                    continue
                ports[kind][a].add(d)
                ports[kind][b].add((d+3)%6)
                track_edges[kind][name].add(tuple(sorted((a,b))))
    return {'ports':ports,'occupancy':occupancy,'tracks':track_edges,'defects':defects}


def phantom_connections(network: dict) -> dict[str,int]:
    """Old preview implicitly connects all occupied neighboring hexes."""
    issues={}
    for kind, cells in network['occupancy'].items():
        cnt=0
        for cell in cells:
            for d in range(6):
                neighbor=adjacent(cell,d)
                if cell < neighbor and neighbor in cells and d not in network['ports'][kind].get(cell,set()):
                    cnt+=1
        issues[kind]=cnt
    return issues


def audit_v3(script: str | Path) -> tuple[dict,dict,dict]:
    arrays, tables = parse_script(script)
    world=build(arrays,tables)
    net=build_edges(source_routes(arrays))
    results={'status':'GEOMETRY_ONLY_NOT_ENGINE_TESTED',
        'dimensions':[W,H],
        'inputs':'provisional v3 hand digitized coordinates',
        'routes':{k:len(v) for k,v in source_routes(arrays).items()},
        'occupied_hexes':{k:len(v) for k,v in net['occupancy'].items()},
        'phantom_links_in_old_set_based_preview':phantom_connections(net),
        'missing_or_unverified_sprite_ports':[],
        'river_route_collisions':[],
        'unresolved_crossings':[],
        'rail_water_crossings_without_rail_bridge':[],
        'roads_hidden_by_railroad_or_town':[],
        'town_on_river':[],
        'defects':net['defects'],
        'crossing_sites_provisional':len(world['approved']),
    }
    for kind in ('river','rail','road'):
        table=RIVER_VARIANTS if kind=='river' else RAIL_VARIANTS if kind=='rail' else {}
        for cell, dirs in sorted(net['ports'][kind].items()):
            shape=tuple(sorted(dirs))
            if shape not in table:
                issue={'kind':kind,'hex':list(cell),'ports':list(shape)}
                issue['reason']=('ROAD_ART_NOT_AUDITED' if kind=='road' else
                    'NEEDS_JUNCTION' if len(shape)>=3 else
                    'NEEDS_ENDPOINT' if len(shape)==1 else
                    'NO_EXACT_MATCHING_SPRITE')
                results['missing_or_unverified_sprite_ports'].append(issue)
    waters=set(net['occupancy']['river'])
    for kind in ('road','rail'):
        for cell in sorted(waters & set(net['occupancy'][kind])):
            entry={'hex':list(cell),'kind':kind,
                'river_names':sorted(net['occupancy']['river'][cell]),
                'route_names':sorted(net['occupancy'][kind][cell]),
                'candidate_site':world['approved'][cell]['Name'] if cell in world['approved'] else None}
            results['river_route_collisions'].append(entry)
            if cell not in world['approved']:
                results['unresolved_crossings'].append(entry)
            if kind=='rail':
                # v3 bridge tile explicitly sets Railroad=False, even at a named bridge.
                results['rail_water_crossings_without_rail_bridge'].append(entry)
    for cell in sorted(set(net['occupancy']['road']) & (set(net['occupancy']['rail'])|set(world['towns']))):
        results['roads_hidden_by_railroad_or_town'].append(list(cell))
    for cell in sorted(waters & set(world['towns'])):
        results['town_on_river'].append({'hex':list(cell),'town':world['towns'][cell]['N']})
    # Every assigned port must be matched reciprocally by its true neighbor.
    for kind, by_hex in net['ports'].items():
        for cell, ports in by_hex.items():
            for direction in ports:
                other=adjacent(cell,direction)
                if (direction+3)%6 not in by_hex.get(other, set()):
                    results['defects'].append({'type':'unpaired_edge','kind':kind,
                        'hex':list(cell),'direction':direction})
    return results,net,world


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('script',type=Path,nargs='?',default=Path(__file__).with_name('build_valley_map_v3.ps1'))
    p.add_argument('--json',type=Path,default=None)
    a=p.parse_args()
    report,_,_=audit_v3(a.script)
    if a.json:
        a.json.parent.mkdir(parents=True,exist_ok=True)
        a.json.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k: len(v) if isinstance(v,list) else v for k,v in report.items()
                     if k not in ('missing_or_unverified_sprite_ports','river_route_collisions','unresolved_crossings',
                                  'rail_water_crossings_without_rail_bridge','roads_hidden_by_railroad_or_town')},indent=2))
    c=Counter(x['kind'] for x in report['missing_or_unverified_sprite_ports'])
    print('Missing/unverified exact tile shapes by network:',dict(c))
    print('River-road or river-rail intersections:',len(report['river_route_collisions']))
    print('Unresolved intersections:',len(report['unresolved_crossings']))
    print('Railways losing rail across water:',len(report['rail_water_crossings_without_rail_bridge']))
    return bool(report['defects'] or report['missing_or_unverified_sprite_ports'] or report['unresolved_crossings'])

if __name__ == '__main__':
    raise SystemExit(main())
