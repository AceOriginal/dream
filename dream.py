import discord
from discord.ext import commands
from discord.ui import Select, View, Button
import asyncio
from datetime import datetime

# Ενεργοποίηση intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True  # Για events όπως join/leave
intents.voice_states = True  # Για voice channel events

bot = commands.Bot(command_prefix="-", intents=intents)

# IDs για τα κανάλια logs
LOG_DELETED_MESSAGES_CHANNEL_ID = 1338992994329694310  # Αντικαταστήστε με το ID για διαγραμμένα μηνύματα
LOG_EDITED_MESSAGES_CHANNEL_ID = 1338993782644805803  # Αντικαταστήστε με το ID για επεξεργασμένα μηνύματα
LOG_BAN_CHANNEL_ID = 1338993741150552145  # Αντικαταστήστε με το ID για bans
LOG_KICK_CHANNEL_ID = 1338993837497913599  # Αντικαταστήστε με το ID για kicks
LOG_VOICE_JOIN_CHANNEL_ID = 1338993895974895707  # Αντικαταστήστε με το ID για voice join
LOG_VOICE_LEFT_CHANNEL_ID = 1338993950899441726  # Αντικαταστήστε με το ID για voice left

# ID για την κατηγορία tickets
TICKET_CATEGORY_ID = 1327424548156604416  # Αντικαταστήστε με το ID της κατηγορίας για τα tickets

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="Dream Project"),
        status=discord.Status.dnd
    )
    print(f"Συνδέθηκε ως {bot.user}")

# Συνάρτηση για αποστολή logs σε συγκεκριμένο κανάλι
async def send_log(channel_id, embed):
    log_channel = bot.get_channel(channel_id)
    if log_channel:
        await log_channel.send(embed=embed)

# Συνάρτηση για δημιουργία embed χωρίς τίτλο
def create_embed(description, color, guild, user=None):
    embed = discord.Embed(
        description=description,  # Το description είναι το κύριο περιεχόμενο του embed
        color=color,
        timestamp=datetime.now()
    )
    # Footer με server icon, server name και ώρα
    embed.set_footer(text=f"{guild.name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", icon_url=guild.icon.url if guild.icon else None)
    
    # Thumbnail με user icon (αν υπάρχει χρήστης)
    if user:
        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
    
    # Author με server name και server icon
    embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
    
    return embed

# Logs για διαγραφή μηνυμάτων
@bot.event
async def on_message_delete(message):
    if message.author.bot:  # Αγνοούμε τα μηνύματα από bots
        return

    guild = message.guild

    # Αναζήτηση στο audit log για να βρούμε ποιος διέγραψε το μήνυμα
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
        deleter = entry.user  # Ο χρήστης που διέγραψε το μήνυμα
        reason = entry.reason  # Ο λόγος διαγραφής (αν υπάρχει)

    # Δημιουργία embed
    embed = create_embed(
        description=f"**Μήνυμα από τον χρήστη {message.author.mention} διαγράφηκε στο κανάλι {message.channel.mention}.**\n\n"
                    f"**Περιεχόμενο:**\n{message.content}\n\n"
                    f"**Διαγράφτηκε από:** {deleter.mention if deleter else 'Άγνωστο'}\n"
                    f"**Λόγος:** {reason if reason else 'Δεν υπάρχει λόγος'}",
        color=discord.Color.red(),
        guild=guild,
        user=message.author
    )

    await send_log(LOG_DELETED_MESSAGES_CHANNEL_ID, embed)

# Logs για επεξεργασία μηνυμάτων
@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content:  # Αγνοούμε bots και μηνύματα χωρίς αλλαγές
        return

    guild = before.guild
    embed = create_embed(
        description=f"**Μήνυμα από τον χρήστη {before.author.mention} επεξεργάστηκε στο κανάλι {before.channel.mention}.**\n\n**Πριν:**\n{before.content}\n\n**Μετά:**\n{after.content}",
        color=discord.Color.orange(),
        guild=guild,
        user=before.author
    )

    await send_log(LOG_EDITED_MESSAGES_CHANNEL_ID, embed)

# Logs για αποκλεισμό (ban)
@bot.event
async def on_member_ban(guild, user):
    # Αναζήτηση στα audit logs για τον λόγο του ban
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.target == user:
            reason = entry.reason  # Ο λόγος του ban
            banner = entry.user  # Ο χρήστης που έκανε το ban

    # Δημιουργία embed
    embed = create_embed(
        description=f"**Ο χρήστης {user.mention} αποκλείστηκε από τον server.**\n\n"
                    f"**Αποκλείστηκε από:** {banner.mention if banner else 'Άγνωστο'}\n"
                    f"**Λόγος:** {reason if reason else 'Δεν υπάρχει λόγος'}",
        color=discord.Color.dark_red(),
        guild=guild,
        user=user
    )

    await send_log(LOG_BAN_CHANNEL_ID, embed)

