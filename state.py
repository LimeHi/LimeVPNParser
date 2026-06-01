"""
state.py  –  общее состояние приложения (разделяется ботом и планировщиком).
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AppState:
    # ── Статус последнего запуска ────────────────────────────────────────
    is_running: bool = False
    last_run:   Optional[datetime] = None
    last_ok:    bool = False

    # ── Статистика последнего запуска ────────────────────────────────────
    total_fetched:  int = 0
    total_checked:  int = 0
    total_working:  int = 0

    # ── Прогресс (для live-обновления в боте) ───────────────────────────
    progress_done:  int = 0
    progress_total: int = 0
    progress_stage: str = ""   # "fetching" | "checking" | "publishing" | "done"

    # ── Лог последних сообщений ──────────────────────────────────────────
    logs: list[str] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def add_log(self, msg: str) -> None:
        with self._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            self.logs.append(f"[{ts}] {msg}")
            if len(self.logs) > 200:
                self.logs = self.logs[-200:]

    def last_logs(self, n: int = 20) -> str:
        with self._lock:
            return "\n".join(self.logs[-n:])

    def reset_progress(self) -> None:
        self.progress_done  = 0
        self.progress_total = 0
        self.progress_stage = ""


state = AppState()
