# Terminal-Befehle Referenz – Galerie-Generator Projekt

## 📁 Navigation & Verzeichnisse

```bash
# Aktuelles Verzeichnis anzeigen
pwd

# In ein Verzeichnis wechseln
cd ~/Projects/galerie-generator
cd ..                           # Eine Ebene höher
cd ~                           # Ins Heimverzeichnis

# Inhalt eines Ordners anzeigen
ls                             # Einfache Liste
ls -la                         # Ausführlich mit versteckten Dateien
ls -lh                         # Mit menschenlesbaren Dateigrößen

# Ordner erstellen
mkdir neuer-ordner
mkdir -p pfad/zu/ordner        # Mit Unterordnern
```

## 📝 Dateien anzeigen & bearbeiten

```bash
# Datei komplett anzeigen
cat datei.txt

# Erste/letzte Zeilen anzeigen
head -20 datei.txt             # Erste 20 Zeilen
tail -20 datei.txt             # Letzte 20 Zeilen
tail -f logfile.log            # Live-Mitlesen (Logs)

# Bestimmte Zeilen anzeigen
sed -n '50,65p' datei.py       # Zeilen 50-65

# Datei bearbeiten
nano datei.txt                 # Einfacher Editor
                               # Speichern: Ctrl+O, Enter
                               # Beenden: Ctrl+X

# Datei mit Sonderzeichen anzeigen
cat -A datei.txt               # Zeigt Tabs, Leerzeichen, etc.
```

## 🔍 Suchen & Filtern

```bash
# In Datei suchen
grep "suchtext" datei.txt
grep -n "def main" script.py   # Mit Zeilennummern
grep -i "error" log.txt        # Case-insensitive

# Text im aktuellen Verzeichnis suchen
grep -r "API_KEY" .            # Rekursiv in allen Dateien

# Dateien finden
find . -name "*.py"            # Alle Python-Dateien
find ~ -name "config.yml"      # config.yml im Heimverzeichnis
find /Users -name "*galerie*" 2>/dev/null  # Unterdrückt Fehler

# Ausgabe filtern
cat log.txt | grep "ERROR"     # Nur Fehlerzeilen
ls -la | grep "galerie"        # Nur Dateien mit "galerie"
```

## 📋 Kopieren, Verschieben, Löschen

```bash
# Kopieren
cp datei.txt backup.txt
cp -r ordner/ backup/          # Ordner rekursiv kopieren

# Verschieben / Umbenennen
mv alte.txt neue.txt
mv datei.txt ~/Documents/

# Löschen
rm datei.txt
rm -rf ordner/                 # VORSICHT: Ordner + Inhalt unwiderruflich löschen!

# Versteckte Dateien
ls -la                         # Zeigt .gitignore, .env, etc.
```

## 🔧 Python & pip

```bash
# Python-Version prüfen
python3 --version
which python3

# Script ausführen
python3 script.py
./script.py                    # Wenn executable (chmod +x)

# Pakete installieren
pip3 install requests
pip3 install --user requests   # Nur für aktuellen User

# Installierte Pakete anzeigen
pip3 list
pip3 show requests             # Details zu einem Paket
```

## 🌳 Git Befehle

```bash
# Repository initialisieren
git init

# Status anzeigen
git status                     # Was ist geändert?
git log --oneline              # Commit-Historie

# Dateien hinzufügen
git add datei.txt
git add .                      # Alle geänderten Dateien
git add -A                     # Alles (inkl. gelöschte)

# Committen
git commit -m "Beschreibung"

# Remote verbinden
git remote add origin https://github.com/user/repo.git
git remote -v                  # Zeigt Remote-URLs

# Push & Pull
git push origin main
git push origin main --force   # Überschreibt Remote (VORSICHT!)
git pull origin main

# Branch-Info
git branch                     # Zeigt lokale Branches
git branch -a                  # Inkl. Remote-Branches

# Remote ändern/entfernen
git remote remove origin
git remote set-url origin https://neue-url.git
```

## 🔐 Berechtigungen & Ausführbar machen

```bash
# Datei ausführbar machen
chmod +x script.py

# Berechtigungen anzeigen
ls -la script.py
# -rwxr-xr-x  = ausführbar
# -rw-r--r--  = nicht ausführbar

# Berechtigungen ändern
chmod 600 ~/.netrc             # Nur User kann lesen/schreiben
chmod 755 script.sh            # User: rwx, Andere: rx
```

## 🍺 Homebrew (macOS Paketmanager)

```bash
# Paket installieren
brew install lftp
brew install git
brew install --cask filezilla  # GUI-Apps

# Installierte Pakete anzeigen
brew list

# Paket suchen
brew search python

# Updates
brew update                    # Paketliste aktualisieren
brew upgrade                   # Alle Pakete updaten
brew upgrade git               # Nur git updaten
```

## 📦 Arbeiten mit diesem Projekt

```bash
# Galerie neu generieren
cd ~/Projects/galerie-generator
./galerie-generator.py

# Config bearbeiten
nano ~/.booklooker-sync.ini

# Ergebnis lokal ansehen
open public/index.html

# Git-Updates
git status
git add .
git commit -m "Update README"
git push origin main

# Projekt-Struktur anzeigen
tree -L 2                      # Falls tree installiert
ls -R                          # Rekursive Liste
```

