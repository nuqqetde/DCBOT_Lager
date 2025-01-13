import os
import json
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime
import discord
from typing import Optional

# Lade die Umgebungsvariablen
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot Setup mit allen Intents und Berechtigungen
intents = discord.Intents.all()
intents.message_content = True  # Aktiviere message_content intent

def load_lager():
    if os.path.exists(LAGER_FILE):
        with open(LAGER_FILE, 'r') as f:
            data = json.load(f)
            for lager_name, lager_data in data.items():
                if isinstance(lager_data, dict) and "items" not in lager_data:
                    data[lager_name] = {"items": lager_data, "log": []}
            return data
    return DEFAULT_LAGER

def save_lager(lager_data):
    with open(LAGER_FILE, 'w') as f:
        json.dump(lager_data, f, indent=4)

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, 'r') as f:
            global channel_ids
            channel_ids = json.load(f)

def save_channels():
    with open(CHANNELS_FILE, 'w') as f:
        json.dump(channel_ids, f, indent=4)

# Lagerdaten
LAGER_FILE = 'lager.json'
CHANNELS_FILE = 'channels.json'

# Channel IDs
channel_ids = {
    "lagerverwaltung": None,
    "lagerlogs": None,
    "lagerbestand": None
}

# Standardlager
DEFAULT_LAGER = {}

class PersistentViewBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.persistent_views_added = False

    async def setup_hook(self) -> None:
        if not self.persistent_views_added:
            # Erstelle die Views
            lager_view = LagerView()
            management_view = StorageManagementView()
            
            # Füge die Views hinzu
            self.add_view(lager_view)
            self.add_view(management_view)
            
            self.persistent_views_added = True

bot = PersistentViewBot()

# Debug Logging
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    print(f"Nachricht erhalten: {message.content}")
    await bot.process_commands(message)

async def send_log(guild, message, user=None):
    """Sendet eine Log-Nachricht und optional eine Bestätigung an den Benutzer"""
    if channel_ids["lagerlogs"]:
        channel = guild.get_channel(channel_ids["lagerlogs"])
        if channel:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await channel.send(f"`{timestamp}` {message}")

async def send_error(interaction: discord.Interaction, error_message: str):
    """Sendet eine Fehlermeldung in den Logs-Channel"""
    if channel_ids["lagerlogs"]:
        channel = interaction.guild.get_channel(channel_ids["lagerlogs"])
        if channel:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await channel.send(f"`{timestamp}` ❌ Fehler von {interaction.user.global_name or str(interaction.user)}: {error_message}")
            # Deferred die Interaktion ohne Nachricht
            try:
                await interaction.response.defer()
            except:
                pass

async def update_bestand(guild, message):
    if channel_ids["lagerbestand"]:
        channel = guild.get_channel(channel_ids["lagerbestand"])
        if channel:
            await channel.send(message)

class SelectStorageModal(discord.ui.Modal):
    def __init__(self, title: str) -> None:
        super().__init__(title=title)
        
        self.lager = discord.ui.TextInput(
            label="Lagername (leer für alle Lager)",
            placeholder="z.B. Waffenlager",
            required=False,
        )
        self.add_item(self.lager)

    async def on_submit(self, interaction: discord.Interaction):
        lager_data = load_lager()
        lager_name = self.lager.value.strip() if self.lager.value else None
        
        if lager_name and lager_name not in lager_data:
            await send_error(interaction, f"Lager '{lager_name}' nicht gefunden!")
            return

        if lager_name:
            if not lager_data[lager_name]["items"]:
                await send_error(interaction, f"{lager_name} ist leer.")
                return

            message = f"**{lager_name}:**\n"
            for item, menge in lager_data[lager_name]["items"].items():
                message += f"- {item}: {menge}x\n"
        else:
            message = "**Alle Lager:**\n"
            for lager, data in lager_data.items():
                if data["items"]:
                    message += f"\n{lager}:\n"
                    for item, menge in data["items"].items():
                        message += f"- {item}: {menge}x\n"

        await update_bestand(interaction.guild, message)
        await send_log(interaction.guild, f"�� {interaction.user.global_name or interaction.user} hat den Lagerbestand abgerufen")
        try:
            await interaction.response.defer()
        except:
            pass

