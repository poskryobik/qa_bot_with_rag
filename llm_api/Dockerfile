## Используем базовый образ с CUDA 12.1
FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Устанавливаем Python и системные зависимости
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python зависимости для GPU
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# COPY llm_api/app ./app
# WORKDIR /app
# Указываем использование CUDA
ENV CUDA_VISIBLE_DEVICES=0

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]