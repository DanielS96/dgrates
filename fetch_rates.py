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
URL_USD_EUR = "https://wise.com/ru/currency-converter/usd-to-eur-rate"
URL_USD_CNY = "https://finance.rambler.ru/calculators/converter/1-USD-CNY/"

# CSS-селекторы
CSS_RATE_RUB_USDT = "#undertable > div.m-hint > span:nth-child(2) > span:nth-child(5) > span"
CSS_RATE_USD_EUR = "#calculator > div > div > div.preset--light > div > div > div > div.m-b-3 > div > div > div._midMarketRateAmount_lbutx_138 > span:nth-child(2)"
CSS_RATE_USD_CNY = "#app > div.dTSkA6xB.commercial-branding > div > div.yP4MAOpL > div.BgJ8We0r.so0OkpgH > div.yw7YVg6D > div.N_cub_8e > div:nth-child(1) > div:nth-child(3) > span.x9LZBMwk"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_url(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        print(f"📄 Загружена страница: {url[:60]}... (размер: {len(resp.text)} символов)")
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

def get_eur_usdt() -> float | None:
    """
    Парсит курс EUR → USDT с Wise.com по CSS-селектору.
    """
    print("=" * 50)
    print("🔍 EUR→USDT: НАЧИНАЕМ ПАРСИНГ WISE (по CSS-селектору)")
    print("=" * 50)

    html = fetch_url(URL_USD_EUR)
    if not html:
        print("❌ Страница не загружена")
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Ваш точный CSS-селектор
    selector = CSS_RATE_USD_EUR
    elements = soup.select(selector)
    
    if elements:
        text = elements[0].get_text(strip=True)
        print(f"✅ Элемент найден: '{text}'")
        
        # Извлекаем число (формат может быть "0,8759" или "0.8759")
        match = re.search(r"([\d,]+)", text)
        if match:
            value_str = match.group(1).replace(",", ".")
            try:
                value = float(value_str)
                print(f"✅ EUR→USDT: {value} EUR за 1 USDT")
                return value
            except ValueError as e:
                print(f"❌ Ошибка преобразования '{value_str}': {e}")
                return None
        else:
            print("❌ Число не найдено в тексте")
            return None
    else:
        print("❌ Элемент не найден по селектору")
        return None

def get_cny_usdt() -> float | None:
    """Парсит курс USD → CNY с Rambler."""
    html = fetch_url(URL_USD_CNY)
    if not html:
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Пробуем CSS-селектор
    print("🔍 CNY→USDT: ищем по CSS-селектору...")
    elements = soup.select(CSS_RATE_USD_CNY)
    
    if elements:
        text = elements[0].get_text(strip=True)
        print(f"🔍 CNY→USDT (CSS) текст: '{text}'")
        
        match = re.search(r"([\d.]+)", text)
        if match:
            value = float(match.group(1))
            print(f"✅ CNY→USDT (CSS) результат: {value} CNY за 1 USDT")
            return value
    
    # 2. Запасные варианты через регулярки
    print("🔍 CNY→USDT: CSS не сработал, пробуем регулярки...")
    
    # Паттерн: "1 USD = X.XXXX CNY"
    pattern = r'1\s*USD\s*=\s*([\d.]+)\s*CNY'
    match = re.search(pattern, html)
    if match:
        value = float(match.group(1))
        print(f"✅ CNY→USDT (регулярка 1) результат: {value} CNY за 1 USDT")
        return value
    
    # Паттерн: "USD1 CNY6.786"
    pattern2 = r'USD1\s*CNY([\d.]+)'
    match = re.search(pattern2, html)
    if match:
        value = float(match.group(1))
        print(f"✅ CNY→USDT (регулярка 2) результат: {value} CNY за 1 USDT")
        return value
    
    print("❌ CNY→USDT: курс не найден")
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
    print("🔄 Обновление курсов All Rates")
    print("=" * 50)

    # Получаем курсы
    rub_usdt = get_rub_usdt()
    eur_usdt = get_eur_usdt()
    cny_usdt = get_cny_usdt()

    # Диагностика
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ПАРСИНГА:")
    print(f"  RUB→USDT: {repr(rub_usdt)}")
    print(f"  EUR→USDT: {repr(eur_usdt)}")
    print(f"  CNY→USDT: {repr(cny_usdt)}")
    print("=" * 50)

    old = load_old_rates()
    
    rates = {
        "rub_usdt": rub_usdt if rub_usdt is not None else old.get("rub_usdt"),
        "eur_usdt": eur_usdt if eur_usdt is not None else old.get("eur_usdt"),
        "cny_usdt": cny_usdt if cny_usdt is not None else old.get("cny_usdt"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    if rates["rub_usdt"] is None and rates["eur_usdt"] is None and rates["cny_usdt"] is None:
        print("❌ Все курсы недоступны! Выход.")
        return

    with open("rates_all.json", "w", encoding="utf-8") as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)

    print("✅ Сохранены курсы (за 1 USDT):")
    print(f"  RUB→USDT: {rates['rub_usdt']} RUB")
    print(f"  EUR→USDT: {rates['eur_usdt']} EUR")
    print(f"  CNY→USDT: {rates['cny_usdt']} CNY")
    print(f"  Обновлено: {rates['updated_at']}")
    print("=" * 50)

if __name__ == "__main__":
    main()
