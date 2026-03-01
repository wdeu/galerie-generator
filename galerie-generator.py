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

# Optional: WordPress-Seite mit Booklooker-Plugin für Direktlinks + Tooltips.
# Voraussetzung: WordPress + wordpress-booklooker-bot Plugin
# wordpress_mode = yes  → WP-Seite scrapen (Links + Beschreibungs-Tooltips)
# wordpress_mode = no   → nur Booklooker-API (Preise, kein Tooltip, kein Direktlink)
#
# [wordpress]
# url = https://deine-domain.de/deine-buchseite
# wordpress_mode = yes
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
    wp_url  = None
    wp_mode = False
    if cfg.has_section('wordpress'):
        wp_url  = cfg.get('wordpress', 'url', fallback=None)
        wp_mode = cfg.get('wordpress', 'wordpress_mode', fallback='yes').strip().lower() == 'yes'

    # Bestellnummer-Präfixe
    raw_prefix   = cfg.get('booklooker', 'order_prefix', fallback='BN,BLX')
    order_prefix = [p.strip().upper() for p in raw_prefix.split(',') if p.strip()]

    return {
        'api_key':      cfg.get('booklooker', 'api_key'),
        'gallery_path': gallery_path,
        'output_path':  output_path,
        'ftp':          ftp,
        'wp_url':       wp_url,
        'wp_mode':      wp_mode,
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

    # Aufruf 2: orderNo + Preis (gleiche Reihenfolge wie Aufruf 1)
    log("Hole Preise...")
    r = requests.get(
        "https://api.booklooker.de/2.0/article_list",
        params={'token': token, 'field': 'orderNo', 'showPrice': 1}, timeout=30
    )
    data = r.json()
    price_map = {}  # orderNo → price
    if data['status'] == 'OK' and data['returnValue'].strip():
        for line in data['returnValue'].strip().split('\n'):
            parts = line.strip().split('\t')
            if parts:
                ono = parts[0].strip().upper()
                price = parts[1].strip() if len(parts) > 1 else ''
                price_map[ono] = price
    ok(f"Preise geladen: {len(price_map)} Einträge")

    # Aufruf 3: ISBN (gleiche Reihenfolge wie Aufruf 1)
    log("Hole ISBNs...")
    r = requests.get(
        "https://api.booklooker.de/2.0/article_list",
        params={'token': token, 'field': 'isbn'}, timeout=30
    )
    data = r.json()
    isbn_map = {}  # orderNo → isbn (per Index, gleiche Reihenfolge)
    if data['status'] == 'OK' and data['returnValue'].strip():
        isbn_lines = [l.strip() for l in data['returnValue'].strip().split('\n')]
        for i, order_no in enumerate(order_nos):
            if i < len(isbn_lines):
                isbn_map[order_no] = isbn_lines[i].strip()
    ok(f"ISBNs geladen: {len([v for v in isbn_map.values() if v])} mit ISBN")

    # Zusammenführen
    article_info = {}
    for order_no in order_nos:
        article_info[order_no] = {
            'isbn':  isbn_map.get(order_no, ''),
            'price': price_map.get(order_no, ''),
        }

    return set(order_nos), article_info


# ============================================================
# WP-SEITE PARSEN → ISBN → detail-URL + Beschreibung
# ============================================================
def get_wp_data(wp_url=None):
    """Liest WP-Seite und baut zwei Dicts:
       wp_links  – isbn → booklooker-detail-URL
       wp_desc   – isbn → Beschreibungstext (für Tooltip)
    Gibt ({}, {}) zurück wenn wp_url nicht konfiguriert oder nicht erreichbar."""
    if not wp_url:
        log("Kein [wordpress] in Config → Cover-Links zeigen auf Händlerkatalog")
        return {}, {}

    log(f"Lese WP-Seite: {wp_url} ...")
    try:
        r = requests.get(wp_url, timeout=20)
        r.raise_for_status()
        r.encoding = 'utf-8'   # Encoding-Fix: verhindert Ã¼ statt ü
    except Exception as e:
        warn(f"WP-Seite nicht erreichbar: {e} → Cover-Links fallen weg")
        return {}, {}

    html = r.text

    # ── Detail-URLs ──────────────────────────────────────────
    # onClick="window.open('https://www.booklooker.de/app/detail.php?id=...')"
    detail_urls = re.findall(
        r"onClick=\"window\.open\('(https://www\.booklooker\.de/app/detail\.php\?id=[^']+)'\)\"",
        html
    )

    # ── ISBNs ────────────────────────────────────────────────
    # Reihenfolge muss mit detail_urls übereinstimmen →
    # wir parsen Artikel-Blöcke strukturiert
    # Jeder Artikel-Block: <tr> … ISBN: XXXX … onClick … Beschreibung …
    # Da das Plugin eine Tabelle rendert, splitten wir nach <tr
    blocks = re.split(r'<tr[\s>]', html, flags=re.IGNORECASE)

    wp_links = {}
    wp_desc  = {}

    for block in blocks:
        # ISBN im Block
        isbn_m = re.search(r'ISBN:\s*(\d{10,13})', block)
        if not isbn_m:
            continue
        isbn = isbn_m.group(1).strip()

        # Detail-URL im Block
        url_m = re.search(
            r"onClick=\"window\.open\('(https://www\.booklooker\.de/app/detail\.php\?id=[^']+)'\)\"",
            block
        )
        if url_m:
            wp_links[isbn] = url_m.group(1)

        # Beschreibungstext: letztes <td> im Block (4. Spalte = Beschreibung)
        # Wir nehmen den längsten Text-Inhalt eines <td> im Block
        tds = re.findall(r'<td[^>]*>(.*?)</td>', block, re.DOTALL | re.IGNORECASE)
        if tds:
            # Längsten td-Inhalt nehmen (= Beschreibung)
            longest = max(tds, key=len)
            # HTML-Tags entfernen
            desc = re.sub(r'<[^>]+>', '', longest)
            # Preis-Zeilen herausfiltern (Preis(€): … Versand(€): …)
            desc = re.sub(r'Preis\(.*', '', desc, flags=re.DOTALL)
            # Whitespace normalisieren
            desc = ' '.join(desc.split()).strip()
            if len(desc) > 30:   # nur echte Beschreibungen
                wp_desc[isbn] = desc

    ok(f"WP-Links: {len(wp_links)} ISBN→URL Paare, {len(wp_desc)} Beschreibungen geladen")
    return wp_links, wp_desc


# Rückwärtskompatibilität (falls irgendwo get_wp_links direkt aufgerufen wird)
def get_wp_links(wp_url=None):
    links, _ = get_wp_data(wp_url)
    return links

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
    # Rekursiv in allen Unterordnern suchen, Verkauft-Ordner ausschließen
    images = sorted(
        [f for f in gallery_path.rglob("*.jpg")
          if sold_dir not in f.parents
          and "galerie-output" not in f.parts],
        key=lambda f: f.name.upper(), reverse=True
    )

    log(f"Bereinige {len(images)} JPGs in {gallery_path} (inkl. Unterordner) ...")
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
def generate_html(gallery_path, output_path, article_info=None, wp_links=None, order_prefix=None, wp_desc=None):
    if order_prefix is None:
        order_prefix = ['BN', 'BLX']
    sold_dir = gallery_path / "Verkauft"
    images = sorted(
        [f for f in gallery_path.rglob("*.jpg")
          if is_valid(f.name, order_prefix)[0]
          and "galerie-output" not in f.parts
          and sold_dir not in f.parents],
        key=lambda f: f.name.upper(), reverse=True
    )
    ok(f"Generiere Galerie mit {len(images)} Bildern...")

    article_info = article_info or {}
    wp_links     = wp_links     or {}
    wp_desc      = wp_desc      or {}

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

        # Beschreibung für Tooltip (HTML-escapen)
        desc_raw  = wp_desc.get(isbn, '')
        desc_attr = desc_raw.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;') if desc_raw else ''
        tooltip_attr = f' data-tooltip="{desc_attr}"' if desc_attr else ''

        # Preis-Overlay nur wenn Preis bekannt
        price_html = ""
        if price:
            try:
                price_fmt = f"{float(price):.2f} €".replace('.', ',')
                price_html = f'<div class="price">{price_fmt}</div>'
            except ValueError:
                pass

        items_html += f"""
    <div class="item"{tooltip_attr}>
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
  <title>Booq – wdeu bei Booklooker.de</title>

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

    header .stats {{
      font-size: 11px;
      color: #aaa;
      margin-top: 4px;
    }}

    /* ── Header-Row: Info links, Slider rechts ── */
    .header-row {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 12px;
      margin-top: 6px;
    }}

    /* ── Slider ── */
    .size-control {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }}
    .size-control label {{
      font-size: 11px;
      color: #848681;
      white-space: nowrap;
    }}
    .size-control input[type=range] {{
      width: 110px;
      accent-color: #37677B;
      cursor: pointer;
    }}
    .size-control .size-val {{
      font-size: 11px;
      color: #37677B;
      font-weight: 600;
      min-width: 32px;
    }}

    /* ── Grid ── */
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(var(--thumb-size, 130px), 1fr));
      gap: 12px;
      padding: 20px;
    }}

    @media (max-width: 480px) {{
      .grid {{
        gap: 8px;
        padding: 12px;
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

    /* ── Tooltip ── */
    .tooltip-box {{
      display: none;
      position: fixed;
      z-index: 9999;
      max-width: 320px;
      background: rgba(30, 30, 30, 0.96);
      color: #f0ece4;
      font-family: 'Raleway', sans-serif;
      font-size: 13px;
      line-height: 1.55;
      padding: 12px 14px;
      border-radius: 7px;
      box-shadow: 0 4px 18px rgba(0,0,0,0.35);
      pointer-events: none;
      word-break: break-word;
    }}

    /* ── X-Button (zurück zu wdeu.de) ── */
    .close-btn {{
      position: fixed;
      top: 14px;
      right: 16px;
      z-index: 200;
      background: #fff;
      border: 1.5px solid #e0ddd5;
      border-radius: 50%;
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      text-decoration: none;
      color: #848681;
      font-size: 18px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.1);
      transition: border-color 0.2s, color 0.2s;
    }}
    .close-btn:hover {{ border-color: #37677B; color: #37677B; }}

    /* ── Footer ── */
    footer {{
      text-align: center;
      padding: 20px 24px;
      font-size: 12px;
      color: #aaa;
      border-top: 1px solid #e0ddd5;
      margin-top: 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 14px;
    }}

    .footer-icons {{
      display: flex;
      gap: 28px;
      align-items: center;
      justify-content: center;
    }}

    .footer-btn {{
      background: none;
      border: none;
      cursor: pointer;
      font-size: 1.4rem;
      padding: 0.3rem;
      border-radius: 0.5rem;
      color: #848681;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      transition: color 0.15s;
    }}
    .footer-btn:hover {{ color: #37677B; }}
  </style>
</head>
<body>

<a class="close-btn" href="https://wdeu.de" title="Zurück zu wdeu.de">✕</a>

<header>
  <h1>Booq</h1>
  <div class="sub">wdeu bei Booklooker.de</div>
  <div class="hint">Klick aufs Cover → direkt zu Booklooker</div>
  <div class="header-row">
    <div class="stats">{count} Bücher · Stand: {now}</div>
    <div class="size-control">
      <label for="sizeSlider">🔍</label>
      <input type="range" id="sizeSlider" min="80" max="280" step="10" value="130"
             oninput="setSize(this.value)">
      <span class="size-val" id="sizeVal">130px</span>
    </div>
  </div>
</header>

<main>
  <div class="grid">{items_html}
  </div>
</main>

<div class="tooltip-box" id="tooltip"></div>

<footer>
  <div class="footer-icons">
    <a class="footer-btn" href="https://wdeu.de" title="wdeu.de">💡</a>
    <button class="footer-btn" id="share-btn" title="Seite teilen">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
        <polyline points="16 6 12 2 8 6"/>
        <line x1="12" y1="2" x2="12" y2="15"/>
      </svg>
    </button>
    <button class="footer-btn" id="homescreen-btn" title="Zum Homescreen hinzufügen">📌</button>
  </div>
  <div>Fachbücher Psychologie &amp; Sozialwissenschaften · wdeu bei Booklooker.de</div>
</footer>

<script>
  const STORAGE_KEY = 'booq-thumb-size';
  const slider = document.getElementById('sizeSlider');
  const sizeVal = document.getElementById('sizeVal');
  const grid = document.querySelector('.grid');

  function setSize(v) {{
    v = parseInt(v);
    grid.style.setProperty('--thumb-size', v + 'px');
    sizeVal.textContent = v + 'px';
    slider.value = v;
    try {{ localStorage.setItem(STORAGE_KEY, v); }} catch(e) {{}}
  }}

  // Gespeicherte Größe laden
  try {{
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) setSize(saved);
  }} catch(e) {{}}  // ── Tooltip ──────────────────────────────────────────────
  const tip = document.getElementById('tooltip');
  let hideTimer;

  document.querySelectorAll('.item[data-tooltip]').forEach(item => {{
    item.addEventListener('mouseenter', e => {{
      clearTimeout(hideTimer);
      tip.textContent = item.dataset.tooltip;
      tip.style.display = 'block';
      positionTip(e);
    }});
    item.addEventListener('mousemove', positionTip);
    item.addEventListener('mouseleave', () => {{
      hideTimer = setTimeout(() => {{ tip.style.display = 'none'; }}, 80);
    }});
  }});

  function positionTip(e) {{
    const pad = 14;
    const tw = tip.offsetWidth;
    const th = tip.offsetHeight;
    let x = e.clientX + pad;
    let y = e.clientY + pad;
    if (x + tw > window.innerWidth  - 8) x = e.clientX - tw - pad;
    if (y + th > window.innerHeight - 8) y = e.clientY - th - pad;
    tip.style.left = x + 'px';
    tip.style.top  = y + 'px';
  }}

  // ── Share & Homescreen ──────────────────────────────────
  document.getElementById('share-btn').addEventListener('click', async () => {{
    if (navigator.share) {{
      try {{
        await navigator.share({{
          title: 'Bücherkiste – wdeu bei Booklooker.de',
          url: 'https://galerie.wdeu.de'
        }});
      }} catch {{}}
    }} else {{
      await navigator.clipboard.writeText('https://galerie.wdeu.de');
      alert('Link kopiert!');
    }}
  }});

  document.getElementById('homescreen-btn').addEventListener('click', () => {{
    const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
    const isAndroid = /android/i.test(navigator.userAgent);
    if (isIOS) {{
      alert('Tippe unten auf das Teilen-Symbol ⬆️, dann „Zum Home-Bildschirm".');
    }} else if (isAndroid) {{
      alert('Tippe oben rechts auf das Menü ⋮, dann „Zum Startbildschirm hinzufügen".');
    }} else {{
      alert('Öffne galerie.wdeu.de auf deinem Smartphone und wähle im Browser-Menü „Zum Homescreen hinzufügen".');
    }}
  }});

</script>

</body>
</html>"""

    # Output-Ordner anlegen
    output_path.mkdir(parents=True, exist_ok=True)
    images_out = output_path / "images"
    # Immer neu befüllen → keine veralteten oder falsch-gecachten Dateien
    if images_out.exists():
        shutil.rmtree(str(images_out))
    images_out.mkdir()

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

# ============================================================
# BL-BILDORDNER AUSWÄHLEN
# ============================================================
def find_bl_image_dir(gallery_path, order_prefix=None):
    """Sucht BL-Bildordner (Pattern: *-images-*) in gallery_path.
    Nimmt den neuesten, warnt bei mehreren."""
    if order_prefix is None:
        order_prefix = ['BN', 'BLX']

    # Alle Unterordner die dem BL-Muster entsprechen
    bl_dirs = sorted(
        [d for d in gallery_path.iterdir()
         if d.is_dir() and '-images-' in d.name.lower()],
        key=lambda d: d.stat().st_mtime, reverse=True
    )

    if not bl_dirs:
        # Kein Unterordner → gallery_path selbst als Quelle
        return gallery_path

    if len(bl_dirs) > 1:
        warn(f"{len(bl_dirs)} BL-Bildordner gefunden – nehme den neuesten:")
        for i, d in enumerate(bl_dirs):
            marker = "  ✓ (wird verwendet)" if i == 0 else "  ✗ (wird ignoriert)"
            warn(f"    {d.name}{marker}")
        warn("Tipp: Alte Ordner löschen um Verwirrung zu vermeiden.")

    ok(f"BL-Bildordner: {bl_dirs[0].name}")
    return bl_dirs[0]


def main():
    print("═" * 56)
    print("  📚 Booklooker Galerie Generator")
    print("═" * 56)
    print()

    cfg = load_config()

    # 1. API: orderNo + ISBN + Preis
    active, article_info = get_article_data(cfg['api_key'])

    # 2. WP-Seite: ISBN → detail-URL + Beschreibung (nur wenn wordpress_mode = yes)
    print()
    if cfg.get('wp_mode') and cfg.get('wp_url'):
        wp_links, wp_desc = get_wp_data(cfg['wp_url'])
    else:
        if cfg.get('wp_url') and not cfg.get('wp_mode'):
            log("wordpress_mode = no → WP-Scraping übersprungen (nur API-Preise)")
        else:
            log("Kein [wordpress] in Config → Cover-Links zeigen auf Händlerkatalog")
        wp_links, wp_desc = {}, {}

    # 3. BL-Bildordner bestimmen (neuester bei mehreren)
    print()
    image_dir = find_bl_image_dir(cfg['gallery_path'], cfg['order_prefix'])

    # 4. Bilder bereinigen
    print()
    cleanup(image_dir, active, cfg['order_prefix'])

    # 5. Galerie generieren
    print()
    count = generate_html(image_dir, cfg['output_path'], article_info, wp_links, cfg['order_prefix'], wp_desc)

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
