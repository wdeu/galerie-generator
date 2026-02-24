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
    # Plattformübergreifende Defaults
    DOWNLOADS    = Path.home() / "Downloads"
    DEFAULT_IN   = DOWNLOADS
    DEFAULT_OUT  = DOWNLOADS / "galerie-output"

    if not os.path.exists(CONFIG_FILE):
        Path(CONFIG_FILE).write_text(f"""[booklooker]
api_key = DEIN_API_KEY_HIER

# Bestellnummer-Präfixe deiner Booklooker-Artikel (kommagetrennt).
# BN  = Einzeltitel-Inserat
# BLX = CSV-Massenupload
# Booklooker erlaubt eigene Präfixe – trage hier alle ein die du verwendest.
# Beispiel: order_prefix = BN,BLX,MGB
order_prefix = BN,BLX

# [paths] ist optional – ohne diesen Abschnitt werden die Defaults verwendet:
#   gallery_path = {DEFAULT_IN}   (BL-Bilder aus Downloads)
#   output_path  = {DEFAULT_OUT}  (fertige Galerie)
#
# Nur eintragen wenn du andere Ordner möchtest:
# [paths]
# gallery_path = {DEFAULT_IN}
# output_path  = {DEFAULT_OUT}

# Optional: WordPress-Seite mit Booklooker-Plugin für Direktlinks.
# Wenn eingetragen, wird jedes Cover direkt mit dem Einzelartikel verknüpft.
# Voraussetzung: WordPress + wordpress-booklooker-bot Plugin
#
# [wordpress]
# url = https://deine-domain.de/deine-buchseite
""")
        err(f"Config erstellt → bitte API-Key eintragen: {CONFIG_FILE}")

    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE)

    # Pfade: Config überschreibt Default
    gallery_path = Path(cfg.get('paths', 'gallery_path', fallback=str(DEFAULT_IN)))
    output_path  = Path(cfg.get('paths', 'output_path',  fallback=str(DEFAULT_OUT)))

    # FTP optional
    ftp = None
    if cfg.has_section('ftp'):
        ftp = {
            'host':     cfg.get('ftp', 'host'),
            'user':     cfg.get('ftp', 'user'),
            'password': cfg.get('ftp', 'password'),
            'remote':   cfg.get('ftp', 'remote'),
        }

    # WordPress optional
    wp_url = None
    if cfg.has_section('wordpress'):
        wp_url = cfg.get('wordpress', 'url', fallback=None)

    # Bestellnummer-Präfixe
    raw_prefix   = cfg.get('booklooker', 'order_prefix', fallback='BN,BLX')
    order_prefix = [p.strip().upper() for p in raw_prefix.split(',') if p.strip()]

    return {
        'api_key':      cfg.get('booklooker', 'api_key'),
        'gallery_path': gallery_path,
        'output_path':  output_path,
        'ftp':          ftp,
        'wp_url':       wp_url,
        'order_prefix': order_prefix,
    }

# ============================================================
# BOOKLOOKER API
# ============================================================
def get_article_data(api_key):
    """Holt orderNo, ISBN und Preis pro Artikel. Gibt zurück:
       articles_set  – set aller orderNos (für cleanup)
       article_info  – dict: orderNo → {'isbn': ..., 'price': ...}
    """
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

    # Aufruf 1: orderNo-Liste
    log("Hole Artikelliste (orderNo)...")
    r = requests.get(
        "https://api.booklooker.de/2.0/article_list",
        params={'token': token, 'field': 'orderNo'}, timeout=30
    )
    data = r.json()
    if data['status'] != 'OK':
        err(f"Artikelliste fehlgeschlagen: {data['returnValue']}")
    order_nos = [a.strip().upper() for a in data['returnValue'].strip().split('\n') if a.strip()]
    ok(f"Aktive Artikel: {len(order_nos)}")

    # Aufruf 2: ISBN + Preis
    log("Hole ISBN + Preise...")
    r = requests.get(
        "https://api.booklooker.de/2.0/article_list",
        params={'token': token, 'field': 'isbn', 'showPrice': 1, 'mediaType': 0}, timeout=30
    )
    data = r.json()
    isbn_lines = []
    if data['status'] == 'OK' and data['returnValue'].strip():
        isbn_lines = [l.strip() for l in data['returnValue'].strip().split('\n') if l.strip()]

    # Zusammenführen (gleiche Reihenfolge laut API-Doku)
    article_info = {}
    for i, order_no in enumerate(order_nos):
        isbn  = ''
        price = ''
        if i < len(isbn_lines):
            parts = isbn_lines[i].split('\t')
            isbn  = parts[0].strip()
            price = parts[1].strip() if len(parts) > 1 else ''
        article_info[order_no] = {'isbn': isbn, 'price': price}

    return set(order_nos), article_info