# Logs για απομάκρυνση (kick ή leave)
@bot.event
async def on_member_remove(member):
    guild = member.guild

    # Αναζήτηση στα audit logs για kick
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        if entry.target == member:
            # Αν βρεθεί kick, δημιουργία embed για kick
            kicker = entry.user  # Ο χρήστης που έκανε το kick
            reason = entry.reason  # Ο λόγος του kick (αν υπάρχει)

            embed = create_embed(
                description=f"**Ο χρήστης {member.mention} απομακρύνθηκε από τον server (Kick).**\n\n"
                            f"**Απομακρύνθηκε από:** {kicker.mention if kicker else 'Άγνωστο'}\n"
                            f"**Λόγος:** {reason if reason else 'Δεν υπάρχει λόγος'}",
                color=discord.Color.dark_orange(),
                guild=guild,
                user=member
            )

            await send_log(LOG_KICK_CHANNEL_ID, embed)
            return  # Τερματίζουμε τη συνάρτηση εδώ, αφού βρήκαμε kick

    # Αν δεν βρεθεί kick, ο χρήστης έφυγε μόνος του (leave)
    embed = create_embed(
        description=f"**Ο χρήστης {member.mention} άφησε τον server.**",
        color=discord.Color.dark_orange(),
        guild=guild,
        user=member
    )

    await send_log(LOG_KICK_CHANNEL_ID, embed)

# Logs για είσοδο σε φωνητικό κανάλι
@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    if before.channel is None and after.channel is not None:  # Είσοδος σε φωνητικό κανάλι
        embed = create_embed(
            description=f"**Ο χρήστης {member.mention} μπήκε στο φωνητικό κανάλι {after.channel.mention}.**",
            color=discord.Color.green(),
            guild=guild,
            user=member
        )

        await send_log(LOG_VOICE_JOIN_CHANNEL_ID, embed)

    elif before.channel is not None and after.channel is None:  # Αποχώρηση από φωνητικό κανάλι
        embed = create_embed(
            description=f"**Ο χρήστης {member.mention} αποχώρησε από το φωνητικό κανάλι {before.channel.mention}.**",
            color=discord.Color.red(),
            guild=guild,
            user=member
        )

        await send_log(LOG_VOICE_LEFT_CHANNEL_ID, embed)

# Ticket Command
@bot.command()
@commands.has_permissions(administrator=True)
async def ticket(ctx):
    guild = ctx.guild
    server_icon = guild.icon.url if guild.icon else None

    embed = discord.Embed(
        title=guild.name,
        description="**Επιλέξτε το είδος του ticket που θέλετε να ανοίξετε και κάποιος από την ομάδα εξυπηρέτησης θα σας εξυπηρετήσει το συντομότερο δυνατόν.**",
        color=discord.Color.red()
    )
    embed.set_author(name=guild.name, icon_url=server_icon)
    embed.set_thumbnail(url=server_icon)
    embed.set_footer(text=f"{guild.name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", icon_url=server_icon)

    options = [
        discord.SelectOption(label="💸 Buy", description="Άνοιγμα ticket για αγορά", emoji="💸"),
        discord.SelectOption(label="👑 Contact With Owner", description="Επικοινωνία με τον ιδιοκτήτη", emoji="👑"),
        discord.SelectOption(label="❓ Question", description="Υποβολή ερώτησης", emoji="❓"),
    ]

    dropdown = Select(placeholder="Παρακαλώ Επιλέξτε...", options=options)

    async def dropdown_callback(interaction):
        selected_option = dropdown.values[0]
        await create_ticket(interaction, selected_option, ctx)

    dropdown.callback = dropdown_callback

    view = View()
    view.add_item(dropdown)

    await ctx.send(embed=embed, view=view)

