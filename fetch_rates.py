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
    Парсит курс EUR → USDT с Wise.com.
    Полная диагностика с сохранением результатов.
    """
    print("=" * 50)
    print("🔍 EUR→USDT: НАЧИНАЕМ ПАРСИНГ WISE")
    print("=" * 50)

    # Шаг 1: Загружаем страницу
    print("\n🔍 Шаг 1: загружаем страницу...")
    html = fetch_url(URL_USD_EUR)
    if not html:
        print("❌ Шаг 1: страница не загружена")
        return None
    print("✅ Шаг 1: страница загружена")
    
    # Шаг 2: Ищем паттерн
    print("\n🔍 Шаг 2: ищем паттерн '1 USD = X,XXXX EUR'...")
    pattern = r'1\s*USD\s*=\s*([\d,]+)\s*EUR'
    match = re.search(pattern, html)
    
    if not match:
        print("❌ Шаг 2: паттерн не найден")
        return None
    
    raw_value = match.group(1)
    print(f"✅ Шаг 2: найден raw_value = '{raw_value}'")
    
    # Шаг 3: Преобразуем запятую в точку
    print(f"\n🔍 Шаг 3: преобразуем запятую в точку...")
    value_str = raw_value.replace(",", ".")
    print(f"   raw_value = '{raw_value}'")
    print(f"   value_str = '{value_str}'")
    
    # Шаг 4: Преобразуем в число
    print(f"\n🔍 Шаг 4: преобразуем в число...")
    try:
        value = float(value_str)
        print(f"✅ Шаг 4: успешно! value = {value}")
        print(f"   Тип: {type(value)}")
        print(f"   repr: {repr(value)}")
        
        # СОХРАНЯЕМ РЕЗУЛЬТАТ В ОТДЕЛЬНЫЙ ФАЙЛ ДЛЯ ДИАГНОСТИКИ
        debug_data = {
            "raw_value": raw_value,
            "value_str": value_str,
            "value": value,
            "value_type": str(type(value)),
            "value_repr": repr(value)
        }
        with open("debug_eur.json", "w", encoding="utf-8") as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2)
        print("📄 debug_eur.json сохранён")
        
        return value
    except ValueError as e:
        print(f"❌ Шаг 4: ошибка преобразования: {e}")
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
    print("🔄 Обновление курсов All Rates (с диагностикой)")
    print("=" * 50)

    # Получаем курсы
    rub_usdt = get_rub_usdt()
    eur_usdt = get_eur_usdt()
    cny_usdt = get_cny_usdt()

    # ДИАГНОСТИКА: точные значения
    print("\n" + "=" * 50)
    print("📊 ТОЧНЫЕ ЗНАЧЕНИЯ ИЗ ПАРСИНГА:")
    print(f"  RUB→USDT: {repr(rub_usdt)} (тип: {type(rub_usdt)})")
    print(f"  EUR→USDT: {repr(eur_usdt)} (тип: {type(eur_usdt)})")
    print(f"  CNY→USDT: {repr(cny_usdt)} (тип: {type(cny_usdt)})")
    print("=" * 50)

    old = load_old_rates()
    
    # Формируем объект с курсами
    rates = {
        "rub_usdt": rub_usdt if rub_usdt is not None else old.get("rub_usdt"),
        "eur_usdt": eur_usdt if eur_usdt is not None else old.get("eur_usdt"),
        "cny_usdt": cny_usdt if cny_usdt is not None else old.get("cny_usdt"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    # ДИАГНОСТИКА: что попадает в JSON (пошагово)
    print("\n" + "=" * 50)
    print("📝 ПОШАГОВАЯ ПРОВЕРКА JSON:")
    print(f"  rates['eur_usdt'] = {repr(rates['eur_usdt'])}")
    print(f"  rates['eur_usdt'] тип: {type(rates['eur_usdt'])}")
    
    # Пробуем преобразовать в JSON
    try:
        json_str = json.dumps(rates, ensure_ascii=False, indent=2)
        print("✅ JSON успешно создан:")
        print(json_str)
    except Exception as e:
        print(f"❌ Ошибка при создании JSON: {e}")
    
    print("=" * 50)

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
