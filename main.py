import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- LINK PIAN UDAH DIISI ---
WELCOME_URL = "https://cdn.discordapp.com/attachments/1569635326928879656/1569635550007140473/97b3c2a7-b1e8-66b1-50e5-563dc75098ea.webp?ex=6af42c85&is=6af2db05&hm=85bd6398b000eed593df57c71ab8212d8b89cb81bf242eea708512e56fbd76e9&"
QRIS_URL = "https://cdn.discordapp.com/attachments/1569635326928879656/1569635930090897448/IMG_5210.jpg?ex=6af42ce0&is=6af2db60&hm=26d9c6a1ea6c6eb5cbfcf6bf3cbab686bd8c7fd862b8cbb97af970b690e65764&"
# ----------------------------

class OrderModal(discord.ui.Modal, title="Pesanan Robux"):
    username = discord.ui.TextInput(label="Username", placeholder="UsernameRoblox", required=True)
    paket = discord.ui.TextInput(label="Paket yang dipilih", placeholder="Contoh: 500 Robux", required=True)
    pembayaran = discord.ui.TextInput(label="Metode Pembayaran", placeholder="QRIS", default="QRIS", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=f"ticket-{interaction.user.name}", overwrites=overwrites)
        embed = discord.Embed(title=f"🎫 Ticket Baru - {interaction.user.name}", description=f"**Username Roblox:** {self.username.value}\n**Paket:** {self.paket.value}\n**Pembayaran:** {self.pembayaran.value}\n\nSilahkan kirim bukti pembayaran QRIS disini ya 💗", color=0xff69b4)
        embed.set_image(url=QRIS_URL)
        await channel.send(f"{interaction.user.mention} Halo! Selamat datang di MIPI STORE! 🌸", embed=embed)
        await interaction.response.send_message(f"Ticket kamu sudah dibuat! 👉 {channel.mention}", ephemeral=True)

class OrderView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="ORDER ROBUX", style=discord.ButtonStyle.primary, custom_id="order_robux")
    async def order_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OrderModal())

@bot.event
async def on_ready():
    print(f"Login {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="ticket", description="Tampilkan panel order MIPI STORE")
async def ticket(interaction: discord.Interaction):
    embed1 = discord.Embed(
        title="Mipi Store - Order Robux 💗",
        description="🌸 **ROBUX VIA USERNAME**\nFast Process • Aman • Instan\n\nSyarat top up via username:\n>> SUDAH 18+\n>> SUDAH TERVERIFIKASI 2 LANGKAH",
        color=0xff69b4
    )
    embed1.set_image(url=WELCOME_URL)

    embed2 = discord.Embed(
        title="💰 PRICELIST ROBUX FAST SEND",
        description=(
            "500 = Rp 78.000\n"
            "1000 = Rp 155.000\n"
            "2000 = Rp 310.000\n"
            "3000 = Rp 465.000\n"
            "4000 = Rp 620.000\n"
            "5000 = Rp 775.000\n\n"
            "🌸 **Robux Eceran**\n"
            "100 = Rp 16.500\n"
            "200 = Rp 33.000\n"
            "300 = Rp 49.500\n"
            "400 = Rp 66.000\n\n"
            "🛒 **Cara Order**\n"
            "Click tombol ORDER ROBUX dibawah, isi formulir, lalu tunggu admin. Pembayaran **hanya QRIS**."
        ),
        color=0xff69b4
    )
    embed2.set_image(url=QRIS_URL)
    embed2.set_footer(text="Mipi Store • Rafi Store • Robux diproses manual oleh admin")

    await interaction.response.send_message(embed=embed1)
    await interaction.followup.send(embed=embed2, view=OrderView())

@bot.tree.command(name="ping", description="Cek bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! 🏓 MIPI STORE online Wal! {round(bot.latency*1000)}ms")

bot.run(os.getenv("DISCORD_TOKEN"))
