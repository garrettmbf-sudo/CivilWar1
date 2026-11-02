"""Side-by-side counter sheet: v3.8.1 (left of each pair) vs v3.9 (right), every template, at one
counter size in px.  60 px = real in-game scale on the board art (2 px per world unit, counters are
30 units); 180 px = 3x.  Usage: counter_compare.py old.json new.json out.png [px]"""
import base64, io, json, sys
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/sand-box/google/Playfair Display/PlayfairDisplay-VariableFont_wght.ttf"


def renders(path):
    d = json.load(open(path))
    out = {}
    for t in d["assets"]["unitTemplates"]:
        b = base64.b64decode(t["visuals"]["renderedUrl"].split(",", 1)[1])
        out[t["id"]] = (t["name"], Image.open(io.BytesIO(b)).convert("RGBA"))
    return out


def main(old, new, out, px=60):
    a, b = renders(old), renders(new)
    ids = sorted(a, key=lambda k: int(k.split("_")[1]))
    cols = 5 if px <= 80 else 4
    gap, lab = max(6, px // 10), max(12, px // 6)
    cw, ch = 2 * px + gap * 3, px + lab + gap * 2
    rows = -(-len(ids) // cols)
    head = 40
    W, H = cols * cw + gap, rows * ch + head
    sheet = Image.new("RGB", (W, H), (214, 206, 186))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT, lab - 2)
    fh = ImageFont.truetype(FONT, 20)
    d.text((gap, 10), f"Kernstown counters at {px} px: v3.8.1 (left) | v3.9 (right)", font=fh, fill=(30, 26, 20))
    for i, k in enumerate(ids):
        x, y = gap + (i % cols) * cw, head + (i // cols) * ch
        name = a[k][0] if a[k][0] == b[k][0] else f"{a[k][0]} -> {b[k][0]}"
        for j, im in enumerate((a[k][1], b[k][1])):
            sheet.paste(im.resize((px, px), Image.LANCZOS), (x + j * (px + gap), y), im.resize((px, px), Image.LANCZOS))
        while d.textlength(name, font=f) > cw - gap and len(name) > 4:
            name = name[:-2]
        d.text((x, y + px + 2), name, font=f, fill=(30, 26, 20))
    sheet.save(out, optimize=True)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 60)