class AddItemModal(discord.ui.Modal):
    def __init__(self, title: str) -> None:
        super().__init__(title=title)

        self.menge = discord.ui.TextInput(
            label="Menge",
            placeholder="z.B. 5",
            required=True,
        )
        self.add_item(self.menge)

        self.item = discord.ui.TextInput(
            label="Item",
            placeholder="z.B. P99",
            required=True,
        )
        self.add_item(self.item)

    async def on_submit(self, interaction: discord.Interaction):
        lager_data = load_lager()
        lager_name = self.selected_lager
        
        try:
            menge = int(self.menge.value)
            item = self.item.value.strip()
        except ValueError:
            await send_error(interaction, "Menge muss eine Zahl sein!")
            return

        if item in lager_data[lager_name]["items"]:
            lager_data[lager_name]["items"][item] += menge
        else:
            lager_data[lager_name]["items"][item] = menge

        log_entry = {
            "zeitpunkt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "aktion": "Einlagerung",
            "item": item,
            "menge": menge,
            "benutzer": interaction.user.global_name or str(interaction.user)
        }
        lager_data[lager_name]["log"].append(log_entry)

        save_lager(lager_data)
        await send_log(interaction.guild, f"�� {interaction.user.global_name or interaction.user} hat {menge}x {item} zum {lager_name} hinzugefügt")
        try:
            await interaction.response.defer()
        except:
            pass

class RemoveItemModal(discord.ui.Modal):
    def __init__(self, title: str) -> None:
        super().__init__(title=title)

        self.menge = discord.ui.TextInput(
            label="Menge",
            placeholder="z.B. 5",
            required=True,
        )
        self.add_item(self.menge)

        self.item = discord.ui.TextInput(
            label="Item",
            placeholder="z.B. P99",
            required=True,
        )
        self.add_item(self.item)

        self.empfaenger = discord.ui.TextInput(
            label="Empfänger (optional)",
            placeholder="z.B. John Doe",
            required=False,
        )
        self.add_item(self.empfaenger)

    async def on_submit(self, interaction: discord.Interaction):
        lager_data = load_lager()
        lager_name = self.selected_lager
        
        try:
            menge = int(self.menge.value)
            item = self.item.value.strip()
        except ValueError:
            await send_error(interaction, "Menge muss eine Zahl sein!")
            return

        if item not in lager_data[lager_name]["items"]:
            await send_error(interaction, f"{item} ist nicht im {lager_name} vorhanden!")
            return

        if lager_data[lager_name]["items"][item] < menge:
            await send_error(interaction, f"Nicht genügend {item} im {lager_name}!")
            return

        lager_data[lager_name]["items"][item] -= menge
        if lager_data[lager_name]["items"][item] == 0:
            del lager_data[lager_name]["items"][item]

        empfaenger = self.empfaenger.value.strip() if self.empfaenger.value else None
        log_entry = {
            "zeitpunkt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "aktion": "Entnahme",
            "item": item,
            "menge": menge,
            "benutzer": interaction.user.global_name or str(interaction.user),
            "empfaenger": empfaenger if empfaenger else "Nicht angegeben"
        }
        lager_data[lager_name]["log"].append(log_entry)

        save_lager(lager_data)
        log_message = f"�� {interaction.user.global_name or interaction.user} hat {menge}x {item} aus dem {lager_name} entfernt"
        if empfaenger:
            log_message += f" (Empfänger: {empfaenger})"
        await send_log(interaction.guild, log_message)
        try:
            await interaction.response.defer()
        except:
            pass

class CreateStorageModal(discord.ui.Modal):
    def __init__(self, title: str) -> None:
        super().__init__(title=title)

        self.lager = discord.ui.TextInput(
            label="Neuer Lagername",
            placeholder="z.B. Elektroniklager",
            required=True,
        )
        self.add_item(self.lager)

    async def on_submit(self, interaction: discord.Interaction):
        lager_data = load_lager()
        lager_name = self.lager.value.strip()
        
        if lager_name in lager_data:
            await send_error(interaction, f"Lager '{lager_name}' existiert bereits!")
            return

        lager_data[lager_name] = {"items": {}, "log": []}
        save_lager(lager_data)
        # Sende nur die Log-Nachricht
        await send_log(interaction.guild, f"�� {interaction.user.global_name or interaction.user} hat das Lager '{lager_name}' erstellt")
        
        # UI im Lagerverwaltung-Channel aktualisieren
        if channel_ids["lagerverwaltung"]:
            channel = interaction.guild.get_channel(channel_ids["lagerverwaltung"])
            if channel:
                # Lösche die letzte Nachricht
                async for message in channel.history(limit=1):
                    await message.delete()
                # Sende neue UI
                view = LagerView()
                await channel.send("Lagerverwaltung:", view=view)
        
        # Deferred die Interaktion ohne Nachricht
        try:
            await interaction.response.defer()
        except:
            pass

