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

# CSS-селекторы
CSS_RATE_RUB_USDT = "#undertable > div.m-hint > span:nth-child(2) > span:nth-child(5) > span"
CSS_RATE_USD_EUR = "#__next > main > div:nth-child(5) > div.relative.bg-gradient-to-l.from-blue-850.to-blue-700.pt-8 > div.m-auto.grid.max-w-screen-xl.gap-6.px-4.md\\:gap-12.md\\:px-10 > div > div:nth-child(2) > div > div:nth-child(4) > div:nth-child(2) > div.flex.flex-wrap.justify-between > div.flex.flex-wrap.items-start > div > p"
CSS_RATE_USD_CNY = "#app > div.dTSkA6xB.commercial-branding > div > div.yP4MAOpL > div.BgJ8We0r.so0OkpgH > div.yw7YVg6D > div.N_cub_8e > div:nth-child(1) > div:nth-child(3) > span.x9LZBMwk"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_url(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"❌ Ошибка запроса к {url}: {e}")
        return None

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
    """
    Парсит курс USD → EUR с XE.com.
    Возвращает сколько EUR дают за 1 USD (что равно EUR за 1 USDT)
    """
    html = fetch_url(URL_USD_EUR)
    if not html:
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Пробуем CSS-селектор
    print("🔍 USD→EUR: ищем по CSS-селектору...")
    elements = soup.select(CSS_RATE_USD_EUR)
    
    if elements:
        text = elements[0].get_text(strip=True)
        print(f"🔍 USD→EUR (CSS) текст: '{text}'")
        
        match = re.search(r"([\d.]+)", text)
        if match:
            value = float(match.group(1))
            print(f"✅ USD→EUR (CSS) результат: {value} EUR за 1 USD")
            return value
    
    # 2. Запасной вариант через регулярку
    print("🔍 USD→EUR: CSS не сработал, пробуем регулярку...")
    pattern = r'1\s*USD\s*=\s*([\d.]+)\s*EUR'
    match = re.search(pattern, html)
    if match:
        value = float(match.group(1))
        print(f"✅ USD→EUR (регулярка) результат: {value} EUR за 1 USD")
        return value
    
    print("❌ USD→EUR: курс не найден")
    return None

def get_usd_cny() -> float | None:
    """
    Парсит курс USD → CNY с Rambler.
    Возвращает сколько CNY дают за 1 USD (что равно CNY за 1 USDT)
    """
    html = fetch_url(URL_USD_CNY)
    if not html:
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Пробуем CSS-селектор
    print("🔍 USD→CNY: ищем по CSS-селектору...")
    elements = soup.select(CSS_RATE_USD_CNY)
    
    if elements:
        text = elements[0].get_text(strip=True)
        print(f"🔍 USD→CNY (CSS) текст: '{text}'")
        
        match = re.search(r"([\d.]+)", text)
        if match:
            value = float(match.group(1))
            print(f"✅ USD→CNY (CSS) результат: {value} CNY за 1 USD")
            return value
    
    # 2. Запасные варианты через регулярки
    print("🔍 USD→CNY: CSS не сработал, пробуем регулярки...")
    
    # Паттерн: "1 USD = X.XXXX CNY"
    pattern = r'1\s*USD\s*=\s*([\d.]+)\s*CNY'
    match = re.search(pattern, html)
    if match:
        value = float(match.group(1))
        print(f"✅ USD→CNY (регулярка 1) результат: {value} CNY за 1 USD")
        return value
    
    # Паттерн: "USD1 CNY6.786"
    pattern2 = r'USD1\s*CNY([\d.]+)'
    match = re.search(pattern2, html)
    if match:
        value = float(match.group(1))
        print(f"✅ USD→CNY (регулярка 2) результат: {value} CNY за 1 USD")
        return value
    
    print("❌ USD→CNY: курс не найден")
    return None

def load_old_rates():
    if os.path.exists("rates_all.json"):
        try:
            with open("rates_all.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def main():
    print("=" * 50)
    print("🔄 Обновление курсов (все валюты за 1 USDT)")
    print("=" * 50)

    rub_usdt = get_rub_usdt()
    usd_eur = get_usd_eur()     # сколько EUR за 1 USD (≈ USDT)
    usd_cny = get_usd_cny()     # сколько CNY за 1 USD (≈ USDT)

    old = load_old_rates()
    
    rates = {
        "rub_usdt": rub_usdt if rub_usdt is not None else old.get("rub_usdt"),
        "usd_eur": usd_eur if usd_eur is not None else old.get("usd_eur"),
        "usd_cny": usd_cny if usd_cny is not None else old.get("usd_cny"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    if rates["rub_usdt"] is None and rates["usd_eur"] is None and rates["usd_cny"] is None:
        print("❌ Все курсы недоступны! Выход.")
        return

    with open("rates_all.json", "w", encoding="utf-8") as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)

    print("✅ Сохранены курсы (за 1 USDT):")
    print(f"  RUB→USDT: {rates['rub_usdt']} RUB за 1 USDT")
    print(f"  USD→EUR:  {rates['usd_eur']} EUR за 1 USDT")
    print(f"  USD→CNY:  {rates['usd_cny']} CNY за 1 USDT")
    print(f"  Обновлено: {rates['updated_at']}")
    print("=" * 50)

if __name__ == "__main__":
    main()
