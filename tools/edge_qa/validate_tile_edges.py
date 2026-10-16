#!/usr/bin/env python3
"""Non-destructive visual/geometry preflight for Shenandoah 1862 concept hex sheets.

Requirements: Python 3.10+, opencv-python, numpy, Pillow optional for contact sheet.

This IS NOT an automated historical-feature recognizer. A matching RGB edge band
alone does not establish that a ROAD, RIVER, RAIL, FENCE or WALL connects.
A verified game's tile needs a signed, human-reviewed explicit ports manifest.

Usage: python validate_tile_edges.py --input /path/to/artwork --out /path/to/audit
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any
import cv2
import numpy as np
from port_validation import validate_network

SCHEMA_VERSION = "0.3"
PORT_TYPES = {"pike", "dirt_road", "farm_lane", "rail", "river", "creek", "wood_fence", "stone_wall"}
SUGGESTED_TYPES = sorted(PORT_TYPES)
EDGE_NAMES = {
    "point_top": ["NE", "E", "SE", "SW", "W", "NW"],
    "flat_top": ["N", "NE", "SE", "S", "SW", "NW"],
}
CANDIDATE_WORDS = ("tile", "terrain", "countryside", "spring", "hex", "farmstead",
    "floodplain", "road", "appalachian", "crossing", "transport", "watercolor")
OMIT_NAMES = ("_preview", "grok_", "stonewall", "_map_preview", "valley_map", "asset_connections", "test_", "imagegen", "tile_variants_montage", "vintage_winchester_kernstown")
# These sheets are standalone objects without a hexagonal ground footprint.
# Building-roof peaks should NOT be confused with the north point of a hex.
OBJECT_OVERLAY_SHEETS = {
    "19th_century_farmstead_building_tiles.png",
    "watercolor_farm_terrain_tile_sheet.png",
    "watercolor_countryside_industry_asset_sheet.png",
}
# Dense mosaic touching across boundaries cannot be reliably isolated by
# simple rectangular cells; retain as review art but do not issue misleading port results.
MANUAL_SEGMENTATION_REQUIRED = {"top_down_isometric_style_game_terrain_tile_sheet.png"}
NOT_INDIVIDUAL_HEXES = OBJECT_OVERLAY_SHEETS | MANUAL_SEGMENTATION_REQUIRED
# Some compositions deliberately mix 5 tiles within a 3x2 artboard;
# a blank cell is not an asset. Connected silhouettes can touch at corners.
GRID_OVERRIDES = {
    "civil_war_era_hex_tile_terrain_sheet.png": (4, 3),
    "shenandoah_valley_terrain_tile_sheet.png": (4, 3),
    "19th_century_farmstead_building_tiles.png": (4, 3),
    "watercolor_farm_terrain_tile_sheet.png": (4, 3),
    "watercolor_countryside_industry_asset_sheet.png": (4, 3),
    "shenandoah_valley_terrain_tile_set.png": (4, 3),
    "springtime_hex_tile_countryside_map.png": (4, 2),
    "civil_war_countryside_hex_map_tiles.png": (4, 2),
    "early_spring_floodplain_hex_tiles.png": (4, 3),
    "shenandoah_terrain_hex_tile_sheet.png": (5, 4),
    "six_tile_americana_terrain_collage.png": (3, 2),
}


def item_files(folder: Path) -> list[Path]:
    return [p for p in sorted(folder.iterdir()) if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
        and any(t in p.name.lower() for t in CANDIDATE_WORDS)
        and not any(t in p.name.lower() for t in OMIT_NAMES)]


def foreground(image: np.ndarray) -> np.ndarray:
    """Conservative color mask for brown/ochre sprites over neutral gray artboard."""
    b, g, r = [channel.astype(np.int16) for channel in cv2.split(image)]
    sat = np.max(image, axis=2).astype(np.int16) - np.min(image, axis=2).astype(np.int16)
    return np.uint8(((r - b > 13) & (r >= g - 16) & (sat > 16))) * 255


def silhouette_stats(image: np.ndarray):
    mask = foreground(image)
    m = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(m, 8)
    minimum = image.shape[0] * image.shape[1] * .030
    good = [tuple(map(int, v)) for v in stats[1:] if v[cv2.CC_STAT_AREA] > minimum]
    return good


def probable_grid(image: np.ndarray, name: str):
    if name in GRID_OVERRIDES:
        return GRID_OVERRIDES[name]
    n = len(silhouette_stats(image))
    if n >= 17: return 5, 4
    if n >= 11: return 4, 3
    if n >= 7: return 4, 2
    # These are primarily 3x2 even when two rows visually touch.
    return (3, 2)


def hex_vertices(box: tuple[int, int, int, int], orientation: str) -> np.ndarray:
    x, y, w, h = box
    if orientation == "point_top":
        v = [(.5, 0), (1, .25), (1, .75), (.5, 1), (0, .75), (0, .25)]
    else:
        v = [(.25, 0), (.75, 0), (1, .5), (.75, 1), (.25, 1), (0, .5)]
    return np.array([(x + u * max(w-1, 1), y + t * max(h-1, 1)) for u, t in v], np.float32)


def edge_rgb_samples(image: np.ndarray, polygon: np.ndarray, edge: int, inset_fraction=.035, samples=64):
    h, w = image.shape[:2]
    a = polygon[edge]
    b = polygon[(edge + 1) % 6]
    center = np.mean(polygon, axis=0)
    # Sample 7%--93% of the edge: excludes joins where isolated drawing artifacts occur.
    ts = np.linspace(.07, .93, samples)[:, None]
    points = a[None, :] * (1-ts) + b[None, :] * ts
    inside = (center[None, :] - points)
    unit = inside / np.maximum(np.linalg.norm(inside, axis=1, keepdims=True), 1e-8)
    points += unit * (inset_fraction * min(np.ptp(polygon[:, 0]), np.ptp(polygon[:, 1])))
    pixels = image[np.clip(np.rint(points[:,1]).astype(int),0,h-1), np.clip(np.rint(points[:,0]).astype(int),0,w-1)]
    lab = cv2.cvtColor(pixels[None, :, :], cv2.COLOR_BGR2LAB)[0].astype(np.float32)
    return lab


def assess_shape(image: np.ndarray, mask: np.ndarray, cell_rect: tuple[int,int,int,int]):
    x0,y0,x1,y1=cell_rect
    roi = mask[y0:y1,x0:x1]
    ys,xs=np.where(roi>0)
    if len(xs) < .08 * (x1-x0)*(y1-y0): return None
    # Edge cut artifacts can create extreme pixels; quantify around the median line.
    left = x0 + int(np.percentile(xs, .4)); right = x0 + int(np.percentile(xs,99.6))
    top = y0 + int(np.percentile(ys, .4)); bottom = y0 + int(np.percentile(ys,99.6))
    bw=right-left+1;bh=bottom-top+1
    if bw < .48*(x1-x0) or bh < .45*(y1-y0): return None
    topband = mask[max(top,min(bottom,top+8)), left:right+1]
    midband = mask[int(top+bh*.50),left:right+1]
    topwidth=np.count_nonzero(topband)
    midwidth=max(1,np.count_nonzero(midband))
    # Point-top artwork has a single peak at the northern edge; a flat-top hex
    # has a broad horizontal upper edge. Distinct from camera angle.
    ratio=topwidth/midwidth
    if ratio < .38: shape="point_top"
    elif ratio > .55: shape="flat_top"
    else: shape="ambiguous"
    return (left,top,bw,bh,shape,round(ratio,3))


def compare_profiles(a: np.ndarray, b: np.ndarray):
    # Local units are OpenCV L*a*b*: L in [0,255], a/b in [0,255].
    # A delta <= 5 means near identity; <= 12 is still only a visual candidate.
    differences=np.linalg.norm(a-b[::-1],axis=1)
    return round(float(np.mean(differences)),2), round(float(np.percentile(differences,90)),2)


def scan_sheets(folder: Path) -> tuple[list[dict],list[dict]]:
    tiles=[];sheets=[]
    for p in item_files(folder):
        if p.name in NOT_INDIVIDUAL_HEXES:
            sheets.append(dict(filename=p.name,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),raw_size_bytes=p.stat().st_size,
                tile_sheet_status="object_overlays" if p.name in OBJECT_OVERLAY_SHEETS else "manual_segmentation_needed",
                tiles_detected=0,grid=None,transparency=None,
                orientation_counts={"point_top":0,"flat_top":0,"ambiguous":0}))
            continue
        image=cv2.imread(str(p),cv2.IMREAD_UNCHANGED)
        if image is None or image.ndim!=3: continue
        channels=image.shape[2]
        im=image[:,:,:3]
        h,w=im.shape[:2]
        nc,nr=probable_grid(im,p.name)
        mask=foreground(im)
        tilecount=0
        for row in range(nr):
            for col in range(nc):
                x0,x1=round(w*col/nc),round(w*(col+1)/nc)
                y0,y1=round(h*row/nr),round(h*(row+1)/nr)
                est=assess_shape(im,mask,(x0,y0,x1,y1))
                if est is None: continue
                x,y,bw,bh,shape,ratio=est
                poly=hex_vertices((x,y,bw,bh), shape if shape!="ambiguous" else "point_top")
                names=EDGE_NAMES[shape] if shape!="ambiguous" else [f"edge_{j}" for j in range(6)]
                profiles=[]
                for edge in range(6):
                    profiles.append(edge_rgb_samples(im,poly,edge))
                tiles.append(dict(id=f"{p.stem}__r{row+1}c{col+1}",sheet=p.name,cell_row=row+1,cell_col=col+1,
                    source_bbox=[x,y,bw,bh],art_orientation=shape,top_to_mid_occupancy=ratio,
                    alpha=channels==4,edge_names=names,profiles=profiles,source_shape=[w,h]))
                tilecount+=1
        sheets.append(dict(filename=p.name,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),raw_size_bytes=p.stat().st_size,tile_sheet_status="hex_atlas",pixel_size=[w,h],grid=[nc,nr],
            tiles_detected=tilecount,transparency=channels==4,
            orientation_counts={s:sum(t["sheet"]==p.name and t["art_orientation"]==s for t in tiles) for s in ("point_top","flat_top","ambiguous")}))
    return tiles,sheets


def cross_compare(tiles: list[dict]):
    # For each edge, compare against the opposing edge from OTHER art in SAME sheet.
    # A visual/color match is not a network-port confirmation!
    for a in tiles:
        results=[]
        for edge in range(6):
            choices=[]
            for b in tiles:
                if a["id"]==b["id"] or a["art_orientation"]!=b["art_orientation"]:continue
                if a["sheet"]!=b["sheet"]:continue
                mean,p90=compare_profiles(a["profiles"][edge],b["profiles"][(edge+3)%6])
                choices.append((mean,p90,b["id"]))
            choices.sort()
            best=choices[0] if choices else None
            results.append({"edge":edge,"direction":a["edge_names"][edge],
                "best_visual_candidate":best[2] if best else None,
                "best_edge_mean_delta_lab":best[0] if best else None,
                "best_edge_p90_delta_lab":best[1] if best else None,
                "edge_pixel_match_pass":bool(best and best[0]<=5.0 and best[1]<=12.0)})
        a["edges"]=results


def report(folder: Path,out: Path,manifest_path=None):
    out.mkdir(parents=True,exist_ok=True)
    tiles,sheets=scan_sheets(folder)
    cross_compare(tiles)
    declared=json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path else None
    errors=validate_network(declared) if declared is not None else []
    npt=sum(t["art_orientation"]=="point_top" for t in tiles)
    nft=sum(t["art_orientation"]=="flat_top" for t in tiles)
    na=sum(t["art_orientation"]=="ambiguous" for t in tiles)
    pass_edges=sum(e["edge_pixel_match_pass"] for t in tiles for e in t["edges"])
    count_edges=6*len(tiles)
    unrenderable=sum(not t["alpha"] for t in tiles)
    manifest={"schema_version":SCHEMA_VERSION,"target_geometry":"flat_top", "game":"Hex of Steel",
        "target_hex_width_yards":250,"sources":"Illustrated concept atlases, not approved game assets",
        "method":"Conservative image color segmentation, six-sided polygon bounding boxes, per-edge Lab samples, best visual candidate restricted to same sheet; orientations are estimates, NOT approvals",
        "not_proven":"Art silhouettes, pixel color and approximate edge continuity cannot establish route semantics, historical placement, native Unity sprite behavior or terrain elevation",
        "sheet_count":len(sheets),"individual_hex_atlas_count":sum(s.get("tile_sheet_status")=="hex_atlas" for s in sheets),
        "object_overlay_sheet_count":sum(s.get("tile_sheet_status")=="object_overlays" for s in sheets),
        "manual_split_sheet_count":sum(s.get("tile_sheet_status")=="manual_segmentation_needed" for s in sheets),
        "candidate_tiles":len(tiles),"art_point_top":npt,
        "art_flat_top":nft,"art_orientation_ambiguous":na,"not_rgba":unrenderable,
        "edge_comparisons":count_edges,"near_pixel_matched_edges":pass_edges,
        "no_near_pixel_match":count_edges-pass_edges,
        "explicit_port_links_registered":len(declared.get("adjacencies", [])) if declared is not None else 0,
        "explicit_port_links_verified":len(declared.get("adjacencies", [])) if (declared is not None and not errors) else 0,
        "port_validation_errors":errors,"edge_port_status":"NOT REGISTERED; no graphical feature ports can be certified without matching source-authored typed/positioned edge port data",
        "overall_result":"FAIL: do not package as production flat-top hex art until orientation and exact road/rail/river/fence ports are rebuilt and reviewed",
        "sheets":sheets}
    (out/'audit_summary.json').write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    keys=["id","sheet","cell_row","cell_col","art_orientation","top_to_mid_occupancy","alpha","source_bbox",
          "near_matched_edge_count","worst_best_delta_lab","blocked"]
    with (out/'tile_edge_audit.csv').open('w',newline='',encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
        for t in tiles:
            writer.writerow({"id":t["id"],"sheet":t["sheet"],"cell_row":t["cell_row"],"cell_col":t["cell_col"],
                "art_orientation":t["art_orientation"],"top_to_mid_occupancy":t["top_to_mid_occupancy"],
                "alpha":t["alpha"],"source_bbox":";".join(map(str,t["source_bbox"])),
                "near_matched_edge_count":sum(e["edge_pixel_match_pass"] for e in t["edges"]),
                "worst_best_delta_lab":max((e["best_edge_mean_delta_lab"] or 999) for e in t["edges"]),
                "blocked":t["art_orientation"]!="flat_top" or not t["alpha"] or not all(e["edge_pixel_match_pass"] for e in t["edges"])})
    details=[]
    for t in tiles:
        details.append({k:v for k,v in t.items() if k!="profiles"})
    (out/'edge_details.json').write_text(json.dumps(details,indent=2),encoding="utf-8")
    with (out/'README.md').open('w',encoding='utf-8') as f:
        f.write(f"# CivilWar1 — Six-edge terrain tile preflight\n\n")
        f.write(f"Analyzed **{len(sheets)} atlas sheets** and detected **{len(tiles)} individual tile silhouettes**.\n\n")
        f.write(f"- **{npt} point-top**, **{nft} flat-top**, **{na} ambiguous**; target game tile design is flat-top.\n")
        f.write(f"- **{unrenderable}** candidate sprites have no native transparency and require masking.\n")
        f.write(f"- Compared all **{count_edges} edge slots** to nearest opposite edge in other tiles of their sheet; **{pass_edges}** near-pixel matches (not verified route ports).\n")
        f.write(f"- **{len(errors)}** explicit-network validation errors.\n\n")
        f.write("## REQUIRED before exporting to game\n\n")
        f.write("1. Author true flat-top (not point-top) art, without beveled raised platform sides.\n")
        f.write("2. Create one continuous common ground-color/elevation representation, including shared vertex heights.\n")
        f.write("3. Register every route/fence/wall exit with a typed port and shared edge coordinate. An illustrated exit is not verified by adjacency.\n")
        f.write("4. Require reciprocal ports, exact road material/width, river stage, rail alignment, and no mismatched bridge types.\n")
        f.write("5. Test a tiled 3x3 neighborhood and inspect all 12 interior connections; use the game save only after that passes.\n")
        f.write("6. Historical river crossings and rails remain unverified unless mapped to primary-source geometry.\n\n")
        f.write("## Limitations\n\n")
        f.write("This is image geometry/visual edge analysis. It does NOT automatically recognize a road, fence or rail in each pixel. ")
        f.write("`edge_pixel_match_pass` is a strict texture/color preflight, not a pass of the reciprocal port/placement rules. ")
        f.write("All inputs are unchanged. No game-ready sprite or verified historical placement has been created by the script.\n")
        f.write("See `tile_edge_audit.csv` and `edge_details.json` for every tile and each of its six sides.\n")
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--ports',type=Path,default=None,help="Optional authored JSON (tiles, adjacencies, perimeter_exits); invokes typed validator")
    a=parser.parse_args(); r=report(a.input,a.out,a.ports)
    print(json.dumps({k:v for k,v in r.items() if k!="sheets"},indent=2))

if __name__=="__main__":main()