class RenameStorageModal(discord.ui.Modal):
    def __init__(self, title: str) -> None:
        super().__init__(title=title)

        self.alter_name = discord.ui.TextInput(
            label="Alter Lagername",
            placeholder="z.B. Elektroniklager",
            required=True,
        )
        self.add_item(self.alter_name)

        self.neuer_name = discord.ui.TextInput(
            label="Neuer Lagername",
            placeholder="z.B. Techniklager",
            required=True,
        )
        self.add_item(self.neuer_name)

    async def on_submit(self, interaction: discord.Interaction):
        lager_data = load_lager()
        alter_name = self.alter_name.value.strip()
        neuer_name = self.neuer_name.value.strip()
        
        if alter_name not in lager_data:
            await send_error(interaction, f"Lager '{alter_name}' nicht gefunden!")
            return

        if neuer_name in lager_data:
            await send_error(interaction, f"Ein Lager mit dem Namen '{neuer_name}' existiert bereits!")
            return

        lager_data[neuer_name] = lager_data.pop(alter_name)
        save_lager(lager_data)
        # Sende nur die Log-Nachricht
        await send_log(interaction.guild, f"✏️ {interaction.user.global_name or interaction.user} hat das Lager '{alter_name}' in '{neuer_name}' umbenannt")
        
        # UI im Lagerverwaltung-Channel aktualisieren
        if channel_ids["lagerverwaltung"]:
            channel = interaction.guild.get_channel(channel_ids["lagerverwaltung"])
            if channel:
                # Lösche die letzte Nachricht
                async for message in channel.history(limit=1):
                    await message.delete()
                # Sende neue UI
                view = LagerView()
                await channel.send("Lagerverwaltung:", view=view)
        
        # Deferred die Interaktion ohne Nachricht
        try:
            await interaction.response.defer()
        except:
            pass

class DeleteStorageModal(discord.ui.Modal):
    def __init__(self, title: str) -> None:
        super().__init__(title=title)

        self.lager = discord.ui.TextInput(
            label="Zu löschendes Lager",
            placeholder="z.B. Elektroniklager",
            required=True,
        )
        self.add_item(self.lager)

    async def on_submit(self, interaction: discord.Interaction):
        lager_data = load_lager()
        lager_name = self.lager.value.strip()
        
        if lager_name not in lager_data:
            await send_error(interaction, f"Lager '{lager_name}' nicht gefunden!")
            return

        if lager_data[lager_name]["items"]:
            await send_error(interaction, f"Das Lager '{lager_name}' enthält noch Items! Bitte leere es zuerst.")
            return

        del lager_data[lager_name]
        save_lager(lager_data)
        # Sende nur die Log-Nachricht
        await send_log(interaction.guild, f"🗑️ {interaction.user.global_name or interaction.user} hat das Lager '{lager_name}' gelöscht")
        
        # UI im Lagerverwaltung-Channel aktualisieren
        if channel_ids["lagerverwaltung"]:
            channel = interaction.guild.get_channel(channel_ids["lagerverwaltung"])
            if channel:
                # Lösche die letzte Nachricht
                async for message in channel.history(limit=1):
                    await message.delete()
                # Sende neue UI
                view = LagerView()
                await channel.send("Lagerverwaltung:", view=view)
        
        # Deferred die Interaktion ohne Nachricht
        try:
            await interaction.response.defer()
        except:
            pass

