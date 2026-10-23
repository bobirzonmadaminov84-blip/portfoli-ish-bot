from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


class IBtn(InlineKeyboardButton):
    """Rangli inline tugma (primary / success / danger)."""

    def __init__(self, text, style=None, **kwargs):
        super().__init__(text, **kwargs)
        self.style = style

    def to_dict(self):
        d = super().to_dict()
        if self.style:
            d["style"] = self.style
        return d


def subscribe_kb(channels):
    m = InlineKeyboardMarkup()
    for ch in channels:
        m.add(IBtn(f"📢 {ch['title']}", url=ch["link"]))
    m.add(IBtn("✅ Obunani tekshirish", style="success", callback_data="check_sub"))
    return m


def project_kb(link):
    m = InlineKeyboardMarkup()
    m.add(IBtn("🔗 Loyihani ko'rish", style="primary", url=link))
    return m


def order_type_kb():
    m = InlineKeyboardMarkup()
    m.add(IBtn("🤖 Telegram bot", style="danger", callback_data="ot_bot"),
          IBtn("🌐 Web sayt", style="danger", callback_data="ot_web"))
    return m


def order_confirm_kb(kind):
    m = InlineKeyboardMarkup()
    m.add(IBtn("✅ Buyurtma berish", style="success", callback_data=f"oc_{kind}"))
    m.add(IBtn("⬅️ Orqaga", callback_data="ot_back"))
    return m


def del_projects_kb(items):
    m = InlineKeyboardMarkup()
    for p in items:
        m.add(IBtn(f"🗑 {p['name']}", style="danger", callback_data=f"delp_{p['id']}"))
    return m


def del_channels_kb(items):
    m = InlineKeyboardMarkup()
    for c in items:
        m.add(IBtn(f"❌ {c['title']}", style="danger", callback_data=f"delc_{c['id']}"))
    return m


def order_done_kb(oid):
    m = InlineKeyboardMarkup()
    m.add(IBtn("✅ Bajarildi", style="success", callback_data=f"done_{oid}"))
    return m


def reply_kb(uid):
    m = InlineKeyboardMarkup()
    m.add(IBtn("↩️ Javob berish", style="primary", callback_data=f"reply_{uid}"))
    return m
