import time

from config import bot, is_admin, cancelled
import db
import keyboard as kb
import inline as il
from db import esc

_bot_id = None


def bot_id():
    global _bot_id
    if _bot_id is None:
        _bot_id = bot.get_me().id
    return _bot_id


def admin_only(m):
    return is_admin(m.from_user.id)


def send_chunks(chat_id, blocks, sep="\n\n"):
    """Uzun ro'yxatni Telegram limitiga (4096) mos bo'laklab yuboradi."""
    buf = ""
    for b in blocks:
        if len(buf) + len(b) + len(sep) > 3800:
            bot.send_message(chat_id, buf)
            buf = ""
        buf += b + sep
    if buf.strip():
        bot.send_message(chat_id, buf)


# ================= /admin =================
@bot.message_handler(commands=["admin"])
def admin_cmd(m):
    if not is_admin(m.from_user.id):
        bot.send_message(m.chat.id, "⛔ Siz admin emassiz.")
        return
    bot.send_message(m.chat.id, "🛠 <b>Admin panel</b>", reply_markup=kb.admin_menu())


@bot.message_handler(func=lambda m: admin_only(m) and m.text == kb.BTN_A_EXIT)
def exit_admin(m):
    bot.send_message(m.chat.id, "🏠 Asosiy menyu", reply_markup=kb.main_menu())


# ================= Foydalanuvchilar =================
@bot.message_handler(func=lambda m: admin_only(m) and m.text == kb.BTN_A_USERS)
def users_list(m):
    users = list(db.load("users").values())
    if not users:
        bot.send_message(m.chat.id, "👥 Hali foydalanuvchi yo'q.")
        return
    blocks = [f"<b>{i}.</b>\n{db.user_line(u)}" for i, u in enumerate(users, 1)]
    bot.send_message(m.chat.id, f"👥 Jami: <b>{len(users)}</b> ta foydalanuvchi")
    send_chunks(m.chat.id, blocks)


# ================= Statistika =================
@bot.message_handler(func=lambda m: admin_only(m) and m.text == kb.BTN_A_STATS)
def stats(m):
    orders = db.load("orders")
    new = sum(1 for o in orders if o["status"] == "new")
    bot.send_message(
        m.chat.id,
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: {len(db.load('users'))}\n"
        f"📂 Loyihalar: {len(db.load('products'))}\n"
        f"📦 Buyurtmalar: {len(orders)} (yangi: {new})\n"
        f"📢 Kanallar: {len(db.load('channels'))}\n"
        f"📣 E'lonlar: {len(db.load('elon'))}",
    )


# ================= Loyiha qo'shish =================
@bot.message_handler(func=lambda m: admin_only(m) and m.text == kb.BTN_A_ADD)
def add_project(m):
    msg = bot.send_message(m.chat.id, "📝 Loyiha nomini yozing:")
    bot.register_next_step_handler(msg, add_name)


def add_name(m):
    if cancelled(m):
        return
    if not m.text:
        msg = bot.send_message(m.chat.id, "❗ Nomni matn ko'rinishida yozing:")
        bot.register_next_step_handler(msg, add_name)
        return
    msg = bot.send_message(m.chat.id, "🖼 Loyiha rasmini yuboring:")
    bot.register_next_step_handler(msg, add_photo, m.text.strip())


def add_photo(m, name):
    if cancelled(m):
        return
    if m.content_type != "photo":
        msg = bot.send_message(m.chat.id, "❗ Iltimos, rasm yuboring:")
        bot.register_next_step_handler(msg, add_photo, name)
        return
    msg = bot.send_message(m.chat.id, "🔗 Loyiha linkini yuboring (masalan: https://example.uz):")
    bot.register_next_step_handler(msg, add_link, name, m.photo[-1].file_id)


def add_link(m, name, photo):
    if cancelled(m):
        return
    link = (m.text or "").strip()
    if not link or " " in link:
        msg = bot.send_message(m.chat.id, "❗ To'g'ri link yuboring:")
        bot.register_next_step_handler(msg, add_link, name, photo)
        return
    if not link.startswith(("http://", "https://", "tg://")):
        if link.startswith("@"):
            link = "https://t.me/" + link[1:]
        else:
            link = "https://" + link
    items = db.load("products")
    items.append({"id": db.next_id(items), "name": name, "photo": photo,
                  "link": link, "date": db.now()})
    db.save("products", items)
    bot.send_message(m.chat.id, f"✅ <b>{esc(name)}</b> loyihasi qo'shildi!")


