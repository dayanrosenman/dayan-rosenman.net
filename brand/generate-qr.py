"""
Generate polished QR codes for the business card back.
Outputs cream-on-burgundy PNGs at 600px (2mm at 300dpi → very crisp).

Run:  python3 brand/generate-qr.py
"""

from pathlib import Path
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from PIL import Image, ImageDraw

BRAND = Path(__file__).parent

VCARD = """BEGIN:VCARD
VERSION:3.0
FN:David Dayan-Rosenman, MD
N:Dayan-Rosenman;David;;MD;
TITLE:Instructor in Psychiatry, Harvard Medical School
TEL;TYPE=CELL:(617) 528-0538
EMAIL:david@dayan-rosenman.net
URL:https://www.dayan-rosenman.net
ADR;TYPE=WORK:;;1 Arnold Circle;Cambridge;MA;02139;USA
END:VCARD""".strip()

# Burgundy background (#670d00), cream modules (#faf7f4)
BG   = (103, 13, 0)    # #670d00
FG   = (250, 247, 244) # #faf7f4

def make_qr(data, out_path, size=600):
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=20,   # large box_size → render big, then downscale for smoothness
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(radius_ratio=0.5),
    ).convert("RGBA")

    # Replace black→FG (cream) and white→BG (burgundy)
    data_px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = data_px[x, y]
            if r < 128:   # dark module
                data_px[x, y] = FG + (255,)
            else:          # light background
                data_px[x, y] = BG + (255,)

    img = img.convert("RGB").resize((size, size), Image.LANCZOS)
    img.save(out_path)
    print(f"  ✓  {out_path.name}  ({size}×{size}px)")

make_qr(VCARD,                           BRAND / "qr-vcard-styled.png")
make_qr("https://www.dayan-rosenman.net", BRAND / "qr-website-styled.png")
print("Done.")
