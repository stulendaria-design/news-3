import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime, timedelta

# ==========================================
# НАСТРОЙКИ
# ==========================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8955474803:AAFNkSGCbIfcJNt4r2BP420kjv4isYEZ_MA")
CHAT_ID = os.environ.get("CHAT_ID", "@Business_review_S")
ADMIN_ID = "1123186704"  # личный ID админа для статистики

CHANNELS = [
    "maydecree",
    "mts_startup_hub",
    "ventureinpics",
    "ventureStuff",
    "dealsma",
    "corpmspof",
    "BizDNA",
    "subsidii_msk",
    "fasietalks",
    "startechmirinnovaci",
    "CDP_Moscow",
    "innocluster",
    "rusven",
    "UnicornRoad",
    "SberInvestments",
    "innovators_msk",
    "rb_ru",
    "ProstoVC",
]

KEYWORDS = [
    # Стартапы
    "стартап", "startup", "фаундер", "основатель", "сооснователь",
    "запустили", "запуск продукта", "новый сервис", "новая платформа",
    "mvp", "питч", "питчинг", "демо день", "demo day",
    # Инвестиции
    "инвестиции в стартап", "венчурный фонд", "венчурные инвестиции",
    "раунд финансирования", "раунд a", "раунд b", "раунд c",
    "pre-seed", "seed раунд", "посевные инвестиции",
    "привлекли инвестиции", "привлекли финансирование",
    "оценка компании", "valuation", "капитализация",
    "млн рублей привлек", "млн долларов привлек",
    "млрд рублей инвестиций", "получили грант",
    # Акселераторы
    "акселератор", "акселерационная программа",
    "y combinator", "ycombinator", "techstars",
    "сколково", "иннополис", "фонд сколково",
    "фрии", "рвк", "конкурс стартапов", "грантовая программа",
    # Технологии
    "нейросеть", "нейросети", "искусственный интеллект",
    "машинное обучение", "компьютерное зрение",
    "большие языковые модели", "генеративный ии",
    "автоматизация бизнеса", "цифровизация",
    # Рынки
    "saas", "b2b стартап", "b2c стартап",
    "маркетплейс", "финтех", "edtech", "healthtech",
    "proptech", "agritech", "legaltech", "hrtech",
    "deeptech", "биотех", "медтех",
    # Законы
    "закон о стартапах", "налоговые льготы для ит",
    "ит аккредитация", "реестр отечественного по",
    "импортозамещение", "цифровая экономика",
    "законопроект об ии", "регулирование ии",
    "регуляторная песочница", "песочница цб",
    # Рост
    "единорог", "unicorn", "масштабирование",
    "вышли на рынок", "международная экспансия",
    "выручка выросла", "рост выручки",
    "монетизация", "прибыльность",
    # Тренды
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

# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
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
    data = load_json(SEEN_FILE, [])
    return set(data)

def save_seen(seen):
    save_json(SEEN_FILE, list(seen))

def load_digest():
    return load_json(DIGEST_FILE, [])

def save_digest(posts):
    save_json(DIGEST_FILE, posts)

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

    # Сброс дневной статистики если новый день
    if stats["today_date"] != today:
        stats["today_date"] = today
        stats["today_total"] = 0
        stats["today_by_channel"] = {}

    # Обновляем дневную
    stats["today_total"] += 1
    stats["today_by_channel"][channel] = stats["today_by_channel"].get(channel, 0) + 1

    # Обновляем общую
    stats["total_all_time"] += 1
    stats["total_by_channel"][channel] = stats["total_by_channel"].get(channel, 0) + 1

    save_stats(stats)

# ==========================================
# ОТПРАВКА СООБЩЕНИЙ
# ==========================================

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, data=data, timeout=15)
        if resp.status_code == 200:
            print(f"  Отправлено в {chat_id}!")
        else:
            print(f"  Ошибка: {resp.text}")
    except Exception as e:
        print(f"  Ошибка отправки: {e}")

def send_post(channel, text, post_url):
    preview = text[:300] + "..." if len(text) > 300 else text
    msg = f"📢 Новость из @{channel}\n\n{preview}\n\n🔗 {post_url}"
    send_message(CHAT_ID, msg)

def send_daily_stats():
    stats = load_stats()
    today = datetime.now().strftime("%d.%m.%Y")

    if stats["today_total"] == 0:
        msg = f"📊 <b>Статистика за {today}</b>\n\nСегодня новостей по ключевым словам не найдено."
    else:
        # Рейтинг каналов за день
        day_channels = sorted(
            stats["today_by_channel"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        day_rating = ""
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, (ch, count) in enumerate(day_channels):
            medal = medals[i] if i < len(medals) else "▪️"
            day_rating += f"{medal} @{ch} — {count} постов\n"

        # Рейтинг каналов за всё время
        all_channels = sorted(
            stats["total_by_channel"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        all_rating = ""
        for i, (ch, count) in enumerate(all_channels):
            medal = medals[i] if i < len(medals) else "▪️"
            all_rating += f"{medal} @{ch} — {count} постов\n"

        msg = (
            f"📊 <b>Статистика за {today}</b>\n\n"
            f"📌 Опубликовано сегодня: <b>{stats['today_total']}</b> постов\n\n"
            f"<b>Рейтинг каналов за сегодня:</b>\n"
            f"{day_rating}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📈 Всего за всё время: <b>{stats['total_all_time']}</b> постов\n\n"
            f"<b>Рейтинг каналов за всё время:</b>\n"
            f"{all_rating}"
        )

    send_message(ADMIN_ID, msg)
    print("Статистика отправлена админу!")

# ==========================================
# ДАЙДЖЕСТ
# ==========================================

def send_digest():
    posts = load_digest()
    if not posts:
        send_message(ADMIN_ID, "📋 Дайджест за эту неделю пуст — новостей не найдено.")
        return

    now = datetime.now()
    week_ago = now - timedelta(days=7)
    date_from = week_ago.strftime("%d.%m")
    date_to = now.strftime("%d.%m.%Y")

    header = (
        f"📋 <b>ДАЙДЖЕСТ СТАРТАП-НОВОСТЕЙ</b>\n"
        f"📅 {date_from} — {date_to}\n\n"
        f"За неделю собрано материалов: <b>{len(posts)}</b>\n\n"
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
    print(f"Дайджест отправлен! Постов: {len(posts)}")

# ==========================================
# ПРОВЕРКИ РАСПИСАНИЯ
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
# ПОИСК ПО КЛЮЧЕВЫМ СЛОВАМ
# ==========================================

def check_keywords(text):
    text_lower = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text_lower:
            return True, kw
    return False, None

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

# ==========================================
# ГЛАВНЫЙ ЦИКЛ
# ==========================================

def main():
    print("=" * 50)
    print("Бот запущен!")
    print(f"Каналов: {len(CHANNELS)}")
    print(f"Ключевых слов: {len(KEYWORDS)}")
    print(f"Дайджест: каждую пятницу в 11:00")
    print(f"Статистика: каждый день в 20:00 админу")
    print("=" * 50)

    seen = load_seen()

    while True:
        now = datetime.now()

        # Дайджест по пятницам в 11:00
        if should_send_digest():
            print("Отправляю еженедельный дайджест...")
            send_digest()
            save_json(LAST_DIGEST_FILE, {"date": now.strftime("%Y-%m-%d")})

        # Статистика каждый день в 20:00
        if should_send_stats():
            print("Отправляю дневную статистику админу...")
            send_daily_stats()
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