async def create_ticket(interaction, option, ctx):
    guild = interaction.guild
    category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)

    if not category:
        await interaction.response.send_message("**Η κατηγορία για τα tickets δεν υπάρχει. Επικοινωνήστε με τον διαχειριστή.**", ephemeral=True)
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }

    ticket_channel = await guild.create_text_channel(
        name=f"{option}-{interaction.user.name}",
        overwrites=overwrites,
        category=category
    )

    embed = discord.Embed(
        title=guild.name,
        description=f"**Καλησπέρα {interaction.user.mention}, πες μας τι χρειάζεσαι και θα σε εξυπηρετήσουμε άμεσα!**",
        color=discord.Color.red()
    )
    server_icon = guild.icon.url if guild.icon else None
    embed.set_author(name=guild.name, icon_url=server_icon)
    embed.set_thumbnail(url=server_icon)
    embed.set_footer(text=f"{guild.name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", icon_url=server_icon)

    view = View()
    await ticket_channel.send(embed=embed, view=view)

# Restock Command
@bot.command()
@commands.has_permissions(administrator=True)
async def restock(ctx, role: discord.Role, *, message: str):
    guild = ctx.guild
    server_icon = guild.icon.url if guild.icon else None

    embed = discord.Embed(title=guild.name, description=message, color=discord.Color.green())
    embed.set_author(name=guild.name, icon_url=server_icon)
    embed.set_thumbnail(url=server_icon)
    embed.set_footer(text=f"{guild.name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", icon_url=server_icon)

    button = Button(label="📦", style=discord.ButtonStyle.gray)

    async def button_callback(interaction):
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"**Πήρες τον ρόλο {role.mention}!**", ephemeral=True)
        else:
            await interaction.response.send_message("**Ήδη έχεις αυτόν τον ρόλο!**", ephemeral=True)

    button.callback = button_callback
    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)

# Say Command
@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, *, message: str):
    guild = ctx.guild
    server_icon = guild.icon.url if guild.icon else None

    embed = discord.Embed(title=guild.name, description=message, color=discord.Color.red())
    embed.set_author(name=guild.name, icon_url=server_icon)
    embed.set_thumbnail(url=server_icon)
    embed.set_footer(text=f"{guild.name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", icon_url=server_icon)

    await ctx.send(embed=embed)
    await ctx.message.delete()

# Status Command
@bot.command()
@commands.has_permissions(administrator=True)
async def status(ctx, *, new_status: str):
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=new_status)
    )

    guild = ctx.guild
    server_icon = guild.icon.url if guild.icon else None

    embed = discord.Embed(title=guild.name, description=f"**Το status του bot άλλαξε σε:** `{new_status}`", color=discord.Color.blue())
    embed.set_author(name=guild.name, icon_url=server_icon)
    embed.set_thumbnail(url=server_icon)
    embed.set_footer(text=f"{guild.name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", icon_url=server_icon)

    await ctx.send(embed=embed)

# Clear Command
@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int):
    if amount <= 0:
        await ctx.send("Παρακαλώ εισάγετε έναν αριθμό μεγαλύτερο από 0.")
        return

    deleted = await ctx.channel.purge(limit=amount)

    guild = ctx.guild
    server_icon = guild.icon.url if guild.icon else None

    embed = discord.Embed(title=guild.name, description=f"**Διαγράφηκαν {len(deleted)} μηνύματα.**", color=discord.Color.red())
    embed.set_author(name=guild.name, icon_url=server_icon)
    embed.set_thumbnail(url=server_icon)
    embed.set_footer(text=f"{guild.name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", icon_url=server_icon)

    await ctx.send(embed=embed, delete_after=5)

# Error Handling
@bot.event
async def on_command_error(ctx, error):
    guild = ctx.guild
    server_icon = guild.icon.url if guild.icon else None

    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title=guild.name, description="🚫 **Δεν έχεις άδεια να εκτελέσεις αυτήν την εντολή!**", color=discord.Color.red())
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title=guild.name, description="⚠ **Λάθος χρήση της εντολής! Δοκίμασε ξανά.**", color=discord.Color.red())
    elif isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(title=guild.name, description="❌ **Η εντολή δεν βρέθηκε!**", color=discord.Color.red())
    else:
        embed = discord.Embed(title=guild.name, description=f"⚠ **Σφάλμα:** `{str(error)}`", color=discord.Color.red())

    embed.set_author(name=guild.name, icon_url=server_icon)
    embed.set_thumbnail(url=server_icon)
    embed.set_footer(text=f"{guild.name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", icon_url=server_icon)

    await ctx.send(embed=embed)

# Βάλε το token σου εδώ
bot.run("MTM0NzY2NzM1OTU5NDE4ODgxMA.Gz5PcZ.ocbVjChgFqDV02yJ7TERtavLziWkNsaY-Co0gI")  # Αντικαταστήστε με το token του bot σας