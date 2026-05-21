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
ADMIN_ID = "1123186704"

CHANNELS = [
    # Старые каналы
    "maydecree", "mts_startup_hub", "ventureinpics", "ventureStuff",
    "dealsma", "corpmspof", "BizDNA", "subsidii_msk", "fasietalks",
    "startechmirinnovaci", "CDP_Moscow", "innocluster", "rusven",
    "UnicornRoad", "SberInvestments", "innovators_msk", "rb_ru", "ProstoVC",
    # Новые каналы
    "drussia", "habr_com", "blockchainRF", "fintechassociation", "fintexno",
    "abulaphia", "showstartup", "Kruche4aka", "kamaflow", "pro100IPO",
    "dsight_media", "brainbox_vc", "proventure", "clvl_invest", "smellslikevc",
    "Theedinorogblog", "chiefinnovationchannel", "TheQubeVC", "news_spin",
    "voskhodvc", "rfoundersgoglobal", "karpovaventures", "startup_venture",
    "ask_vc", "vcnews", "disruptors_official", "sbmarketing", "TheInnovations",
    # Новейшие каналы
    "univertechpred", "skolkovoleaks", "skd_russia",
]

KEYWORDS_COMPETITORS = [
    'скд', 'яндекс', 'yandex', 'втб', 'vtb', 'сбер', 'sber',
    'сбер технологии', 'сбертех', 'sbertech', 'академия инноваторов',
    'акселератор', 'accelerator', 'акселерационная программа',
    'y combinator', 'ycombinator', 'techstars', 'сколково', 'skolkovo',
    'иннополис', 'innopolis', 'фонд сколково', 'rvk', 'рвк',
    'конкурс стартапов', 'грантовая программа', 'грант', 'grant',
    'корпоративный акселератор', 'втб инвест', 'яндекс венчур', 'сбер венчурс',
]

KEYWORDS_TRENDS = [
    'нейросеть', 'искусственный интеллект', 'ии', 'ai', 'машинное обучение', 'ml',
    'компьютерное зрение', 'cv', 'большие языковые модели', 'llm',
    'генеративный ии', 'genai', 'автоматизация бизнеса', 'цифровизация',
    'тренды стартапов', 'единорог', 'unicorn', 'масштабирование',
    'международная экспансия', 'финтех', 'fintech', 'edtech', 'healthtech',
    'deeptech', 'биотех', 'biotech', 'инновации',
    'цифровая экономика', 'технологический тренд', 'новые технологии', 'saas',
    'b2b стартап', 'b2c стартап', 'маркетплейс', 'закон о стартапах',
    'налоговые льготы для ит', 'ит аккредитация', 'импортозамещение',
    'регуляторная песочница', 'цифровая трансформация', 'технологический прорыв',
    'блокчейн', 'web3', 'кибербезопасность', 'робототехника', 'беспилотники',
    '5g', 'квантовые вычисления', 'интернет вещей', 'iot', 'big data',
    'аналитика данных', 'data science',
]

KEYWORDS_STARTUPS = [
    'стартап', 'startup', 'фаундер', 'founder', 'основатель', 'сооснователь',
    'запустили', 'запуск продукта', 'новый сервис', 'новая платформа', 'mvp',
    'питч', 'pitch', 'питчинг', 'демо день', 'demo day', 'сбер 500', 'sber 500',
    'русский венчур', 'russian venture', 'инвестиции в стартап', 'венчурный фонд',
    'венчурные инвестиции', 'раунд финансирования', 'привлекли инвестиции',
    'привлекли финансирование', 'раунд a', 'раунд b', 'раунд c',
    'pre-seed', 'seed раунд', 'посевные инвестиции', 'венчур', 'vc', 'venture',
    'инвестор', 'angel investor', 'ангел', 'бизнес-ангел', 'частные инвестиции',
    'стартап привлёк', 'стартап запустил', 'стартап получил', 'стартап выпустил',
    'новости стартапов', 'стартап из россии', 'российский стартап',
    'венчурный рынок рф', 'российский венчурный фонд', 'венчурная сделка',
    'венчурный рынок', 'инвестиционный раунд', 'посевной раунд',
    'оценка компании', 'капитализация', 'стартап закрылся', 'стартап обанкротился',
]

ALL_KEYWORDS = list(set(KEYWORDS_COMPETITORS + KEYWORDS_TRENDS + KEYWORDS_STARTUPS))

CHECK_INTERVAL = 300

# ==========================================
# ФАЙЛЫ
# ==========================================

