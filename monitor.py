import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime, timedelta
import threading

# ==========================================
# НАСТРОЙКИ
# ==========================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8955474803:AAFNkSGCbIfcJNt4r2BP420kjv4isYEZ_MA")
CHAT_ID = os.environ.get("CHAT_ID", "@Business_review_S")
ADMIN_ID = "1123186704"

CHANNELS = [
    "maydecree", "mts_startup_hub", "ventureinpics", "ventureStuff",
    "dealsma", "corpmspof", "BizDNA", "subsidii_msk", "fasietalks",
    "startechmirinnovaci", "CDP_Moscow", "innocluster", "rusven",
    "UnicornRoad", "SberInvestments", "innovators_msk", "rb_ru", "ProstoVC",
]

KEYWORDS = [
    "стартап", "startup", "фаундер", "основатель", "сооснователь",
    "запустили", "запуск продукта", "новый сервис", "новая платформа",
    "mvp", "питч", "питчинг", "демо день", "demo day",
    "инвестиции в стартап", "венчурный фонд", "венчурные инвестиции",
    "раунд финансирования", "раунд a", "раунд b", "раунд c",
    "pre-seed", "seed раунд", "посевные инвестиции",
    "привлекли инвестиции", "привлекли финансирование",
    "оценка компании", "valuation", "капитализация",
    "млн рублей привлек", "млн долларов привлек",
    "млрд рублей инвестиций", "получили грант",
    "акселератор", "акселерационная программа",
    "y combinator", "ycombinator", "techstars",
    "сколково", "иннополис", "фонд сколково",
    "фрии", "рвк", "конкурс стартапов", "грантовая программа",
    "нейросеть", "нейросети", "искусственный интеллект",
    "машинное обучение", "компьютерное зрение",
    "большие языковые модели", "генеративный ии",
    "автоматизация бизнеса", "цифровизация",
    "saas", "b2b стартап", "b2c стартап",
    "маркетплейс", "финтех", "edtech", "healthtech",
    "proptech", "agritech", "legaltech", "hrtech",
    "deeptech", "биотех", "медтех",
    "закон о стартапах", "налоговые льготы для ит",
    "ит аккредитация", "реестр отечественного по",
    "импортозамещение", "цифровая экономика",
    "законопроект об ии", "регулирование ии",
    "регуляторная песочница", "песочница цб",
    "единорог", "unicorn", "масштабирование",
    "вышли на рынок", "международная экспансия",
    "выручка выросла", "рост выручки", "монетизация", "прибыльность",
    "тренды стартапов", "рынок венчура",
    "венчурный рынок", "экосистема стартапов",
    "стартап закрылся", "стартап обанкротился",
]

CHECK_INTERVAL = 300

# ==========================================
# ФАЙЛЫ
# ==========================================

SEEN_FILE = "seen_posts.json"
DIGEST_FILE = "digest_posts.json"
LAST_DIGEST_FILE = "last_digest.json"
STATS_FILE = "stats.json"
PAUSE_FILE = "paused.json"

# ==========================================
# УТИЛИТЫ
# ==========================================

def load_json(filepath, default):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_seen():
    return set(load_json(SEEN_FILE, []))

def save_seen(seen):
    save_json(SEEN_FILE, list(seen))

def load_digest():
    return load_json(DIGEST_FILE, [])

def save_digest(posts):
    save_json(DIGEST_FILE, posts)

def is_paused():
    return load_json(PAUSE_FILE, {"paused": False}).get("paused", False)

def set_paused(value):
    save_json(PAUSE_FILE, {"paused": value})

def load_stats():
    return load_json(STATS_FILE, {
        "today_date": "",
        "today_total": 0,
        "today_by_channel": {},
        "total_all_time": 0,
        "total_by_channel": {}
    })

def save_stats(stats):
    save_json(STATS_FILE, stats)

def update_stats(channel):
    stats = load_stats()
    today = datetime.now().strftime("%Y-%m-%d")
    if stats["today_date"] != today:
        stats["today_date"] = today
        stats["today_total"] = 0
        stats["today_by_channel"] = {}
    stats["today_total"] += 1
    stats["today_by_channel"][channel] = stats["today_by_channel"].get(channel, 0) + 1
    stats["total_all_time"] += 1
    stats["total_by_channel"][channel] = stats["total_by_channel"].get(channel, 0) + 1
    save_stats(stats)

# ==========================================
# ОТПРАВКА
# ==========================================

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        resp = requests.post(url, data=data, timeout=15)
        if resp.status_code != 200:
            print(f"  Ошибка отправки: {resp.text}")
    except Exception as e:
        print(f"  Ошибка: {e}")

def send_post(channel, text, post_url):
    if is_paused():
        print("  Бот на паузе — пост пропущен")
        return
    preview = text[:300] + "..." if len(text) > 300 else text
    msg = f"📢 Новость из @{channel}\n\n{preview}\n\n🔗 {post_url}"
    send_message(CHAT_ID, msg)

# ==========================================
# КОМАНДЫ АДМИНА
# ==========================================

