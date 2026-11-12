import discord
from discord.ext import commands, tasks
import os
import time
import io
import html
import re
import asyncio
import json
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

WELCOME_URL = "https://raw.githubusercontent.com/mipistore/mipi-store/main/97b3c2a7-b1e8-66b1-50e5-563dc75098ea.jpeg"
THANKYOU_URL = "https://raw.githubusercontent.com/mipistore/mipi-store/main/IMG_6021.jpeg"
QRIS_URL = "https://raw.githubusercontent.com/mipistore/mipi-store/main/IMG_5210.jpeg"

ticket_data = {}
ticket_counter = 0
user_ratings = {}
user_last_ticket = {}

PRICELIST = {100: 16500, 200: 33000, 300: 49500, 400: 66000, 500: 78000, 1000: 155000, 2000: 310000, 3000: 465000, 4000: 620000, 5000: 775000}

# === LEADERBOARD - TOP BUYER ===
LEADERBOARD_FILE = "leaderboard.json"

def load_leaderboard():
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_leaderboard(data):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_to_leaderboard(user_id, username, paket_text):
    m = re.search(r'(\d+)', str(paket_text).replace('.', '').replace(',', ''))
    if not m: return
    jumlah = int(m.group(1))
    data = load_leaderboard()
    bulan = datetime.now().strftime("%Y-%m")
    if bulan not in data:
        data[bulan] = {}
    uid = str(user_id)
    if uid not in data[bulan]:
        data[bulan][uid] = {"username": username, "total": 0, "transaksi": 0}
    data[bulan][uid]["username"] = username
    data[bulan][uid]["total"] += jumlah
    data[bulan][uid]["transaksi"] += 1
    save_leaderboard(data)

# === PILIHAN A - BOLEH JUAL AKUN PRIBADI, DILARANG JUAL ROBUX / LIMITED ===
BANNED_WORDS = ["wts robux", "jual robux", "sell robux", "jual rb", "wts rb", "jual limited", "wts limited", "sell limited", "jual robux murah", "robux murah", "top up robux", "jual akun robux", "wts akun robux", "wtt robux", "wtb robux", "jual robux via", "robux via username murah"]
ALLOWED_IF_HAS = ["akun pribadi", "akun roblox", "akun pribadi secepatnya"]

def is_banned_selling(text):
    low = text.lower()
    if any(a in low for a in ALLOWED_IF_HAS) and "robux" not in low and "limited" not in low:
        return False
    return any(w in low for w in BANNED_WORDS)

def hitung_harga(paket_text):
    m = re.search(r'(\d+)', str(paket_text).replace('.', '').replace(',', ''))
    if not m: return "500", "Rp 78.000"
    jumlah = int(m.group(1))
    harga = PRICELIST.get(jumlah, jumlah * 156)
    return str(jumlah), f"Rp {harga:,}".replace(",", ".")

def get_status_channel(guild):
    for ch in guild.text_channels:
        if ch.name == "📦┆・order-status": return ch
    for ch in guild.text_channels:
        if "order-status" in ch.name.lower(): return ch
    return None

def get_history_channel(guild):
    for ch in guild.text_channels:
        if ch.name == "🗂️・history-order": return ch
    for ch in guild.text_channels:
        if "history-order" in ch.name.lower(): return ch
    for ch in guild.text_channels:
        if "history" in ch.name.lower(): return ch
    return None

def get_ticket_category(guild):
    for cat in guild.categories:
        if "TICKET" in cat.name.upper(): return cat
    return None

def get_vouch_channel(guild):
    for ch in guild.channels:
        if "vouch" in ch.name.lower(): return ch
    return None

def make_html_transcript(number, messages, username, paket, duration):
    rows = ""
    for m in messages:
        rows += f"""<div style="margin:6px 0;padding:8px;background:#2b2d31;border-radius:8px;"><b style="color:#fff;">{html.escape(str(m['author']))}</b> <span style="color:#949ba4;font-size:12px;">{m['time']}</span><br><span style="color:#dbdee1;">{html.escape(m['content'] or '(gambar / embed)')}</span></div>"""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Ticket #{number} Transcript - MIPI STORE</title></head><body style="background:#1e1f22;font-family:sans-serif;padding:20px;"><h2 style="color:white;">MIPI STORE - Ticket #{number}</h2><p style="color:#949ba4;">Created by {html.escape(username)} | Subject: {html.escape(paket)} | Duration: {duration} minutes | {len(messages)} messages</p>{rows}<p style="color:#949ba4;margin-top:20px;">MIPI STORE • Auto-Generated Transcript</p></body></html>"""

