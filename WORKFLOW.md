# Booq – Workflow: Vom Buch zur live Galerie

*Schritt für Schritt: fotografieren, inserieren, Texte pflegen, Preise optimieren, deployen.*

---

## Voraussetzungen (einmalig)

- `~/.booklooker-sync.ini` befüllt: `api_key`, `seller_id`, `cover_base_url`
- Raycast Scripts eingerichtet: Galerie Generator, BL Update, Preisvergleich, Klappentexter
- IONOS: `~/buecher/` als Webroot für `galerie.wdeu.de`
- SSH-Zugang zu `cover.wdeu.de` für Cover-Upload

---

## Neues Buch inserieren

### Schritt 1 – Buch fotografieren

iPhone, Hochformat, Frontalansicht:
- Buch flach auf hellen/neutralen Untergrund legen
- Von oben fotografieren, formatfüllend, kein Schatten
- Bestellnummer vorab vergeben (nächste freie `ISBxxxx`)
- Foto umbenennen: `ISB0008.jpg`
- Per SFTP nach `cover.wdeu.de/ISB0008.jpg` hochladen

### Schritt 2 – Buch inserieren

`inserate.wdeu.de` öffnen:
- ISBN scannen oder manuell eingeben
- Metadaten prüfen: Titel, Autor, Preis, Zustand
- Bestellnummer eintragen (`ISB0008`)
- Cover-URL wird automatisch gesetzt: `https://cover.wdeu.de/ISB0008.jpg`
- Mehrere Bücher sammeln → Batch
- **CSV exportieren** → landet in `~/Downloads/`

### Schritt 3 – CSV bei Booklooker importieren

Booklooker → Mein Depot → Artikel-Import → CSV hochladen

Das Buch ist jetzt live. Booklooker cached das Cover beim ersten Aufruf von `cover.wdeu.de`.

---

## Bestehende Artikel verbessern

### Klappentexte pflegen

```
Raycast → Klappentexter
```

- Bücher ohne Beschreibung werden priorisiert
- Text per KI generieren oder manuell eingeben
- Accept / Skip pro Buch
- **CSV exportieren** → `~/Downloads/`
- Booklooker → Artikel-Import

### Preise prüfen und anpassen

```
Raycast → Preisvergleich
```

- Eurobuch-Konkurrenz wird abgefragt (ISBN-basiert)
- Eigener Rang im Markt pro Buch sichtbar (Perzentil)
- `preisvorschlaege.json` wird automatisch erzeugt
- HTML-Ansicht: grün = günstig, rot = teuer
- Preisanpassungen werden über BL Update übernommen (siehe unten)

### Cover ersetzen (Foto verbessern)

1. Neues Foto aufnehmen (Frontalansicht, Hochformat)
2. Als `BN00413_v2.jpg` nach `cover.wdeu.de` hochladen
3. `cover-changes.json` anlegen in `~/Downloads/galerie-output/`:

```json
[
  {"orderNo": "BN00413", "bild_url": "https://cover.wdeu.de/BN00413_v2.jpg"}
]
```

4. BL Update starten (siehe unten) → CSV exportieren → bei BL importieren

> **Wichtig:** Booklooker cached Bilder von der Basis-URL beim ersten Aufruf.
> Bei Änderungen muss die URL geändert werden (`_v2`, `_v3` etc.),
> damit Booklooker das neue Bild herunterlädt.

---

## Alle Änderungen zusammenführen

```
Raycast → BL Update
```

Das Script liest vier Quellen gleichzeitig:

| Quelle | Datei | Änderungstyp |
|--------|-------|--------------|
| inserate.wdeu.de | `*ISB*.csv` / `*inserate*.csv` in `~/Downloads/` | Neu |
| Klappentexter | `*klappentexter*.csv` in `~/Downloads/` | Klappentext |
| Preisvergleich | `galerie-output/preisvorschlaege.json` | Preis |
| Cover-Änderungen | `galerie-output/cover-changes.json` | Cover |

**Preview HTML** öffnet sich automatisch:
- Alle geplanten Änderungen auf einen Blick
- Häkchen setzen/entfernen pro Artikel
- Filter: Alle / Neu / Klappentext / Preis / Cover
- **CSV exportieren** → `bl-update.csv`

**CSV bei Booklooker importieren:**
Booklooker → Mein Depot → Artikel-Import → `bl-update.csv` hochladen

---

## Galerie aktualisieren und deployen

### Galerie neu generieren

```
Raycast → Galerie Generator
```

- Holt aktuelle Preise und Artikel per API
- Neue ISB-Cover werden von `cover.wdeu.de` nachgeladen
- `~/Downloads/galerie-output/index.html` wird neu gebaut

Lokal prüfen:
```bash
open ~/Downloads/galerie-output/index.html
```

### Auf IONOS deployen

```
Raycast → IONOS Sync galerie push
```

`galerie.wdeu.de` ist live mit neuen Büchern, aktuellen Preisen und neuen Covern.

```
Raycast → IONOS Sync preisvergleich push
```

`wdeu.de/preisvergleich/` ist aktualisiert (auch auf dem iPhone abrufbar).

---

## Übersicht: Welches Tool wann

| Situation | Tool | Output |
|-----------|------|--------|
| Neues Buch fotografieren | iPhone + SFTP | `cover.wdeu.de/ISBxxxx.jpg` |
| Neues Buch inserieren | inserate.wdeu.de | CSV → BL Update |
| Klappentext fehlt | Klappentexter | CSV → BL Update |
| Preise prüfen | Preisvergleich | JSON → BL Update |
| Cover verbessern | cover-changes.json | → BL Update |
| Alle Änderungen zu BL | BL Update | CSV → Artikel-Import |
| Galerie neu bauen | Galerie Generator | index.html |
| Alles live stellen | IONOS Sync | galerie.wdeu.de |

---

## Typischer Tagesablauf

```
1. Foto → cover.wdeu.de
2. inserate.wdeu.de → CSV
3. Klappentexter → CSV          (optional)
4. Preisvergleich                (optional, erzeugt JSON)
5. BL Update → CSV → BL Import
6. Galerie Generator
7. IONOS Sync galerie push
```

---

## Repos

| Projekt | GitHub | Sichtbarkeit |
|---------|--------|--------------|
| galerie-generator | github.com/wdeu/galerie-generator | public |
| bl-update | github.com/wdeu/bl-update | private |
| preisvergleich | github.com/wdeu/preisvergleich | private |
| klappentexter | github.com/wdeu/klappentexter | private |
