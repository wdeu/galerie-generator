#!/usr/bin/env python3
"""
Booklooker Galerie Generator
Generiert direkt eine index.html im Stil von wdeu.de/galerie
- API-Sync mit Booklooker
- Löscht Mehrfachbilder (_2, _3 etc.)
- Verschiebt verkaufte Bücher nach /Verkauft
- Generiert fertige index.html für IONOS Upload
"""

import os
import sys
import re
import shutil
import configparser
from pathlib import Path
from datetime import datetime
import requests

# ============================================================
# KONFIGURATION
# ============================================================
CONFIG_FILE = os.path.expanduser("~/.booklooker-sync.ini")

# ============================================================
# FARBEN
# ============================================================
class C:
    RED    = '\033[0;31m'
    GREEN  = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE   = '\033[0;34m'
    NC     = '\033[0m'

def log(msg):     print(f"{C.BLUE}[{datetime.now().strftime('%H:%M:%S')}]{C.NC} {msg}")
def ok(msg):      print(f"{C.GREEN}✓{C.NC} {msg}")
def warn(msg):    print(f"{C.YELLOW}⚠{C.NC}  {msg}")
def err(msg):     print(f"{C.RED}✗{C.NC}  {msg}"); sys.exit(1)

# ============================================================
# CONFIG LADEN
# ============================================================
def load_config():
    if not os.path.exists(CONFIG_FILE):
        Path(CONFIG_FILE).write_text("""[booklooker]
api_key = DEIN_API_KEY_HIER

[paths]
gallery_path = /Users/wdeupro/Pictures/Galerie
output_path  = /Users/wdeupro/Projects/galerie-generator/public
""")
        err(f"Config erstellt → bitte ausfüllen: {CONFIG_FILE}")

    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE)
    
    # FTP optional laden
    ftp = None
    if cfg.has_section('ftp'):
        ftp = {
            'host':     cfg.get('ftp', 'host'),
            'user':     cfg.get('ftp', 'user'),
            'password': cfg.get('ftp', 'password'),
            'remote':   cfg.get('ftp', 'remote'),
        }
    
    return {
        'api_key':      cfg.get('booklooker', 'api_key'),
        'gallery_path': Path(cfg.get('paths', 'gallery_path')),
        'output_path':  Path(cfg.get('paths', 'output_path')),
        'ftp':          ftp,
    }

# ============================================================
# BOOKLOOKER API
# ============================================================
def get_active_articles(api_key):
    log("Authentifiziere bei Booklooker...")
    r = requests.post(
        "https://api.booklooker.de/2.0/authenticate",
        params={'apiKey': api_key}, timeout=10
    )
    data = r.json()
    if data['status'] != 'OK':
        err(f"Auth fehlgeschlagen: {data['returnValue']}")
    token = data['returnValue']
    ok(f"Token: {token[:20]}...")

    log("Hole Artikelliste...")
    r = requests.get(
        "https://api.booklooker.de/2.0/article_list",
        params={'token': token, 'field': 'orderNo'}, timeout=30
    )
    data = r.json()
    if data['status'] != 'OK':
        err(f"Artikelliste fehlgeschlagen: {data['returnValue']}")

    articles = {
        a.strip().upper()
        for a in data['returnValue'].strip().split('\n')
        if a.strip()
    }
    ok(f"Aktive Artikel: {len(articles)}")
    return articles

# ============================================================
# BILDER BEREINIGEN
# ============================================================
def is_valid(filename):
    """Prüfe ob Dateiname gültig ist (kein _2, _3 Suffix)"""
    stem = Path(filename).stem
    if re.search(r'_\d+$', stem):
        return False, None
    m = re.match(r'^(BLX|BN)\d+', stem, re.IGNORECASE)
    if m:
        return True, m.group(0).upper()
    return False, None

def cleanup(gallery_path, active_articles):
    sold_dir = gallery_path / "Verkauft"
    sold_dir.mkdir(exist_ok=True)

    moved = cleaned = 0
    images = sorted(gallery_path.glob("*.jpg"), key=lambda f: f.name.upper(), reverse=True)

    log(f"Bereinige {len(images)} Bilder...")

    for img in images:
        valid, article_no = is_valid(img.name)

        if not valid:
            warn(f"Lösche Mehrfachbild: {img.name}")
            img.unlink()
            cleaned += 1
            continue

        if article_no not in active_articles:
            target = sold_dir / img.name
            if target.exists():
                target.unlink()
            warn(f"Verschiebe verkauft: {img.name}")
            shutil.move(str(img), str(target))
            moved += 1

    ok(f"Bereinigt: {cleaned} Mehrfachbilder gelöscht, {moved} verkaufte verschoben")
    return moved, cleaned