def get_main_keyboard():
    return {
        "keyboard": [
            [{"text": "📊 Статистика"}, {"text": "📋 Дайджест сейчас"}],
            [{"text": "⏸ Пауза"}, {"text": "▶️ Возобновить"}],
            [{"text": "📡 Каналы"}, {"text": "🔑 Ключевые слова"}],
            [{"text": "ℹ️ Помощь"}],
        ],
        "resize_keyboard": True,
        "persistent": True
    }

def cmd_start():
    text = (
        "👋 <b>Привет, Дарья!</b>\n\n"
        "Я твой бот для мониторинга стартап-новостей.\n\n"
        "🔍 Слежу за <b>18 каналами</b>\n"
        "🔑 Ищу по <b>60+ ключевым словам</b>\n"
        "📢 Публикую в <b>@Business_review_S</b>\n"
        "📊 Статистика каждый день в <b>20:00</b>\n"
        "📋 Дайджест каждую <b>пятницу в 11:00</b>\n\n"
        "Используй кнопки внизу 👇"
    )
    send_message(ADMIN_ID, text, get_main_keyboard())

def cmd_stats():
    stats = load_stats()
    today = datetime.now().strftime("%d.%m.%Y")
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    if stats["today_total"] == 0:
        day_rating = "Сегодня постов ещё не было"
    else:
        day_channels = sorted(stats["today_by_channel"].items(), key=lambda x: x[1], reverse=True)
        day_rating = ""
        for i, (ch, count) in enumerate(day_channels):
            medal = medals[i] if i < len(medals) else "▪️"
            day_rating += f"{medal} @{ch} — {count}\n"

    if stats["total_all_time"] == 0:
        all_rating = "Постов ещё не было"
    else:
        all_channels = sorted(stats["total_by_channel"].items(), key=lambda x: x[1], reverse=True)
        all_rating = ""
        for i, (ch, count) in enumerate(all_channels):
            medal = medals[i] if i < len(medals) else "▪️"
            all_rating += f"{medal} @{ch} — {count}\n"

    paused = "⏸ На паузе" if is_paused() else "✅ Работает"

    text = (
        f"📊 <b>Статистика на {today}</b>\n\n"
        f"Статус бота: {paused}\n\n"
        f"📌 <b>Сегодня опубликовано:</b> {stats['today_total']} постов\n"
        f"{day_rating}\n"
        f"━━━━━━━━━━━━━━\n"
        f"📈 <b>Всего за всё время:</b> {stats['total_all_time']} постов\n"
        f"{all_rating}"
    )
    send_message(ADMIN_ID, text)

def cmd_digest():
    posts = load_digest()
    if not posts:
        send_message(ADMIN_ID, "📋 В дайджесте пока нет постов.")
        return
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    header = (
        f"📋 <b>ДАЙДЖЕСТ СТАРТАП-НОВОСТЕЙ</b>\n"
        f"📅 {week_ago.strftime('%d.%m')} — {now.strftime('%d.%m.%Y')}\n\n"
        f"Собрано материалов: <b>{len(posts)}</b>\n\n"
    )
    links = ""
    for i, post in enumerate(posts[-30:], 1):
        links += f"{i}. {post['url']}\n"
    footer = "\n#дайджест #стартапы #инвестиции #технологии"
    full_msg = header + links + footer
    if len(full_msg) > 4096:
        full_msg = full_msg[:4090] + "..."
    send_message(CHAT_ID, full_msg)
    save_digest([])
    send_message(ADMIN_ID, f"✅ Дайджест опубликован в канал! Постов: {len(posts)}")

def cmd_channels():
    text = "📡 <b>Мониторю каналы:</b>\n\n"
    for i, ch in enumerate(CHANNELS, 1):
        text += f"{i}. @{ch}\n"
    text += f"\nВсего: {len(CHANNELS)} каналов"
    send_message(ADMIN_ID, text)

def cmd_keywords():
    text = "🔑 <b>Ключевые слова:</b>\n\n"
    text += ", ".join(KEYWORDS[:30])
    text += f"\n\n...и ещё {len(KEYWORDS) - 30} слов. Всего: {len(KEYWORDS)}"
    send_message(ADMIN_ID, text)

def cmd_pause():
    set_paused(True)
    send_message(ADMIN_ID, "⏸ <b>Бот на паузе.</b>\nНовые посты не будут публиковаться в канал.\n\nНажми ▶️ Возобновить чтобы продолжить.")

def cmd_resume():
    set_paused(False)
    send_message(ADMIN_ID, "▶️ <b>Бот возобновлён!</b>\nСнова публикую новости в канал.")

