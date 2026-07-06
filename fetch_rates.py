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

CSS_RATE_RUB_USDT = "#undertable > div.m-hint > span:nth-child(2) > span:nth-child(5) > span"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ------------------------------
# Вспомогательные функции
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
# Парсеры для каждого курса
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
    match = re.search(r"([\d.,]+)", text)
    if not match:
        return None
    
    rate_str = match.group(1).replace(",", ".")
    try:
        return float(rate_str)
    except ValueError:
        return None

def get_usd_eur() -> float | None:
    """Парсит курс USD → EUR с XE.com."""
    html = fetch_url(URL_USD_EUR)
    if not html:
        return None
    
    # Ищем паттерн: 1 USD = X.XXXXXX EUR
    match = re.search(r'1\s*USD\s*=\s*([\d.]+)\s*EUR', html)
    if match:
        return float(match.group(1))
    else:
        print("❌ USD→EUR: курс не найден")
        return None

def get_usd_cny() -> float | None:
    """Парсит курс USD → CNY с Rambler."""
    html = fetch_url(URL_USD_CNY)
    if not html:
        return None
    
    # Ищем паттерн: 1 USD = X.XXXX CNY
    match = re.search(r'1\s*USD\s*=\s*([\d.]+)\s*CNY', html)
    if match:
        return float(match.group(1))
    else:
        print("❌ USD→CNY: курс не найден")
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
    print("🔄 Начинаем обновление курсов")
    print("=" * 50)

    # Получаем текущие курсы (с обработкой ошибок)
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
