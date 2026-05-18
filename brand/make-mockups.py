"""
Final card design — Version D (photo) and Version A (no photo).
No lisere. Single vCard QR on back. Icon labels on front.

Outputs:
  pdf/card-D-front.pdf   — with photo
  pdf/card-D-back.pdf    — shared back
  pdf/card-A-front.pdf   — no photo
  pdf/card-A-back.pdf    — shared back (identical)

Run:  python3 brand/make-mockups.py
"""

import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT  = Path(__file__).parent.parent
BRAND = Path(__file__).parent
OUT   = BRAND / "pdf"
OUT.mkdir(exist_ok=True)

def b64(path):
    data = Path(path).read_bytes()
    ext  = Path(path).suffix.lstrip(".")
    mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png"}.get(ext,"png")
    return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"

PHOTO       = b64(ROOT / "uploads" / "headshot3.jpg")
QR_VCARD    = b64(BRAND / "qr-vcard-styled.png")

W, H = "3.66in", "2.16in"
PW   = "37mm"

# ── Icons ─────────────────────────────────────────────────────────────────────
ICON_PHONE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 5.17 12.8 19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>'
ICON_EMAIL  = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>'
ICON_PIN    = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>'

# ── Front D (with photo) CSS ──────────────────────────────────────────────────
FRONT_D_CSS = f"""
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
@page {{ size: {W} {H}; margin: 0; }}
html, body {{
  width: {W}; height: {H}; overflow: hidden;
  font-family: Arial, Helvetica, sans-serif;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
  background: #faf7f4;
}}
.card {{ width: {W}; height: {H}; display: flex; background: #faf7f4; }}

/* Photo: bleeds full height; pushed down so hair clears safe-area line */
.fp-photo {{
  width: {PW}; flex-shrink: 0; overflow: hidden; background: #faf7f4;
}}
.fp-photo img {{
  width: 100%; height: calc(100% - 4.5mm); margin-top: 4.5mm;
  object-fit: cover; object-position: 45% 0%; display: block;
}}

/* Content panel */
.fp-content {{
  flex: 1; display: flex; flex-direction: column; justify-content: center;
  padding: 4mm 5.5mm 4mm 3.5mm;
  border-left: 0.5mm solid #670d00;
}}
.fp-name {{ font-family: Georgia,serif; font-size: 7.9pt; font-weight: bold;
           color: #3d0800; line-height: 1.15; margin-bottom: 1mm; }}
.fp-cred {{ font-size: 4pt; color: #8a7a72; line-height: 1.65; margin-bottom: 1.6mm; }}
.fp-rule {{ border: none; border-top: 0.2mm solid #ddd5cf; margin-bottom: 1.6mm; }}
.fp-rows {{ display: flex; flex-direction: column; gap: 0.7mm; }}
.fp-row  {{ display: flex; align-items: center; gap: 1.5mm; }}
.fp-icon {{ width: 3.6pt; height: 3.6pt; flex-shrink: 0; color: #8a7a72; display: block; }}
.fp-icon svg {{ width: 100%; height: 100%; }}
.fp-val  {{ font-size: 4.3pt; color: #3a3230; }}
"""

# ── Front A (no photo) CSS ────────────────────────────────────────────────────
FRONT_A_CSS = f"""
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
@page {{ size: {W} {H}; margin: 0; }}
html, body {{
  width: {W}; height: {H}; overflow: hidden;
  font-family: Arial, Helvetica, sans-serif;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
  background: #faf7f4;
}}
.card {{
  width: {W}; height: {H};
  background: #faf7f4;
  display: flex; flex-direction: column; justify-content: center;
  padding: 5mm 7mm;
  border-left: 3mm solid #670d00;   /* strong left accent in lieu of photo */
}}
.fn-name {{ font-family: Georgia,serif; font-size: 10pt; font-weight: bold;
           color: #3d0800; line-height: 1.15; margin-bottom: 1.1mm; }}
.fn-cred {{ font-size: 4.4pt; color: #8a7a72; line-height: 1.65; margin-bottom: 2mm; }}
.fn-rule {{ border: none; border-top: 0.2mm solid #ddd5cf; margin-bottom: 2mm; }}
.fn-spec {{ font-size: 4.3pt; text-transform: uppercase; letter-spacing: 0.1em;
           color: #8a7a72; margin-bottom: 2mm; }}
.fn-rows {{ display: flex; flex-direction: column; gap: 0.7mm; }}
.fn-row  {{ display: flex; align-items: center; gap: 1.7mm; }}
.fn-icon {{ width: 3.8pt; height: 3.8pt; flex-shrink: 0; color: #8a7a72; display: block; }}
.fn-icon svg {{ width: 100%; height: 100%; }}
.fn-val  {{ font-size: 4.6pt; color: #3a3230; }}
"""

