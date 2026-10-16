#!/usr/bin/env python3
import json, math, sys, time, csv, random
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from hex_grid import KERNSTOWN as G
from build_kernstown_layers import dem_at, slope_at, trace_waypoints
meta=json.load(open(ROOT/"data/basemap_meta.json"))
W,H,R_PX,PX_PER_M=meta["W"],meta["H"],meta["R_px"],meta["px_per_m"]
arr=np.array(Image.open(ROOT/"data/basemap_kernstown.png").convert("RGBA"))
mask=np.array(Image.open(ROOT/"data/hex_mask.png").convert("L").resize((2000,2000), Image.Resampling.NEAREST))
def hexc(c,r):
    x,y=G.hex_to_xy_m(c,r); return x*PX_PER_M, H-y*PX_PER_M
out=ROOT/"mod/Graphics/Tiles/Summer"; out.mkdir(parents=True, exist_ok=True)
spring=ROOT/"mod/Graphics/Tiles/Spring"; spring.mkdir(parents=True, exist_ok=True)
side_i=int(round(2*R_PX)); hexes=[]; t0=time.time(); n=0; total=G.cols*G.rows
for col in range(G.cols):
    for row in range(G.rows):
        cx,cy=hexc(col,row); left,top=cx-R_PX,cy-R_PX
        region=np.zeros((side_i,side_i,4),np.uint8)
        region[:,:,0]=210; region[:,:,1]=190; region[:,:,2]=150; region[:,:,3]=255
        x0,y0=int(math.floor(left)),int(math.floor(top))
        sx0,sy0=max(0,x0),max(0,y0); sx1,sy1=min(W,x0+side_i),min(H,y0+side_i)
        dx0,dy0=sx0-x0,sy0-y0
        if sx1>sx0 and sy1>sy0:
            region[dy0:dy0+(sy1-sy0), dx0:dx0+(sx1-sx0)] = arr[sy0:sy1, sx0:sx1]
        rgba=np.array(Image.fromarray(region).resize((2000,2000), Image.Resampling.BILINEAR))
        rgba[:,:,3]=mask
        name=f"SV_K_{col}_{row}"
        Image.fromarray(rgba).save(out/f"{name}.png", compress_level=6)
        sp=spring/f"{name}.png"
        if sp.exists() or sp.is_symlink(): sp.unlink()
        sp.symlink_to(f"../Summer/{name}.png")
        hexes.append({"col":col,"row":row,"tile_name":name}); n+=1
        if n%500==0: print(f"{n}/{total}", flush=True)
print(f"sliced {n} in {(time.time()-t0)/60:.1f}m", flush=True)
FEAT=json.loads((ROOT/"data/features/kernstown_features.json").read_text())
dem=np.array(Image.open(ROOT/"data/dem/kernstown_3dep.tif"), np.float32)
dem=np.where(np.isfinite(dem), dem, np.nanmedian(dem))
river=set()
for riv in FEAT["rivers"].values(): river |= trace_waypoints(G, riv["waypoints"])
pike=trace_waypoints(G, FEAT["roads"]["valley_pike"]["waypoints"]); dirt=set()
for k,rd in FEAT["roads"].items():
    if rd.get("kind")!="pike": dirt |= trace_waypoints(G, rd["waypoints"])
rail=set()
for rr in FEAT["railroads"].values(): rail |= trace_waypoints(G, rr["waypoints"])
forest=set()
for r in range(G.rows):
    for c in range(G.cols):
        lon,lat=G.hex_to_lonlat(c,r)
        near=any((lon-a)**2+(lat-b)**2<0.00028 for a,b in FEAT["ridge_cores"]["sandy_ridge"])
        s=slope_at(dem,G,lon,lat); e=dem_at(dem,G,lon,lat)
        if (near and e>230) or (s>0.15 and e>260): forest.add((c,r))
open_clear=set()
for lon,lat in FEAT["ridge_cores"]["pritchards_hill"]:
    pc,pr=G.lonlat_to_hex(lon,lat)
    for dc in range(-3,4):
        for dr in range(-3,4): open_clear.add((pc+dc,pr+dr))
for p in FEAT["places"]:
    pc,pr=G.lonlat_to_hex(p["lon"],p["lat"]); rad=3 if p.get("kind")=="city" else 2
    for dc in range(-rad,rad+1):
        for dr in range(-rad,rad+1): open_clear.add((pc+dc,pr+dr))
forest -= open_clear
hills=set()
for lon,lat in FEAT["ridge_cores"]["pritchards_hill"]:
    pc,pr=G.lonlat_to_hex(lon,lat)
    for dc in range(-2,3):
        for dr in range(-2,3):
            if (pc+dc,pr+dr) not in forest: hills.add((pc+dc,pr+dr))
place={G.lonlat_to_hex(p["lon"],p["lat"]):p for p in FEAT["places"]}
for h in hexes:
    c,r=h["col"],h["row"]; typ,filt="Plain","FilterAll"; flags={}
    if (c,r) in hills: typ,filt="Hill","FilterTerrain"
    if (c,r) in forest: typ,filt="Forest","FilterForest"
    if (c,r) in river: typ,filt="River","FilterRiver"
    if (c,r) in dirt or (c,r) in pike: typ,filt="Road","FilterRoad"
    if (c,r) in rail: flags["Railroad"]=True
    if (c,r) in place:
        p=place[(c,r)]; flags["CityName"]=p["name"]
        if p.get("vp"):
            flags["IsVictoryPoint"]=True; flags["PrimaryObjective"]=bool(p.get("primary"))
            filt="FilterVP"; typ="City"
        if p.get("owner"): flags["OwnerName"]=p["owner"]
    h.update(type=typ, filter=filt, label=flags.get("CityName",""), flags=flags)
layers={"grid":{"cols":G.cols,"rows":G.rows,"hex_yards":G.hex_yards,"orientation":"flat-top odd-q",
 "bbox":{"west":G.west,"south":G.south,"east":G.east,"north":G.north},"neighbor_m":G.hex_m,"size_m":G.size_m},
 "hexes":hexes,"season":"Summer",
 "notes":"2000px cl=6; continuous DEM slices; modest oblique props; no hex-stamped trees; counter-clear centers"}
(ROOT/"data/layers").mkdir(parents=True, exist_ok=True)
(ROOT/"data/layers/kernstown_hexes.json").write_text(json.dumps(layers))
with open(ROOT/"data/layers/kernstown_hexes.csv","w",newline="") as f:
    w=csv.DictWriter(f, fieldnames=["col","row","tile_name","type","filter","label"], extrasaction="ignore")
    w.writeheader(); w.writerows(hexes)
print(Counter(h["type"] for h in hexes), flush=True)
files=list(out.glob("SV_K_*.png")); sample=random.sample(files, min(40,len(files)))
mean=sum(p.stat().st_size for p in sample)/len(sample)
print(f"TOTAL_GB={mean*len(files)/1e9:.2f} mean_kb={mean/1024:.0f} n={len(files)}", flush=True)
print("SLICE_DONE", flush=True)
