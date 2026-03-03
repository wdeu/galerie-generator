# 📚 Booklooker Galerie Generator

Automatische Buchcover-Galerie für Booklooker-Verkäufer.

Das Script holt deine aktiven Artikel per Booklooker-API, bereitet Deinen Buchcover--Download
auf und generiert eine fertige, hochladbare `index.html` mit
Cover-Grid, Preis-Overlay und direkten Links zu Booklooker.

**Live-Beispiel:** [galerie.wdeu.de](https://galerie.wdeu.de)

---

## Voraussetzungen

- Python 3.8 oder neuer
- `pip install requests --break-system-packages`
- Booklooker-Account mit API-Key
  ([hier abrufen](https://www.booklooker.de/app/priv/api_key.php))

---

## Installation

```bash
git clone https://github.com/wdeu/galerie-generator.git
cd galerie-generator
pip install requests --break-system-packages
chmod +x galerie-generator.py
```

---

## Konfiguration

Beim ersten Start wird `~/.booklooker-sync.ini` automatisch angelegt:

```ini
[booklooker]
api_key = DEIN_API_KEY_HIER

# Bestellnummer-Präfixe deiner Booklooker-Artikel (kommagetrennt).
# BN  = Einzeltitel-Inserat
# BLX = CSV-Massenupload
# Booklooker erlaubt eigene Präfixe – trage hier alle ein die du verwendest.
# Beispiel: order_prefix = BN,BLX,MGB
order_prefix = BN,BLX

# [paths] ist optional.
# Standard: ~/Downloads als Quelle, ~/Downloads/galerie-output als Ziel.
# Nur eintragen wenn du andere Ordner möchtest:
# [paths]
# gallery_path = /Users/DEINNAME/Pictures/Galerie
# output_path  = /Users/DEINNAME/Projects/galerie-output

# Optional: WordPress + Booklooker-Plugin für Direktlinks pro Buch.
# Ohne diesen Abschnitt zeigen alle Cover-Klicks auf deinen Händlerkatalog.
# [wordpress]
# url = https://deine-domain.de/deine-buchseite
```

Öffnen mit:
```bash
open ~/.booklooker-sync.ini
```

### Bestellnummer-Präfixe

Booklooker vergibt Bestellnummern nach einem Muster, das vom Upload-Weg
abhängt (Einzelinserat, CSV-Upload o.ä.). Schau in deinen Booklooker-Bestand
und trage alle Präfixe ein die dort vorkommen. Standardmäßig sind `BN` und
`BLX` vorbelegt.

---

## Workflow

### 1. Cover-Bilder herunterladen

Logge dich bei Booklooker ein, fordere den Bilder-Download an, warte auf die
Mail mit dem Download-Link und lade die ZIP-Datei herunter. macOS entpackt
sie automatisch in `~/Downloads`, oder per Mausklick entpacken.

### 2. Generator starten

```bash
./galerie-generator.py
```

Das Script:
- Holt deine aktiven Artikel per API (orderNo, ISBN, Preis)
- Liest optional deine WordPress-Seite für Direktlinks
- Bereinigt `~/Downloads`: Mehrfachbilder (z.B. `BN00322 2.jpg`) werden
  ignoriert, verkaufte Bücher wandern nach `~/Downloads/Verkauft/`,
  alle anderen Dateien werden **nicht** angetastet
- Generiert `~/Downloads/galerie-output/index.html` mit fertigem Cover-Grid

### 3. Hochladen

Lade den Inhalt von `~/Downloads/galerie-output/` per FTP/SFTP auf deinen
Webspace hoch. Mit [Forklift](https://binarynights.com) oder FileZilla.

---

## Funktionen

| Feature | Beschreibung |
|---|---|
| **Preis-Overlay** | Roter Preisbalken am unteren Coverrand, direkt aus der API |
| **Direktlinks** | Cover-Klick → Einzelartikel bei Booklooker (erfordert WordPress-Option) |
| **Fallback-Link** | Ohne WordPress: Klick → dein Händlerkatalog nach Datum sortiert |
| **Verkauft-Ordner** | Verkaufte Bücher landen in `~/Downloads/Verkauft/` |
| **Nicht-BL-Dateien** | Andere JPGs im Downloads-Ordner werden ignoriert |
| **Responsive Grid** | 1–3 Spalten je nach Bildschirmbreite, Mobile-optimiert |

---

## Optionale WordPress-Integration

Wenn du WordPress mit dem Plugin
[wordpress-booklooker-bot](https://wordpress.org/plugins/wordpress-booklooker-bot/)
betreibst, kann der Generator die dort generierten Direktlinks auslesen.

Trage in der INI ein:

```ini
[wordpress]
url = https://deine-domain.de/deine-buchseite
```

Der Generator parst die Seite beim Start und verknüpft jeden Cover-Klick
direkt mit dem kaufbaren Einzelartikel bei Booklooker. Ist die Seite nicht
erreichbar, greift automatisch der Fallback-Link — kein Absturz.

---

## Automatisierung mit Raycast

Das Script lässt sich als
[Raycast Script Command](https://github.com/raycast/script-commands)
einbinden. Beispiel-Script `ionos-sync.sh` für den anschließenden Upload
liegt im Repo.

---

## Lizenz

MIT — frei verwendbar, veränderbar, weiterggebbar.
