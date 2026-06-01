"""
main.py  –  точка входа.

Запускает Telegram-бота + планировщик обновлений.
При первом запуске сразу выполняет один цикл обновления.
"""

import logging
import sys
import threading

import config as cfg
from bot import start_bot_with_scheduler
from pipeline import run_pipeline
from state import state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def _validate_config() -> bool:
    errors = []
    if not cfg.TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN not set")
    if not cfg.TELEGRAM_ADMIN_ID:
        errors.append("TELEGRAM_ADMIN_ID not set")
    if not cfg.GITHUB_TOKEN:
        errors.append("GITHUB_TOKEN not set")
    if not cfg.GITHUB_REPO:
        errors.append("GITHUB_REPO not set")
    if errors:
        for e in errors:
            logger.error("Config error: %s", e)
        return False
    return True


if __name__ == "__main__":
    if not _validate_config():
        logger.error("Fix .env before starting")
        sys.exit(1)

    logger.info("Starting VPN Config Parser")
    logger.info("GitHub repo: %s", cfg.GITHUB_REPO)
    logger.info("Update interval: every %dh", cfg.UPDATE_INTERVAL_HOURS)
    logger.info("Max configs: %d, Workers: %d", cfg.MAX_CONFIGS, cfg.MAX_WORKERS)

    # Первый запуск в фоне
    def _initial_run():
        logger.info("Running initial pipeline…")
        run_pipeline()

    threading.Thread(target=_initial_run, daemon=True).start()

    # Запуск бота (блокирующий)
    start_bot_with_scheduler()
