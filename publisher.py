"""
publisher.py  –  публикует конфиги на GitHub.

Структура файлов в репозитории:
  configs/all.txt          – все рабочие конфиги (plain text)
  configs/all_b64.txt      – те же конфиги в base64 (для клиентов)
  configs/vmess.txt        – только VMess
  configs/vless.txt        – только VLESS
  configs/trojan.txt       – только Trojan
  configs/shadowsocks.txt  – только Shadowsocks
  configs/hysteria2.txt    – только Hysteria2
  README.md                – статистика + инструкция
"""

import base64
import logging
from datetime import datetime, timezone

from github import Github, GithubException

import config as cfg

logger = logging.getLogger(__name__)

PROTO_MAP = {
    "vmess":        "vmess",
    "vless":        "vless",
    "trojan":       "trojan",
    "ss":           "shadowsocks",
    "shadowsocks":  "shadowsocks",
    "hysteria2":    "hysteria2",
    "hy2":          "hysteria2",
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
    lines = [
        "# 🔒 Free VPN Configs",
        "",
        f"> Обновлено: **{ts} UTC**",
        "",
        "## 📊 Статистика",
        "",
        f"| Всего рабочих | VMess | VLESS | Trojan | Shadowsocks | Hysteria2 |",
        f"|:---:|:---:|:---:|:---:|:---:|:---:|",
        f"| {len(uris)} "
        f"| {len(buckets.get('vmess', []))} "
        f"| {len(buckets.get('vless', []))} "
        f"| {len(buckets.get('trojan', []))} "
        f"| {len(buckets.get('shadowsocks', []))} "
        f"| {len(buckets.get('hysteria2', []))} |",
        "",
        "## 📥 Подписка (скопируй ссылку в клиент)",
        "",
        f"| Файл | Описание |",
        f"|---|---|",
        f"| [all_b64.txt](configs/all_b64.txt) | Все протоколы (base64) |",
        f"| [all.txt](configs/all.txt) | Все протоколы (plain text) |",
        f"| [vmess.txt](configs/vmess.txt) | VMess |",
        f"| [vless.txt](configs/vless.txt) | VLESS |",
        f"| [trojan.txt](configs/trojan.txt) | Trojan |",
        f"| [shadowsocks.txt](configs/shadowsocks.txt) | Shadowsocks |",
        f"| [hysteria2.txt](configs/hysteria2.txt) | Hysteria2 |",
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
        "_Автоматически собирается каждые 6 часов из открытых источников._",
    ]
    return "\n".join(lines)


def publish(uris: list[str]) -> bool:
    """
    Публикует конфиги в GitHub.
    Возвращает True при успехе.
    """
    if not cfg.GITHUB_TOKEN or not cfg.GITHUB_REPO:
        logger.error("GitHub credentials not set")
        return False

    try:
        gh    = Github(cfg.GITHUB_TOKEN)
        repo  = gh.get_repo(cfg.GITHUB_REPO)
        ts    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        msg   = f"🔄 Update configs – {ts} UTC"

        buckets  = _split_by_proto(uris)
        all_text = "\n".join(uris) + "\n"

        files: dict[str, str] = {
            "configs/all.txt":          all_text,
            "configs/all_b64.txt":      _b64(all_text),
            "configs/vmess.txt":        "\n".join(buckets["vmess"]) + "\n",
            "configs/vless.txt":        "\n".join(buckets["vless"]) + "\n",
            "configs/trojan.txt":       "\n".join(buckets["trojan"]) + "\n",
            "configs/shadowsocks.txt":  "\n".join(buckets["shadowsocks"]) + "\n",
            "configs/hysteria2.txt":    "\n".join(buckets["hysteria2"]) + "\n",
            "README.md":                _readme(uris, buckets, ts),
        }

        for path, content in files.items():
            try:
                existing = repo.get_contents(path, ref=cfg.GITHUB_BRANCH)
                repo.update_file(path, msg, content, existing.sha,
                                 branch=cfg.GITHUB_BRANCH)
                logger.info("Updated %s", path)
            except GithubException:
                repo.create_file(path, msg, content, branch=cfg.GITHUB_BRANCH)
                logger.info("Created %s", path)

        logger.info("Published %d configs to %s", len(uris), cfg.GITHUB_REPO)
        return True

    except Exception as e:
        logger.error("Publish failed: %s", e)
        return False
