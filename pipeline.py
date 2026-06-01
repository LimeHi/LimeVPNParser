"""
pipeline.py  –  полный цикл обновления конфигов.

1. Скачать конфиги из всех источников
2. Проверить каждый через xray
3. Присвоить имена (страна + канал)
4. Опубликовать на GitHub
"""

import logging
from datetime import datetime

import config as cfg
import sources as src
from checker import check_all
from namer import name_configs
from parser import fetch_all
from publisher import publish
from state import state

logger = logging.getLogger(__name__)


def run_pipeline(notify_cb=None) -> bool:
    """
    Запускает полный цикл.
    notify_cb(msg: str)  –  вызывается для отправки уведомлений в Telegram.
    Возвращает True если успешно.
    """
    if state.is_running:
        logger.warning("Pipeline already running, skipping")
        return False

    state.is_running = True
    state.reset_progress()
    ok = False

    def _notify(msg: str) -> None:
        state.add_log(msg)
        if notify_cb:
            try:
                notify_cb(msg)
            except Exception:
                pass

    try:
        # ── 1. Сбор ──────────────────────────────────────────────────────
        _notify("⏳ Шаг 1/3: сбор конфигов из источников…")
        state.progress_stage = "fetching"
        all_uris = fetch_all(src.sources)
        state.total_fetched = len(all_uris)
        _notify(f"📥 Собрано: {len(all_uris)} конфигов")

        if not all_uris:
            _notify("❌ Не удалось получить конфиги ни из одного источника")
            return False

        # ── 2. Проверка ───────────────────────────────────────────────────
        _notify(f"⏳ Шаг 2/3: проверка {len(all_uris)} конфигов…")
        state.progress_stage  = "checking"
        state.progress_total  = len(all_uris)

        def _progress(done: int, total: int) -> None:
            state.progress_done  = done
            state.progress_total = total
            if done % 50 == 0 or done == total:
                _notify(f"🔍 Проверено: {done}/{total}")

        results = check_all(all_uris, max_workers=cfg.MAX_WORKERS, progress_cb=_progress)

        working_uris = [r.uri for r in results if r.ok][:cfg.MAX_CONFIGS]
        state.total_checked = len(all_uris)
        state.total_working = len(working_uris)

        _notify(
            f"✅ Рабочих: {len(working_uris)} / {len(all_uris)} "
            f"({len(working_uris) * 100 // max(len(all_uris), 1)}%)"
        )

        if not working_uris:
            _notify("❌ Ни один конфиг не прошёл проверку")
            return False

        # ── 3. Именование ─────────────────────────────────────────────────
        _notify("🏷 Именование конфигов (геолукап)…")
        named_uris = name_configs(working_uris)

        # ── 4. Публикация ─────────────────────────────────────────────────
        _notify("⏳ Шаг 3/3: публикация на GitHub…")
        state.progress_stage = "publishing"
        ok = publish(named_uris)

        if ok:
            _notify(
                f"🎉 Готово! Опубликовано {len(named_uris)} конфигов\n"
                f"🔗 https://github.com/{cfg.GITHUB_REPO}"
            )
        else:
            _notify("❌ Ошибка публикации на GitHub")

        state.last_ok  = ok
        state.last_run = datetime.now()
        state.progress_stage = "done"
        return ok

    except Exception as e:
        logger.exception("Pipeline error")
        _notify(f"💥 Ошибка: {e}")
        return False
    finally:
        state.is_running = False
