import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .common import record

BASE_URL = 'https://www.rea.ru'
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; UniversityNewsMonitor/1.0)'}
CATEGORY_MAP = {
    'Наука': 'Наука и инновации', 'Спорт': 'Спорт', 'Абитуриентам': 'Абитуриентам',
    'В мире': 'Объявления и события', 'Образование': 'Образование',
    'Студенчество': 'Студенческая жизнь', 'Международная деятельность': 'Международная деятельность',
    'Проекты': 'Сотрудничество и партнёрство', 'Университет': 'Культура и творчество',
}

def parse(max_pages=10):
    results = {}
    session = requests.Session()
    session.headers.update(HEADERS)
    for page in range(1, max_pages + 1):
        url = f'{BASE_URL}/news?tree-content-path=news&page={page}&per-page=12'
        try:
            response = session.get(url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f'[РЭУ] Не удалось загрузить список, страница {page}: {exc}')
            continue
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('a.catalog__item-content')
        if not items:
            if page == 1:
                print('[РЭУ] Карточки не найдены: возможно, сайт изменил HTML-разметку.')
            break
        for item in items:
            title_tag = item.select_one('.catalog__item-title')
            title = title_tag.get_text(' ', strip=True) if title_tag else item.get_text(' ', strip=True)
            href = item.get('href')
            if not title or not href:
                continue
            link = urljoin(BASE_URL, href).split('?')[0]
            date_tag = item.select_one('.catalog__item-date')
            date_text = date_tag.get_text(' ', strip=True) if date_tag else None
            content, category = '', 'Без категории'
            try:
                detail_response = session.get(link, timeout=15)
                detail_response.raise_for_status()
                detail = BeautifulSoup(detail_response.text, 'html.parser')
                content_tag = detail.select_one('.catalog-detail__text')
                if content_tag:
                    content = content_tag.get_text(' ', strip=True)
                category_tag = detail.select_one('li.catalog-detail__tag')
                if category_tag:
                    category = CATEGORY_MAP.get(category_tag.get_text(' ', strip=True), 'Без категории')
            except requests.RequestException as exc:
                print(f'[РЭУ] Не удалось загрузить текст новости {link}: {exc}')
            results[link] = record(title, link, date_text, content, category, 'РЭУ')
    print(f'[РЭУ] Найдено карточек: {len(results)}')
    return list(results.values())
