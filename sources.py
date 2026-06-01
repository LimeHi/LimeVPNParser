"""
sources.py  –  загружает список источников из sources.txt

Формат sources.txt: одна ссылка на строку, строки с # игнорируются.
Файл можно редактировать прямо на GitHub — при следующем запуске
парсер подхватит изменения автоматически.
"""

import logging
import os

logger = logging.getLogger(__name__)

SOURCES_FILE = os.path.join(os.path.dirname(__file__), "sources.txt")


def load_sources() -> list[str]:
    """Читает sources.txt и возвращает список URL."""
    if not os.path.exists(SOURCES_FILE):
        logger.warning("sources.txt not found at %s", SOURCES_FILE)
        return []
    result = []
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                result.append(line)
    logger.info("Loaded %d sources from sources.txt", len(result))
    return result


# Runtime-mutable list (бот может добавлять/удалять на лету)
sources: list[str] = load_sources()


def save_sources() -> None:
    """Сохраняет текущий список обратно в sources.txt."""
    with open(SOURCES_FILE, "w", encoding="utf-8") as f:
        f.write("# VPN Config Sources\n")
        f.write("# Одна ссылка на строку. Строки с # игнорируются.\n\n")
        for url in sources:
            f.write(url + "\n")
    logger.info("Saved %d sources to sources.txt", len(sources))
