import re
import json
import os
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

# ------------------------------
# Конфигурация
# ------------------------------
URL_RUB_USDT = "https://www.bestchange.ru/cash-ruble-to-tether-trc20-in-msk.html"
URL_USD_EUR = "https://www.xe.com/currencycharts/?from=USD&to=EUR"
URL_USD_CNY = "https://finance.rambler.ru/calculators/converter/1-USD-CNY/"

# CSS-селекторы для каждого курса
CSS_RATE_RUB_USDT = "#undertable > div.m-hint > span:nth-child(2) > span:nth-child(5) > span"
CSS_RATE_USD_EUR = "#__next > main > div:nth-child(5) > div.relative.bg-gradient-to-l.from-blue-850.to-blue-700.pt-8 > div.m-auto.grid.max-w-screen-xl.gap-6.px-4.md\\:gap-12.md\\:px-10 > div > div:nth-child(2) > div > div:nth-child(4) > div:nth-child(2) > div.flex.flex-wrap.justify-between > div.flex.flex-wrap.items-start > div > p"
CSS_RATE_USD_CNY = "#app > div.dTSkA6xB.commercial-branding > div > div.yP4MAOpL > div.BgJ8We0r.so0OkpgH > div.yw7YVg6D > div.N_cub_8e > div:nth-child(1) > div:nth-child(3) > span.x9LZBMwk"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ------------------------------
# Вспомогательная функция
# ------------------------------
def fetch_url(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"❌ Ошибка запроса к {url}: {e}")
        return None

# ------------------------------
# Парсеры для каждого курса (с использованием селекторов)
# ------------------------------
def get_rub_usdt() -> float | None:
    """Парсит курс RUB → USDT с BestChange."""
    html = fetch_url(URL_RUB_USDT)
    if not html:
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    elements = soup.select(CSS_RATE_RUB_USDT)
    if not elements:
        print("❌ RUB→USDT: элемент не найден")
        return None
    
    text = elements[0].get_text(strip=True)
    print(f"🔍 RUB→USDT текст: {text}")
    
    match = re.search(r"([\d.,]+)", text)
    if not match:
        return None
    
    rate_str = match.group(1).replace(",", ".")
    try:
        return float(rate_str)
    except ValueError:
        return None

def get_usd_eur() -> float | None:
    """Парсит курс USD → EUR с XE.com по CSS-селектору."""
    html = fetch_url(URL_USD_EUR)
    if not html:
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    elements = soup.select(CSS_RATE_USD_EUR)
    
    if not elements:
        print("❌ USD→EUR: элемент не найден по селектору")
        # Пробуем запасной вариант через регулярное выражение
        match = re.search(r'1\s*USD\s*=\s*([\d.]+)\s*EUR', html)
        if match:
            print("⚠️ USD→EUR: найден через regex (запасной вариант)")
            return float(match.group(1))
        return None
    
    text = elements[0].get_text(strip=True)
    print(f"🔍 USD→EUR текст: {text}")
    
    # Извлекаем число из текста (может быть "0.876098 EUR" или просто "0.876098")
    match = re.search(r"([\d.]+)", text)
    if match:
        return float(match.group(1))
    else:
        print("❌ USD→EUR: число не найдено в тексте элемента")
        return None

def get_usd_cny() -> float | None:
    """Парсит курс USD → CNY с Rambler по CSS-селектору."""
    html = fetch_url(URL_USD_CNY)
    if not html:
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    elements = soup.select(CSS_RATE_USD_CNY)
    
    if not elements:
        print("❌ USD→CNY: элемент не найден по селектору")
        # Пробуем запасные варианты через регулярные выражения
        match = re.search(r'1\s*USD\s*=\s*([\d.]+)\s*CNY', html)
        if match:
            print("⚠️ USD→CNY: найден через regex (запасной вариант)")
            return float(match.group(1))
        match = re.search(r'USD1\s*CNY([\d.]+)', html)
        if match:
            print("⚠️ USD→CNY: найден через альтернативный regex")
            return float(match.group(1))
        return None
    
    text = elements[0].get_text(strip=True)
    print(f"🔍 USD→CNY текст: {text}")
    
    # Извлекаем число из текста
    match = re.search(r"([\d.]+)", text)
    if match:
        return float(match.group(1))
    else:
        print("❌ USD→CNY: число не найдено в тексте элемента")
        return None

# ------------------------------
# Загрузка старых данных для fallback
# ------------------------------
def load_old_rates():
    if os.path.exists("rates_all.json"):
        try:
            with open("rates_all.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

# ------------------------------
# Основная функция
# ------------------------------
def main():
    print("=" * 50)
    print("🔄 Начинаем обновление курсов (с CSS-селекторами)")
    print("=" * 50)

    # Получаем текущие курсы
    rub_usdt = get_rub_usdt()
    usd_eur = get_usd_eur()
    usd_cny = get_usd_cny()

    # Загружаем старые данные (на случай ошибки)
    old = load_old_rates()
    
    # Формируем новый объект
    rates = {
        "rub_usdt": rub_usdt if rub_usdt is not None else old.get("rub_usdt"),
        "usd_eur": usd_eur if usd_eur is not None else old.get("usd_eur"),
        "usd_cny": usd_cny if usd_cny is not None else old.get("usd_cny"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    # Проверяем, что хоть что-то получено
    if rates["rub_usdt"] is None and rates["usd_eur"] is None and rates["usd_cny"] is None:
        print("❌ Все курсы недоступны! Выход.")
        return

    # Сохраняем в файл
    with open("rates_all.json", "w", encoding="utf-8") as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)

    print("✅ Сохранены курсы:")
    print(f"  RUB→USDT: {rates['rub_usdt']}")
    print(f"  USD→EUR:  {rates['usd_eur']}")
    print(f"  USD→CNY:  {rates['usd_cny']}")
    print(f"  Обновлено: {rates['updated_at']}")
    print("=" * 50)

if __name__ == "__main__":
    main()