SEEN_FILE = "seen_posts.json"
DIGEST_FILE = "digest_posts.json"
LAST_DIGEST_FILE = "last_digest.json"
STATS_FILE = "stats.json"
PAUSE_FILE = "paused.json"
INITIALIZED_FILE = "initialized.json"
CUSTOM_KEYWORDS_FILE = "custom_keywords.json"
STATE_FILE = "admin_state.json"

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

def is_initialized():
    return os.path.exists(INITIALIZED_FILE)

def mark_initialized():
    save_json(INITIALIZED_FILE, {"date": datetime.now().strftime("%Y-%m-%d %H:%M")})

def load_custom_keywords():
    return load_json(CUSTOM_KEYWORDS_FILE, {"competitors": [], "trends": [], "startups": []})

def save_custom_keywords(kws):
    save_json(CUSTOM_KEYWORDS_FILE, kws)

def get_all_keywords():
    custom = load_custom_keywords()
    all_kw = set(ALL_KEYWORDS)
    for cat_list in custom.values():
        all_kw.update(cat_list)
    return list(all_kw)

def get_keywords_by_category(cat):
    custom = load_custom_keywords()
    base = {"competitors": KEYWORDS_COMPETITORS, "trends": KEYWORDS_TRENDS, "startups": KEYWORDS_STARTUPS}
    return base.get(cat, []) + custom.get(cat, [])

# Состояние диалога с админом (ожидаем ввод слова)
def get_state():
    return load_json(STATE_FILE, {"waiting": None})

def set_state(waiting_category):
    save_json(STATE_FILE, {"waiting": waiting_category})

def clear_state():
    save_json(STATE_FILE, {"waiting": None})

