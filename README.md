# GTA RP Fraktions-Lager Bot

Ein Discord Bot zur Verwaltung von Lagerbeständen für GTA RP Fraktionen. Der Bot ermöglicht eine einfache und übersichtliche Verwaltung verschiedener Lagerbestände über Discord.

## Features

- 🎮 Benutzerfreundliche grafische Oberfläche
- 📦 Verwaltung mehrerer Lager
- 📝 Detaillierte Protokollierung aller Aktivitäten
- 🔒 Rollenbasierte Berechtigungen
- ⚡ Schnelle Reaktionszeiten
- 🛡️ Sicherheit durch Backup-System

## Installation

1. Installieren Sie Python 3.8 oder höher
2. Klonen Sie das Repository:
   ```
   git clone [Repository-URL]
   cd [Projektordner]
   ```
3. Installieren Sie die erforderlichen Pakete:
   ```
   pip install -r requirements.txt
   ```
4. Erstellen Sie eine `.env` Datei mit folgendem Inhalt:
   ```
   DISCORD_TOKEN=Ihr_Bot_Token
   ```
5. Starten Sie den Bot:
   ```
   python bot.py
   ```

## Verwendung

Der Bot bietet zwei Nutzungsmöglichkeiten:

### 1. Grafische Benutzeroberfläche (empfohlen)
Verwenden Sie den Befehl `!lager` um das Hauptmenü zu öffnen. 

#### Verfügbare Funktionen:

- **📊 Lagerbestand anzeigen** (Blauer Button)
  - Übersicht eines oder aller Lager
  - Filteroptionen verfügbar

- **➕ Item hinzufügen** (Grüner Button)
  - Schnelles Hinzufügen von Items
  - Automatische Bestandsaktualisierung

- **➖ Item entnehmen** (Roter Button)
  - Einfache Entnahme von Items
  - Optional mit Empfängerdokumentation

- **⚙️ Lager verwalten** (Grauer Button)
  - Lager erstellen/umbenennen/löschen
  - Berechtigungen verwalten

### 2. Textbefehle

Alternative Steuerung über Textbefehle:

| Befehl | Beschreibung | Beispiel |
|--------|--------------|----------|
| `!add` | Items hinzufügen | `!add 1x P99 Waffenlager` |
| `!remove` | Items entnehmen | `!remove 1x P99 Waffenlager John` |
| `!bestand` | Bestand anzeigen | `!bestand Waffenlager` |
| `!log` | Aktivitäten anzeigen | `!log Waffenlager` |

## Lagerverwaltung

Der Bot ermöglicht eine vollständig dynamische Lagerverwaltung:

- **Flexible Lagerstruktur**: Erstellen Sie beliebig viele Lager nach Ihren Bedürfnissen
- **Einfache Verwaltung**: Lager können jederzeit erstellt, umbenannt oder gelöscht werden
- **Bestandskontrolle**: Übersichtliche Darstellung aller Items und Mengen pro Lager
- **Aktivitätsverfolgung**: Lückenlose Dokumentation aller Lagerbewegungen

## Support

Bei Fragen oder Problemen können Sie:
- Ein Issue auf GitHub erstellen
- Den Support-Discord beitreten

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Weitere Details finden Sie in der `LICENSE` Datei. 