# ── Back CSS ──────────────────────────────────────────────────────────────────
BACK_CSS = f"""
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
@page {{ size: {W} {H}; margin: 0; }}
html, body {{
  width: {W}; height: {H}; overflow: hidden;
  font-family: Arial, Helvetica, sans-serif;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
  background: #670d00;
}}
.back {{
  width: {W}; height: {H}; background: #670d00;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0;
}}
.back-eyebrow  {{ font-size: 3.8pt; text-transform: uppercase; letter-spacing: 0.18em;
                  color: rgba(255,255,255,0.4); margin-bottom: 2mm; }}
.back-name     {{ font-family: Georgia,serif; font-size: 7.5pt; font-weight: bold;
                  color: #fff; letter-spacing: 0.02em; margin-bottom: 2mm; }}
.back-rule     {{ width: 7mm; border: none;
                  border-top: 0.2mm solid rgba(255,255,255,0.25); margin-bottom: 2mm; }}
.back-spec     {{ font-size: 4.1pt; text-transform: uppercase; letter-spacing: 0.14em;
                  color: rgba(255,255,255,0.6); margin-bottom: 0.9mm; }}
.back-loc      {{ font-size: 3.8pt; color: rgba(255,255,255,0.38);
                  letter-spacing: 0.05em; margin-bottom: 4mm; }}
.back-qr       {{ width: 18mm; height: 18mm; display: block; margin-bottom: 1.8mm; }}
.back-cta      {{ font-size: 3.4pt; text-transform: uppercase; letter-spacing: 0.15em;
                  color: rgba(255,255,255,0.45); }}
"""

# ── HTML ──────────────────────────────────────────────────────────────────────
FRONT_D_HTML = f"""
<div class="card">
  <div class="fp-photo">
    <img src="{PHOTO}" alt="Dr. David Dayan-Rosenman">
  </div>
  <div class="fp-content">
    <div class="fp-name">David Dayan-Rosenman, MD</div>
    <div class="fp-cred">Board Certified in Addiction Medicine &amp; Internal Medicine<br>
      Instructor in Psychiatry, Harvard Medical School</div>
    <hr class="fp-rule">
    <div class="fp-rows">
      <div class="fp-row">
        <span class="fp-icon">{ICON_PHONE}</span>
        <span class="fp-val">(617) 528-0538</span>
      </div>
      <div class="fp-row">
        <span class="fp-icon">{ICON_EMAIL}</span>
        <span class="fp-val">david@dayan-rosenman.net</span>
      </div>
      <div class="fp-row">
        <span class="fp-icon">{ICON_PIN}</span>
        <span class="fp-val">1 Arnold Circle, Cambridge MA 02139</span>
      </div>
    </div>
  </div>
</div>"""

FRONT_A_HTML = f"""
<div class="card">
  <div class="fn-name">David Dayan-Rosenman, MD</div>
  <div class="fn-cred">Board Certified in Addiction Medicine &amp; Internal Medicine<br>
    Instructor in Psychiatry, Harvard Medical School</div>
  <hr class="fn-rule">
  <div class="fn-spec">Mental Health &amp; Addiction Care &nbsp;&middot;&nbsp; Cambridge, MA</div>
  <div class="fn-rows">
    <div class="fn-row">
      <span class="fn-icon">{ICON_PHONE}</span>
      <span class="fn-val">(617) 528-0538</span>
    </div>
    <div class="fn-row">
      <span class="fn-icon">{ICON_EMAIL}</span>
      <span class="fn-val">david@dayan-rosenman.net</span>
    </div>
    <div class="fn-row">
      <span class="fn-icon">{ICON_PIN}</span>
      <span class="fn-val">1 Arnold Circle, Cambridge, MA 02139</span>
    </div>
  </div>
</div>"""

BACK_HTML = f"""
<div class="back">
  <div class="back-eyebrow">Private Practice</div>
  <div class="back-name">David Dayan-Rosenman, MD</div>
  <hr class="back-rule">
  <div class="back-spec">Mental Health &amp; Addiction Care</div>
  <div class="back-loc">Cambridge, MA &nbsp;&middot;&nbsp; Telehealth in MA &amp; NY</div>
  <img class="back-qr" src="{QR_VCARD}" alt="Scan to add contact">
  <div class="back-cta">Scan to add contact</div>
</div>"""

# ── Render ────────────────────────────────────────────────────────────────────
def render(browser, css, body, filename):
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<style>{css}</style></head><body>{body}</body></html>"""
    pg = browser.new_page()
    pg.set_content(html, wait_until="networkidle")
    pdf = pg.pdf(width=W, height=H, print_background=True,
                 margin={"top":"0","bottom":"0","left":"0","right":"0"})
    pg.close()
    path = OUT / filename
    path.write_bytes(pdf)
    print(f"  ✓  {filename}")
    return path

def generate():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        paths = [
            render(browser, FRONT_D_CSS, FRONT_D_HTML, "card-D-front.pdf"),
            render(browser, BACK_CSS,    BACK_HTML,    "card-D-back.pdf"),
            render(browser, FRONT_A_CSS, FRONT_A_HTML, "card-A-front.pdf"),
            render(browser, BACK_CSS,    BACK_HTML,    "card-A-back.pdf"),
        ]
        browser.close()
    return paths

if __name__ == "__main__":
    import subprocess
    paths = generate()
    subprocess.run(["open"] + [str(p) for p in paths])
    print("\nOpened all 4 PDFs in Preview.")
