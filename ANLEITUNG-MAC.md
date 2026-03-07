# Booq – Deine Booklooker-Galerie einrichten (Mac)

*Keine Vorkenntnisse nötig. Wir öffnen einmal das Terminal und richten alles ein – danach läuft die Galerie per Klick.*

---

## Was du brauchst

- Einen Mac
- Einen Booklooker-Account mit API-Key
- Deine Booklooker-UID (7-stellige Nummer)
- Ca. 20 Minuten

---

## Schritt 1 – Terminal öffnen

**⌘ + Leertaste** drücken, „Terminal" eingeben, Enter drücken.

Ein Fenster mit Texteingabe öffnet sich – keine Angst, wir machen dort nur ein paar einfache Dinge.

---

## Schritt 2 – Script herunterladen

Diesen Befehl ins Terminal eingeben und Enter drücken:

```bash
git clone https://github.com/wdeu/galerie-generator.git ~/projects/galerie-generator
```

*Was passiert: Das Script wird in den Ordner `~/projects/galerie-generator/` geladen.*

---

## Schritt 3 – Einmalig starten (Config anlegen)

```bash
python3 ~/projects/galerie-generator/galerie-generator.py
```

Das Script bricht mit einer Meldung ab: *„Config erstellt – bitte API-Key eintragen."*

Das ist gut so – weiter zu Schritt 4!

---

## Schritt 4 – Config ausfüllen

```bash
open ~/.booklooker-sync.ini
```

Die Datei öffnet sich im Texteditor. Dort trägst du ein:

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

Datei speichern (`⌘ + S`), Texteditor schließen.

---

## Schritt 5 – Bilder herunterladen

In deinem Booklooker-Konto: Mein Depot → Bilder → alle als ZIP herunterladen.
Das ZIP in den Ordner `~/Downloads/` entpacken (Doppelklick auf das ZIP genügt).

---

## Schritt 6 – Galerie generieren

```bash
python3 ~/projects/galerie-generator/galerie-generator.py
```

Das Script läuft jetzt durch:
- Bilder werden sortiert (verkaufte Bücher wandern in einen Unterordner)
- Preise werden live aus der Booklooker-API geholt
- Eine fertige `index.html` wird gebaut

Das Ergebnis liegt im Ordner `~/Downloads/galerie-output/`.

Vorschau im Browser:
```bash
open ~/Downloads/galerie-output/index.html
```

---

## Schritt 7 – Galerie veröffentlichen

Du hast zwei Möglichkeiten:

### Option A – Eigener Webserver (FTP)

Den Inhalt von `galerie-output/` (also `index.html` + Ordner `images/`) per FTP auf deinen Webserver hochladen.
Kostenloser FTP-Client für Mac: [Cyberduck](https://cyberduck.io)

### Option B – Netlify (kostenlos, kein Webserver nötig)

1. Kostenlosen Account anlegen auf [netlify.com](https://netlify.com)
2. Auf der Netlify-Startseite gibt es einen Bereich **„Drag & Drop"**
3. Den Ordner `galerie-output/` einfach dort hineinziehen
4. Netlify vergibt automatisch eine Adresse (z.B. `zufaelliger-name.netlify.app`)
5. Diese Adresse kannst du in deinem Booklooker-Profil oder im Forum teilen

*Beim nächsten Update: Ordner einfach erneut hineinziehen – Netlify aktualisiert die Seite automatisch.*

---

## Galerie aktualisieren

Neue Bilder von Booklooker herunterladen, entpacken, Script nochmal starten, Ordner erneut hochladen (FTP oder Netlify Drag & Drop). Das war's.

```bash
python3 ~/projects/galerie-generator/galerie-generator.py
```

---

## Optionale Erweiterung: WordPress-Integration

Wer WordPress mit dem Plugin *wordpress-booklooker-bot* betreibt, kann zusätzlich Direktlinks zu einzelnen Artikeln und Beschreibungs-Tooltips aktivieren. Dazu in der Config ergänzen:

```ini
[wordpress]
url             = https://deine-domain.de/deine-buchseite
wordpress_mode  = yes
```

Ohne WordPress funktioniert die Galerie trotzdem vollständig – Preise und Links zum eigenen Händlerkatalog werden automatisch eingebunden.
