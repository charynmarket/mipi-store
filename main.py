import discord
from discord.ext import commands
from discord import app_commands
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Buat Ticket Buat Order", style=discord.ButtonStyle.green, custom_id="buat_ticket_mipi")
    async def buat_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="🎫 TICKET")
        if not category:
            category = await guild.create_category("🎫 TICKET")
        
        # Cek kalau sudah punya ticket
        for ch in guild.text_channels:
            if ch.name == f"ticket-{interaction.user.name.lower()}":
                await interaction.response.send_message(f"Kamu sudah punya ticket! 👉 {ch.mention}", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)
        await channel.send(f"Halo {interaction.user.mention} 💗 Selamat datang di **MIPI STORE**!\n\n🌸 **Jual Robux Fast & Aman**\nSilahkan tulis mau order Robux berapa ya?\nOwner: Rafi & miraaaa akan segera melayani 💗")
        await interaction.response.send_message(f"Ticket kamu sudah dibuat! 👉 {channel.mention}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(TicketView())
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.tree.command(name="ticket", description="Kirim tombol ticket jualan MIPI STORE")
async def ticket(interaction: discord.Interaction):
    embed = discord.Embed(title="🎫 MIPI STORE - Jual Robux Fast & Aman 💗", description="Mau order Robux?\n\nPencet tombol di bawah ini!\nNanti dibuatkan room khusus buat kamu, cuma kamu sama admin yang bisa lihat.\n\nOwner: Rafi & miraaaa", color=0xFF69B4)
    embed.set_thumbnail(url="https://i.imgur.com/placeholder.png")
    await interaction.response.send_message(embed=embed, view=TicketView())

@bot.tree.command(name="close", description="Tutup ticket ini")
async def close(interaction: discord.Interaction):
    if "ticket-" in interaction.channel.name:
        await interaction.response.send_message("Ticket ditutup dalam 3 detik... Terimakasih sudah order di MIPI STORE 💗")
        await asyncio.sleep(3)
        await interaction.channel.delete()
    else:
        await interaction.response.send_message("Ini bukan channel ticket Wal!", ephemeral=True)

@bot.tree.command(name="ping", description="Cek bot MIPI online atau tidak")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! 🏓 MIPI STORE online Wal! {round(bot.latency*1000)}ms")

# GANTI INI DENGAN TOKEN MIPI STORE PIAN YANG 1 ITU
bot.run(“MTU2OTU3MjE3NTExMzg3OTY3NA.GU3VM8.CEvKaxhqM__Z1FYmtfYUgEzg6oRKNIktteWt-g”)