def load_stats():
    return load_json(STATS_FILE, {
        "today_date": "", "today_total": 0, "today_by_channel": {},
        "total_all_time": 0, "total_by_channel": {}
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

def get_post_category(text):
    text_lower = text.lower()
    scores = {"competitors": 0, "trends": 0, "startups": 0}
    for kw in get_keywords_by_category("competitors"):
        if kw.lower() in text_lower:
            scores["competitors"] += 1
    for kw in get_keywords_by_category("trends"):
        if kw.lower() in text_lower:
            scores["trends"] += 1
    for kw in get_keywords_by_category("startups"):
        if kw.lower() in text_lower:
            scores["startups"] += 1
    return max(scores, key=scores.get)

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
        return
    preview = text[:300] + "..." if len(text) > 300 else text
    msg = f"📢 Новость из @{channel}\n\n{preview}\n\n🔗 {post_url}"
    send_message(CHAT_ID, msg)

# ==========================================
# КЛАВИАТУРЫ
# ==========================================

def get_main_keyboard():
    return {
        "keyboard": [
            [{"text": "📊 Статистика"}, {"text": "📋 Дайджест сейчас"}],
            [{"text": "⏸ Пауза"}, {"text": "▶️ Возобновить"}],
            [{"text": "📡 Каналы"}, {"text": "🔑 Ключевые слова"}],
            [{"text": "➕ Добавить слово"}, {"text": "ℹ️ Помощь"}],
        ],
        "resize_keyboard": True,
        "persistent": True
    }

def get_category_keyboard():
    return {
        "keyboard": [
            [{"text": "🏢 Конкуренты"}],
            [{"text": "🔥 Тренды"}],
            [{"text": "💰 Наши стартапы"}],
            [{"text": "❌ Отмена"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }

# ==========================================
# КОМАНДЫ
# ==========================================

def cmd_start():
    custom = load_custom_keywords()
    total_custom = sum(len(v) for v in custom.values())
    text = (
        "👋 <b>Привет, Дарья!</b>\n\n"
        f"🔍 Слежу за <b>{len(CHANNELS)} каналами</b>\n"
        f"🔑 Ищу по <b>{len(get_all_keywords())} ключевым словам</b>\n"
        "📢 Публикую в <b>@Business_review_S</b>\n"
        "📊 Статистика каждый день в <b>20:00</b>\n"
        "📋 Дайджест каждую <b>пятницу в 11:00</b>\n\n"
        "Используй кнопки внизу 👇"
    )
    send_message(ADMIN_ID, text, get_main_keyboard())

def cmd_stats():
    stats = load_stats()
    today = datetime.now().strftime("%d.%m.%Y")
    today_str = datetime.now().strftime("%Y-%m-%d")
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

    today_total = stats["today_total"] if stats["today_date"] == today_str else 0
    today_by_channel = stats["today_by_channel"] if stats["today_date"] == today_str else {}

    day_rating = "Сегодня новостей ещё не публиковалось\n" if today_total == 0 else ""
    if today_total > 0:
        for i, (ch, cnt) in enumerate(sorted(today_by_channel.items(), key=lambda x: x[1], reverse=True)[:10]):
            day_rating += f"{medals[i] if i < len(medals) else '▪️'} @{ch} — {cnt}\n"

    all_rating = "Постов ещё не было\n" if stats["total_all_time"] == 0 else ""
    if stats["total_all_time"] > 0:
        for i, (ch, cnt) in enumerate(sorted(stats["total_by_channel"].items(), key=lambda x: x[1], reverse=True)[:10]):
            all_rating += f"{medals[i] if i < len(medals) else '▪️'} @{ch} — {cnt}\n"

    custom = load_custom_keywords()
    total_custom = sum(len(v) for v in custom.values())

    text = (
        f"📊 <b>Статистика на {today}</b>\n\n"
        f"Статус: {'⏸ На паузе' if is_paused() else '✅ Работает'}\n"
        f"В дайджесте: {len(load_digest())} постов\n"
        f"Доп. слов добавлено: {total_custom}\n\n"
        f"📌 <b>Сегодня: {today_total} постов</b>\n{day_rating}\n"
        f"━━━━━━━━━━━━━━\n"
        f"📈 <b>Всего: {stats['total_all_time']} постов</b>\n{all_rating}"
    )
    send_message(ADMIN_ID, text)

def cmd_digest():
    posts = load_digest()
    if not posts:
        send_message(ADMIN_ID, "📋 В дайджесте пока нет постов.")
        return
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    date_from = week_ago.strftime("%d.%m")
    date_to = now.strftime("%d.%m.%Y")

    cats = {"competitors": [], "trends": [], "startups": []}
    for post in posts:
        cats[post.get("category", "startups")].append(post)

    cat_config = [
        ("competitors", "🏢 КОНКУРЕНТЫ И ЭКОСИСТЕМЫ", "#конкуренты #экосистемы #акселераторы #дайджест"),
        ("trends",      "🔥 ТРЕНДЫ И ТЕХНОЛОГИИ",     "#тренды #технологии #инновации #ии #дайджест"),
        ("startups",    "💰 СТАРТАПЫ И ВЕНЧУР",        "#стартапы #венчур #инвестиции #фаундеры #дайджест"),
    ]

    sent = 0
    for cat_key, cat_title, hashtags in cat_config:
        cat_posts = cats[cat_key]
        if not cat_posts:
            continue
        header = (
            f"📋 <b>ДАЙДЖЕСТ — {cat_title}</b>\n"
            f"📅 {date_from} — {date_to} | Материалов: <b>{len(cat_posts)}</b>\n\n"
        )
        links = "".join(f"{i}. {p['url']}\n" for i, p in enumerate(cat_posts[-20:], 1))
        full_msg = header + links + f"\n{hashtags}"
        if len(full_msg) > 4096:
            full_msg = full_msg[:4090] + "..."
        send_message(CHAT_ID, full_msg)
        sent += 1
        time.sleep(1)

    # НЕ очищаем посты при ручном запросе — они войдут в пятничный дайджест тоже
    send_message(ADMIN_ID, f"✅ Дайджест опубликован! {sent} сообщений, {len(posts)} постов.\n\n📌 Посты сохранены — войдут в пятничный дайджест тоже.")

def cmd_channels():
    text = f"📡 <b>Мониторю {len(CHANNELS)} каналов:</b>\n\n"
    text += "".join(f"{i}. @{ch}\n" for i, ch in enumerate(CHANNELS, 1))
    send_message(ADMIN_ID, text)

def cmd_keywords():
    custom = load_custom_keywords()
    text = f"🔑 <b>Ключевые слова — всего {len(get_all_keywords())} шт:</b>\n\n"
    text += f"🏢 Конкуренты: {len(KEYWORDS_COMPETITORS) + len(custom['competitors'])} слов"
    if custom["competitors"]:
        text += f" (+{len(custom['competitors'])} твоих: {', '.join(custom['competitors'])})"
    text += f"\n🔥 Тренды: {len(KEYWORDS_TRENDS) + len(custom['trends'])} слов"
    if custom["trends"]:
        text += f" (+{len(custom['trends'])} твоих: {', '.join(custom['trends'])})"
    text += f"\n💰 Стартапы: {len(KEYWORDS_STARTUPS) + len(custom['startups'])} слов"
    if custom["startups"]:
        text += f" (+{len(custom['startups'])} твоих: {', '.join(custom['startups'])})"
    text += "\n\nНажми ➕ Добавить слово чтобы добавить новое."
    send_message(ADMIN_ID, text)

def cmd_ask_category():
    clear_state()
    send_message(ADMIN_ID,
        "➕ <b>Добавить ключевое слово</b>\n\nВыбери категорию:",
        get_category_keyboard())

def cmd_ask_word(category):
    cat_names = {
        "competitors": "🏢 Конкуренты",
        "trends": "🔥 Тренды",
        "startups": "💰 Наши стартапы"
    }
    set_state(category)
    send_message(ADMIN_ID,
        f"Категория: <b>{cat_names[category]}</b>\n\n"
        f"Напиши слово или фразу которую хочешь добавить:\n"
        f"(или нажми ❌ Отмена)",
        {"keyboard": [[{"text": "❌ Отмена"}]], "resize_keyboard": True})

def cmd_save_word(word):
    state = get_state()
    category = state.get("waiting")
    if not category:
        return False

    word = word.strip().lower()
    custom = load_custom_keywords()
    all_existing = get_all_keywords()

    if word in [k.lower() for k in all_existing]:
        send_message(ADMIN_ID,
            f"⚠️ Слово «{word}» уже есть в списке!",
            get_main_keyboard())
        clear_state()
        return True

    custom[category].append(word)
    save_custom_keywords(custom)
    clear_state()

    cat_names = {"competitors": "🏢 Конкуренты", "trends": "🔥 Тренды", "startups": "💰 Наши стартапы"}
    send_message(ADMIN_ID,
        f"✅ Слово «{word}» добавлено в категорию <b>{cat_names[category]}</b>!\n"
        f"Теперь всего {len(get_all_keywords())} ключевых слов.",
        get_main_keyboard())
    return True

def cmd_removeword(word):
    word = word.strip().lower()
    custom = load_custom_keywords()
    found = False
    for cat in custom:
        if word in custom[cat]:
            custom[cat].remove(word)
            found = True
            break
    if not found:
        send_message(ADMIN_ID, f"❌ Слово «{word}» не найдено в твоих добавленных словах.\n(Базовые слова удалить нельзя)")
        return
    save_custom_keywords(custom)
    send_message(ADMIN_ID, f"✅ Слово «{word}» удалено!")

def cmd_pause():
    set_paused(True)
    send_message(ADMIN_ID, "⏸ <b>Бот на паузе.</b>\nНажми ▶️ Возобновить чтобы продолжить.")

def cmd_resume():
    set_paused(False)
    send_message(ADMIN_ID, "▶️ <b>Бот возобновлён!</b>")

def cmd_help():
    text = (
        "ℹ️ <b>Команды:</b>\n\n"
        "📊 <b>Статистика</b> — посты за сегодня и рейтинг каналов\n\n"
        "📋 <b>Дайджест сейчас</b> — опубликовать дайджест в канал (3 сообщения по темам)\n\n"
        "⏸ / ▶️ — пауза и возобновление публикации\n\n"
        "📡 <b>Каналы</b> — список всех 46 каналов\n\n"
        "🔑 <b>Ключевые слова</b> — слова по категориям\n\n"
        "➕ <b>Добавить слово</b> — выбрать категорию и добавить слово\n\n"
        "<b>Текстом:</b> /removeword слово — удалить добавленное слово\n\n"
        "━━━━━━━━━━━━━━\n"
        "🤖 Каждые 5 мин — проверка каналов\n"
        "📊 20:00 — статистика тебе\n"
        "📋 Пятница 11:00 — дайджест в канал"
    )
    send_message(ADMIN_ID, text)

# ==========================================
# ОБРАБОТКА КОМАНД
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
                continue
            print(f"Команда: {text}")

            # Сначала проверяем состояние — ждём ввода слова
            state = get_state()
            if state.get("waiting"):
                if text == "❌ Отмена":
                    clear_state()
                    send_message(ADMIN_ID, "Отменено.", get_main_keyboard())
                    continue
                # Проверяем не нажата ли другая кнопка меню
                menu_buttons = ["📊 Статистика", "📋 Дайджест сейчас", "⏸ Пауза",
                               "▶️ Возобновить", "📡 Каналы", "🔑 Ключевые слова",
                               "➕ Добавить слово", "ℹ️ Помощь"]
                if text not in menu_buttons:
                    if cmd_save_word(text):
                        continue

            # Выбор категории
            if text == "🏢 Конкуренты":
                cmd_ask_word("competitors")
            elif text == "🔥 Тренды":
                cmd_ask_word("trends")
            elif text == "💰 Наши стартапы":
                cmd_ask_word("startups")
            elif text == "❌ Отмена":
                clear_state()
                send_message(ADMIN_ID, "Отменено.", get_main_keyboard())
            # Основные команды
            elif text in ["/start"]:
                cmd_start()
            elif text in ["📊 Статистика", "/stats"]:
                cmd_stats()
            elif text in ["📋 Дайджест сейчас", "/digest"]:
                cmd_digest()
            elif text in ["⏸ Пауза", "/pause"]:
                cmd_pause()
            elif text in ["▶️ Возобновить", "/resume"]:
                cmd_resume()
            elif text in ["📡 Каналы", "/channels"]:
                cmd_channels()
            elif text in ["🔑 Ключевые слова", "/keywords"]:
                cmd_keywords()
            elif text in ["➕ Добавить слово"]:
                cmd_ask_category()
            elif text in ["ℹ️ Помощь", "/help"]:
                cmd_help()
            elif text.startswith("/removeword "):
                cmd_removeword(text[12:])

    except Exception as e:
        print(f"Ошибка получения обновлений: {e}")

# ==========================================
# РАСПИСАНИЕ
# ==========================================

def should_send_digest():
    now = datetime.now()
    if now.weekday() != 4 or now.hour != 11:
        return False
    return load_json(LAST_DIGEST_FILE, {"date": ""}).get("date") != now.strftime("%Y-%m-%d")

def should_send_stats():
    now = datetime.now()
    if now.hour != 20 or now.minute > 5:
        return False
    return load_json("last_stats.json", {"date": ""}).get("date") != now.strftime("%Y-%m-%d")

# ==========================================
# ПАРСИНГ
# ==========================================

def get_posts(channel):
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        result = []
        for msg in soup.find_all("div", class_="tgme_widget_message"):
            text_div = msg.find("div", class_="tgme_widget_message_text")
            link_tag = msg.find("a", class_="tgme_widget_message_date")
            if text_div and link_tag:
                result.append((text_div.get_text(separator=" "), link_tag.get("href", "")))
        return result
    except Exception as e:
        print(f"  Ошибка @{channel}: {e}")
        return []

def check_keywords(text):
    text_lower = text.lower()
    for kw in get_all_keywords():
        if kw.lower() in text_lower:
            return True, kw
    return False, None

# ==========================================
# ГЛАВНЫЙ ЦИКЛ
# ==========================================

def main():
    print("=" * 50)
    print(f"Бот запущен! Каналов: {len(CHANNELS)}, слов: {len(get_all_keywords())}")
    print("=" * 50)

    seen = load_seen()

    if not is_initialized():
        print("Первый запуск — инициализация...")
        send_message(ADMIN_ID,
            "🚀 <b>Бот запущен!</b>\n\nСобираю существующие посты — не буду их дублировать.\nНовые посты начну публиковать через минуту!",
            get_main_keyboard())
        for channel in CHANNELS:
            print(f"  @{channel}...")
            for _, post_url in get_posts(channel):
                seen.add(post_url)
        save_seen(seen)
        mark_initialized()
        send_message(ADMIN_ID, f"✅ Готово! Запомнил {len(seen)} постов. Слежу за новыми 👀")
    else:
        send_message(ADMIN_ID, "🔄 <b>Бот перезапущен и работает!</b>", get_main_keyboard())

    while True:
        now = datetime.now()
        process_updates()

        if should_send_digest():
            cmd_digest()
            save_digest([])  # Очищаем только в пятницу
            save_json(LAST_DIGEST_FILE, {"date": now.strftime("%Y-%m-%d")})

        if should_send_stats():
            cmd_stats()
            save_json("last_stats.json", {"date": now.strftime("%Y-%m-%d")})

        print(f"Проверяю каналы... ({now.strftime('%H:%M')})")
        digest = load_digest()
        digest_urls = {p["url"] for p in digest}

        for channel in CHANNELS:
            print(f"  -> @{channel}")
            for text, post_url in get_posts(channel):
                if post_url in seen:
                    continue
                matched, keyword = check_keywords(text)
                if matched:
                    print(f"  Найдено: {keyword}")
                    send_post(channel, text, post_url)
                    update_stats(channel)
                    if post_url not in digest_urls:
                        digest.append({"url": post_url, "channel": channel, "category": get_post_category(text)})
                        digest_urls.add(post_url)
                    time.sleep(2)
                seen.add(post_url)

        save_seen(seen)
        save_digest(digest)
        print("Жду 5 минут...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
