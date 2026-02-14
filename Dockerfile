FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем необходимые папки
RUN mkdir -p /app/data/generated
RUN mkdir -p /app/app/static
RUN mkdir -p /app/app/templates

# Указываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["python", "app/main_final_separate.py"]
