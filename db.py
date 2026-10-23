import html
import json
import os
import threading
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))

# nom: (fayl, boshlang'ich qiymat)
FILES = {
    "users": ("users.json", {}),
    "products": ("products.json", []),
    "elon": ("elon.json", []),
    "channels": ("channels.json", []),
    "orders": ("orders.json", []),
}
_lock = threading.RLock()


def esc(s) -> str:
    return html.escape(str(s or ""))


def _path(name):
    return os.path.join(BASE, FILES[name][0])


def _default(name):
    return json.loads(json.dumps(FILES[name][1]))


def save(name, data):
    with _lock:
        tmp = _path(name) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _path(name))


def load(name):
    with _lock:
        if not os.path.exists(_path(name)):
            save(name, _default(name))
            return _default(name)
        try:
            with open(_path(name), encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return _default(name)


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ---------- users ----------
def register_user(tg_user):
    with _lock:
        users = load("users")
        key = str(tg_user.id)
        old = users.get(key, {})
        users[key] = {
            "id": tg_user.id,
            "name": tg_user.full_name,
            "username": tg_user.username or "",
            "phone": old.get("phone", ""),
            "joined": old.get("joined", now()),
        }
        save("users", users)
        return users[key]


def get_user(uid):
    return load("users").get(str(uid))


def set_phone(uid, phone):
    with _lock:
        users = load("users")
        if str(uid) in users:
            users[str(uid)]["phone"] = phone
            save("users", users)


def user_line(u: dict) -> str:
    uname = f"@{esc(u.get('username'))}" if u.get("username") else "—"
    return (f"👤 {esc(u.get('name'))}\n"
            f"📞 {esc(u.get('phone')) or '—'}\n"
            f"🔗 {uname}\n"
            f"🆔 <code>{u.get('id')}</code>")


def next_id(items: list) -> int:
    return (max((i["id"] for i in items), default=0)) + 1
