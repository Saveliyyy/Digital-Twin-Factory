FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data/generated
RUN mkdir -p /app/app/static
RUN mkdir -p /app/app/templates

ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE $PORT

CMD ["python", "app/main_full.py"]