class StorageSelect(discord.ui.Select):
    def __init__(self, action: str):
        self.action = action
        lager_data = load_lager()
        options = [
            discord.SelectOption(label=name, description=f"{len(data['items'])} Items") 
            for name, data in lager_data.items()
        ]
        if action == "show":
            options.insert(0, discord.SelectOption(label="Alle Lager", description="Zeigt den Bestand aller Lager"))
        
        super().__init__(
            placeholder="Wähle ein Lager...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if self.action == "show":
            if self.values[0] == "Alle Lager":
                lager_data = load_lager()
                message = "**Alle Lager:**\n"
                for lager, data in lager_data.items():
                    if data["items"]:
                        message += f"\n{lager}:\n"
                        for item, menge in data["items"].items():
                            message += f"- {item}: {menge}x\n"
                await update_bestand(interaction.guild, message)
                await send_log(interaction.guild, f"�� {interaction.user.global_name or interaction.user} hat den Lagerbestand aller Lager abgerufen")
            else:
                lager_data = load_lager()
                lager_name = self.values[0]
                if not lager_data[lager_name]["items"]:
                    await send_error(interaction, f"{lager_name} ist leer.")
                    return
                message = f"**{lager_name}:**\n"
                for item, menge in lager_data[lager_name]["items"].items():
                    message += f"- {item}: {menge}x\n"
                await update_bestand(interaction.guild, message)
                await send_log(interaction.guild, f"�� {interaction.user.global_name or interaction.user} hat den Lagerbestand von {lager_name} abgerufen")
        elif self.action == "add":
            await interaction.response.send_modal(AddItemModal("Item hinzufügen"))
        elif self.action == "remove":
            await interaction.response.send_modal(RemoveItemModal("Item entnehmen"))
        try:
            await interaction.response.defer()
        except:
            pass

class StorageSelectView(discord.ui.View):
    def __init__(self, action: str):
        super().__init__()
        self.add_item(StorageSelect(action))

def get_short_storage_list(lager_data, max_length=90):
    """Erstellt eine gekürzte Liste der Lager"""
    names = list(lager_data.keys())
    if len(names) <= 3:
        return ", ".join(names)
    
    # Zeige die ersten zwei und das letzte Lager
    short_list = f"{names[0]}, {names[1]} ... {names[-1]}"
    return f"z.B. {short_list}"

class LagerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.selected_lager = None
        self.update_select()

    def update_select(self):
        # Erstelle das Select-Menü
        lager_data = load_lager()
        options = []
        for name, data in lager_data.items():
            options.append(discord.SelectOption(
                label=name,
                description=f"{len(data['items'])} Items"
            ))

        # Wenn keine Lager existieren, deaktiviere das Select-Menü
        if not options:
            options.append(discord.SelectOption(
                label="Keine Lager vorhanden",
                description="Erstelle zuerst ein neues Lager"
            ))

        async def select_callback(interaction: discord.Interaction):
            if not options or options[0].label == "Keine Lager vorhanden":
                await interaction.response.send_message("Es existieren noch keine Lager. Erstelle zuerst ein neues Lager!", ephemeral=True)
                return
            self.selected_lager = interaction.data['values'][0]
            await interaction.response.defer()

        select = discord.ui.Select(
            placeholder="Wähle ein Lager aus...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="storage_select",
            row=0,
            disabled=not options or options[0].label == "Keine Lager vorhanden"
        )
        select.callback = select_callback
        self.add_item(select)

        # Erstelle die Buttons für Lageroperationen (Reihe 1)
        show_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Lagerbestand anzeigen",
            custom_id="show_inventory",
            row=1
        )
        add_button = discord.ui.Button(
            style=discord.ButtonStyle.green,
            label="Item hinzufügen",
            custom_id="add_item",
            row=1
        )
        remove_button = discord.ui.Button(
            style=discord.ButtonStyle.red,
            label="Item entnehmen",
            custom_id="remove_item",
            row=1
        )

        # Erstelle die Buttons für Lagerverwaltung (Reihe 2)
        create_button = discord.ui.Button(
            style=discord.ButtonStyle.green,
            label="Neues Lager",
            custom_id="create_storage",
            row=2
        )
        rename_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Lager umbenennen",
            custom_id="rename_storage",
            row=2
        )
        delete_button = discord.ui.Button(
            style=discord.ButtonStyle.red,
            label="Lager löschen",
            custom_id="delete_storage",
            row=2
        )

        async def show_callback(interaction: discord.Interaction):
            if not self.selected_lager:
                await interaction.response.send_message("Bitte wähle zuerst ein Lager aus!", ephemeral=True)
                return
            
            lager_data = load_lager()
            if not lager_data[self.selected_lager]["items"]:
                await send_error(interaction, f"{self.selected_lager} ist leer.")
                return

            message = f"**{self.selected_lager}:**\n"
            for item, menge in lager_data[self.selected_lager]["items"].items():
                message += f"- {item}: {menge}x\n"
            await update_bestand(interaction.guild, message)
            await send_log(interaction.guild, f"�� {interaction.user.global_name or interaction.user} hat den Lagerbestand von {self.selected_lager} abgerufen")
            await interaction.response.defer()

        async def add_callback(interaction: discord.Interaction):
            if not self.selected_lager:
                await interaction.response.send_message("Bitte wähle zuerst ein Lager aus!", ephemeral=True)
                return
            
            modal = AddItemModal("Item hinzufügen")
            modal.selected_lager = self.selected_lager
            await interaction.response.send_modal(modal)

        async def remove_callback(interaction: discord.Interaction):
            if not self.selected_lager:
                await interaction.response.send_message("Bitte wähle zuerst ein Lager aus!", ephemeral=True)
                return
            
            modal = RemoveItemModal("Item entnehmen")
            modal.selected_lager = self.selected_lager
            await interaction.response.send_modal(modal)

        async def create_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(CreateStorageModal(title="Neues Lager erstellen"))

        async def rename_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(RenameStorageModal(title="Lager umbenennen"))

        async def delete_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(DeleteStorageModal(title="Lager löschen"))

        show_button.callback = show_callback
        add_button.callback = add_callback
        remove_button.callback = remove_callback
        create_button.callback = create_callback
        rename_button.callback = rename_callback
        delete_button.callback = delete_callback

        self.add_item(show_button)
        self.add_item(add_button)
        self.add_item(remove_button)
        self.add_item(create_button)
        self.add_item(rename_button)
        self.add_item(delete_button)

