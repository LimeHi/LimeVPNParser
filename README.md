# 🔒 VPN Config Parser

Автоматический сборщик бесплатных VPN конфигов с проверкой через **xray-core** и публикацией на GitHub. Управление через Telegram-бота.

## ✨ Возможности

- 🔍 Сбор конфигов из 20+ GitHub-источников
- ✅ Проверка работоспособности через **xray-core** (реальное подключение)
- 🌍 Автоматическое определение страны + флаг + название по-русски
- 📤 Публикация на ваш GitHub (plain + base64 + по протоколам)
- 🤖 Telegram-бот для полного контроля
- ⏰ Обновление каждые 6 часов
- 🚀 Деплой на **Railway** одной кнопкой

## 📦 Протоколы

| Протокол | Поддержка |
|---|---|
| VMess | ✅ |
| VLESS | ✅ (включая REALITY) |
| Trojan | ✅ |
| Shadowsocks | ✅ |
| Hysteria2 | ✅ |

## 🚀 Деплой на Railway

### 1. Подготовка

**Создай Telegram-бота:**
1. Напиши [@BotFather](https://t.me/BotFather) → `/newbot`
2. Сохрани `TELEGRAM_BOT_TOKEN`
3. Узнай свой Telegram ID через [@userinfobot](https://t.me/userinfobot)

**Создай GitHub токен:**
1. GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained
2. Дай права: `Contents: Read & Write` на нужный репозиторий
3. Сохрани токен

**Создай GitHub репозиторий** для хранения конфигов (можно публичный).

### 2. Деплой

```bash
# Клонируй этот репо
git clone <this-repo>
cd vpn-parser

# Запушь в свой GitHub
git remote set-url origin https://github.com/YOUR_USERNAME/vpn-parser
git push -u origin main
```

В Railway:
1. New Project → Deploy from GitHub repo
2. Выбери репозиторий
3. Перейди в **Variables** и добавь все переменные из `.env.example`
4. Deploy!

### 3. Переменные окружения Railway

| Переменная | Описание | Пример |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен бота | `123456:ABC...` |
| `TELEGRAM_ADMIN_ID` | Ваш Telegram ID | `123456789` |
| `GITHUB_TOKEN` | GitHub токен | `ghp_xxx...` |
| `GITHUB_REPO` | Репо для конфигов | `user/free-vpn` |
| `GITHUB_BRANCH` | Ветка | `main` |
| `UPDATE_INTERVAL_HOURS` | Интервал в часах | `6` |
| `MAX_CONFIGS` | Макс. конфигов | `100` |
| `MAX_WORKERS` | Параллельных проверок | `30` |
| `CHECK_TIMEOUT` | Таймаут проверки (сек) | `8` |
| `CHANNEL_TAG` | Тег в названии | `@YourChannel` |

## 🤖 Команды бота

| Команда | Описание |
|---|---|
| `/status` | Статус, статистика последнего запуска |
| `/run` | Запустить обновление вручную |
| `/stop` | Остановить планировщик |
| `/resume` | Запустить планировщик |
| `/logs [N]` | Последние N строк лога |
| `/sources` | Список источников |
| `/add <url>` | Добавить источник |
| `/remove <N>` | Удалить источник |
| `/reset_sources` | Вернуть источники по умолчанию |
| `/settings` | Текущие настройки |

## 📁 Структура файлов на GitHub

```
configs/
  all.txt          ← все конфиги (plain text)
  all_b64.txt      ← все конфиги в base64 (ссылка для подписки)
  vmess.txt
  vless.txt
  trojan.txt
  shadowsocks.txt
  hysteria2.txt
README.md          ← статистика и инструкция
```

## 📲 Использование

Ссылка для подписки в клиенте (например v2rayNG):
```
https://raw.githubusercontent.com/YOUR_USERNAME/free-vpn/main/configs/all_b64.txt
```

## 🏗 Локальный запуск

```bash
pip install -r requirements.txt
cp .env.example .env
# Заполни .env

# Убедись что xray установлен:
# https://github.com/XTLS/Xray-core/releases

python main.py
```

## 📜 Формат имён

```
1.🇧🇷Бразилия | @LimeVPNFREE
2.🇩🇪Германия | @LimeVPNFREE
3.🇺🇸США | @LimeVPNFREE
```
