# Используем базовый образ с Python и CPU
FROM python:3.10-slim

# Устанавливаем системные зависимости для FAISS и Unstructured
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libgl1 \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python зависимости для CPU
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]