class StorageManagementView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        create_button = discord.ui.Button(
            style=discord.ButtonStyle.green,
            label="Neues Lager erstellen",
            custom_id="create_storage"
        )
        rename_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Lager umbenennen",
            custom_id="rename_storage"
        )
        delete_button = discord.ui.Button(
            style=discord.ButtonStyle.red,
            label="Lager löschen",
            custom_id="delete_storage"
        )

        async def create_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(CreateStorageModal(title="Neues Lager erstellen"))

        async def rename_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(RenameStorageModal(title="Lager umbenennen"))

        async def delete_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(DeleteStorageModal(title="Lager löschen"))

        create_button.callback = create_callback
        rename_button.callback = rename_callback
        delete_button.callback = delete_callback

        self.add_item(create_button)
        self.add_item(rename_button)
        self.add_item(delete_button)

async def check_channels_exist(guild):
    """Überprüft ob die Kanäle tatsächlich auf dem Server existieren"""
    if not all(channel_ids.values()):
        return False
        
    for channel_id in channel_ids.values():
        if not guild.get_channel(channel_id):
            # Wenn ein Kanal nicht gefunden wurde, setze alle IDs zurück
            channel_ids["lagerverwaltung"] = None
            channel_ids["lagerlogs"] = None
            channel_ids["lagerbestand"] = None
            save_channels()
            return False
    return True

@bot.event
async def on_ready():
    print(f'{bot.user} ist online!')
    if not os.path.exists(LAGER_FILE):
        save_lager(DEFAULT_LAGER)
    load_channels()

