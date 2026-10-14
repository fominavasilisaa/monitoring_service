from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import re

MONTHS = {'января':1, 'февраля':2, 'марта':3, 'апреля':4, 'мая':5, 'июня':6, 'июля':7, 'августа':8, 'сентября':9, 'октября':10, 'ноября':11, 'декабря':12}

def normalize_date(value):
    if not value:
        return 'Не указана'
    text = ' '.join(value.replace(',', ' ').split()).strip()
    if text.lower() in ('сегодня', 'today'):
        return datetime.now().strftime('%Y-%m-%d')
    if text.lower() in ('вчера', 'yesterday'):
        return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    m = re.search(r'(\d{1,2})\s+([а-яё]+)\s+(\d{4})', text, re.I)
    if m and m.group(2).lower() in MONTHS:
        try:
            return datetime(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))).strftime('%Y-%m-%d')
        except ValueError:
            pass
    for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%d %m %Y'):
        try:
            return datetime.strptime(text, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    try:
        return parsedate_to_datetime(text).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return text or 'Не указана'

def guess_category(text, category_map=None):
    if not text or not category_map:
        return 'Без категории'
    text_lower = text.lower()
    for key, category in category_map.items():
        if key.lower() in text_lower:
            return category
    return 'Без категории'

def record(title, link, date=None, content='', category='Без категории', university=''):
    return {
        'title': title.strip() if title else 'Без заголовка', 
        'link': link,
        'published_date': normalize_date(date), 
        'content': content.strip() if content else '',
        'category': category, 
        'university': university
    }