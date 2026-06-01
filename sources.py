"""
sources.py  –  список источников конфигов.
Каждый элемент – прямая ссылка на файл с конфигами (base64 или plain-text).
Список хранится в памяти; Telegram-бот позволяет добавлять/удалять источники на лету.
"""

DEFAULT_SOURCES: list[str] = [
    # ── barry-far / V2ray-Configs ───────────────────────────────────────
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub3.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub4.txt",

    # ── mahdibland / V2RayAggregator ───────────────────────────────────
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/vmess.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/vless.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/trojan.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/shadowsocks.txt",

    # ── yebekhe / TelegramV2rayCollector ──────────────────────────────
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/vmess",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/vless",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/trojan",

    # ── soroushmirzaei / telegram-configs-collector ────────────────────
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/protocols/vmess",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/protocols/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/protocols/trojan",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/protocols/shadowsocks",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/protocols/hysteria2",

    # ── mheidari98 / proxy ────────────────────────────────────────────
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/all",

    # ── Pawdroid / Free-servers ───────────────────────────────────────
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",

    # ── ermaozi / get_subscribe ───────────────────────────────────────
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
]

# Runtime-mutable list (bot can add/remove)
sources: list[str] = list(DEFAULT_SOURCES)
