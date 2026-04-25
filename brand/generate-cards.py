#!/usr/bin/env python3
"""Generate Moo-ready PDF business cards (84×55mm, 300 DPI) using Chrome headless.

Output: brand/pdf/card-A.pdf, card-B.pdf, card-C.pdf, card-D.pdf
Each PDF has two pages: page 1 = front, page 2 = back.
"""

import base64
import subprocess
import tempfile
import urllib.request
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BRAND_DIR = Path(__file__).parent
OUT_DIR = BRAND_DIR / "pdf"
HEADSHOT = BRAND_DIR.parent / "uploads" / "headshot3.jpg"

OUT_DIR.mkdir(exist_ok=True)

# ── Encode headshot as data URI ──────────────────────────────────────────────
headshot_b64 = base64.b64encode(HEADSHOT.read_bytes()).decode()
HEADSHOT_URI = f"data:image/jpeg;base64,{headshot_b64}"

# ── Fetch QR code and encode ─────────────────────────────────────────────────
QR_URL = "https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=https%3A%2F%2Fwww.dayan-rosenman.net&color=3d0800&bgcolor=faf7f4&ecc=M&margin=1"
try:
    with urllib.request.urlopen(QR_URL, timeout=10) as r:
        qr_b64 = base64.b64encode(r.read()).decode()
    QR_URI = f"data:image/png;base64,{qr_b64}"
    print("QR code fetched OK")
except Exception as e:
    print(f"Warning: could not fetch QR code ({e}), using URL directly")
    QR_URI = QR_URL

# ── Shared CSS ───────────────────────────────────────────────────────────────
CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: 84mm 55mm; margin: 0; }
html, body { width: 84mm; height: 55mm; background: white; }
* { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }

.card {
  width: 84mm;
  height: 55mm;
  overflow: hidden;
  position: relative;
  page-break-after: always;
  break-after: page;
}