# ================= Loyiha o'chirish =================
@bot.message_handler(func=lambda m: admin_only(m) and m.text == kb.BTN_A_DEL)
def del_project(m):
    items = db.load("products")
    if not items:
        bot.send_message(m.chat.id, "📂 O'chirish uchun loyiha yo'q.")
        return
    bot.send_message(m.chat.id, "🗑 O'chiriladigan loyihani tanlang:",
                     reply_markup=il.del_projects_kb(items))


@bot.callback_query_handler(func=lambda c: c.data.startswith("delp_"))
def del_project_cb(c):
    if not is_admin(c.from_user.id):
        return bot.answer_callback_query(c.id, "⛔")
    pid = int(c.data.split("_")[1])
    items = [p for p in db.load("products") if p["id"] != pid]
    db.save("products", items)
    bot.answer_callback_query(c.id, "🗑 O'chirildi")
    if items:
        bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id,
                                      reply_markup=il.del_projects_kb(items))
    else:
        bot.edit_message_text("📂 Barcha loyihalar o'chirildi.",
                              c.message.chat.id, c.message.message_id)


# ================= Buyurtmalar =================
@bot.message_handler(func=lambda m: admin_only(m) and m.text == kb.BTN_A_ORDERS)
def orders_list(m):
    orders = db.load("orders")
    if not orders:
        bot.send_message(m.chat.id, "📦 Hali buyurtma yo'q.")
        return
    bot.send_message(m.chat.id, f"📦 Oxirgi buyurtmalar (jami {len(orders)} ta):")
    for o in orders[-20:]:
        mark = "🆕" if o["status"] == "new" else "✅"
        text = (f"{mark} <b>Buyurtma #{o['id']}</b> — {esc(o['type'])}\n"
                f"🕒 {o['date']}\n\n{db.user_line(o['user'])}\n\n"
                f"📝 {esc(o['text'])}")
        bot.send_message(m.chat.id, text,
                         reply_markup=il.order_done_kb(o["id"]) if o["status"] == "new" else None)


@bot.callback_query_handler(func=lambda c: c.data.startswith("done_"))
def order_done_cb(c):
    if not is_admin(c.from_user.id):
        return bot.answer_callback_query(c.id, "⛔")
    oid = int(c.data.split("_")[1])
    orders = db.load("orders")
    for o in orders:
        if o["id"] == oid:
            o["status"] = "done"
    db.save("orders", orders)
    bot.answer_callback_query(c.id, "✅ Bajarildi deb belgilandi")
    bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)


# ================= Kanal qo'shish / o'chirish =================
@bot.message_handler(func=lambda m: admin_only(m) and m.text == kb.BTN_A_CH_ADD)
def add_channel(m):
    msg = bot.send_message(
        m.chat.id,
        "📢 Avval botni kanalga <b>admin</b> qiling.\n\n"
        "Keyin kanal @username'ini (yoki ID sini) yuboring, "
        "yoki kanaldan istalgan postni shu yerga forward qiling:")
    bot.register_next_step_handler(msg, add_channel_step)


def add_channel_step(m):
    if cancelled(m):
        return
    target = None
    if m.forward_from_chat:
        target = m.forward_from_chat.id
    elif m.text:
        target = m.text.strip()
        if not target.startswith("@") and not target.lstrip("-").isdigit():
            target = "@" + target
        elif target.lstrip("-").isdigit():
            target = int(target)
    if target is None:
        msg = bot.send_message(m.chat.id, "❗ Kanal username yoki forward post yuboring:")
        bot.register_next_step_handler(msg, add_channel_step)
        return
    try:
        chat = bot.get_chat(target)
        me = bot.get_chat_member(chat.id, bot_id())
        if me.status not in ("administrator", "creator"):
            raise ValueError("not admin")
    except Exception:
        bot.send_message(m.chat.id,
                         "❌ Kanal topilmadi yoki bot kanalda admin emas.\n"
                         "Botni kanalga admin qilib, qaytadan urinib ko'ring.")
        return
    if chat.username:
        link = f"https://t.me/{chat.username}"
    else:
        try:
            link = chat.invite_link or bot.export_chat_invite_link(chat.id)
        except Exception:
            bot.send_message(m.chat.id, "❌ Kanal linkini olib bo'lmadi. "
                                        "Botga «Invite users» huquqini bering.")
            return
    channels = db.load("channels")
    if any(c["id"] == chat.id for c in channels):
        bot.send_message(m.chat.id, "ℹ️ Bu kanal allaqachon qo'shilgan.")
        return
    channels.append({"id": chat.id, "title": chat.title, "link": link})
    db.save("channels", channels)
    bot.send_message(m.chat.id,
                     f"✅ <b>{esc(chat.title)}</b> kanali qo'shildi.\n"
                     "Endi foydalanuvchi /start bosganda shu kanalga obuna bo'lishi so'raladi.")