## 🔄 Prozesse & System

```bash
# Laufende Prozesse anzeigen
ps aux | grep python           # Python-Prozesse finden

# Prozess beenden
Ctrl+C                         # Im Terminal
kill <PID>                     # Mit Prozess-ID

# Festplattenplatz
df -h                          # Verfügbarer Speicher
du -sh ordner/                 # Größe eines Ordners
du -sh public/*                # Größe aller Dateien in public/

# Speicher/CPU
top                            # System-Monitor
htop                           # Besser (falls installiert)
```

## 💡 Nützliche Kombinationen

```bash
# Mehrere Befehle nacheinander
cd ~/Projects && ls -la
./script.py && open public/index.html

# Befehl nur bei Erfolg ausführen
git add . && git commit -m "Update" && git push

# Output in Datei schreiben
ls -la > dateiliste.txt        # Überschreibt
ls -la >> dateiliste.txt       # Hängt an

# Befehl-Output als Input nutzen
echo "Dateien: $(ls -1 | wc -l)"

# Letzten Befehl wiederholen
!!                             # Ganzer letzter Befehl
!$                             # Letztes Argument
```

## 🔧 Umgebungsvariablen & Konfiguration

```bash
# Variablen anzeigen
echo $HOME
echo $PATH
env                            # Alle Umgebungsvariablen

# Variable temporär setzen
export GOROOT=/usr/local/go

# Shell-Config bearbeiten
nano ~/.zshrc                  # zsh (macOS Standard)
nano ~/.bash_profile           # bash
source ~/.zshrc                # Neu laden ohne Terminal-Neustart
```

## 🐛 Debugging & Problemlösung

```bash
# Datei-Encoding prüfen
file datei.txt

# Python-Syntax prüfen
python3 -m py_compile script.py

# Welches Programm wird ausgeführt?
which python3
which git

# Fehlerausgabe unterdrücken
befehl 2>/dev/null             # Stderr weg
befehl > /dev/null 2>&1        # Stdout + Stderr weg

# Befehl mit Debug-Output
set -x                         # Bash Debug aktivieren
set +x                         # Deaktivieren
```

## 📊 Spezielle Befehle aus diesem Projekt

```bash
# Go-Installation prüfen
go version
go env GOROOT

# Python Dependencies
pip3 install requests
python3 -c "import requests; print('OK')"

# Git Repo-Probleme lösen
git pull origin main --allow-unrelated-histories
git push origin main --force

# Mehrfachbilder finden
find ~/Pictures/Galerie -name "*_2.jpg"
find ~/Pictures/Galerie -name "*_3.jpg"

# Anzahl Bilder zählen
ls ~/Pictures/Galerie/*.jpg | wc -l
```

## 🎓 Wichtige Tastenkombinationen

```bash
Ctrl+C          # Befehl abbrechen
Ctrl+D          # EOF / Logout
Ctrl+Z          # Prozess pausieren (bg zum Fortsetzen)
Ctrl+L          # Terminal leeren (wie 'clear')
Ctrl+A          # Cursor an Zeilenanfang
Ctrl+E          # Cursor an Zeilenende
Ctrl+R          # Befehlshistorie durchsuchen
Tab             # Auto-Vervollständigung
↑ / ↓           # Durch Befehlshistorie

# In nano:
Ctrl+O          # Speichern
Ctrl+X          # Beenden
Ctrl+K          # Zeile ausschneiden
Ctrl+U          # Einfügen
Ctrl+W          # Suchen
```

## 📚 Hilfe & Dokumentation

```bash
# Manual-Pages
man ls                         # Hilfe zu ls-Befehl
man git-commit                 # Git-Commit Hilfe

# Kurz-Hilfe
ls --help
git --help
python3 --help

# Befehlshistorie
history                        # Alle bisherigen Befehle
history | grep "git"           # Nur git-Befehle
```

## ⚠️ Vorsicht bei diesen Befehlen!

```bash
# GEFÄHRLICH - können Daten unwiderruflich löschen:
rm -rf /                       # NIEMALS ausführen!
rm -rf *                       # Löscht alles im Ordner
sudo rm -rf                    # Mit Admin-Rechten noch gefährlicher

# Immer erst prüfen mit:
ls -la                         # Was würde gelöscht?
rm -i datei.txt                # Fragt vor jedem Löschen nach

# Git Force-Befehle überschreiben History:
git push --force               # Nur bei eigenen Repos!
git reset --hard               # Verwirft alle lokalen Änderungen
```

## 🎯 Quick Reference - Die 10 wichtigsten

```bash
pwd                            # Wo bin ich?
ls -la                         # Was ist hier?
cd ordner                      # Wohin gehe ich?
nano datei.txt                 # Datei bearbeiten
cat datei.txt                  # Datei anzeigen
git status                     # Git-Status
git add . && git commit -m "x" # Änderungen speichern
./script.py                    # Script ausführen
open datei.html               # Datei im Browser
Ctrl+C                        # Befehl abbrechen
```

---

**Pro-Tipp:** `man befehl` gibt dir zu fast jedem Befehl eine ausführliche Anleitung!