/* ── FRONT — No Photo ── */
.front-nophoto {
  background: #faf7f4;
  border-top: 5px solid #670d00;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 5mm 9mm;
}
.fn-name {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 16.5pt;
  font-weight: bold;
  color: #3d0800;
  line-height: 1.15;
  margin-bottom: 2mm;
}
.fn-cred {
  font-size: 7.5pt;
  color: #8a7a72;
  line-height: 1.65;
  margin-bottom: 3mm;
}
.fn-rule {
  border: none;
  border-top: 1px solid #ddd5cf;
  margin-bottom: 3mm;
}
.fn-specialty {
  font-size: 7.5pt;
  text-transform: uppercase;
  letter-spacing: 0.11em;
  color: #8a7a72;
  margin-bottom: 3mm;
}
.fn-contact { display: flex; flex-direction: column; gap: 1mm; }
.fn-row { display: flex; align-items: baseline; gap: 3mm; font-size: 8pt; }
.fn-lbl {
  font-size: 6.5pt;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #8a7a72;
  width: 9mm;
  flex-shrink: 0;
}
.fn-val { color: #3a3230; }

/* ── FRONT — With Photo ── */
.front-photo {
  background: #faf7f4;
  display: flex;
  border-top: 5px solid #670d00;
}
.fp-photo {
  width: 22mm;
  flex-shrink: 0;
  overflow: hidden;
  background: #e8ddd9;
}
.fp-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
  display: block;
}
.fp-content {
  flex: 1;
  padding: 4mm 5mm 4mm 4mm;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.fp-name {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 13.5pt;
  font-weight: bold;
  color: #3d0800;
  line-height: 1.15;
  margin-bottom: 1.5mm;
}
.fp-cred {
  font-size: 6.5pt;
  color: #8a7a72;
  line-height: 1.6;
  margin-bottom: 2.5mm;
}
.fp-rule {
  border: none;
  border-top: 1px solid #ddd5cf;
  margin-bottom: 2.5mm;
}
.fp-contact { display: flex; flex-direction: column; gap: 0.8mm; }
.fp-row { display: flex; align-items: baseline; gap: 2.5mm; font-size: 7.5pt; }
.fp-lbl {
  font-size: 6pt;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #8a7a72;
  width: 8mm;
  flex-shrink: 0;
}
.fp-val { color: #3a3230; }

/* ── QR code ── */
.qr {
  position: absolute;
  bottom: 3.5mm;
  right: 4mm;
  width: 17mm;
  height: 17mm;
  display: block;
}

/* ── BACK ── */
.back-card {
  background: #670d00;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 6mm 8mm;
}
.back-eyebrow {
  font-size: 6.5pt;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: rgba(255,255,255,0.55);
  margin-bottom: 2mm;
}
.back-name {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 15pt;
  font-weight: bold;
  color: #fff;
  line-height: 1.2;
  margin-bottom: 2mm;
}
.back-rule {
  border: none;
  border-top: 1px solid rgba(255,255,255,0.3);
  width: 24mm;
  margin-bottom: 2mm;
}
.back-specialty {
  font-size: 8pt;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: rgba(255,255,255,0.75);
  margin-bottom: 1.5mm;
}
.back-location {
  font-size: 7.5pt;
  color: rgba(255,255,255,0.55);
  margin-bottom: 2mm;
}
.back-url {
  font-size: 8pt;
  color: rgba(255,255,255,0.85);
  letter-spacing: 0.04em;
}
"""

# ── Back card HTML (shared by all versions) ──────────────────────────────────
BACK_HTML = """
<div class="card back-card">
  <div class="back-eyebrow">Private Practice</div>
  <div class="back-name">David Dayan-Rosenman, MD</div>
  <hr class="back-rule">
  <div class="back-specialty">Mental Health &amp; Addiction Care</div>
  <div class="back-location">Cambridge, MA &nbsp;·&nbsp; Telehealth in MA &amp; NY</div>
  <div class="back-url">www.dayan-rosenman.net</div>
</div>
"""

# ── Front card variants ───────────────────────────────────────────────────────
def front_nophoto(qr=False):
    qr_tag = f'<img class="qr" src="{QR_URI}" alt="">' if qr else ""
    return f"""
<div class="card front-nophoto">
  <div class="fn-name">David Dayan-Rosenman, MD</div>
  <div class="fn-cred">
    Board Certified in Addiction Medicine &amp; Internal Medicine<br>
    Instructor in Psychiatry, Harvard Medical School
  </div>
  <hr class="fn-rule">
  <div class="fn-specialty">Mental Health &amp; Addiction Care &nbsp;·&nbsp; Cambridge, MA</div>
  <div class="fn-contact">
    <div class="fn-row"><span class="fn-lbl">Phone</span><span class="fn-val">(617) 528-0538</span></div>
    <div class="fn-row"><span class="fn-lbl">Email</span><span class="fn-val">david@dayan-rosenman.net</span></div>
    <div class="fn-row"><span class="fn-lbl">Web</span><span class="fn-val">www.dayan-rosenman.net</span></div>
    <div class="fn-row"><span class="fn-lbl">Office</span><span class="fn-val">1 Arnold Circle, Cambridge, MA 02139</span></div>
  </div>
  {qr_tag}
</div>
"""

def front_photo(qr=False):
    qr_tag = f'<img class="qr" src="{QR_URI}" alt="">' if qr else ""
    return f"""
<div class="card front-photo">
  <div class="fp-photo"><img src="{HEADSHOT_URI}" alt="Dr. David Dayan-Rosenman"></div>
  <div class="fp-content">
    <div class="fp-name">David Dayan-Rosenman, MD</div>
    <div class="fp-cred">
      Board Certified in Addiction Medicine &amp; Internal Medicine<br>
      Instructor in Psychiatry, Harvard Medical School
    </div>
    <hr class="fp-rule">
    <div class="fp-contact">
      <div class="fp-row"><span class="fp-lbl">Phone</span><span class="fp-val">(617) 528-0538</span></div>
      <div class="fp-row"><span class="fp-lbl">Email</span><span class="fp-val">david@dayan-rosenman.net</span></div>
      <div class="fp-row"><span class="fp-lbl">Office</span><span class="fp-val">1 Arnold Circle, Cambridge MA 02139</span></div>
    </div>
  </div>
  {qr_tag}
</div>
"""

# ── Build HTML + print to PDF ─────────────────────────────────────────────────
def make_pdf(version_name, front_html):
    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<style>{CSS}</style>
</head><body>
{front_html}
{BACK_HTML}
</body></html>"""

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        tmp = f.name

    out = OUT_DIR / f"card-{version_name}.pdf"
    result = subprocess.run([
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-web-security",
        f"--print-to-pdf={out}",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=5000",
        f"file://{tmp}",
    ], capture_output=True, text=True, timeout=30)

    Path(tmp).unlink(missing_ok=True)

    if out.exists():
        size_kb = out.stat().st_size // 1024
        print(f"  card-{version_name}.pdf  ({size_kb} KB)")
    else:
        print(f"  ERROR generating card-{version_name}.pdf")
        print(result.stderr[-500:] if result.stderr else "(no stderr)")


print("Generating PDFs …")
make_pdf("A", front_nophoto(qr=False))
make_pdf("B", front_photo(qr=False))
make_pdf("C", front_nophoto(qr=True))
make_pdf("D", front_photo(qr=True))
print(f"Done — files in {OUT_DIR}/")
