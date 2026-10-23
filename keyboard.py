from telebot.types import ReplyKeyboardMarkup, KeyboardButton


class StyledButton(KeyboardButton):
    """Rangli tugma (Bot API 9.4+): danger = qizil, success = yashil, primary = ko'k."""

    def __init__(self, text, style=None, **kwargs):
        super().__init__(text, **kwargs)
        self.style = style

    def to_dict(self):
        d = super().to_dict()
        if self.style:
            d["style"] = self.style
        return d


# ---------- foydalanuvchi menyusi (QIZIL) ----------
BTN_PROJECTS = "📂 Loyihalar"
BTN_ORDER = "🛒 Loyiha buyurtma qilish"
BTN_PRICES = "💰 Narxlar"
BTN_CONTACT = "📩 Adminga murojaat"

# ---------- admin menyusi (YASHIL) ----------
BTN_A_USERS = "👥 Foydalanuvchilar"
BTN_A_ADD = "➕ Loyiha qo'shish"
BTN_A_DEL = "🗑 Loyiha o'chirish"
BTN_A_ORDERS = "📦 Buyurtmalar"
BTN_A_CH_ADD = "📢 Kanal qo'shish"
BTN_A_CH_DEL = "❌ Kanal o'chirish"
BTN_A_ELON = "📣 E'lon yuborish"
BTN_A_STATS = "📊 Statistika"
BTN_A_EXIT = "🏠 Asosiy menyu"

USER_TEXTS = {BTN_PROJECTS, BTN_ORDER, BTN_PRICES, BTN_CONTACT}
ADMIN_TEXTS = {BTN_A_USERS, BTN_A_ADD, BTN_A_DEL, BTN_A_ORDERS, BTN_A_CH_ADD,
               BTN_A_CH_DEL, BTN_A_ELON, BTN_A_STATS, BTN_A_EXIT}
ALL_TEXTS = USER_TEXTS | ADMIN_TEXTS


def main_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(StyledButton(BTN_PROJECTS, style="danger"),
          StyledButton(BTN_ORDER, style="danger"))
    m.add(StyledButton(BTN_PRICES, style="danger"),
          StyledButton(BTN_CONTACT, style="danger"))
    return m


def admin_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(StyledButton(BTN_A_USERS, style="success"),
          StyledButton(BTN_A_ORDERS, style="success"))
    m.add(StyledButton(BTN_A_ADD, style="success"),
          StyledButton(BTN_A_DEL, style="success"))
    m.add(StyledButton(BTN_A_CH_ADD, style="success"),
          StyledButton(BTN_A_CH_DEL, style="success"))
    m.add(StyledButton(BTN_A_ELON, style="success"),
          StyledButton(BTN_A_STATS, style="success"))
    m.add(StyledButton(BTN_A_EXIT, style="success"))
    return m


def contact_kb():
    m = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    m.add(StyledButton("📱 Raqamni yuborish", style="primary", request_contact=True))
    return m