@bot.message_handler(func=lambda m: admin_only(m) and m.text == kb.BTN_A_CH_DEL)
def del_channel(m):
    items = db.load("channels")
    if not items:
        bot.send_message(m.chat.id, "📢 Qo'shilgan kanal yo'q.")
        return
    bot.send_message(m.chat.id, "❌ O'chiriladigan kanalni tanlang:",
                     reply_markup=il.del_channels_kb(items))


@bot.callback_query_handler(func=lambda c: c.data.startswith("delc_"))
def del_channel_cb(c):
    if not is_admin(c.from_user.id):
        return bot.answer_callback_query(c.id, "⛔")
    cid = int(c.data.split("_", 1)[1])
    items = [x for x in db.load("channels") if x["id"] != cid]
    db.save("channels", items)
    bot.answer_callback_query(c.id, "❌ O'chirildi")
    if items:
        bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id,
                                      reply_markup=il.del_channels_kb(items))
    else:
        bot.edit_message_text("📢 Barcha kanallar o'chirildi.",
                              c.message.chat.id, c.message.message_id)


# ================= E'lon (broadcast) =================
@bot.message_handler(func=lambda m: admin_only(m) and m.text == kb.BTN_A_ELON)
def elon_start(m):
    msg = bot.send_message(m.chat.id, "📣 E'lon matnini yoki rasmini (izoh bilan) yuboring:")
    bot.register_next_step_handler(msg, elon_send)


def elon_send(m):
    if cancelled(m):
        return
    if m.content_type not in ("text", "photo"):
        msg = bot.send_message(m.chat.id, "❗ Faqat matn yoki rasm yuboring:")
        bot.register_next_step_handler(msg, elon_send)
        return
    users = db.load("users")
    ok = fail = 0
    status = bot.send_message(m.chat.id, "⏳ Yuborilmoqda...")
    for uid in users:
        try:
            if m.content_type == "photo":
                bot.send_photo(int(uid), m.photo[-1].file_id, caption=m.caption or "")
            else:
                bot.send_message(int(uid), "📣 <b>E'lon</b>\n\n" + esc(m.text))
            ok += 1
        except Exception:
            fail += 1
        time.sleep(0.05)
    elon = db.load("elon")
    elon.append({"id": db.next_id(elon), "type": m.content_type,
                 "text": m.text or m.caption or "", "date": db.now(),
                 "sent": ok, "failed": fail})
    db.save("elon", elon)
    bot.edit_message_text(f"✅ E'lon yuborildi\n\n📨 Yetdi: {ok}\n🚫 Yetmadi: {fail}",
                          status.chat.id, status.message_id)


# ================= Foydalanuvchiga javob =================
@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_"))
def reply_cb(c):
    if not is_admin(c.from_user.id):
        return bot.answer_callback_query(c.id, "⛔")
    uid = int(c.data.split("_")[1])
    bot.answer_callback_query(c.id)
    msg = bot.send_message(c.message.chat.id, "✍️ Javobingizni yozing:")
    bot.register_next_step_handler(msg, reply_send, uid)


def reply_send(m, uid):
    if cancelled(m):
        return
    if not m.text:
        msg = bot.send_message(m.chat.id, "❗ Javobni matn ko'rinishida yozing:")
        bot.register_next_step_handler(msg, reply_send, uid)
        return
    try:
        bot.send_message(uid, f"📩 <b>Admin javobi:</b>\n\n{esc(m.text)}")
        bot.send_message(m.chat.id, "✅ Javob yuborildi.")
    except Exception:
        bot.send_message(m.chat.id, "❌ Yuborib bo'lmadi (foydalanuvchi botni bloklagan bo'lishi mumkin).")
