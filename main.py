import discord
from discord.ext import commands
import os
import time
import io

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

WELCOME_URL = "https://cdn.discordapp.com/attachments/1569635326928879656/1569635550007140473/97b3c2a7-b1e8-66b1-50e5-563dc75098ea.webp?ex=6af42c85&is=6af2db05&hm=85bd6398b000eed593df57c71ab8212d8b89cb81bf242eea708512e56fbd76e9&"
QRIS_URL = "https://cdn.discordapp.com/attachments/1569635326928879656/1569635930090897448/IMG_5210.jpg?ex=6af42ce0&is=6af2db60&hm=26d9c6a1ea6c6eb5cbfcf6bf3cbab686bd8c7fd862b8cbb97af970b690e65764&"

ticket_data = {}
ticket_counter = 0

def get_status_channel(guild):
    for ch in guild.text_channels:
        if ch.name == "order-status":
            return ch
    return None

def get_ticket_category(guild):
    # Kunci ke kategori pian: ── ── ── 🎫 ✦ TICKET ✦ ── ── ──
    for cat in guild.categories:
        if "TICKET" in cat.name.upper():
            return cat
    return None

async def send_status_update(guild, number, username, user_id, paket, status_text, color):
    ch = get_status_channel(guild)
    if not ch: return
    embed = discord.Embed(title=f"📦 Order Status - Ticket #{number}", description=f"**Customer:** <@{user_id}> ({username})\n**Paket:** {paket}\n**Status:** {status_text}", color=color)
    embed.set_footer(text="MIPI STORE • Order Status")
    await ch.send(embed=embed)

