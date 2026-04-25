"""
Generate Moo-ready business card PDFs at full bleed size.

Moo Standard Business Card specs:
  Bleed (full canvas / PDF size): 3.66" × 2.16"
  Trim (where Moo cuts):          3.50" × 2.00"
  Safe area (keep text inside):   3.34" × 1.84"

  Bleed margin each side: 0.08" = ~2mm
  Safe area margin from trim: 0.08" = ~2mm
  → Min content padding from bleed edge: 0.16" = ~4mm  (we use 5mm for comfort)

Output: brand/pdf/  — front + back PDF for each version A–D.
Run:    python3 brand/make-card-pdfs.py
"""

import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT  = Path(__file__).parent.parent
BRAND = Path(__file__).parent
OUT   = BRAND / "pdf"
OUT.mkdir(exist_ok=True)

# ── Embed assets ──────────────────────────────────────────────────────────────
def b64(path):
    data = Path(path).read_bytes()
    ext  = Path(path).suffix.lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png"}.get(ext, "png")
    return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"

PHOTO = b64(ROOT / "uploads" / "headshot3.jpg")
QR    = b64(BRAND / "qr-website.png")

# ── CSS ───────────────────────────────────────────────────────────────────────
# PDF page = bleed canvas: 3.66" × 2.16"
# Trim line sits 0.08" (≈2mm) inside the bleed edge on all sides.
# Safe area sits another 0.08" inside the trim line.
# We pad all content at least 5mm from the bleed edge (= 3mm inside safe area).
#
# Photo panel: extends from bleed left edge to 37mm (35mm design + 2mm bleed).
# Backgrounds & borders: extend to full bleed canvas.