async def send_status_update(guild, number, username, user_id, paket, status_text, color):
    ch = get_status_channel(guild)
    if not ch: return
    embed = discord.Embed(title=f"📦 Order Status - Ticket #{number}", description=f"**Customer:** <@{user_id}> ({username})\n**Paket:** {paket}\n**Status:** {status_text}", color=color)
    embed.set_footer(text="MIPI STORE • Order Status")
    await ch.send(embed=embed)

async def send_history_log(guild, channel, data, admin_user):
    ch = get_history_channel(guild)
    if not ch: return
    number = data["number"]; user_id = data["user_id"]
    roblox_user = data.get("roblox_username", data.get("username", "-"))
    paket = data.get("paket", "500 Robux")
    pembayaran = data.get("pembayaran", "Qrs")
    jumlah, harga = hitung_harga(paket)
    ticket_name = channel.name if channel else f"robux-via-username-{number}-{data.get('username','user')}"
    embed = discord.Embed(color=0x2b2d31)
    embed.description = f"🔒 Ticket Log\n\n🎫 Ticket\n{ticket_name}\n🔒 Action\nClosed\n⚡ Panel\nRobux Via Username\n🎀 Member\n<@{user_id}>\n👤 Username Roblox\n{roblox_user}\n✨ Jumlah Robux\n{jumlah}\n💰 Total Harga\n{harga}\n💳 Payment\n{pembayaran}\n✅ Admin\n{admin_user.mention if admin_user else 'Auto-Close'}"
    embed.set_image(url=THANKYOU_URL)
    await ch.send(embed=embed)

async def send_vouch(guild, user, paket, stars, komentar, ticket_number=0, ticket_name=""):
    ch = get_vouch_channel(guild)
    if not ch: return
    jumlah, harga = hitung_harga(paket)
    star_str = "⭐" * stars
    seller = guild.owner.mention if guild.owner else "MIPI STORE"
    if not ticket_name:
        ticket_name = f"robux-via-username-{ticket_number}-{user.name}"
    embed = discord.Embed(color=0x2b2d31)
    embed.description = f"✅ VOUCH RECEIVED ✅\n\n**Ticket ID**\n{ticket_number}\n**Nominal**\n{harga}\n**Seller**\n{seller}\n**Buyer**\n<@{user.id}>\n**Handled by**\n{seller}\n**Rating**\n{star_str}\n**Komentar**\n{komentar} 💗\n**Source**\n{ticket_name}"
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=f"MIPI STORE Vouch System | {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    msg = await ch.send(embed=embed)
    try:
        thread_name = f"Vouch - {user.name} | Ticket #{ticket_number}"
        if isinstance(ch, discord.ForumChannel):
            await ch.create_thread(name=thread_name, content=f"Vouch dari {user.mention} - Ticket #{ticket_number} - {paket} - {star_str} - {komentar}")
        else:
            thread = await msg.create_thread(name=thread_name, auto_archive_duration=1440)
            await thread.send(f"💗 **Vouch dari {user.mention}**\n\n📦 **Paket:** {paket} ({harga})\n⭐ **Rating:** {star_str}\n💬 **Komentar:** {komentar}\n🎫 **Ticket:** {ticket_name}\n\nTerima kasih sudah order di MIPI STORE! 🌸")
    except Exception as e:
        print(f"Gagal buat thread vouch: {e}")

