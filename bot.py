"""
bot.py  –  Telegram-бот для управления парсером.

Команды:
  /start          – приветствие
  /status         – текущий статус и статистика
  /run            – запустить обновление вручную
  /stop           – остановить планировщик
  /resume         – возобновить планировщик
  /logs [N]       – последние N строк лога (по умолчанию 20)
  /sources        – список источников
  /add <url>      – добавить источник
  /remove <N>     – удалить источник по номеру
  /reset_sources  – вернуть источники по умолчанию
  /settings       – текущие настройки
"""

import asyncio
import logging
import threading
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

import config as cfg
import sources as src
from pipeline import run_pipeline
from sources import DEFAULT_SOURCES
from state import state

logger = logging.getLogger(__name__)

_scheduler_running = False
_scheduler_task = None
_event_loop = None   # сохраняем event loop для вызовов из потоков


# ── Хелперы ───────────────────────────────────────────────────────────────────

def _admin_only(func):
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if update.effective_user and update.effective_user.id != cfg.TELEGRAM_ADMIN_ID:
            await update.message.reply_text("⛔ Нет доступа")
            return
        return await func(update, ctx)
    wrapper.__name__ = func.__name__
    return wrapper


def _run_pipeline_thread(app: Application) -> None:
    """Запускает pipeline в отдельном потоке, уведомляет через бот."""
    def _notify(msg: str):
        if _event_loop and not _event_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                app.bot.send_message(chat_id=cfg.TELEGRAM_ADMIN_ID, text=msg),
                _event_loop,
            )

    thread = threading.Thread(target=run_pipeline, args=(_notify,), daemon=True)
    thread.start()


# ── Команды ───────────────────────────────────────────────────────────────────

@_admin_only
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *VPN Config Parser Bot*\n\n"
        "Я собираю бесплатные VPN конфиги, проверяю их через Xray и публикую на GitHub.\n\n"
        "📋 *Команды:*\n"
        "/status — статус и статистика\n"
        "/run — запустить обновление\n"
        "/stop — остановить планировщик\n"
        "/resume — запустить планировщик\n"
        "/logs — последние логи\n"
        "/sources — список источников\n"
        "/add <url> — добавить источник\n"
        "/remove <N> — удалить источник\n"
        "/settings — настройки"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


