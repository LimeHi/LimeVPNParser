FROM python:3.11-slim

# ── Системные зависимости + скачиваем xray-core ──────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl unzip ca-certificates \
    && XRAY_VERSION=$(curl -fsSL https://api.github.com/repos/XTLS/Xray-core/releases/latest \
        | grep '"tag_name"' | head -1 | sed 's/.*"tag_name": *"\(.*\)".*/\1/') \
    && echo "Installing Xray ${XRAY_VERSION}" \
    && curl -fsSL \
        "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-linux-64.zip" \
        -o /tmp/xray.zip \
    && unzip /tmp/xray.zip xray -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/xray \
    && rm -rf /tmp/xray.zip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Приложение ────────────────────────────────────────────────────────────────
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV XRAY_PATH=/usr/local/bin/xray

CMD ["python", "main.py"]