def cmd_help():
    text = (
        "ℹ️ <b>Список команд:</b>\n\n"
        "📊 <b>Статистика</b> — сколько постов опубликовано сегодня и за всё время, рейтинг каналов\n\n"
        "📋 <b>Дайджест сейчас</b> — опубликовать дайджест в канал прямо сейчас (не дожидаясь пятницы)\n\n"
        "⏸ <b>Пауза</b> — остановить публикацию в канал (бот продолжает мониторить, но не постит)\n\n"
        "▶️ <b>Возобновить</b> — снова начать публиковать после паузы\n\n"
        "📡 <b>Каналы</b> — список всех каналов которые мониторю\n\n"
        "🔑 <b>Ключевые слова</b> — список ключевых слов по которым фильтрую посты\n\n"
        "━━━━━━━━━━━━━━\n"
        "🤖 <b>Автоматически:</b>\n"
        "• Каждые 5 минут проверяю каналы\n"
        "• Каждый день в 20:00 отправляю тебе статистику\n"
        "• Каждую пятницу в 11:00 публикую дайджест в канал"
    )
    send_message(ADMIN_ID, text)

# ==========================================
# ОБРАБОТКА ВХОДЯЩИХ СООБЩЕНИЙ
# ==========================================

last_update_id = 0

def process_updates():
    global last_update_id
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 5}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if not data.get("ok"):
            return
        for update in data.get("result", []):
            last_update_id = update["update_id"]
            msg = update.get("message", {})
            chat_id = str(msg.get("chat", {}).get("id", ""))
            text = msg.get("text", "").strip()

            if chat_id != ADMIN_ID:
                continue  # отвечаем только админу

            print(f"Команда от админа: {text}")

            if text in ["/start", "ℹ️ Помощь"]:
                cmd_start()
            elif text in ["/stats", "📊 Статистика"]:
                cmd_stats()
            elif text in ["/digest", "📋 Дайджест сейчас"]:
                cmd_digest()
            elif text in ["/pause", "⏸ Пауза"]:
                cmd_pause()
            elif text in ["/resume", "▶️ Возобновить"]:
                cmd_resume()
            elif text in ["/channels", "📡 Каналы"]:
                cmd_channels()
            elif text in ["/keywords", "🔑 Ключевые слова"]:
                cmd_keywords()
            elif text in ["/help", "ℹ️ Помощь"]:
                cmd_help()
    except Exception as e:
        print(f"Ошибка получения обновлений: {e}")

# ==========================================
# РАСПИСАНИЕ
# ==========================================

def should_send_digest():
    now = datetime.now()
    if now.weekday() != 4 or now.hour != 11:
        return False
    today_str = now.strftime("%Y-%m-%d")
    data = load_json(LAST_DIGEST_FILE, {"date": ""})
    return data.get("date") != today_str

def should_send_stats():
    now = datetime.now()
    if now.hour != 20 or now.minute > 5:
        return False
    today_str = now.strftime("%Y-%m-%d")
    data = load_json("last_stats.json", {"date": ""})
    return data.get("date") != today_str

# ==========================================
# ПАРСИНГ КАНАЛОВ
# ==========================================

def get_posts(channel):
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        messages = soup.find_all("div", class_="tgme_widget_message")
        result = []
        for msg in messages:
            text_div = msg.find("div", class_="tgme_widget_message_text")
            link_tag = msg.find("a", class_="tgme_widget_message_date")
            if text_div and link_tag:
                text = text_div.get_text(separator=" ")
                post_url = link_tag.get("href", "")
                result.append((text, post_url))
        return result
    except Exception as e:
        print(f"  Ошибка при чтении @{channel}: {e}")
        return []

def check_keywords(text):
    text_lower = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text_lower:
            return True, kw
    return False, None

# ==========================================
# ГЛАВНЫЙ ЦИКЛ
# ==========================================

def main():
    print("=" * 50)
    print("Бот запущен!")
    print(f"Каналов: {len(CHANNELS)}")
    print(f"Ключевых слов: {len(KEYWORDS)}")
    print("=" * 50)

    # Отправляем приветствие админу при старте
    cmd_start()

    seen = load_seen()

    while True:
        now = datetime.now()

        # Проверяем входящие команды от админа
        process_updates()

        # Дайджест по пятницам в 11:00
        if should_send_digest():
            print("Отправляю еженедельный дайджест...")
            cmd_digest()
            save_json(LAST_DIGEST_FILE, {"date": now.strftime("%Y-%m-%d")})

        # Статистика каждый день в 20:00
        if should_send_stats():
            print("Отправляю дневную статистику...")
            cmd_stats()
            save_json("last_stats.json", {"date": now.strftime("%Y-%m-%d")})

        # Мониторинг каналов
        print(f"Проверяю каналы... ({now.strftime('%H:%M')})")
        digest = load_digest()
        digest_urls = {p["url"] for p in digest}

        for channel in CHANNELS:
            print(f"  -> @{channel}")
            posts = get_posts(channel)
            for text, post_url in posts:
                if post_url in seen:
                    continue
                matched, keyword = check_keywords(text)
                if matched:
                    print(f"  Найдено: {keyword}")
                    send_post(channel, text, post_url)
                    update_stats(channel)
                    if post_url not in digest_urls:
                        digest.append({"url": post_url, "channel": channel})
                        digest_urls.add(post_url)
                    time.sleep(2)
                seen.add(post_url)

        save_seen(seen)
        save_digest(digest)
        print(f"Жду 5 минут...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
