import requests
import asyncio
import logging
from telegram import Bot

# =============================================
# KONFIGURASI - ISI BAGIAN INI
# =============================================
BOT_TOKEN  = "8749664968:AAHz1bp7-1ayk_GPMzColj0MggQlINuRKaY"  # Dari @BotFather
CHAT_ID    = "6691055199"             # Dari @userinfobot
# =============================================

STOCK_URL      = "https://smspva.com/priemnik.php"
SERVICE        = "opt16"  # WhatsApp
COUNTRY        = "MX"     # Mexico
CHECK_INTERVAL = 180      # 3 menit

last_stock = 0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S"
)

# ─── CEK STOK ────────────────────────────────

def check_stock() -> dict:
    try:
        params = {
            "metod":   "get_count_new",
            "country": COUNTRY,
            "service": SERVICE,
        }
        r    = requests.get(STOCK_URL, params=params, timeout=10)
        data = r.json()
        if data:
            online = int(data.get("online", 0))
            total  = int(data.get("total", 0))
            return {"success": True, "online": online, "total": total}
        return {"success": False, "msg": "Response kosong"}
    except Exception as e:
        return {"success": False, "msg": str(e)}

# ─── KIRIM NOTIFIKASI ────────────────────────

async def send_notif(bot: Bot, online: int, total: int, is_restock: bool):
    if is_restock:
        msg = (
            f"🔔 *RESTOK DETECTED!*\n\n"
            f"🇲🇽 *Negara:* Mexico (+52)\n"
            f"📱 *Service:* WhatsApp\n"
            f"✅ *Stok tersedia:* `{online}` nomor\n"
            f"📦 *Total stok:* `{total}` nomor\n\n"
            f"⚡ Cepat beli sebelum habis!\n"
            f"🔗 https://smspva.com"
        )
    else:
        msg = (
            f"📊 *Update Stok Mexico WhatsApp*\n\n"
            f"✅ *Online:* `{online}` nomor\n"
            f"📦 *Total:* `{total}` nomor"
        )
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

# ─── LOOP UTAMA ──────────────────────────────

async def tracker_loop():
    global last_stock
    bot = Bot(token=BOT_TOKEN)

    await bot.send_message(
        chat_id=CHAT_ID,
        text=(
            "🚀 *SMSpva Stock Tracker aktif!*\n\n"
            f"🇲🇽 Tracking: *Mexico (+52) WhatsApp*\n"
            f"⏱ Cek setiap: *3 menit*\n"
            f"🔑 Mode: *Tanpa API Key*\n\n"
            "Kamu akan dapat notifikasi otomatis kalau ada restok! 🔔"
        ),
        parse_mode="Markdown"
    )

    logging.info("✅ SMSpva Tracker aktif — cek setiap 3 menit")

    while True:
        result = check_stock()

        if result["success"]:
            online = result["online"]
            total  = result["total"]

            logging.info(f"Stok: {online} online / {total} total")

            # Notif hanya kalau stok naik dari 0 ke ada (restok!)
            if online > 0 and last_stock == 0:
                logging.info(f"🔔 RESTOK! {online} nomor tersedia")
                await send_notif(bot, online, total, is_restock=True)

            last_stock = online
        else:
            logging.warning(f"Gagal cek stok: {result['msg']}")

        await asyncio.sleep(CHECK_INTERVAL)

# ─── MAIN ────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(tracker_loop())
