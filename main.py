import json
import time

from db import (
    init_news_db,
    init_users_db,
    save_news,
    users_with_categories,
    category_ids_for_news,
)

from parsers.parser_ranepa import parse as parse_ranepa
from parsers.parser_reu import parse as parse_reu
from parsers.parser_hse import run as parse_hse


def load_config():
    with open("config.json", "r", encoding="utf-8") as file:
        return json.load(file)


def write_send_list(new_news):
    users = users_with_categories("users.db")
    news_ids = [item["id"] for item in new_news]
    categories = category_ids_for_news("news.db", news_ids)

    with open("send_list.txt", "w", encoding="utf-8") as file:
        for user_id, user in users.items():
            matching = [
                str(news_id)
                for news_id, category_id in categories.items()
                if category_id in user["categories"]
            ]

            if matching:
                file.write(f'{user_id}: {", ".join(matching)}\n')


def run_parser(name, parser):
    try:
        print(f"\nСобираем новости: {name}")
        records = parser()

        if not records:
            print(f"{name}: новых записей для сохранения нет")
            return []

        saved = save_news("news.db", records)
        print(f"{name}: добавлено новостей — {len(saved)}")
        return saved

    except Exception as error:
        print(f"{name}: ошибка парсинга — {error}")
        return []


def main():
    config = load_config()
    interval = config.get("interval_minutes", 60)

    init_news_db("news.db")
    init_users_db("users.db")

    parsers = [
        ("РАНХиГС", parse_ranepa),
        ("РЭУ", parse_reu),
        ("ВШЭ", parse_hse),
    ]

    print("Мониторинг запущен. Первый сбор выполняется сразу.")

    try:
        while True:
            new_news = []

            for name, parser in parsers:
                new_news.extend(run_parser(name, parser))

            write_send_list(new_news)

            print(f"\nСледующая проверка через {interval} мин.")
            time.sleep(interval * 60)

    except KeyboardInterrupt:
        print("\nМониторинг остановлен.")


if __name__ == "__main__":
    main()