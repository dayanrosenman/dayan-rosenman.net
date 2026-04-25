"""
Generate Moo-ready business card PDFs.
Output: brand/pdf/  — one PDF per version (A/B/C/D), 2 pages each (front + back).
Card trim size: 89 × 51 mm  (Moo Standard Business Card).
Run:  python3 brand/make-card-pdfs.py
"""

import base64, os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT   = Path(__file__).parent.parent          # repo root
BRAND  = Path(__file__).parent
OUT    = BRAND / "pdf"
OUT.mkdir(exist_ok=True)

# ── Embed assets as base64 ────────────────────────────────────────────────────
def b64(path):
    data = Path(path).read_bytes()
    ext  = Path(path).suffix.lstrip(".")
    mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png"}.get(ext,"png")
    return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"

PHOTO = b64(ROOT / "uploads" / "headshot3.jpg")
QR    = b64(BRAND / "qr-website.png")

# ── Shared CSS (mm-based, 89×51mm card) ──────────────────────────────────────
BASE_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: 89mm 51mm; margin: 0; }
html, body {
  width: 89mm; height: 51mm; overflow: hidden;
  font-family: Arial, Helvetica, sans-serif;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

/* ── FRONT — no photo ────────────────────────── */
.front-nophoto {
  width: 89mm; height: 51mm;
  background: #faf7f4;
  border-top: 0.9mm solid #670d00;
  display: flex; flex-direction: column; justify-content: center;
  padding: 4.5mm 6mm;
  position: relative;
}
.fn-name  { font-family: Georgia,serif; font-size: 9.6pt; font-weight: bold; color: #3d0800; line-height: 1.15; margin-bottom: 1.1mm; }
.fn-cred  { font-size: 4.3pt; color: #8a7a72; line-height: 1.65; margin-bottom: 1.9mm; }
.fn-rule  { border: none; border-top: 0.2mm solid #ddd5cf; margin-bottom: 1.9mm; }
.fn-spec  { font-size: 4.2pt; text-transform: uppercase; letter-spacing: 0.11em; color: #8a7a72; margin-bottom: 1.9mm; }
.fn-rows  { display: flex; flex-direction: column; gap: 0.5mm; }
.fn-row   { display: flex; align-items: baseline; gap: 1.7mm; font-size: 4.6pt; }
.fn-lbl   { font-size: 3.8pt; text-transform: uppercase; letter-spacing: 0.08em; color: #8a7a72; width: 5.8mm; flex-shrink: 0; }
.fn-val   { color: #3a3230; }

/* ── FRONT — with photo ──────────────────────── */
.front-photo {
  width: 89mm; height: 51mm;
  background: #faf7f4;
  border-top: 0.9mm solid #670d00;
  display: flex;
  position: relative;
}
.fp-photo { width: 35mm; flex-shrink: 0; overflow: hidden; }
.fp-photo img { width: 100%; height: 100%; object-fit: cover; object-position: center 10%; display: block; }
.fp-content {
  flex: 1; display: flex; flex-direction: column; justify-content: center;
  padding: 3mm 4mm 3mm 3mm;
  border-left: 0.5mm solid #670d00;
}
.fp-name  { font-family: Georgia,serif; font-size: 7.9pt; font-weight: bold; color: #3d0800; line-height: 1.15; margin-bottom: 0.9mm; }
.fp-cred  { font-size: 4pt; color: #8a7a72; line-height: 1.65; margin-bottom: 1.5mm; }
.fp-rule  { border: none; border-top: 0.2mm solid #ddd5cf; margin-bottom: 1.5mm; }
.fp-rows  { display: flex; flex-direction: column; gap: 0.5mm; }
.fp-row   { display: flex; align-items: baseline; gap: 1.4mm; font-size: 4.3pt; }
.fp-lbl   { font-size: 3.6pt; text-transform: uppercase; letter-spacing: 0.08em; color: #8a7a72; width: 5.1mm; flex-shrink: 0; }
.fp-val   { color: #3a3230; }

/* ── QR code (versions C & D) ───────────────── */
.qr { position: absolute; bottom: 2mm; right: 2.4mm; width: 11mm; height: 11mm; display: block; }

/* ── BACK (all versions) ─────────────────────── */
.back-card {
  width: 89mm; height: 51mm;
  background: #670d00;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.back-eyebrow  { font-size: 3.8pt; text-transform: uppercase; letter-spacing: 0.18em; color: rgba(255,255,255,0.45); margin-bottom: 2mm; }
.back-name     { font-family: Georgia,serif; font-size: 7.2pt; font-weight: bold; color: #fff; letter-spacing: 0.02em; margin-bottom: 2mm; }
.back-rule     { width: 7.5mm; border: none; border-top: 0.2mm solid rgba(255,255,255,0.28); margin-bottom: 2mm; }
.back-specialty{ font-size: 4.1pt; text-transform: uppercase; letter-spacing: 0.14em; color: rgba(255,255,255,0.65); margin-bottom: 0.9mm; }
.back-location { font-size: 3.8pt; color: rgba(255,255,255,0.4); letter-spacing: 0.06em; margin-bottom: 2.4mm; }
.back-url      { font-size: 4.1pt; color: rgba(255,255,255,0.38); letter-spacing: 0.06em; }
"""

# ── Card HTML fragments ───────────────────────────────────────────────────────
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

def page_html(body_html):
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<style>{BASE_CSS}</style>
</head><body>
{body_html}
</body></html>"""

# ── Versions: (name, front_html, back_html) ──────────────────────────────────
VERSIONS = [
    ("A-no-photo",        FRONT_NOPHOTO,          BACK_HTML),
    ("B-with-photo",      FRONT_PHOTO,             BACK_HTML),
    ("C-no-photo-qr",     FRONT_NOPHOTO_QR,        BACK_HTML),
    ("D-with-photo-qr",   FRONT_PHOTO_QR,          BACK_HTML),
]

def generate():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        for name, front_tpl, back_tpl in VERSIONS:
            front_html = page_html(front_tpl.replace("{PHOTO}", PHOTO).replace("{QR}", QR))
            back_html  = page_html(back_tpl)

            # Render front PDF bytes
            page = browser.new_page()
            page.set_content(front_html, wait_until="networkidle")
            front_bytes = page.pdf(
                width="89mm", height="51mm",
                print_background=True,
                margin={"top":"0","bottom":"0","left":"0","right":"0"}
            )
            page.close()

            # Render back PDF bytes
            page = browser.new_page()
            page.set_content(back_html, wait_until="networkidle")
            back_bytes = page.pdf(
                width="89mm", height="51mm",
                print_background=True,
                margin={"top":"0","bottom":"0","left":"0","right":"0"}
            )
            page.close()

            # Write separate front / back PDFs
            front_out = OUT / f"card-{name}-front.pdf"
            back_out  = OUT / f"card-{name}-back.pdf"
            front_out.write_bytes(front_bytes)
            back_out.write_bytes(back_bytes)
            print(f"✓  {front_out.name}")
            print(f"✓  {back_out.name}")

        browser.close()
    print(f"\nAll PDFs saved to {OUT}/")

if __name__ == "__main__":
    generate()