class RatingView(discord.ui.View):
    def __init__(self, ticket_number):
        super().__init__(timeout=None); self.ticket_number = ticket_number
    async def send_thanks(self, interaction, stars):
        embed = discord.Embed(title="Terima Kasih! 💗", description=f"Kamu memberi rating **{stars} ⭐** untuk MIPI STORE!\n\nTerima kasih sudah order di Mipi Store! Ditunggu order berikutnya ya 🌸", color=0xff69b4)
        await interaction.response.edit_message(embed=embed, view=None)
    @discord.ui.button(label="⭐ 1", style=discord.ButtonStyle.secondary, custom_id="rate1")
    async def r1(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_thanks(interaction, 1)
    @discord.ui.button(label="⭐ 2", style=discord.ButtonStyle.secondary, custom_id="rate2")
    async def r2(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_thanks(interaction, 2)
    @discord.ui.button(label="⭐ 3", style=discord.ButtonStyle.primary, custom_id="rate3")
    async def r3(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_thanks(interaction, 3)
    @discord.ui.button(label="⭐ 4", style=discord.ButtonStyle.success, custom_id="rate4")
    async def r4(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_thanks(interaction, 4)
    @discord.ui.button(label="⭐ 5", style=discord.ButtonStyle.success, custom_id="rate5")
    async def r5(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_thanks(interaction, 5)
    @discord.ui.button(label="📝 Add Comment", style=discord.ButtonStyle.secondary, custom_id="add_comment", row=1)
    async def comment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(ticket_number=self.ticket_number))
    @discord.ui.button(label="❌ No Thanks", style=discord.ButtonStyle.secondary, custom_id="no_thanks", row=1)
    async def no_thanks(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Oke! Terima kasih sudah order di MIPI STORE 💗", embed=None, view=None)

class CommentModal(discord.ui.Modal, title="Komentar / Testimoni"):
    def __init__(self, ticket_number):
        super().__init__(); self.ticket_number = ticket_number
    komentar = discord.ui.TextInput(label="Komentar kamu", placeholder="Pelayanannya cepat banget, recommended!", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Terima kasih komentarnya! 💗\n> {self.komentar.value}\n\nKomentar kamu untuk Ticket #{self.ticket_number} sudah tersimpan!", ephemeral=True)

class StatusView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    async def check_owner(self, interaction):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Hanya **Owner** yang bisa update status!", ephemeral=True); return False
        return True
    @discord.ui.button(label="⏳ Menunggu Pembayaran", style=discord.ButtonStyle.secondary, custom_id="status_waiting")
    async def waiting(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        data = ticket_data.get(interaction.channel.id, {})
        await interaction.response.send_message("⏳ Status diubah: **Menunggu Pembayaran**", ephemeral=False)
        await send_status_update(interaction.guild, data.get("number", "?"), data.get("username", interaction.user.name), data.get("user_id", interaction.user.id), data.get("paket", "ORDER ROBUX"), "⏳ Menunggu Pembayaran", 0xfee75c)
    @discord.ui.button(label="🔄 Diproses", style=discord.ButtonStyle.primary, custom_id="status_process")
    async def process(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        data = ticket_data.get(interaction.channel.id, {})
        await interaction.response.send_message("🔄 Status diubah: **Sedang Diproses**", ephemeral=False)
        await send_status_update(interaction.guild, data.get("number", "?"), data.get("username", interaction.user.name), data.get("user_id", interaction.user.id), data.get("paket", "ORDER ROBUX"), "🔄 Sedang Diproses", 0x5865f2)
    @discord.ui.button(label="✅ Selesai", style=discord.ButtonStyle.success, custom_id="status_done")
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        data = ticket_data.get(interaction.channel.id, {})
        await interaction.response.send_message("✅ Status diubah: **Selesai** - Robux sudah masuk!", ephemeral=False)
        await send_status_update(interaction.guild, data.get("number", "?"), data.get("username", interaction.user.name), data.get("user_id", interaction.user.id), data.get("paket", "ORDER ROBUX"), "✅ Selesai / Done", 0x57f287)

class CloseView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔒 CLOSE TICKET", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Hanya **Owner** yang bisa menutup ticket ini!", ephemeral=True); return
        channel = interaction.channel; data = ticket_data.get(channel.id)
        if not data: await channel.delete(); return
        user_id = data["user_id"]; created = data["created_at"]; number = data["number"]; paket = data.get("paket", "ORDER ROBUX")
        resolved_min = int((time.time() - created) // 60)
        if resolved_min < 1: resolved_min = 1
        await interaction.response.send_message(f"Ticket ditutup oleh {interaction.user.mention}. Membuat transcript...")
        try:
            messages = []
            async for m in channel.history(limit=200, oldest_first=True):
                messages.append(f"[{m.created_at.strftime('%H:%M')}] {m.author}: {m.content}")
            transcript_text = "\n".join(messages) if messages else "Tidak ada pesan"
            file = discord.File(io.BytesIO(transcript_text.encode()), filename=f"ticket-{number}-transcript.txt")
            status_ch = get_status_channel(interaction.guild)
            if status_ch:
                embed = discord.Embed(title="Auto-Generated Transcript (Auto-Closed)", description=f"Transcript automatically generated for auto-closed ticket #{number}\n\n**Ticket**\nTicket #{number}\nCreated by <@{user_id}>\n{len(messages)} messages\n\n**Generation**\nDuration: {resolved_min} minutes\nStatus: Closed -> Transcript\n\n**Subject**\n{paket}", color=0x2b2d31)
                await status_ch.send(embed=embed, file=file)
        except Exception as e: print(f"Gagal transcript: {e}")
        try:
            user = await bot.fetch_user(user_id)
            embed = discord.Embed(title="Rate Your Experience", description=f"Hi {user.name}! Your support ticket has been resolved.\nPlease rate your experience by clicking a star below.\n\n**Ticket #{number} in 🛒 ORDER ROBUX**\n**Resolved in**\n{resolved_min} minutes\n\n**Closed by**\n{interaction.user.name}", color=0x2b2d31)
            await user.send(embed=embed, view=RatingView(number))
        except Exception as e: print(f"Gagal DM: {e}")
        import asyncio; await asyncio.sleep(3); await channel.delete()

class OrderModal(discord.ui.Modal, title="Pesanan Robux"):
    username = discord.ui.TextInput(label="Username", placeholder="UsernameRoblox", required=True)
    paket = discord.ui.TextInput(label="Paket yang dipilih", placeholder="Contoh: 500 Robux", required=True)
    pembayaran = discord.ui.TextInput(label="Metode Pembayaran", placeholder="QRIS", default="QRIS", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        global ticket_counter
        ticket_counter += 1
        guild = interaction.guild
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        # === MASUK KE KATEGORI ── ── ── 🎫 ✦ TICKET ✦ ── ── ── ===
        category = get_ticket_category(guild)
        channel = await guild.create_text_channel(name=f"ticket-{interaction.user.name}", overwrites=overwrites, category=category)
        ticket_data[channel.id] = {"user_id": interaction.user.id, "username": interaction.user.name, "created_at": time.time(), "number": ticket_counter, "paket": self.paket.value}
        embed = discord.Embed(title=f"🎫 Ticket Baru - {interaction.user.name}", description=f"**Username Roblox:** {self.username.value}\n**Paket:** {self.paket.value}\n**Pembayaran:** {self.pembayaran.value}\n**Ticket #{ticket_counter}**\n\nSilahkan kirim bukti pembayaran QRIS disini ya 💗", color=0xff69b4)
        embed.set_image(url=QRIS_URL)
        await channel.send(f"{interaction.user.mention} Halo! Selamat datang di MIPI STORE! 🌸", embed=embed, view=CloseView())
        await channel.send("**📦 STATUS ORDER - Owner only:**", view=StatusView())
        await send_status_update(guild, ticket_counter, interaction.user.name, interaction.user.id, self.paket.value, "🆕 Ticket Baru Dibuat", 0xff69b4)
        go_view = discord.ui.View()
        go_view.add_item(discord.ui.Button(label="🚀 BUKA TICKET SAYA", style=discord.ButtonStyle.link, url=f"https://discord.com/channels/{guild.id}/{channel.id}"))
        await interaction.response.send_message(f"✅ Ticket kamu sudah dibuat!\nPencet tombol dibawah untuk langsung masuk ke ticket kamu 👇\n👉 {channel.mention}", view=go_view, ephemeral=True)
        try:
            await interaction.user.send(f"✅ Ticket MIPI STORE kamu sudah dibuat!\nLangsung klik disini ya: 👉 {channel.mention}\nLink: https://discord.com/channels/{guild.id}/{channel.id}\n\nKirim bukti QRIS kamu disana ya 💗")
        except: pass

class OrderView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="ORDER ROBUX", style=discord.ButtonStyle.primary, custom_id="order_robux")
    async def order_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OrderModal())

@bot.event
async def on_ready():
    print(f"Login {bot.user}"); await bot.tree.sync()

@bot.tree.command(name="ticket", description="Tampilkan panel order MIPI STORE")
async def ticket(interaction: discord.Interaction):
    embed1 = discord.Embed(title="Mipi Store - Order Robux 💗", description="🌸 **ROBUX VIA USERNAME**\nFast Process • Aman • Instan\n\nSyarat top up via username:\n>> SUDAH 18+\n>> SUDAH TERVERIFIKASI 2 LANGKAH", color=0xff69b4)
    embed1.set_image(url=WELCOME_URL)
    embed2 = discord.Embed(title="💰 PRICELIST ROBUX FAST SEND", description="500 = Rp 78.000\n1000 = Rp 155.000\n2000 = Rp 310.000\n3000 = Rp 465.000\n4000 = Rp 620.000\n5000 = Rp 775.000\n\n🌸 **Robux Eceran**\n100 = Rp 16.500\n200 = Rp 33.000\n300 = Rp 49.500\n400 = Rp 66.000\n\n🛒 **Cara Order**\nClick tombol ORDER ROBUX dibawah, isi formulir, lalu tunggu admin. Pembayaran **hanya QRIS**.", color=0xff69b4)
    embed2.set_image(url=QRIS_URL)
    embed2.set_footer(text="Mipi Store • Rafi Store")
    await interaction.response.send_message(embed=embed1)
    await interaction.followup.send(embed=embed2, view=OrderView())

@bot.tree.command(name="ping", description="Cek bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! 🏓 MIPI STORE online Wal! {round(bot.latency*1000)}ms")

bot.run(os.getenv("DISCORD_TOKEN"))
