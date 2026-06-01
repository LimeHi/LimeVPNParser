"""
parser.py  –  загружает конфиги из источников.

Поддерживаемые форматы:
  • plain-text  (одна ссылка на строку)
  • base64-encoded (весь файл или построчно)

Поддерживаемые протоколы:
  vmess:// | vless:// | trojan:// | ss:// | hysteria2:// | hy2://
"""

import base64
import logging
import re
from typing import Iterator

import requests

logger = logging.getLogger(__name__)

SUPPORTED = re.compile(
    r"(vmess|vless|trojan|ss|hysteria2|hy2)://[^\s]+"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; VPNParser/1.0)",
}


def _try_b64(data: str) -> str:
    """Пробует декодировать строку из base64; возвращает исходное если не вышло."""
    try:
        padded = data + "=" * (-len(data) % 4)
        decoded = base64.b64decode(padded).decode("utf-8", errors="ignore")
        # Если декодированное содержит протоколы – успех
        if SUPPORTED.search(decoded):
            return decoded
    except Exception:
        pass
    return data


def _extract_configs(text: str) -> list[str]:
    """Извлекает все VPN URI из текста."""
    # 1. Попробуем декодировать как base64 целиком
    text = _try_b64(text.strip())

    # 2. Построчно декодируем base64 (некоторые источники кодируют каждую строку)
    lines = text.splitlines()
    decoded_lines: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        decoded_lines.append(_try_b64(line))

    full = "\n".join(decoded_lines)
    configs = SUPPORTED.findall(full)
    # findall возвращает группы (только схему), нам нужна полная строка
    return SUPPORTED.findall_full(full) if hasattr(SUPPORTED, "findall_full") else _full_matches(full)


def _full_matches(text: str) -> list[str]:
    return [m.group(0) for m in SUPPORTED.finditer(text)]


def fetch_source(url: str, timeout: int = 15) -> list[str]:
    """Скачивает один источник и возвращает список VPN URI."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        configs = _full_matches(_try_b64(resp.text.strip()))
        logger.info("Source %s → %d configs", url, len(configs))
        return configs
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return []


def fetch_all(sources: list[str]) -> list[str]:
    """Скачивает все источники и возвращает дедуплицированный список URI."""
    seen: set[str] = set()
    result: list[str] = []
    for url in sources:
        for cfg in fetch_source(url):
            if cfg not in seen:
                seen.add(cfg)
                result.append(cfg)
    logger.info("Total unique configs fetched: %d", len(result))
    return result


# ── Парсинг URI для получения хоста ──────────────────────────────────────────

import json
import urllib.parse


def extract_host(uri: str) -> str | None:
    """Извлекает hostname/IP из конфига для геолукапа."""
    try:
        scheme = uri.split("://")[0].lower()

        if scheme == "vmess":
            b64 = uri[len("vmess://"):]
            padded = b64 + "=" * (-len(b64) % 4)
            data = json.loads(base64.b64decode(padded).decode())
            return data.get("add") or data.get("host")

        elif scheme in ("vless", "trojan"):
            parsed = urllib.parse.urlparse(uri)
            return parsed.hostname

        elif scheme == "ss":
            # ss://BASE64@host:port#name  or  ss://BASE64#name
            rest = uri[len("ss://"):]
            rest = rest.split("#")[0]
            if "@" in rest:
                return rest.split("@")[-1].split(":")[0]
            else:
                decoded = base64.b64decode(rest + "==").decode()
                return decoded.split("@")[-1].split(":")[0]

        elif scheme in ("hysteria2", "hy2"):
            parsed = urllib.parse.urlparse(uri)
            return parsed.hostname

    except Exception:
        pass
    return None