async def do_auto_close(guild, channel, data, reason="auto-closed due to inactivity • inactive for 15 minutes", admin_user=None):
    number = data["number"]; user_id = data["user_id"]; paket = data.get("paket", "ORDER ROBUX")
    created = data["created_at"]; duration = int((time.time() - created)//60)
    if duration < 1: duration = 1
    user_last_ticket[user_id] = {"number": number, "paket": paket, "ticket_name": channel.name if channel else "", "seller_id": guild.owner_id}
    try: await send_history_log(guild, channel, data, admin_user)
    except Exception as e: print(f"Gagal history: {e}")
    messages = []
    try:
        async for m in channel.history(limit=200, oldest_first=True):
            messages.append({"author": str(m.author), "time": m.created_at.strftime("%H:%M"), "content": m.content})
    except: pass
    status_ch = get_status_channel(guild)
    if status_ch:
        embed1 = discord.Embed(title="Ticket Auto-Closed", description=f"**#{number} {reason}**\n**Ticket ID**\n{number}", color=0xfee75c)
        embed1.set_footer(text=datetime.now().strftime("%B %d, %Y at %I:%M %p"))
        await status_ch.send(embed=embed1)
        html_text = make_html_transcript(number, messages, data.get("username","User"), paket, duration)
        file = discord.File(io.BytesIO(html_text.encode()), filename=f"ticket-{number}-auto-transcript.html")
        embed2 = discord.Embed(title="Auto-Generated Transcript (Auto-Closed)", description=f"Transcript automatically generated for auto-closed ticket #{number}\n\n**Ticket**\nTicket #{number}\nCreated by <@{user_id}>\n{len(messages)} messages\n\n**Generation**\nDuration: {duration} minutes\nStatus: Auto-Closed -> Auto-Transcript\n\n**Subject**\n{paket}", color=0x5865f2)
        embed2.set_footer(text=datetime.now().strftime("%B %d, %Y at %I:%M %p"))
        await status_ch.send(embed=embed2, file=file)
    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(title="Rate Your Experience", description=f"Hi {user.name}! Your support ticket has been resolved.\nPlease rate your experience by clicking a star below.\n\n**Ticket #{number} in 🛒 ORDER ROBUX**\n**Resolved in**\n{duration} minutes\n\n**Closed by**\n{admin_user.name if admin_user else 'MIPI STORE (Auto-Close)'}", color=0x2b2d31)
        await user.send(embed=embed, view=RatingView(number))
    except: pass
    # Catat ke leaderboard pas ticket ditutup
    try:
        add_to_leaderboard(user_id, data.get("username", "User"), paket)
    except Exception as e:
        print(f"Gagal leaderboard: {e}")
    if channel.id in ticket_data: del ticket_data[channel.id]
    try: await channel.delete()
    except: pass

@tasks.loop(minutes=1)
async def check_inactive():
    now = time.time()
    for channel_id, data in list(ticket_data.items()):
        last = data.get("last_activity", data["created_at"])
        if now - last > 15*60:
            ch = bot.get_channel(channel_id)
            if not ch: del ticket_data[channel_id]; continue
            await do_auto_close(ch.guild, ch, data)

class RatingView(discord.ui.View):
    def __init__(self, ticket_number):
        super().__init__(timeout=None); self.ticket_number = ticket_number
    async def send_thanks(self, interaction, stars):
        user_ratings[interaction.user.id] = stars
        star_str = "⭐" * stars
        embed = discord.Embed(title="Terima Kasih! 💗", description=f"Kamu memberi rating **{star_str} ({stars}/5)** untuk MIPI STORE!\n\nTerima kasih sudah order di Mipi Store! Ditunggu order berikutnya ya 🌸\n\n👇 **Pencet Add Comment dibawah biar vouch kamu muncul di #⭐┆・vouch + jadi thread kayak 404 STORE!**", color=0xff69b4)
        embed.set_image(url=THANKYOU_URL)
        await interaction.response.edit_message(embed=embed, view=self)
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
    komentar = discord.ui.TextInput(label="Komentar kamu", placeholder="satset poll", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        stars = user_ratings.get(interaction.user.id, 5)
        last = user_last_ticket.get(interaction.user.id, {})
        paket = last.get("paket", "500 Robux")
        ticket_name = last.get("ticket_name", f"robux-via-username-{self.ticket_number}-{interaction.user.name}")
        try:
            guild = None
            for g in bot.guilds:
                ch = get_vouch_channel(g)
                if ch: guild = g; break
            if guild: await send_vouch(guild, interaction.user, paket, stars, self.komentar.value, ticket_number=self.ticket_number, ticket_name=ticket_name)
        except Exception as e: print(f"Gagal vouch: {e}")
        await interaction.response.send_message(f"Terima kasih komentarnya! 💗\n> {self.komentar.value}\n\nVouch kamu sudah muncul di **#⭐┆・vouch** + jadi thread! 🎉\nRating: {'⭐'*stars} ({stars}/5)", ephemeral=True)

class StatusView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⏳ Menunggu Pembayaran", style=discord.ButtonStyle.secondary, custom_id="status_waiting")
    async def waiting(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("❌ Hanya **Owner** yang bisa update status!", ephemeral=True); return
        data = ticket_data.get(interaction.channel.id, {})
        if data: data["last_activity"] = time.time()
        await interaction.followup.send("⏳ Status diubah: **Menunggu Pembayaran**")
        await send_status_update(interaction.guild, data.get("number", "?"), data.get("username", interaction.user.name), data.get("user_id", interaction.user.id), data.get("paket", "ORDER ROBUX"), "⏳ Menunggu Pembayaran", 0xfee75c)
    @discord.ui.button(label="🔄 Diproses", style=discord.ButtonStyle.primary, custom_id="status_process")
    async def process(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("❌ Hanya **Owner** yang bisa update status!", ephemeral=True); return
        data = ticket_data.get(interaction.channel.id, {})
        if data: data["last_activity"] = time.time()
        await interaction.followup.send("🔄 Status diubah: **Sedang Diproses**")
        await send_status_update(interaction.guild, data.get("number", "?"), data.get("username", interaction.user.name), data.get("user_id", interaction.user.id), data.get("paket", "ORDER ROBUX"), "🔄 Sedang Diproses", 0x5865f2)
    @discord.ui.button(label="✅ Selesai", style=discord.ButtonStyle.success, custom_id="status_done")
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("❌ Hanya **Owner** yang bisa update status!", ephemeral=True); return
        data = ticket_data.get(interaction.channel.id, {})
        if data: data["last_activity"] = time.time()
        await interaction.followup.send("✅ Status diubah: **Selesai** - Robux sudah masuk!")
        await send_status_update(interaction.guild, data.get("number", "?"), data.get("username", interaction.user.name), data.get("user_id", interaction.user.id), data.get("paket", "ORDER ROBUX"), "✅ Selesai / Done", 0x57f287)

class CloseView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔒 CLOSE TICKET", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("❌ Hanya **Owner** yang bisa menutup ticket ini!", ephemeral=True); return
        channel = interaction.channel; data = ticket_data.get(channel.id)
        if not data:
            await interaction.followup.send("Ticket ditutup..."); await channel.delete(); return
        await interaction.followup.send(f"Ticket ditutup oleh {interaction.user.mention}. Membuat transcript...")
        await do_auto_close(interaction.guild, channel, data, reason="closed by owner", admin_user=interaction.user)

class OrderModal(discord.ui.Modal, title="Pesanan Robux"):
    username = discord.ui.TextInput(label="Username", placeholder="UsernameRoblox", required=True)
    paket = discord.ui.TextInput(label="Paket yang dipilih", placeholder="Contoh: 500 Robux", required=True)
    pembayaran = discord.ui.TextInput(label="Metode Pembayaran", placeholder="QRIS", default="QRIS", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        global ticket_counter
        ticket_counter += 1
        guild = interaction.guild
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        category = get_ticket_category(guild)
        channel = await guild.create_text_channel(name=f"robux-via-username-{ticket_counter}-{interaction.user.name}", overwrites=overwrites, category=category)
        ticket_data[channel.id] = {"user_id": interaction.user.id, "username": interaction.user.name, "roblox_username": self.username.value, "pembayaran": self.pembayaran.value, "created_at": time.time(), "last_activity": time.time(), "number": ticket_counter, "paket": self.paket.value}
        embed = discord.Embed(title=f"🎫 Ticket Baru - {interaction.user.name}", description=f"**Username Roblox:** {self.username.value}\n**Paket:** {self.paket.value}\n**Pembayaran:** {self.pembayaran.value}\n**Ticket #{ticket_counter}**\n\nSilahkan kirim bukti pembayaran QRIS disini ya 💗", color=0xff69b4)
        embed.set_image(url=WELCOME_URL)
        await channel.send(f"{interaction.user.mention} Halo! Selamat datang di MIPI STORE! 🌸", embed=embed, view=CloseView())
        embed_qris = discord.Embed(title="💳 Scan QRIS Disini", description="Silahkan scan QRIS ini untuk pembayaran ya 💗", color=0xff69b4)
        embed_qris.set_image(url=QRIS_URL)
        await channel.send(embed=embed_qris)
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
async def on_message(message):
    if message.author.bot: return
    if message.guild and "market" in message.channel.name.lower():
        if message.author.id != message.guild.owner_id and not message.author.guild_permissions.administrator:
            if is_banned_selling(message.content):
                try: await message.delete()
                except: pass
                embed = discord.Embed(title="Stickied Message:", description="DILARANG MENJUAL PRODUK YANG KAMI JUAL SEPERTI ROBUX DAN LIMITED ITEM", color=0xff0000)
                warn = await message.channel.send(f"{message.author.mention}", embed=embed)
                await asyncio.sleep(10)
                try: await warn.delete()
                except: pass
                try: await message.author.send(f"⚠️ Pesan kamu di **#{message.channel.name}** dihapus!\n\n**Alasan:** Dilarang menjual produk yang kami jual seperti Robux dan Limited Item di MIPI STORE!")
                except: pass
                return
    if message.channel.id in ticket_data: ticket_data[message.channel.id]["last_activity"] = time.time()
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Login {bot.user}")
    bot.add_view(OrderView()); bot.add_view(CloseView()); bot.add_view(StatusView()); bot.add_view(RatingView(0))
    if not check_inactive.is_running(): check_inactive.start()
    await bot.tree.sync()

@bot.tree.command(name="ticket", description="Tampilkan panel order MIPI STORE")
async def ticket(interaction: discord.Interaction):
    embed1 = discord.Embed(title="Mipi Store - Order Robux 💗", description="🌸 **ROBUX VIA USERNAME**\nFast Process • Aman • Instan\n\nSyarat top up via username:\n>> SUDAH 18+\n>> SUDAH TERVERIFIKASI 2 LANGKAH", color=0xff69b4)
    embed1.set_image(url=WELCOME_URL)
    embed2 = discord.Embed(title="💰 PRICELIST ROBUX FAST SEND", description="500 = Rp 78.000\n1000 = Rp 155.000\n2000 = Rp 310.000\n3000 = Rp 465.000\n4000 = Rp 620.000\n5000 = Rp 775.000\n\n🌸 **Robux Eceran**\n100 = Rp 16.500\n200 = Rp 33.000\n300 = Rp 49.500\n400 = Rp 66.000\n\n🛒 **Cara Order**\nClick tombol ORDER ROBUX dibawah, isi formulir, lalu tunggu admin. Pembayaran **hanya QRIS**.", color=0xff69b4)
    embed2.set_image(url=QRIS_URL)
    embed2.set_footer(text="Mipi Store • Rafi Store")
    await interaction.response.send_message(embed=embed1)
    await interaction.followup.send(embed=embed2, view=OrderView())

@bot.tree.command(name="leaderboard", description="Lihat Top Buyer MIPI STORE bulan ini")
async def leaderboard(interaction: discord.Interaction):
    bulan = datetime.now().strftime("%Y-%m")
    bulan_tampil = datetime.now().strftime("%Y-%m")
    data = load_leaderboard()
    bulan_data = data.get(bulan, {})
    if not bulan_data:
        await interaction.response.send_message("Belum ada data Top Buyer bulan ini Wal! 🌸\nNanti otomatis keisi kalau ada ticket yang di-close!", ephemeral=True)
        return
    sorted_users = sorted(bulan_data.items(), key=lambda x: x[1]["total"], reverse=True)[:10]
    medali = ["🥇", "🥈", "🥉", "#4", "#5", "#6", "#7", "#8", "#9", "#10"]
    desc = f"Leaderboard bulanan • {bulan_tampil}\nPeringkat berdasarkan total Robux yang tercatat.\n\n**TOP 10 BUYERS**\n"
    for i, (uid, info) in enumerate(sorted_users):
        desc += f"{medali[i]} <@{uid}> — {info['total']:,} R$ · {info['transaksi']} transaksi\n"
    desc += f"\nMIPI STORE OFFICIAL • Data berdasarkan transaksi yang dicatat admin | {datetime.now().strftime('%m/%d/%y, %I:%M %p')}"
    embed = discord.Embed(title="🏆 MIPI STORE — TOP BUYER", description=desc, color=0xff69b4)
    embed.set_footer(text="Mipi Store • Rafi Store")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="market-rules", description="Kirim aturan market")
async def market_rules(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Hanya Owner!", ephemeral=True); return
    embed = discord.Embed(title="Stickied Message:", description="DILARANG MENJUAL PRODUK YANG KAMI JUAL SEPERTI ROBUX DAN LIMITED ITEM", color=0xff0000)
    msg = await interaction.channel.send(embed=embed)
    try: await msg.pin()
    except: pass
    await interaction.response.send_message("✅ Aturan market sudah di-pin!", ephemeral=True)

@bot.command(name="market-rules")
async def market_rules_prefix(ctx):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("❌ Hanya Owner!"); return
    embed = discord.Embed(title="Stickied Message:", description="DILARANG MENJUAL PRODUK YANG KAMI JUAL SEPERTI ROBUX DAN LIMITED ITEM", color=0xff0000)
    msg = await ctx.send(embed=embed)
    try: await msg.pin()
    except: pass
    await ctx.send("✅ Aturan market sudah di-pin!")

@bot.tree.command(name="ping", description="Cek bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! 🏓 MIPI STORE online Wal! {round(bot.latency*1000)}ms")

@bot.command(name="ping")
async def ping_prefix(ctx):
    await ctx.send(f"Pong! 🏓 MIPI STORE online Wal! {round(bot.latency*1000)}ms")

bot.run(os.getenv("DISCORD_TOKEN"))
