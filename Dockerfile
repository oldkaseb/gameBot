# مرحله اول: بیلد فرانت‌اند مینی‌اپ (React / Vite)
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY webapp/frontend/package*.json ./
RUN npm install
COPY webapp/frontend/ ./
RUN npm run build

# مرحله دوم: اجرای پایتون (ربات تلگرام + بک‌اند FastAPI مینی‌اپ)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# نصب پکیج‌های سیستمی مورد نیاز برای PostgreSQL و فونت/تصویر
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# نصب کتابخانه‌های پایتون
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# کپی کل فایل‌های پروژه
COPY . .

# کپی خروجی بیلد شده فرانت‌اند به داخل پوشه بک‌اند برای سرو شدن
COPY --from=frontend-builder /frontend/dist /app/webapp/frontend/dist

EXPOSE 8000

# اجرای یکپارچه: هم ربات تلگرام و هم سرور مینی‌اپ با هم اجرا می‌شوند
CMD ["python", "main.py"]
