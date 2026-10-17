"""Write tests/fixtures/hex_utils_neighbors.json from src/hex_utils.py (native flat-top even-q, PR #9 version from 2026-10-17).

Usage: python tools/gen_hex_fixture.py path/to/hex_utils.py
"""
import importlib.util, json, sys, pathlib
p = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("hex_utils", p)
m = importlib.util.module_from_spec(spec); sys.modules["hex_utils"] = m; spec.loader.exec_module(m)
cases = []
for col in range(0, 8):
    for row in range(0, 6):
        cx, cy = m.hex_center(col, row)
        for port in range(6):
            nc, nr = m.offset_neighbor(col, row, port)
            nx, ny = m.hex_center(nc, nr)
            gx, gy = m.game_position(col, row)
            cases.append(dict(col=col, row=row, port=port, ncol=nc, nrow=nr, cx=cx, cy=cy, nx=nx, ny=ny, gx=gx, gy=gy))
out = dict(source=str(p), layout="even-q (MapGO)", port_names=list(m.PORT_NAMES), cases=cases)
dst = pathlib.Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "hex_utils_neighbors.json"
dst.write_text(json.dumps(out, indent=1))
print(f"wrote {len(cases)} cases to {dst}")
