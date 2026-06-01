import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ─────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_ID  = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))

# ── GitHub ────────────────────────────────────────────────
GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO   = os.getenv("GITHUB_REPO", "")        # "username/repo"
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

# ── Scheduler ─────────────────────────────────────────────
UPDATE_INTERVAL_HOURS = int(os.getenv("UPDATE_INTERVAL_HOURS", "6"))

# ── Checker ───────────────────────────────────────────────
CHECK_TIMEOUT   = int(os.getenv("CHECK_TIMEOUT", "8"))      # seconds per config
MAX_CONFIGS     = int(os.getenv("MAX_CONFIGS", "100"))       # max working configs to keep
MAX_WORKERS     = int(os.getenv("MAX_WORKERS", "30"))        # parallel check threads
MAX_LATENCY_MS  = int(os.getenv("MAX_LATENCY_MS", "3000"))  # drop configs with latency above this (ms), 0 = disabled
XRAY_PATH       = os.getenv("XRAY_PATH", "/usr/local/bin/xray")
TEST_URL        = os.getenv("TEST_URL", "http://www.gstatic.com/generate_204")
SOCKS_BASE_PORT = int(os.getenv("SOCKS_BASE_PORT", "20000"))

# ── Channel tag appended to config names ──────────────────
CHANNEL_TAG = os.getenv("CHANNEL_TAG", "@LimeVPNFREE")
