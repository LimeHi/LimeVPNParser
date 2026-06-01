"""
namer.py  –  присваивает имена конфигам.

Формат: {index}.{flag}{страна} | {channel_tag}
Пример: 1.🇧🇷Бразилия | @LimeVPNFREE

Если в конфиге уже есть фрагмент (#название) – сохраняем канал-источник.
"""

import urllib.parse
import logging

from geo import get_country
from parser import extract_host
import config as cfg

logger = logging.getLogger(__name__)


def _extract_fragment(uri: str) -> str:
    """Возвращает фрагмент URI (#...) или пустую строку."""
    try:
        return urllib.parse.unquote(uri.split("#", 1)[1]) if "#" in uri else ""
    except Exception:
        return ""


def _strip_fragment(uri: str) -> str:
    return uri.split("#")[0]


def _guess_channel(fragment: str) -> str:
    """Если во фрагменте есть @channel – вернуть его."""
    for part in fragment.split():
        if part.startswith("@"):
            return part
    return cfg.CHANNEL_TAG


def name_configs(uris: list[str]) -> list[str]:
    """
    Принимает список URI, возвращает список с добавленными именами (#fragment).
    Геолукап делается по IP/хосту каждого конфига.
    """
    named: list[str] = []
    for idx, uri in enumerate(uris, start=1):
        base_uri  = _strip_fragment(uri)
        fragment  = _extract_fragment(uri)
        channel   = _guess_channel(fragment)

        host = extract_host(base_uri)
        if host:
            flag, country = get_country(host)
        else:
            flag, country = "🌐", "Неизвестно"

        name = f"{idx}.{flag}{country} | {channel}"
        named.append(f"{base_uri}#{urllib.parse.quote(name)}")
        logger.debug("Named %d: %s", idx, name)

    return named