BASE_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: 3.66in 2.16in; margin: 0; }
html, body {
  width: 3.66in; height: 2.16in; overflow: hidden;
  font-family: Arial, Helvetica, sans-serif;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

/* ─────────────────────────────────────────────
   FRONT — No photo
   Canvas: 3.66"×2.16" (bleed)
   Content padding: 5mm from bleed edge
───────────────────────────────────────────── */
.front-nophoto {
  width: 3.66in; height: 2.16in;
  background: #faf7f4;
  border-top: 0.9mm solid #670d00;
  display: flex; flex-direction: column; justify-content: center;
  padding: 5mm 6.5mm;
  position: relative;
}
.fn-name  { font-family: Georgia,serif; font-size: 9.6pt; font-weight: bold;
            color: #3d0800; line-height: 1.15; margin-bottom: 1.1mm; }
.fn-cred  { font-size: 4.3pt; color: #8a7a72; line-height: 1.65; margin-bottom: 1.9mm; }
.fn-rule  { border: none; border-top: 0.2mm solid #ddd5cf; margin-bottom: 1.9mm; }
.fn-spec  { font-size: 4.2pt; text-transform: uppercase; letter-spacing: 0.11em;
            color: #8a7a72; margin-bottom: 1.9mm; }
.fn-rows  { display: flex; flex-direction: column; gap: 0.5mm; }
.fn-row   { display: flex; align-items: baseline; gap: 1.7mm; font-size: 4.6pt; }
.fn-lbl   { font-size: 3.8pt; text-transform: uppercase; letter-spacing: 0.08em;
            color: #8a7a72; width: 5.8mm; flex-shrink: 0; }
.fn-val   { color: #3a3230; }

/* ─────────────────────────────────────────────
   FRONT — With photo
   Photo panel: 37mm wide (bleeds 2mm off left edge)
   Text content: padded 5mm from right/top/bottom bleed edges
───────────────────────────────────────────── */
.front-photo {
  width: 3.66in; height: 2.16in;
  background: #faf7f4;
  border-top: 0.9mm solid #670d00;
  display: flex;
  position: relative;
}
.fp-photo { width: 37mm; flex-shrink: 0; overflow: hidden; }
.fp-photo img { width: 100%; height: 100%; object-fit: cover;
                object-position: center 10%; display: block; }
.fp-content {
  flex: 1;
  display: flex; flex-direction: column; justify-content: center;
  padding: 4mm 5.5mm 4mm 3.5mm;
  border-left: 0.5mm solid #670d00;
}
.fp-name  { font-family: Georgia,serif; font-size: 7.9pt; font-weight: bold;
            color: #3d0800; line-height: 1.15; margin-bottom: 0.9mm; }
.fp-cred  { font-size: 4pt; color: #8a7a72; line-height: 1.65; margin-bottom: 1.5mm; }
.fp-rule  { border: none; border-top: 0.2mm solid #ddd5cf; margin-bottom: 1.5mm; }
.fp-rows  { display: flex; flex-direction: column; gap: 0.5mm; }
.fp-row   { display: flex; align-items: baseline; gap: 1.4mm; font-size: 4.3pt; }
.fp-lbl   { font-size: 3.6pt; text-transform: uppercase; letter-spacing: 0.08em;
            color: #8a7a72; width: 5.1mm; flex-shrink: 0; }
.fp-val   { color: #3a3230; }

/* QR code — bottom-right, inside safe area */
.qr { position: absolute; bottom: 4mm; right: 4.5mm;
      width: 11mm; height: 11mm; display: block; }

/* ─────────────────────────────────────────────
   BACK — Burgundy full-bleed
   Text centred, well inside safe area
───────────────────────────────────────────── */
.back-card {
  width: 3.66in; height: 2.16in;
  background: #670d00;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.back-eyebrow  { font-size: 3.8pt; text-transform: uppercase; letter-spacing: 0.18em;
                 color: rgba(255,255,255,0.45); margin-bottom: 2mm; }
.back-name     { font-family: Georgia,serif; font-size: 7.2pt; font-weight: bold;
                 color: #fff; letter-spacing: 0.02em; margin-bottom: 2mm; }
.back-rule     { width: 7.5mm; border: none;
                 border-top: 0.2mm solid rgba(255,255,255,0.28); margin-bottom: 2mm; }
.back-specialty{ font-size: 4.1pt; text-transform: uppercase; letter-spacing: 0.14em;
                 color: rgba(255,255,255,0.65); margin-bottom: 0.9mm; }
.back-location { font-size: 3.8pt; color: rgba(255,255,255,0.4);
                 letter-spacing: 0.06em; margin-bottom: 2.4mm; }
.back-url      { font-size: 4.1pt; color: rgba(255,255,255,0.38); letter-spacing: 0.06em; }
"""

# ── HTML fragments ────────────────────────────────────────────────────────────
BACK_HTML = """
<div class="back-card">
  <div class="back-eyebrow">Private Practice</div>
  <div class="back-name">David Dayan-Rosenman, MD</div>
  <hr class="back-rule">
  <div class="back-specialty">Mental Health &amp; Addiction Care</div>
  <div class="back-location">Cambridge, MA &nbsp;&middot;&nbsp; Telehealth in MA &amp; NY</div>
  <div class="back-url">www.dayan-rosenman.net</div>
</div>
"""

FRONT_NOPHOTO = """
<div class="front-nophoto">
  <div class="fn-name">David Dayan-Rosenman, MD</div>
  <div class="fn-cred">
    Board Certified in Addiction Medicine &amp; Internal Medicine<br>
    Instructor in Psychiatry, Harvard Medical School
  </div>
  <hr class="fn-rule">
  <div class="fn-spec">Mental Health &amp; Addiction Care &nbsp;&middot;&nbsp; Cambridge, MA</div>
  <div class="fn-rows">
    <div class="fn-row"><span class="fn-lbl">Phone</span><span class="fn-val">(617) 528-0538</span></div>
    <div class="fn-row"><span class="fn-lbl">Email</span><span class="fn-val">david@dayan-rosenman.net</span></div>
    <div class="fn-row"><span class="fn-lbl">Web</span><span class="fn-val">www.dayan-rosenman.net</span></div>
    <div class="fn-row"><span class="fn-lbl">Office</span><span class="fn-val">1 Arnold Circle, Cambridge, MA 02139</span></div>
  </div>
</div>
"""

FRONT_NOPHOTO_QR = """
<div class="front-nophoto">
  <div class="fn-name">David Dayan-Rosenman, MD</div>
  <div class="fn-cred">
    Board Certified in Addiction Medicine &amp; Internal Medicine<br>
    Instructor in Psychiatry, Harvard Medical School
  </div>
  <hr class="fn-rule">
  <div class="fn-spec">Mental Health &amp; Addiction Care &nbsp;&middot;&nbsp; Cambridge, MA</div>
  <div class="fn-rows">
    <div class="fn-row"><span class="fn-lbl">Phone</span><span class="fn-val">(617) 528-0538</span></div>
    <div class="fn-row"><span class="fn-lbl">Email</span><span class="fn-val">david@dayan-rosenman.net</span></div>
    <div class="fn-row"><span class="fn-lbl">Office</span><span class="fn-val">1 Arnold Circle, Cambridge, MA 02139</span></div>
  </div>
  <img class="qr" src="{QR}" alt="QR">
</div>
"""

FRONT_PHOTO = """
<div class="front-photo">
  <div class="fp-photo"><img src="{PHOTO}" alt="Dr. David Dayan-Rosenman"></div>
  <div class="fp-content">
    <div class="fp-name">David Dayan-Rosenman, MD</div>
    <div class="fp-cred">
      Board Certified in Addiction Medicine &amp; Internal Medicine<br>
      Instructor in Psychiatry, Harvard Medical School
    </div>
    <hr class="fp-rule">
    <div class="fp-rows">
      <div class="fp-row"><span class="fp-lbl">Phone</span><span class="fp-val">(617) 528-0538</span></div>
      <div class="fp-row"><span class="fp-lbl">Email</span><span class="fp-val">david@dayan-rosenman.net</span></div>
      <div class="fp-row"><span class="fp-lbl">Web</span><span class="fp-val">www.dayan-rosenman.net</span></div>
      <div class="fp-row"><span class="fp-lbl">Office</span><span class="fp-val">1 Arnold Circle, Cambridge MA 02139</span></div>
    </div>
  </div>
</div>
"""

FRONT_PHOTO_QR = """
<div class="front-photo">
  <div class="fp-photo"><img src="{PHOTO}" alt="Dr. David Dayan-Rosenman"></div>
  <div class="fp-content">
    <div class="fp-name">David Dayan-Rosenman, MD</div>
    <div class="fp-cred">
      Board Certified in Addiction Medicine &amp; Internal Medicine<br>
      Instructor in Psychiatry, Harvard Medical School
    </div>
    <hr class="fp-rule">
    <div class="fp-rows">
      <div class="fp-row"><span class="fp-lbl">Phone</span><span class="fp-val">(617) 528-0538</span></div>
      <div class="fp-row"><span class="fp-lbl">Email</span><span class="fp-val">david@dayan-rosenman.net</span></div>
      <div class="fp-row"><span class="fp-lbl">Office</span><span class="fp-val">1 Arnold Circle, Cambridge MA 02139</span></div>
    </div>
  </div>
  <img class="qr" src="{QR}" alt="QR">
</div>
"""

def page_html(body):
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<style>{BASE_CSS}</style>
</head><body>
{body}
</body></html>"""

VERSIONS = [
    ("A-no-photo",      FRONT_NOPHOTO,      BACK_HTML),
    ("B-with-photo",    FRONT_PHOTO,         BACK_HTML),
    ("C-no-photo-qr",   FRONT_NOPHOTO_QR,   BACK_HTML),
    ("D-with-photo-qr", FRONT_PHOTO_QR,     BACK_HTML),
]

PDF_OPTS = dict(
    width="3.66in", height="2.16in",
    print_background=True,
    margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
)

def generate():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, front_tpl, back_tpl in VERSIONS:
            front_html = page_html(front_tpl.replace("{PHOTO}", PHOTO).replace("{QR}", QR))
            back_html  = page_html(back_tpl)

            pg = browser.new_page()
            pg.set_content(front_html, wait_until="networkidle")
            (OUT / f"card-{name}-front.pdf").write_bytes(pg.pdf(**PDF_OPTS))
            pg.close()

            pg = browser.new_page()
            pg.set_content(back_html, wait_until="networkidle")
            (OUT / f"card-{name}-back.pdf").write_bytes(pg.pdf(**PDF_OPTS))
            pg.close()

            print(f"✓  card-{name}-front.pdf  +  card-{name}-back.pdf")

        browser.close()
    print(f"\nAll PDFs saved to {OUT}/")
    print("Page size: 3.66\" × 2.16\" (Moo bleed canvas)")
    print("Trim line: 0.08\" inside each edge  |  Safe area: 0.16\" inside each edge")

if __name__ == "__main__":
    generate()
