"""
publisher.py  –  публикует конфиги на GitHub.

Структура файлов в репозитории:
  LimeVPN.txt   – все рабочие конфиги в base64 (ссылка для подписки)
  README.md     – статистика + инструкция
"""

import base64
import logging
from datetime import datetime, timezone

from github import Github, GithubException

import config as cfg

logger = logging.getLogger(__name__)

PROTO_MAP = {
    "vmess":       "vmess",
    "vless":       "vless",
    "trojan":      "trojan",
    "ss":          "shadowsocks",
    "shadowsocks": "shadowsocks",
    "hysteria2":   "hysteria2",
    "hy2":         "hysteria2",
}


def _split_by_proto(uris: list[str]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {p: [] for p in set(PROTO_MAP.values())}
    for uri in uris:
        scheme = uri.split("://")[0].lower()
        proto  = PROTO_MAP.get(scheme)
        if proto:
            buckets[proto].append(uri)
    return buckets


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def _readme(uris: list[str], buckets: dict[str, list[str]], ts: str) -> str:
    repo_url = f"https://raw.githubusercontent.com/{cfg.GITHUB_REPO}/{cfg.GITHUB_BRANCH}/LimeVPN.txt"
    lines = [
        "# 🔒 LimeVPN — Free Configs",
        "",
        f"> Обновлено: **{ts} UTC**",
        "",
        "## 📊 Статистика",
        "",
        "| Всего | VMess | VLESS | Trojan | Shadowsocks | Hysteria2 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|",
        f"| {len(uris)}"
        f" | {len(buckets.get('vmess', []))}"
        f" | {len(buckets.get('vless', []))}"
        f" | {len(buckets.get('trojan', []))}"
        f" | {len(buckets.get('shadowsocks', []))}"
        f" | {len(buckets.get('hysteria2', []))} |",
        "",
        "## 📥 Ссылка для подписки",
        "",
        f"```",
        repo_url,
        f"```",
        "",
        "Вставь эту ссылку в клиент (v2rayNG, Hiddify, Shadowrocket и др.)",
        "",
        "> ⚠️ Если клиент не принимает plain text — попробуй скопировать конфиги вручную из файла.",
        "",
        "## 🛠 Совместимые клиенты",
        "",
        "- **Android**: v2rayNG, NekoBox",
        "- **iOS**: Shadowrocket, Streisand",
        "- **Windows**: v2rayN, Hiddify",
        "- **macOS**: FoXray, Hiddify",
        "- **Linux**: v2ray, Xray",
        "",
        "---",
        "_Автоматически обновляется каждые 6 часов._",
    ]
    return "\n".join(lines)


def _upsert(repo, path: str, content: str, msg: str) -> None:
    """Создаёт или обновляет файл в репозитории."""
    try:
        existing = repo.get_contents(path, ref=cfg.GITHUB_BRANCH)
        repo.update_file(path, msg, content, existing.sha, branch=cfg.GITHUB_BRANCH)
        logger.info("Updated %s", path)
    except GithubException:
        repo.create_file(path, msg, content, branch=cfg.GITHUB_BRANCH)
        logger.info("Created %s", path)


def publish(uris: list[str]) -> bool:
    """Публикует конфиги в GitHub. Возвращает True при успехе."""
    if not cfg.GITHUB_TOKEN or not cfg.GITHUB_REPO:
        logger.error("GitHub credentials not set")
        return False

    try:
        gh      = Github(cfg.GITHUB_TOKEN)
        repo    = gh.get_repo(cfg.GITHUB_REPO)
        ts      = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        msg     = f"🔄 Update {len(uris)} configs – {ts} UTC"
        buckets = _split_by_proto(uris)

        all_text = "\n".join(uris) + "\n"

        _upsert(repo, "LimeVPN.txt", all_text, msg)
        _upsert(repo, "README.md",   _readme(uris, buckets, ts), msg)

        logger.info("Published %d configs → LimeVPN.txt", len(uris))
        return True

    except Exception as e:
        logger.error("Publish failed: %s", e)
        return False
