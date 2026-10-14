import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from parsers.common import normalize_date, guess_category

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}

BASE_URL = "https://www.hse.ru/news/"
UNIVERSITY_NAME = "ВШЭ"
PAGES_PER_CATEGORY = 10

CATEGORIES = {
    "admission/": "Абитуриентам",
    "edu/": "Образование",
    "science/": "Наука и инновации",
    "expertise/": "Сотрудничество и партнёрство",
    "community/": "Культура и творчество",
    "communication/": "Международная деятельность",
    "life/": "Студенческая жизнь",
}


def run():
    print("\nНачинаем сбор новостей ВШЭ")

    news = []
    seen_links = set()

    for path, category in CATEGORIES.items():
        for page in range(1, PAGES_PER_CATEGORY + 1):
            if page == 1:
                url = urljoin(BASE_URL, path)
            else:
                url = urljoin(BASE_URL, path + f"page{page}.html")

            try:
                response = requests.get(
                    url,
                    headers=HEADERS,
                    timeout=15
                )
                response.raise_for_status()
            except requests.RequestException as error:
                print(f"ВШЭ: ошибка запроса: {error}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select("div.post")

            if not items:
                break

            for item in items:
                heading = item.find("h2")
                link_tag = heading.find("a") if heading else None

                if not link_tag or not link_tag.get("href"):
                    continue

                title = link_tag.get_text(" ", strip=True)
                link = urljoin(url, link_tag["href"])

                if link in seen_links:
                    continue

                seen_links.add(link)

                day = item.select_one("div.post-meta__day")
                month = item.select_one("div.post-meta__month")
                year = item.select_one("div.post-meta__year")

                date = None

                if day and month and year:
                    months = {
                        "янв": "01", "фев": "02", "мар": "03",
                        "апр": "04", "май": "05", "мая": "05",
                        "июн": "06", "июл": "07", "авг": "08",
                        "сен": "09", "окт": "10", "ноя": "11",
                        "дек": "12"
                    }

                    month_number = months.get(
                        month.get_text(strip=True).lower()
                    )

                    if month_number:
                        date = (
                            f"{year.get_text(strip=True)}-"
                            f"{month_number}-"
                            f"{day.get_text(strip=True).zfill(2)}"
                        )

                if not date:
                    date = normalize_date(
                        item.get_text(" ", strip=True)
                    )

                news.append({
                    "title": title,
                    "content": title,
                    "link": link,
                    "published_date": date,
                    "category": category or guess_category(title),
                    "university": UNIVERSITY_NAME
                })

    print(f"ВШЭ: найдено новостей — {len(news)}")

    return news


if __name__ == "__main__":
    run()
