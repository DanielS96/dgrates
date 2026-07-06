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
# Ваш точный селектор для Wise
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
    Полностью переписанная логика с подробной отладкой.
    """
    print("=" * 40)
    print("🔍 EUR→USDT: НАЧИНАЕМ ПАРСИНГ WISE")
    print("=" * 40)
    
    # 1. Загружаем страницу
    html = fetch_url(URL_USD_EUR)
    if not html:
        print("❌ EUR→USDT: страница не загружена")
        return None
    
    # 2. Сохраняем HTML для отладки (первые 500 символов)
    print(f"📄 Первые 500 символов HTML:")
    print("-" * 40)
    print(html[:500])
    print("-" * 40)
    
    # 3. Парсим с BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    
    # 4. Ищем по вашему селектору
    print(f"🔍 EUR→USDT: ищем по селектору:")
    print(f"   {CSS_RATE_USD_EUR}")
    
    elements = soup.select(CSS_RATE_USD_EUR)
    
    # 5. Проверяем результат
    if not elements:
        print("❌ EUR→USDT: элемент НЕ НАЙДЕН по селектору")
        
        # Пробуем найти похожие элементы для отладки
        print("🔍 EUR→USDT: ищем все span с классом _midMarketRateAmount...")
        all_spans = soup.find_all('span', class_=re.compile(r'_midMarketRateAmount'))
        print(f"   Найдено span с таким классом: {len(all_spans)}")
        for i, span in enumerate(all_spans[:3]):
            print(f"   span {i+1}: '{span.get_text(strip=True)}'")
        
        # Пробуем найти по атрибуту data-testid
        print("🔍 EUR→USDT: ищем span с data-testid='mid-market-rate'")
        testid_spans = soup.select('span[data-testid="mid-market-rate"]')
        print(f"   Найдено: {len(testid_spans)}")
        for i, span in enumerate(testid_spans[:3]):
            print(f"   span {i+1}: '{span.get_text(strip=True)}'")
        
        return None
    
    # 6. Элемент найден — извлекаем текст
    text = elements[0].get_text(strip=True)
    print(f"✅ EUR→USDT: элемент НАЙДЕН!")
    print(f"🔍 EUR→USDT: текст элемента: '{text}'")
    print(f"🔍 EUR→USDT: длина текста: {len(text)} символов")
    print(f"🔍 EUR→USDT: repr текста: {repr(text)}")
    
    # 7. Извлекаем число из текста
    # Пробуем разные паттерны
    patterns = [
        r'([\d,]+\.?[\d]*)',  # 0,8760 или 0.8760
        r'([\d.]+)',          # 0.8760
        r'([\d,]+)',          # 0,8760
    ]
    
    for i, pattern in enumerate(patterns, 1):
        match = re.search(pattern, text)
        if match:
            value_str = match.group(1).replace(",", ".")
            try:
                value = float(value_str)
                print(f"✅ EUR→USDT: паттерн {i} сработал: {value_str} → {value}")
                return value
            except ValueError as e:
                print(f"⚠️ EUR→USDT: не удалось преобразовать '{value_str}': {e}")
    
    print("❌ EUR→USDT: не удалось извлечь число из текста")
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

    rub_usdt = get_rub_usdt()
    eur_usdt = get_eur_usdt()
    cny_usdt = get_cny_usdt()

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
