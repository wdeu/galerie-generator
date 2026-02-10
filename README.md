# 📚 Bücherkiste – Automatische Galerie für Booklooker-Verkäufer

Eine einfache Lösung für alle, die ihre Buchcover als Bildergalerie im Web zeigen möchten – **immer automatisch aktuell**, ohne manuelles Pflegen.

**→ [Live-Demo ansehen](https://wdeu.de/galerie)**

---

## Was macht dieses Programm?

Zunächst etwas Handarbeit:

1. Du brauchst Deine Buchcover.
2. Du brauchst einen persönlichen API-Key (siehe unten).

Das Programm erledigt dann den Rest **automatisch**:

- ✅ Fragt deine aktuelle Artikelliste bei Booklooker ab
- ✅ Entfernt Mehrfachfotos vom selben Buch (`_2.jpg`, `_3.jpg` usw.)
- ✅ Verschiebt Fotos von **bereits verkauften** Büchern in einen separaten Ordner
- ✅ Erstellt eine fertige Webseite mit allen aktuellen Covers
- ✅ Zeigt die Bestellnummer unter jedem Buchcover an
- ✅ Funktioniert auf Desktop und Smartphone

Das Ergebnis ist eine Datei (`index.html`), die du auf deinen Webspace hochlädst.
Hast Du nicht? Dann nimm "Netlify" (kostenlos) - siehe unten Option A.

---

## Voraussetzungen

Du lädst Deine Buchcover bei [booklooker.de → Ihre angebotenen Artikel](https://www.booklooker.de/app/priv/my_overview.php) herunter. 
Klicke ganz unten auf den Link: "Hochgeladene Bilder zum Download anfordern". 
Eine Mail bestätigt wenig später, dass der Download bereit liegt. 
Klicke dann auf derselben Webseite unten auf "ZIP-Datei mit hochgeladenen Bildern herunterladen".
In Deinem Downloads-Verzeichnis liegt ein Ordner mit dem wenig schönen Namen "(Deine User-ID)-images-5cc2f422e1fA82a7ff712349d7da4569". Oder so ähnlich.
Verschiebe (copy & paste) ALLE darin befindlichen Buchcover in Deinen Ordner /Users/deinBenutzerordnerName/Pictures/Galerie 
Existiert dieser Ordner noch nicht, lege ihn an: Bilder/Galerie (Schiebe hier die Fotos Deiner Buchcover rein).

Dann:

| Was | Wo herunterladen | Kosten |
|-----|-----------------|--------|
| **Python 3** | https://www.python.org/downloads/ | kostenlos |
| **Booklooker API Key** | [Persönliche Daten → API Key](https://www.booklooker.de/app/priv/api_key.php) | kostenlos |
| Einen **Webspace** (für das Ergebnis) | z.B. Netlify (kostenlos), IONOS, Strato, ... | je nach Anbieter |

Auf **macOS** ist Python meist schon vorinstalliert.  
Auf **Windows** einmal von python.org herunterladen und installieren (Haken bei „Add to PATH" setzen!).

API-Key: Du loggst Dich ein, gehst zu  [Persönliche Daten → Zugang zur Booklooker REST API](https://www.booklooker.de/app/priv/api_key.php) 
Kopiere unter "Ihr persönlicher API-Key" den Zahlencode, Du brauchst ihn unten bei "Schritt 3".
---

## Einrichtung (einmalig, ca. 10 Minuten)

### Schritt 1 – Programm herunterladen

Klicke oben rechts auf dieser Seite auf **`Code` → `Download ZIP`**.  
Entpacke den ZIP-Ordner an einen Ort deiner Wahl, z.B. `Dokumente/buecherkiste`.

### Schritt 2 – Python-Paket installieren

Öffne das Terminal (macOS) bzw. die Eingabeaufforderung (Windows) und tippe:

```
pip3 install requests
```

Auf Windows eventuell:
```
pip install requests
```

### Schritt 3 – Konfiguration einrichten

Öffne die Datei `.booklooker-sync.ini.example` mit einem Texteditor  
(z.B. Editor/Notepad auf Windows, TextEdit auf macOS).

Trage deine Daten ein:

```ini
[booklooker]
api_key = abc123xyz...   ← deinen echten API Key hier eintragen

[paths]
gallery_path = /Users/deinName/Pictures/Galerie   ← Ordner mit deinen Buchfotos
output_path  = /Users/deinName/Documents/buecherkiste/public   ← Ausgabe-Ordner
```

**Speichere die Datei als `.booklooker-sync.ini`** (ohne `.example` am Ende)  
im Benutzer-Heimordner:
- **macOS/Linux:** `/Users/deinName/` → Dateiname: `.booklooker-sync.ini`
- **Windows:** `C:\Users\deinName\` → Dateiname: `.booklooker-sync.ini`

> 💡 **API Key:** Den findest du nach dem Einloggen unter  
> [booklooker.de → Persönliche Daten → API Key](https://www.booklooker.de/app/priv/api_key.php)

### Schritt 4 – Buchfotos vorbereiten

Lege alle Buchcover-Fotos in den Ordner, den du unter `gallery_path` eingetragen hast.

**Wichtig:** Die Dateinamen müssen der Booklooker-Bestellnummer entsprechen:
```
✅ bn00561.jpg     (passt – wird angezeigt)
✅ BLX0040.jpg     (passt – Groß/Kleinschreibung egal)
✅ blx0040.jpg     (passt)
❌ blx0040_2.jpg   (wird automatisch gelöscht – Mehrfachfoto)
❌ IMG_1234.jpg    (wird ignoriert – kein Booklooker-Format)
```

---

## Galerie erstellen

### macOS / Linux

Öffne das Terminal, wechsle in den Programm-Ordner und starte:

```bash
cd ~/Documents/buecherkiste
./galerie-generator.py
```

### Windows

Doppelklick auf `galerie-generator.py`  
— oder im Terminal:

```
python galerie-generator.py
```

Das Programm zeigt dir dann seinen Fortschritt:

```
════════════════════════════════════════════════════════
  📚 Booklooker Galerie Generator
════════════════════════════════════════════════════════

✓ Token: d1985eb547a968...
✓ Aktive Artikel: 212
⚠  Lösche Mehrfachbild: blx0040_2.jpg
⚠  Verschiebe verkauft: bn00305.jpg
✓ Bereinigt: 8 Mehrfachbilder gelöscht, 5 verkaufte verschoben
✓ Galerie mit 207 Büchern generiert

════════════════════════════════════════════════════════
✓ Fertig! 207 Bücher in Galerie.

  📁 Output:  .../public/index.html
════════════════════════════════════════════════════════
```

---

## Ergebnis online stellen

Im Ordner `public/` liegen jetzt:
```
public/
├── index.html        ← die fertige Webseite
└── images/           ← alle aktuellen Buchcover
    ├── bn00561.jpg
    ├── blx0001.jpg
    └── ...
```

### Option A: Netlify (kostenlos, empfohlen für Einsteiger)

1. Kostenlos registrieren auf [netlify.com](https://www.netlify.com)
2. Den `public/`-Ordner per **Drag & Drop** auf das Netlify-Dashboard ziehen
3. Fertig – Netlify gibt dir eine URL wie `https://deinname.netlify.app`

Beim nächsten Update: einfach wieder den `public/`-Ordner hochziehen.

### Option B: Eigener Webspace (IONOS, Strato, All-Inkl. etc.)

Verbinde dich per FTP mit deinem Webspace (z.B. mit [FileZilla](https://filezilla-project.org/))  
und lade den Inhalt des `public/`-Ordners in dein gewünschtes Verzeichnis hoch.

---

## Galerie aktuell halten

Führe das Programm einfach **jedes Mal aus**, wenn du neue Bücher eingestellt  
oder Bücher verkauft hast. Es dauert nur wenige Sekunden.

---

## Häufige Fragen

**Meine verkauften Bücher verschwinden nicht sofort.**  
Booklooker aktualisiert die Artikelliste mit ca. 1–2 Stunden Verzögerung nach dem Verkauf. Einfach etwas später nochmal das Programm starten.

**Das Programm findet meinen API Key nicht.**  
Prüfe, ob die Datei `.booklooker-sync.ini` (mit Punkt am Anfang!) wirklich im  
Heimordner liegt und korrekt benannt ist. Unter Windows zeigt der Explorer  
Dateien mit Punkt am Anfang manchmal nicht an — im Editor → Datei öffnen → alle Dateien anzeigen.

**`pip3 install requests` schlägt fehl.**  
Versuche `pip install requests` (ohne die 3). Falls das auch nicht klappt:  
`python3 -m pip install requests` (macOS/Linux) oder `python -m pip install requests` (Windows).

**Ich habe keine eigene Website.**  
Netlify ist kostenlos und braucht keine technischen Kenntnisse – einfach  
den `public/`-Ordner per Drag & Drop hochladen.

---

## Danke & Mitmachen

Entstanden im [Booklooker-Forum](https://www.booklookerforum.de/viewtopic.php?t=32241).  
Verbesserungsvorschläge und Fehlermeldungen gerne als [GitHub Issue](../../issues) oder im Forum.

---

*Lizenz: MIT – kostenlos nutzbar und anpassbar*