from config import bot, is_admin, notify_admins, cancelled, PRICES, money
import db
import keyboard as kb
import inline as il
from db import esc
import admin  # noqa: F401  (admin handlerlarini ro'yxatdan o'tkazadi)


# ================= Yordamchi =================
def not_subscribed(uid):
    """Foydalanuvchi obuna bo'lmagan kanallar ro'yxati."""
    missing = []
    for ch in db.load("channels"):
        try:
            st = bot.get_chat_member(ch["id"], uid).status
            if st in ("left", "kicked"):
                missing.append(ch)
        except Exception as e:  # bot kanaldan chiqarilgan bo'lsa foydalanuvchini to'smaymiz
            print("Obunani tekshirib bo'lmadi:", ch["title"], e)
    return missing


def allowed(chat_id, user) -> bool:
    """Kanalga obuna va telefon raqamni tekshiradi."""
    if is_admin(user.id):
        return True
    missing = not_subscribed(user.id)
    if missing:
        bot.send_message(chat_id,
                         "📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling, "
                         "so'ng «Obunani tekshirish» tugmasini bosing:",
                         reply_markup=il.subscribe_kb(missing))
        return False
    u = db.get_user(user.id)
    if not u or not u.get("phone"):
        bot.send_message(chat_id, "📱 Davom etish uchun telefon raqamingizni yuboring:",
                         reply_markup=kb.contact_kb())
        return False
    return True


def show_menu(chat_id, name):
    bot.send_message(chat_id,
                     f"👋 Assalomu alaykum, <b>{esc(name)}</b>!\n\n"
                     "Portfolio botimizga xush kelibsiz. Kerakli bo'limni tanlang 👇",
                     reply_markup=kb.main_menu())


# ================= /start =================
@bot.message_handler(commands=["start"])
def start(m):
    bot.clear_step_handler_by_chat_id(m.chat.id)
    db.register_user(m.from_user)
    if allowed(m.chat.id, m.from_user):
        show_menu(m.chat.id, m.from_user.first_name)


@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(c):
    if not_subscribed(c.from_user.id):
        bot.answer_callback_query(c.id, "❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        return
    bot.answer_callback_query(c.id, "✅ Rahmat!")
    try:
        bot.delete_message(c.message.chat.id, c.message.message_id)
    except Exception:
        pass
    db.register_user(c.from_user)
    if allowed(c.message.chat.id, c.from_user):
        show_menu(c.message.chat.id, c.from_user.first_name)


@bot.message_handler(content_types=["contact"])
def got_contact(m):
    if m.contact.user_id != m.from_user.id:
        bot.send_message(m.chat.id, "❗ Iltimos, o'zingizning raqamingizni yuboring.")
        return
    db.register_user(m.from_user)
    db.set_phone(m.from_user.id, m.contact.phone_number)
    show_menu(m.chat.id, m.from_user.first_name)


# ================= Loyihalar =================
@bot.message_handler(func=lambda m: m.text == kb.BTN_PROJECTS)
def projects(m):
    if not allowed(m.chat.id, m.from_user):
        return
    items = db.load("products")
    if not items:
        bot.send_message(m.chat.id, "📂 Hali loyiha qo'shilmagan.")
        return
    for p in items:
        bot.send_photo(m.chat.id, p["photo"], caption=f"<b>{esc(p['name'])}</b>",
                       reply_markup=il.project_kb(p["link"]))


# ================= Narxlar =================
@bot.message_handler(func=lambda m: m.text == kb.BTN_PRICES)
def prices(m):
    if not allowed(m.chat.id, m.from_user):
        return
    web, tg = PRICES["web"], PRICES["bot"]
    bot.send_message(
        m.chat.id,
        "💰 <b>Narxlar (o'rtacha)</b>\n\n"
        f"{web['title']}: <b>{money(web['avg'])}</b>\n"
        f"{tg['title']}: <b>{money(tg['avg'])}</b>\n\n"
        "Aniq narx loyiha murakkabligiga qarab kelishiladi.")


# ================= Loyiha buyurtma qilish =================
@bot.message_handler(func=lambda m: m.text == kb.BTN_ORDER)
def order(m):
    if not allowed(m.chat.id, m.from_user):
        return
    bot.send_message(m.chat.id, "🛒 Qanday loyiha buyurtma qilmoqchisiz?",
                     reply_markup=il.order_type_kb())


@bot.callback_query_handler(func=lambda c: c.data.startswith("ot_"))
def order_type(c):
    kind = c.data[3:]
    bot.answer_callback_query(c.id)
    if kind == "back":
        bot.edit_message_text("🛒 Qanday loyiha buyurtma qilmoqchisiz?",
                              c.message.chat.id, c.message.message_id,
                              reply_markup=il.order_type_kb())
        return
    p = PRICES[kind]
    bot.edit_message_text(
        f"{p['title']}\n\n💰 Narxi: <b>{money(p['min'])} – {money(p['max'])}</b>",
        c.message.chat.id, c.message.message_id,
        reply_markup=il.order_confirm_kb(kind))


@bot.callback_query_handler(func=lambda c: c.data.startswith("oc_"))
def order_confirm(c):
    kind = c.data[3:]
    bot.answer_callback_query(c.id)
    msg = bot.send_message(c.message.chat.id,
                           f"📝 {PRICES[kind]['title']} bo'yicha buyurtmangizni batafsil yozing "
                           "(nima kerak, qanday funksiyalar, muddat):")
    bot.register_next_step_handler(msg, save_order, kind, c.from_user)


def save_order(m, kind, user):
    if cancelled(m):
        return
    if not m.text:
        msg = bot.send_message(m.chat.id, "❗ Buyurtmani matn ko'rinishida yozing:")
        bot.register_next_step_handler(msg, save_order, kind, user)
        return
    u = db.get_user(user.id) or db.register_user(user)
    orders = db.load("orders")
    o = {"id": db.next_id(orders), "type": PRICES[kind]["title"], "text": m.text,
         "user": u, "status": "new", "date": db.now()}
    orders.append(o)
    db.save("orders", orders)
    bot.send_message(m.chat.id, "✅ Buyurtmangiz qabul qilindi! Admin tez orada siz bilan bog'lanadi.",
                     reply_markup=kb.main_menu())
    notify_admins(f"🆕 <b>Yangi buyurtma #{o['id']}</b> — {esc(o['type'])}\n\n"
                  f"{db.user_line(u)}\n\n📝 {esc(m.text)}",
                  il.order_done_kb(o["id"]))


# ================= Adminga murojaat =================
@bot.message_handler(func=lambda m: m.text == kb.BTN_CONTACT)
def contact(m):
    if not allowed(m.chat.id, m.from_user):
        return
    msg = bot.send_message(m.chat.id, "✍️ Adminga yuboriladigan xabaringizni yozing:")
    bot.register_next_step_handler(msg, send_to_admin)


def send_to_admin(m):
    if cancelled(m):
        return
    if not m.text:
        msg = bot.send_message(m.chat.id, "❗ Xabarni matn ko'rinishida yozing:")
        bot.register_next_step_handler(msg, send_to_admin)
        return
    u = db.get_user(m.from_user.id) or db.register_user(m.from_user)
    notify_admins(f"📩 <b>Yangi murojaat</b>\n\n{db.user_line(u)}\n\n💬 {esc(m.text)}",
                  il.reply_kb(m.from_user.id))
    bot.send_message(m.chat.id, "✅ Xabaringiz adminga yuborildi.", reply_markup=kb.main_menu())


if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.infinity_polling(skip_pending=True)