@_admin_only
async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = state
    last_run    = s.last_run.strftime("%Y-%m-%d %H:%M:%S") if s.last_run else "никогда"
    status_icon = "🟢" if s.last_ok else "🔴"
    running_str = "⚙️ Выполняется..." if s.is_running else "💤 Ожидает"
    sched_str   = "✅ Активен" if _scheduler_running else "⛔ Остановлен"

    lines = [
        "📊 *Статус парсера*",
        "",
        f"Состояние: {running_str}",
        f"Планировщик: {sched_str}",
        f"Последний запуск: `{last_run}`",
        f"Результат: {status_icon}",
        "",
        f"📥 Собрано конфигов: `{s.total_fetched}`",
        f"🔍 Проверено: `{s.total_checked}`",
        f"✅ Рабочих: `{s.total_working}`",
        "",
        f"📁 Источников: `{len(src.sources)}`",
        f"🔗 Репозиторий: `{cfg.GITHUB_REPO}`",
        f"⏱ Интервал: каждые {cfg.UPDATE_INTERVAL_HOURS}ч",
    ]

    if s.is_running and s.progress_total > 0:
        pct = s.progress_done * 100 // s.progress_total
        lines.append(
            f"\n🔄 Прогресс: {s.progress_done}/{s.progress_total} ({pct}%) [{s.progress_stage}]"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@_admin_only
async def cmd_run(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if state.is_running:
        await update.message.reply_text("⚠️ Обновление уже выполняется!")
        return
    await update.message.reply_text("🚀 Запускаю обновление конфигов…")
    _run_pipeline_thread(ctx.application)


@_admin_only
async def cmd_stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global _scheduler_running, _scheduler_task
    _scheduler_running = False
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
    await update.message.reply_text("⛔ Планировщик остановлен. /resume — возобновить.")


@_admin_only
async def cmd_resume(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global _scheduler_running
    if _scheduler_running:
        await update.message.reply_text("ℹ️ Планировщик уже работает.")
        return
    _scheduler_running = True
    _start_scheduler(ctx.application)
    await update.message.reply_text(
        f"✅ Планировщик запущен. Обновление каждые {cfg.UPDATE_INTERVAL_HOURS}ч."
    )


@_admin_only
async def cmd_logs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    n = 20
    if ctx.args:
        try:
            n = int(ctx.args[0])
        except ValueError:
            pass
    logs = state.last_logs(n)
    if not logs:
        await update.message.reply_text("📭 Лог пуст")
        return
    for i in range(0, len(logs), 4000):
        await update.message.reply_text(
            f"```\n{logs[i:i+4000]}\n```", parse_mode="Markdown"
        )


@_admin_only
async def cmd_sources(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = ["📋 *Список источников:*", ""]
    for i, url in enumerate(src.sources, start=1):
        short = url if len(url) < 60 else url[:57] + "…"
        lines.append(f"`{i}.` {short}")
    lines.append(f"\nВсего: {len(src.sources)}")
    text = "\n".join(lines)
    for i in range(0, len(text), 4000):
        await update.message.reply_text(text[i:i+4000], parse_mode="Markdown")


@_admin_only
async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("⚠️ Укажи URL: /add <url>")
        return
    url = ctx.args[0].strip()
    if url in src.sources:
        await update.message.reply_text("ℹ️ Этот источник уже добавлен.")
        return
    src.sources.append(url)
    src.save_sources()
    await update.message.reply_text(
        f"✅ Добавлен источник #{len(src.sources)}:\n`{url}`", parse_mode="Markdown"
    )


@_admin_only
async def cmd_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("⚠️ Укажи номер: /remove <N>")
        return
    try:
        idx     = int(ctx.args[0]) - 1
        removed = src.sources.pop(idx)
        src.save_sources()
        await update.message.reply_text(
            f"🗑 Удалён источник:\n`{removed}`", parse_mode="Markdown"
        )
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Неверный номер источника")


@_admin_only
async def cmd_reset_sources(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    src.sources[:] = src.load_sources()
    await update.message.reply_text(f"♻️ Источники сброшены. Активных: {len(src.sources)}")


@_admin_only
async def cmd_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = [
        "⚙️ *Настройки*",
        "",
        f"GitHub репо: `{cfg.GITHUB_REPO}`",
        f"GitHub ветка: `{cfg.GITHUB_BRANCH}`",
        f"Макс. конфигов: `{cfg.MAX_CONFIGS}`",
        f"Параллельных воркеров: `{cfg.MAX_WORKERS}`",
        f"Таймаут проверки: `{cfg.CHECK_TIMEOUT}s`",
        f"Интервал: `{cfg.UPDATE_INTERVAL_HOURS}h`",
        f"Тэг канала: `{cfg.CHANNEL_TAG}`",
        f"Xray: `{cfg.XRAY_PATH}`",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── Планировщик ───────────────────────────────────────────────────────────────

def _start_scheduler(app: Application) -> None:
    global _scheduler_task

    async def _loop():
        global _scheduler_running
        interval = cfg.UPDATE_INTERVAL_HOURS * 3600
        while _scheduler_running:
            await asyncio.sleep(interval)
            if not _scheduler_running:
                break
            logger.info("Scheduler: starting scheduled run")
            _run_pipeline_thread(app)

    _scheduler_task = asyncio.ensure_future(_loop())


# ── Сборка и запуск ───────────────────────────────────────────────────────────

def build_app() -> Application:
    app = Application.builder().token(cfg.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",         cmd_start))
    app.add_handler(CommandHandler("status",        cmd_status))
    app.add_handler(CommandHandler("run",           cmd_run))
    app.add_handler(CommandHandler("stop",          cmd_stop))
    app.add_handler(CommandHandler("resume",        cmd_resume))
    app.add_handler(CommandHandler("logs",          cmd_logs))
    app.add_handler(CommandHandler("sources",       cmd_sources))
    app.add_handler(CommandHandler("add",           cmd_add))
    app.add_handler(CommandHandler("remove",        cmd_remove))
    app.add_handler(CommandHandler("reset_sources", cmd_reset_sources))
    app.add_handler(CommandHandler("settings",      cmd_settings))
    return app


def start_bot_with_scheduler() -> None:
    global _scheduler_running, _event_loop

    app = build_app()

    async def _post_init(application: Application) -> None:
        global _scheduler_running, _event_loop
        _event_loop        = asyncio.get_event_loop()
        _scheduler_running = True
        _start_scheduler(application)
        logger.info("Scheduler started: every %dh", cfg.UPDATE_INTERVAL_HOURS)
        try:
            await application.bot.send_message(
                chat_id=cfg.TELEGRAM_ADMIN_ID,
                text=(
                    "🤖 Бот запущен!\n"
                    f"Планировщик активен: обновление каждые {cfg.UPDATE_INTERVAL_HOURS}ч\n"
                    "Используй /run для запуска вручную"
                ),
            )
        except Exception as e:
            logger.warning("Could not send startup message: %s", e)

    app.post_init = _post_init
    logger.info("Starting Telegram bot polling…")
    app.run_polling(drop_pending_updates=True)
