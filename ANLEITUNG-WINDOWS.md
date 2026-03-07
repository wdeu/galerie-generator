# Booq – Deine Booklooker-Galerie einrichten (Windows)

*Keine Vorkenntnisse nötig. Wir richten einmal alles ein – danach läuft die Galerie per Doppelklick.*

---

## Was du brauchst

- Einen Windows-PC (Windows 10 oder 11)
- Einen Booklooker-Account mit API-Key
- Deine Booklooker-UID (7-stellige Nummer)
- Ca. 30 Minuten (einmalig)

---

## Schritt 1 – Python installieren

1. [python.org/downloads](https://www.python.org/downloads/) aufrufen
2. Den großen „Download Python"-Button klicken
3. Installer starten – **wichtig:** Haken bei **„Add Python to PATH"** setzen, bevor du auf „Install Now" klickst

---

## Schritt 2 – Git installieren

1. [git-scm.com](https://git-scm.com) aufrufen
2. „Download for Windows" klicken und Installer starten
3. Alle Voreinstellungen einfach bestätigen (mehrfach „Next", dann „Install")

---

## Schritt 3 – Script herunterladen

Die Windows-Taste drücken, „cmd" eingeben, Enter drücken.

Ein schwarzes Fenster öffnet sich (die „Eingabeaufforderung"). Dort eingeben:

```
git clone https://github.com/wdeu/galerie-generator.git %USERPROFILE%\projekte\galerie-generator
```

Enter drücken. Das Script wird heruntergeladen.

---

## Schritt 4 – Einmalig starten (Config anlegen)

Im gleichen schwarzen Fenster:

```
python %USERPROFILE%\projekte\galerie-generator\galerie-generator.py
```

Das Script bricht mit einer Meldung ab: *„Config erstellt – bitte API-Key eintragen."*

Das ist gut so – weiter zu Schritt 5!

---

## Schritt 5 – Config ausfüllen

Die Konfigurationsdatei öffnen:

```
notepad %USERPROFILE%\.booklooker-sync.ini
```

Der Texteditor öffnet sich. Dort trägst du ein:

```ini
[booklooker]
api_key    = DEIN_API_KEY
seller_id  = 1234567
```

**Wo findest du den API-Key?**
booklooker.de → Mein Depot → API

**Wo findest du die seller_id?**
booklooker.de → Mein Depot → Meine Angebote → *„Eigene Angebote aus Kundensicht"*
→ in der Adresszeile des Browsers steht dann `showAlluID=1234567`
→ diese 7-stellige Nummer ist deine seller_id

Datei speichern (`Strg + S`), Notepad schließen.

---

## Schritt 6 – Bilder herunterladen

In deinem Booklooker-Konto: Mein Depot → Bilder → alle als ZIP herunterladen.
Das ZIP in den Ordner `Downloads` entpacken (Rechtsklick → „Alle extrahieren").

---

## Schritt 7 – Galerie generieren

Im schwarzen Fenster (Eingabeaufforderung):

```
python %USERPROFILE%\projekte\galerie-generator\galerie-generator.py
```

Das Script läuft jetzt durch:
- Bilder werden sortiert (verkaufte Bücher wandern in einen Unterordner)
- Preise werden live aus der Booklooker-API geholt
- Eine fertige `index.html` wird gebaut

Das Ergebnis liegt im Ordner `Downloads\galerie-output\`.

Vorschau: Doppelklick auf `Downloads\galerie-output\index.html` – der Browser öffnet die Galerie.

---

## Schritt 8 – Galerie veröffentlichen

Du hast zwei Möglichkeiten:

### Option A – Eigener Webserver (FTP)

Den Inhalt von `galerie-output\` (also `index.html` + Ordner `images\`) per FTP auf deinen Webserver hochladen.
Kostenloser FTP-Client für Windows: [FileZilla](https://filezilla-project.org)

### Option B – Netlify (kostenlos, kein Webserver nötig)

1. Kostenlosen Account anlegen auf [netlify.com](https://netlify.com)
2. Auf der Netlify-Startseite gibt es einen Bereich **„Drag & Drop"**
3. Den Ordner `galerie-output` einfach dort hineinziehen
4. Netlify vergibt automatisch eine Adresse (z.B. `zufaelliger-name.netlify.app`)
5. Diese Adresse kannst du in deinem Booklooker-Profil oder im Forum teilen

*Beim nächsten Update: Ordner einfach erneut hineinziehen – Netlify aktualisiert die Seite automatisch.*

---

## Galerie aktualisieren

Neue Bilder von Booklooker herunterladen, entpacken, Script nochmal starten, Ordner erneut hochladen (FTP oder Netlify Drag & Drop).

Im schwarzen Fenster:
```
python %USERPROFILE%\projekte\galerie-generator\galerie-generator.py
```

---

## Tipp: Verknüpfung anlegen

Damit du das Script künftig per Doppelklick starten kannst:

1. Rechtsklick auf den Desktop → Neu → Verknüpfung
2. Als Ziel eingeben:
   ```
   python %USERPROFILE%\projekte\galerie-generator\galerie-generator.py
   ```
3. Namen vergeben z.B. „Galerie aktualisieren"

---

## Optionale Erweiterung: WordPress-Integration

Wer WordPress mit dem Plugin *wordpress-booklooker-bot* betreibt, kann zusätzlich Direktlinks zu einzelnen Artikeln und Beschreibungs-Tooltips aktivieren. Dazu in der Config ergänzen:

```ini
[wordpress]
url             = https://deine-domain.de/deine-buchseite
wordpress_mode  = yes
```

Ohne WordPress funktioniert die Galerie trotzdem vollständig – Preise und Links zum eigenen Händlerkatalog werden automatisch eingebunden.
