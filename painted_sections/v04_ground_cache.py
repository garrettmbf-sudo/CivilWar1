"""v0.4 stage A: broom ground texture (painting-quilted, build_sandy_ridge.py method) + DEM hillshade,
cached to /workspace/cache so the v0.4 art passes can iterate quickly."""
import os, sys
os.environ['FULL'] = '1'
sys.path.insert(0, 'scripts')
src = open('painted_sections/build_sandy_ridge.py').read()
ground = src.split('# plowed: each field')[0]
hill = src.split('# ---------- 3. hillshade ----------')[1].split('img *= np.clip(shade')[0]
exec(ground)
dk = np.clip(fbm(shape, 41)*0.5+0.1, 0, 1)[..., None]
base = base*(1-dk*0.28)+base*np.array([0.78, 0.70, 0.62])*dk*0.28
exec(hill)
CACHE = os.environ.get('V04_CACHE', '/workspace/cache')
np.save(f'{CACHE}/ground.npy', np.clip(base, 0, 255).astype(np.uint8))
np.save(f'{CACHE}/shade.npy', shade.astype(np.float16))
np.save(f'{CACHE}/elev.npy', elev.astype(np.float16))
np.save(f'{CACHE}/forest.npy', forest.astype(np.float16))
print('cached', base.shape)
