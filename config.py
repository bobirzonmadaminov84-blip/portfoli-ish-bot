import telebot
from keyboard import ALL_TEXTS

# ====== SOZLAMALAR (to'g'ridan-to'g'ri shu yerga yozing) ======
BOT_TOKEN = "8799178078:AAEGoKBvvMJHE11xm57oXd0rk-FVwbzbTNY"
ADMIN_IDS = [944890609]          # bir nechta admin: [111, 222]

# Narxlar (so'm)
PRICES = {
    "bot": {"title": "🤖 Telegram bot", "min": 200_000, "max": 500_000, "avg": 250_000},
    "web": {"title": "🌐 Web sayt",     "min": 100_000, "max": 200_000, "avg": 150_000},
}
# ===============================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


def money(n: int) -> str:
    return f"{n:,}".replace(",", " ") + " so'm"


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def notify_admins(text, markup=None):
    for aid in ADMIN_IDS:
        try:
            bot.send_message(aid, text, reply_markup=markup)
        except Exception as e:
            print("Adminga yuborib bo'lmadi:", aid, e)


def cancelled(m) -> bool:
    """Next-step paytida foydalanuvchi menyu tugmasi yoki /komanda bossa,
    jarayon bekor qilinadi va xabar odatdagi handlerga qaytariladi."""
    if m.text and (m.text.startswith("/") or m.text in ALL_TEXTS):
        bot.process_new_messages([m])
        return True
    return False
