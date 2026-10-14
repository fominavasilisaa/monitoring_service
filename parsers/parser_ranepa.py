import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .common import record

BASE_URL = 'https://www.ranepa.ru'
START_URL = 'https://www.ranepa.ru/news/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
}

def parse(max_pages=5):
    results = {}
    session = requests.Session()
    session.headers.update(HEADERS)
    session.trust_env = False

    for page in range(1, max_pages + 1):
        # На РАНХиГС параметры пагинации могут передаваться через PAGEN_1
        url = START_URL if page == 1 else f'{START_URL}?PAGEN_1={page}'
        try:
            response = session.get(url, timeout=20)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f'[РАНХиГС] Не удалось загрузить страницу {page}: {exc}')
            continue

        soup = BeautifulSoup(response.text, 'html.parser')

        cards = soup.select('.nl-news__item, .news-item, .card, article')
        if not cards:
            cards = soup.select('a[href*="/news/"]')

        for card in cards:
            anchor = card if card.name == 'a' and card.get('href') else card.select_one('a[href]')
            if not anchor:
                continue
                
            href = anchor.get('href')
            if not href or '/news/' not in href:
                continue
                
            link = urljoin(BASE_URL, href).split('?')[0]
            if link in results:
                continue

            title_tag = card.select_one('.nl-card__heading, .news-item__title, h3, h2, .title')
            date_tag = card.select_one('.nl-card__date, .news-item__date, .date, time')

            title = title_tag.get_text(' ', strip=True) if title_tag else anchor.get_text(' ', strip=True)
            if not title or len(title) < 3:
                continue

            date_text = date_tag.get_text(' ', strip=True) if date_tag else None

            results[link] = record(
                title=title, 
                link=link, 
                date=date_text,
                category='Без категории', 
                university='РАНХиГС'
            )

    print(f'[РАНХиГС] Найдено карточек: {len(results)}')
    return list(results.values())