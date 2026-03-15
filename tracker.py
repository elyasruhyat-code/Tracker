import requests
import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError

# =============================================
# KONFIGURASI
# =============================================
BOT_TOKEN      = "8749664968:AAHz1bp7-1ayk_GPMzColj0MggQlINuRKaY"
CHAT_ID        = "6691055199"
SMSPVA_API_KEY = "kF4niDhtZysgZls4Zp0cWoQapv8yyk"
# =============================================

STOCK_URL      = "https://smspva.com/priemnik.php"
SERVICE        = "opt20"  # WhatsApp
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
            "apikey":  SMSPVA_API_KEY,
        }
        r    = requests.get(STOCK_URL, params=params, timeout=10)
        logging.info(f"Raw response: {r.text[:100]}")
        data = r.json()
        if data:
            # "online" = stok tersedia sekarang untuk negara ini
            # "forTotal" = stok khusus negara yang dipilih
            online   = int(data.get("online", 0))
            total    = int(data.get("total", 0))
            forTotal = int(data.get("forTotal", 0))  # Stok khusus MX
            logging.info(f"Detail: online={online}, total={total}, forTotal={forTotal}")
            # Pakai online langsung karena forTotal selalu 0
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
    try:
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
    except TelegramError as e:
        logging.error(f"Gagal kirim notif: {e}")

# ─── LOOP UTAMA ──────────────────────────────

async def tracker_loop():
    global last_stock
    bot = Bot(token=BOT_TOKEN)

    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=(
                "🚀 *SMSpva Stock Tracker aktif!*\n\n"
                f"🇲🇽 Tracking: *Mexico (+52) WhatsApp*\n"
                f"⏱ Cek setiap: *3 menit*\n\n"
                "Notifikasi otomatis kalau ada restok! 🔔"
            ),
            parse_mode="Markdown"
        )
    except TelegramError as e:
        logging.error(f"Gagal kirim pesan start: {e}")

    logging.info("✅ SMSpva Tracker aktif — cek setiap 3 menit")

    while True:
        result = check_stock()

        if result["success"]:
            online = result["online"]
            total  = result["total"]

            logging.info(f"Stok: {online} online / {total} total")

            # Notif kalau stok naik (restok!)
            if online > last_stock:
                logging.info(f"🔔 STOK NAIK! {last_stock} -> {online} nomor")
                await send_notif(bot, online, total, is_restock=True)

            last_stock = online
        else:
            logging.warning(f"Gagal cek stok: {result['msg']}")

        await asyncio.sleep(CHECK_INTERVAL)

# ─── MAIN ────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(tracker_loop())
