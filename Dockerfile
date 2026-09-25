# ═══════════════════════════════════════════
# RiddlerChat Backend Container
# Post-Quantum Encrypted Messenger v2.0
# 1337_TECH DBA, Austin Texas - 2026
# ═══════════════════════════════════════════

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssl \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/

ENV RIDDLER_HOST=0.0.0.0
ENV RIDDLER_WS_PORT=7576

EXPOSE 7576

CMD ["python", "-m", "uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "7576"]
