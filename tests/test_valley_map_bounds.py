"""Static checks on tools/powershell/valley_map_data.ps1 (runs on Linux without PowerShell)."""
import re
from pathlib import Path

PS1 = Path(__file__).resolve().parents[1] / "tools" / "powershell" / "valley_map_data.ps1"
FRAME = PS1.with_name("ValleyFrame.ps1")  # bounds are shared with build_valley_map.ps1 since 2026-10-17


def _bounds(text):
    get = lambda n: float(re.search(rf"\${n}\s*=\s*([0-9.]+)", text).group(1))
    return get("southBound"), get("northBound"), get("westBound"), get("eastBound")


def _towns(text):
    pat = re.compile(r'Name="([^"]+)";\s*Lat=([0-9.]+);\s*Lon=([0-9.]+)')
    return {m.group(1): (float(m.group(2)), float(m.group(3))) for m in pat.finditer(text)}


def test_lexington_present_with_real_coordinates():
    lat, lon = _towns(PS1.read_text())["Lexington"]
    assert abs(lat - 37.784) < 0.01 and abs(lon - 79.443) < 0.01


def test_all_named_locations_inside_bounds():
    text = PS1.read_text()
    south, north, west, east = _bounds(FRAME.read_text())
    for name, (lat, lon) in _towns(text).items():
        assert south <= lat <= north, name
        assert east <= lon <= west, name  # west longitudes are positive degrees W


def test_lexington_is_southernmost_location():
    towns = _towns(PS1.read_text())
    assert min(towns, key=lambda n: towns[n][0]) == "Lexington"