# ============================================================
# HTML GENERIEREN
# ============================================================
def generate_html(gallery_path, output_path):
    images = sorted(gallery_path.glob("*.jpg"), key=lambda f: f.name.upper(), reverse=True)
    ok(f"Generiere Galerie mit {len(images)} Bildern...")

    # Baue Bild-Tags
    items_html = ""
    for img in images:
        stem   = img.stem.upper()          # z.B. BN00561
        fname  = img.name.lower()          # z.B. bn00561.jpg

        items_html += f"""
    <div class="item">
      <a href="images/{fname}" data-lightbox="galerie" data-title="{stem}">
        <img src="images/{fname}" alt="{stem}" title="{stem}" loading="lazy">
      </a>
      <div class="label">{stem}</div>
    </div>"""

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    count = len(images)

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bücherkiste – wdeu bei Booklooker.de</title>

  <!-- Lightbox2 -->
  <link rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/lightbox2/2.11.4/css/lightbox.min.css">

  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@300;400;700&display=swap"
        rel="stylesheet">

  <style>
    /* ── Reset & Base ── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      background: #f4f2ee;
      font-family: 'Raleway', sans-serif;
      color: #333;
    }}

    /* ── Header ── */
    header {{
      background: #fff;
      border-bottom: 2px solid #e0ddd5;
      padding: 18px 24px 14px;
      position: sticky;
      top: 0;
      z-index: 100;
    }}

    header h1 {{
      font-size: 22px;
      font-weight: 700;
      letter-spacing: 0.04em;
      margin-bottom: 2px;
    }}

    header .sub {{
      font-size: 13px;
      font-weight: 300;
      color: #848681;
    }}

    header .hint {{
      font-size: 11px;
      color: #37677B;
      margin-top: 4px;
    }}

    header .bl-link {{
      display: inline-block;
      margin-top: 8px;
      padding: 6px 14px;
      background: #37677B;
      color: #fff;
      text-decoration: none;
      border-radius: 4px;
      font-size: 13px;
      font-weight: 500;
      transition: background 0.2s;
    }}
    header .bl-link:hover {{ background: #2a4f5f; }}

    header .stats {{
      font-size: 11px;
      color: #aaa;
      margin-top: 6px;
    }}

    /* ── Grid ── */
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
      gap: 12px;
      padding: 20px;
    }}

    @media (max-width: 480px) {{
      .grid {{
        grid-template-columns: repeat(auto-fill, minmax(95px, 1fr));
        gap: 8px;
        padding: 12px;
      }}
    }}

    @media (min-width: 1400px) {{
      .grid {{
        grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
        gap: 10px;
      }}
    }}

    /* ── Item ── */
    .item {{
      display: flex;
      flex-direction: column;
      align-items: center;
      background: #fff;
      border-radius: 6px;
      overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
      transition: transform 0.15s, box-shadow 0.15s;
    }}

    .item:hover {{
      transform: translateY(-3px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}

    .item a {{
      display: block;
      width: 100%;
    }}

    .item img {{
      width: 100%;
      height: auto;
      display: block;
      object-fit: cover;
    }}

    /* ── Artikelnummer-Label ── */
    .label {{
      font-family: 'Courier New', monospace;
      font-size: 11px;
      font-weight: bold;
      color: #37677B;
      padding: 5px 4px 6px;
      text-align: center;
      letter-spacing: 0.03em;
      width: 100%;
      background: #f9f8f6;
      border-top: 1px solid #eee;
    }}

    /* ── Footer ── */
    footer {{
      text-align: center;
      padding: 24px;
      font-size: 12px;
      color: #aaa;
      border-top: 1px solid #e0ddd5;
      margin-top: 12px;
    }}
  </style>
</head>
<body>

<header>
  <h1>Bücherkiste</h1>
  <div class="sub">wdeu bei Booklooker.de</div>
  <div class="hint">Artikelnummer steht unter jedem Cover</div>
  <a class="bl-link"
     href="https://www.booklooker.de/wdeu/B%C3%BCcher/Angebote/?sortOrder=offerDate&sortDirection=desc"
     target="_blank">zu Booklooker.de &rsaquo;&rsaquo;</a>
  <div class="stats">{count} Bücher · Stand: {now}</div>
</header>

<main>
  <div class="grid">{items_html}
  </div>
</main>

<footer>
  Fachbücher Psychologie &amp; Sozialwissenschaften · wdeu bei Booklooker.de
</footer>

<!-- Lightbox2 -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/lightbox2/2.11.4/js/lightbox.min.js"></script>
<script>
  lightbox.option({{
    'resizeDuration': 200,
    'wrapAround': true,
    'albumLabel': 'Bild %1 von %2',
    'fadeDuration': 150
  }});
</script>

</body>
</html>"""

    # Output-Ordner anlegen
    output_path.mkdir(parents=True, exist_ok=True)
    images_out = output_path / "images"
    images_out.mkdir(exist_ok=True)

    # HTML schreiben
    html_file = output_path / "index.html"
    html_file.write_text(html, encoding='utf-8')
    ok(f"index.html → {html_file}")

    # Bilder kopieren/verlinken
    log("Kopiere Bilder nach public/images/ ...")
    copied = 0
    for img in images:
        target = images_out / img.name.lower()
        if not target.exists() or target.stat().st_mtime < img.stat().st_mtime:
            shutil.copy2(str(img), str(target))
            copied += 1

    ok(f"{copied} Bilder neu kopiert ({len(images)} gesamt)")
    return len(images)

# ============================================================
# MAIN
# ============================================================
def main():
    print("═" * 56)
    print("  📚 Booklooker Galerie Generator")
    print("═" * 56)
    print()

    cfg = load_config()

    # 1. API
    active = get_active_articles(cfg['api_key'])

    # 2. Bilder bereinigen
    print()
    cleanup(cfg['gallery_path'], active)

    # 3. Galerie generieren
    print()
    count = generate_html(cfg['gallery_path'], cfg['output_path'])

    print()
    print("═" * 56)
    ok(f"Fertig! {count} Bücher in Galerie.")
    print()
    print(f"  📁 Output: {cfg['output_path']}")
    print(f"  🌐 Preview: open {cfg['output_path']}/index.html")
    print()
    print(f"  💡 Upload: Inhalt von public/ mit Forklift nach")
    print(f"     /galerie/buecher/ auf IONOS hochladen")
    print("═" * 56)

if __name__ == "__main__":
    main()
