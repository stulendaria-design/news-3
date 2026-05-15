import requests
from bs4 import BeautifulSoup
import time
import json
import os

# ==========================================
# НАСТРОЙКИ
# ==========================================

BOT_TOKEN = "8955474803:AAFNkSGCbIfcJNt4r2BP420kjv4isYEZ_MA"
CHAT_ID = "@Business_review_S"  # для каналов нужен префикс -100

CHANNELS = [
    "buisness_ideal",
    "rus_buzines",
    "startup_club24",
    "startapnaya",
    "neuromaximru",
]

KEYWORDS = [
    # Стартапы общее
    "стартап",
    "startup",
    "основатель",
    "фаундер",
    "founder",
    "запуск проекта",
    "новый проект",
    "mvp",
    "питч",
    "pitch",

    # Инвестиции
    "инвестиции",
    "инвестор",
    "раунд",
    "раунд a",
    "раунд b",
    "seed",
    "венчур",
    "венчурный",
    "финансирование",
    "привлекли",
    "вложения",
    "оценка компании",
    "valuation",

    # Деньги и цифры
    "млн $",
    "млн долларов",
    "млрд",
    "миллион долларов",
    "$1",
    "$5",
    "$10",
    "$50",
    "$100",

    # Технологии и тренды
    "искусственный интеллект",
    "ии",
    "ai стартап",
    "нейросеть",
    "нейросети",
    "автоматизация",
    "saas",
    "маркетплейс",
    "платформа",
    "b2b",
    "b2c",
    "fintech",
    "финтех",
    "edtech",
    "healthtech",

    # Акселераторы и конкурсы
    "акселератор",
    "акселерация",
    "y combinator",
    "ycombinator",
    "skolkovo",
    "сколково",
    "грант",
    "конкурс стартапов",
    "demo day",

    # Успех и рост
    "единорог",
    "unicorn",
    "выход на рынок",
    "масштабирование",
    "рост x",
    "выручка",
    "прибыль",
    "монетизация",
]

CHECK_INTERVAL = 300  # каждые 5 минут

# ==========================================
# КОД (не трогай)
# ==========================================

SEEN_FILE = "seen_posts.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False)

def get_posts(channel):
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
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
        print(f"  ⚠️  Ошибка при чтении @{channel}: {e}")
        return []

def send_to_telegram(channel, text, post_url):
    preview = text[:300] + "..." if len(text) > 300 else text
    msg = (
        f"📢 Новость из @{channel}\n\n"
        f"{preview}\n\n"
        f"🔗 Читать полностью: {post_url}"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            print(f"  ✅ Отправлено в канал!")
        else:
            print(f"  ❌ Ошибка отправки: {resp.text}")
    except Exception as e:
        print(f"  ❌ Ошибка отправки: {e}")

def check_keywords(text):
    text_lower = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text_lower:
            return True, kw
    return False, None

def main():
    print("=" * 50)
    print("🤖 Бот запущен!")
    print(f"📡 Мониторю каналов: {len(CHANNELS)}")
    print(f"🔑 Ключевых слов: {len(KEYWORDS)}")
    print(f"⏱  Интервал проверки: {CHECK_INTERVAL} сек")
    print("Нажми Ctrl+C чтобы остановить")
    print("=" * 50)

    seen = load_seen()

    while True:
        print(f"\n🔍 Проверяю каналы...")
        for channel in CHANNELS:
            print(f"  → @{channel}")
            posts = get_posts(channel)
            for text, post_url in posts:
                if post_url in seen:
                    continue
                matched, keyword = check_keywords(text)
                if matched:
                    print(f"  🎯 Найдено слово «{keyword}»!")
                    send_to_telegram(channel, text, post_url)
                    time.sleep(2)  # небольшая пауза между отправками
                seen.add(post_url)
        save_seen(seen)
        print(f"\n💤 Жду {CHECK_INTERVAL // 60} мин до следующей проверки...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