@bot.command()
async def lager(ctx):
    """Öffnet das Lagerverwaltungs-Interface"""
    print(f"!lager Befehl von {ctx.author} erhalten")
    try:
        # Überprüfe ob die Kanäle tatsächlich existieren
        channels_exist = await check_channels_exist(ctx.guild)
        
        if not channels_exist:
            print("Erstelle neue Kanäle...")
            # Erstelle Kategorie
            category = await ctx.guild.create_category("📦 Lagersystem")
            
            # Erstelle Kanäle
            lagerverwaltung = await category.create_text_channel("lagerverwaltung")
            lagerlogs = await category.create_text_channel("lagerlogs")
            lagerbestand = await category.create_text_channel("lagerbestand")
            
            # Speichere Channel IDs
            channel_ids["lagerverwaltung"] = lagerverwaltung.id
            channel_ids["lagerlogs"] = lagerlogs.id
            channel_ids["lagerbestand"] = lagerbestand.id
            save_channels()
            print("Kanäle erstellt und IDs gespeichert")
            
            # Sende UI nur im Lagerverwaltung-Channel
            view = LagerView()
            await lagerverwaltung.send("Lagerverwaltung:", view=view)
            print("UI im Lagerverwaltung-Channel gesendet")
            
            # Sende Willkommensnachrichten in die anderen Kanäle
            await lagerlogs.send("**Lager-Logs**\nHier werden alle Aktivitäten protokolliert.")
            await lagerbestand.send("**Lagerbestand**\nHier wird der aktuelle Lagerbestand angezeigt.")
            
            # Sende Bestätigung in den Logs
            await lagerlogs.send(f"`{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}` 📦 Lagersystem wurde von {ctx.author.global_name or ctx.author} eingerichtet")

            # Sende Erfolgsmeldung mit Verlinkungen und Anleitung
            success_message = (
                "✅ **Lagersystem erfolgreich eingerichtet!**\n\n"
                f"Die folgenden Kanäle wurden erstellt:\n"
                f"🔧 {lagerverwaltung.mention} - Hier findest du die Benutzeroberfläche zur Verwaltung\n"
                f"📝 {lagerlogs.mention} - Hier werden alle Aktivitäten protokolliert\n"
                f"📦 {lagerbestand.mention} - Hier wird der aktuelle Bestand angezeigt\n\n"
                "**Kurzanleitung:**\n"
                "1. Gehe zum Lagerverwaltungs-Channel\n"
                "2. Wähle ein Lager aus dem Dropdown-Menü\n"
                "3. Nutze die Buttons um Items hinzuzufügen/zu entnehmen\n"
                "4. Der Bestand wird automatisch im Lagerbestand-Channel aktualisiert\n"
                "5. Alle Aktivitäten werden im Logs-Channel protokolliert\n\n"
                "Auf der Suche nach weiteren Discord Bots, oder hast Anregungen / Ideen, dann schau bei nuqqeT.de vorbei!"
            )
            await ctx.send(success_message)
        else:
            print("Kanäle existieren bereits")
            # Wenn Kanäle bereits existieren, sende UI nur wenn im richtigen Kanal
            if ctx.channel.id == channel_ids["lagerverwaltung"]:
                view = LagerView()
                await ctx.send("Lagerverwaltung:", view=view)
                print("UI im existierenden Lagerverwaltung-Channel gesendet")
            else:
                print("Befehl wurde im falschen Kanal ausgeführt")
                # Sende Hinweis in die Logs
                if channel_ids["lagerlogs"]:
                    logs_channel = ctx.guild.get_channel(channel_ids["lagerlogs"])
                    if logs_channel:
                        verwaltung_channel = ctx.guild.get_channel(channel_ids["lagerverwaltung"])
                        await logs_channel.send(f"`{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}` ℹ️ {ctx.author.global_name or ctx.author} wurde auf den Lagerverwaltung-Channel hingewiesen")
    except discord.Forbidden as e:
        print(f"Berechtigungsfehler: {str(e)}")
        if channel_ids["lagerlogs"]:
            logs_channel = ctx.guild.get_channel(channel_ids["lagerlogs"])
            if logs_channel:
                await logs_channel.send(f"`{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}` ❌ Fehler: Bot hat nicht die nötigen Berechtigungen - {str(e)}")
    except Exception as e:
        print(f"Allgemeiner Fehler: {str(e)}")
        if channel_ids["lagerlogs"]:
            logs_channel = ctx.guild.get_channel(channel_ids["lagerlogs"])
            if logs_channel:
                await logs_channel.send(f"`{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}` ❌ Fehler: {str(e)}")

@bot.command()
async def reset(ctx):
    """Setzt alle Lager zurück"""
    if os.path.exists(LAGER_FILE):
        os.remove(LAGER_FILE)
    save_lager(DEFAULT_LAGER)
    await send_log(ctx.guild, f"🔄 {ctx.author.global_name or ctx.author} hat alle Lager zurückgesetzt")
    await ctx.send("✅ Alle Lager wurden zurückgesetzt!")

# Bot starten
bot.run(TOKEN) 