# ============================================================
# WP-SEITE PARSEN → ISBN → detail-URL Mapping
# ============================================================
def get_wp_links(wp_url=None):
    """Liest WP-Seite und baut dict: isbn → booklooker-detail-URL.
    Gibt {} zurück wenn wp_url nicht konfiguriert oder nicht erreichbar."""
    if not wp_url:
        log("Kein [wordpress] in Config → Cover-Links zeigen auf Händlerkatalog")
        return {}

    log(f"Lese WP-Seite: {wp_url} ...")
    try:
        r = requests.get(wp_url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        warn(f"WP-Seite nicht erreichbar: {e} → Cover-Links fallen weg")
        return {}

    # onClick="window.open('https://www.booklooker.de/app/detail.php?id=...')"
    detail_urls = re.findall(
        r"onClick=\"window\.open\('(https://www\.booklooker\.de/app/detail\.php\?id=[^']+)'\)\"",
        r.text
    )
    # ISBN aus dem HTML: ISBN: 9783593353838
    isbns = re.findall(r'ISBN:\s*(\d{10,13})', r.text)

    mapping = {}
    for isbn, url in zip(isbns, detail_urls):
        mapping[isbn] = url

    ok(f"WP-Links: {len(mapping)} ISBN→URL Paare gefunden")
    return mapping

# ============================================================
# BILDER BEREINIGEN
# ============================================================
def is_valid(filename, order_prefix=None):
    """Prüfe ob Dateiname gültig ist (kein _2, _3 Suffix, passt zu Präfix-Liste)"""
    if order_prefix is None:
        order_prefix = ['BN', 'BLX']
    stem = Path(filename).stem
    # Mehrfachbild-Suffix (_2, _3 ...) → ungültig
    if re.search(r'_\d+$', stem):
        return False, None
    # Präfix-Pattern dynamisch aufbauen
    pattern = r'^(' + '|'.join(re.escape(p) for p in order_prefix) + r')\d+'
    m = re.match(pattern, stem, re.IGNORECASE)
    if m:
        return True, stem.upper()
    return False, None

def cleanup(gallery_path, active_articles, order_prefix=None):
    sold_dir = gallery_path / "Verkauft"
    sold_dir.mkdir(exist_ok=True)

    moved = cleaned = skipped = 0
    images = sorted(gallery_path.glob("*.jpg"), key=lambda f: f.name.upper(), reverse=True)

    log(f"Bereinige {len(images)} JPGs in {gallery_path} ...")
    log(f"Erkannte Präfixe: {', '.join(order_prefix or ['BN','BLX'])}")

    for img in images:
        valid, article_no = is_valid(img.name, order_prefix)

        if not valid:
            # Kein BL-Bild → unangetastet lassen
            skipped += 1
            continue

        if re.search(r'_\d+$', Path(img.name).stem):
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

    ok(f"Bereinigt: {cleaned} Mehrfachbilder gelöscht, {moved} verkaufte verschoben, {skipped} Nicht-BL-Dateien ignoriert")
    return moved, cleaned

# ============================================================
# HTML GENERIEREN
# ============================================================
def generate_html(gallery_path, output_path, article_info=None, wp_links=None, order_prefix=None):
    if order_prefix is None:
        order_prefix = ['BN', 'BLX']
    images = sorted(
        [f for f in gallery_path.glob("*.jpg") if is_valid(f.name, order_prefix)[0]],
        key=lambda f: f.name.upper(), reverse=True
    )
    ok(f"Generiere Galerie mit {len(images)} Bildern...")

    article_info = article_info or {}
    wp_links     = wp_links     or {}

    # Fallback-URL wenn kein Direktlink verfügbar
    FALLBACK_URL = "https://www.booklooker.de/wdeu/B%C3%BCcher/Angebote/?sortOrder=offerDate&sortDirection=desc"

    # Baue Bild-Tags
    items_html = ""
    for img in images:
        stem  = img.stem.upper()   # z.B. BN00561
        fname = img.name.lower()   # z.B. bn00561.jpg

        info  = article_info.get(stem, {})
        isbn  = info.get('isbn', '')
        price = info.get('price', '')

        # Detail-Link: WP-Mapping per ISBN, sonst Fallback
        href  = wp_links.get(isbn, FALLBACK_URL)

        # Preis-Overlay nur wenn Preis bekannt
        price_html = ""
        if price:
            try:
                price_fmt = f"{float(price):.2f} €".replace('.', ',')
                price_html = f'<div class="price">{price_fmt}</div>'
            except ValueError:
                pass

        items_html += f"""
    <div class="item">
      <a href="{href}" target="_blank" rel="noopener" title="Bei Booklooker kaufen">
        <div class="thumb-wrap">
          <img src="images/{fname}" alt="{stem}" title="{stem}" loading="lazy">
          {price_html}
        </div>
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

    /* ── Thumb-Wrapper für Preis-Overlay ── */
    .thumb-wrap {{
      position: relative;
      width: 100%;
    }}

    /* ── Preis-Overlay ── */
    .price {{
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(180, 30, 30, 0.82);
      color: #fff;
      font-family: 'Raleway', sans-serif;
      font-size: 15px;
      font-weight: 700;
      text-align: center;
      padding: 4px 2px;
      letter-spacing: 0.03em;
      pointer-events: none;
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
  <div class="hint">Klick aufs Cover → direkt zu Booklooker</div>
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

    # 1. API: orderNo + ISBN + Preis
    active, article_info = get_article_data(cfg['api_key'])

    # 2. WP-Seite: ISBN → detail-URL Mapping
    print()
    wp_links = get_wp_links(cfg.get('wp_url'))

    # 3. Bilder bereinigen
    print()
    cleanup(cfg['gallery_path'], active, cfg['order_prefix'])

    # 4. Galerie generieren
    print()
    count = generate_html(cfg['gallery_path'], cfg['output_path'], article_info, wp_links, cfg['order_prefix'])

    print()
    print("═" * 56)
    ok(f"Fertig! {count} Bücher in Galerie.")
    print()
    print(f"  📥 Quelle:  {cfg['gallery_path']}")
    print(f"  📁 Output:  {cfg['output_path']}")
    print(f"  🌐 Preview: open \"{cfg['output_path']}/index.html\"")
    print()
    print(f"  💡 Upload: Inhalt von galerie-output/ mit Forklift")
    print(f"     nach /buecher/ auf IONOS hochladen")
    print("═" * 56)

if __name__ == "__main__":
    main()
