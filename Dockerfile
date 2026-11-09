# ─────────────────────────────────────────
# Stage 1: Builder
# ─────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# نصب وابستگی‌های سیستمی مورد نیاز برای کامپایل
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# کپی requirements و نصب پکیج‌ها در یک virtualenv
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─────────────────────────────────────────
# Stage 2: Runtime
# ─────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# وابستگی‌های runtime (libpq برای asyncpg و psycopg2، فونت‌ها)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# کپی پکیج‌های نصب‌شده از مرحله قبل
COPY --from=builder /install /usr/local

# کپی سورس کد
COPY . .

# ─── فونت وزیر (برای بازی تایپ سرعتی) ───
# اگر فایل Vazir.ttf را در ریشه پروژه داری، این خط کافی است.
# در غیر این صورت، از فونت پیش‌فرض DejaVu استفاده می‌شود.
# COPY Vazir.ttf /app/Vazir.ttf

# ─── متغیرهای محیطی پیش‌فرض ───
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# ─── healthcheck (اختیاری) ───
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import os, socket; s=socket.socket(); s.settimeout(3); s.connect(('127.0.0.1', int(os.getenv('PORT', 8080)))); s.close()" || exit 1

# ─── اجرا ───
CMD ["python", "main.py"]
