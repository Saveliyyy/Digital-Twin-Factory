#!/bin/bash

echo "========================================="
echo "🚀 ОПТИМИЗАЦИЯ СКОРОСТИ ЗАГРУЗКИ"
echo "========================================="

cd /root/digital-twin-factory

# 1. Увеличить интервал обновления в генераторе
sed -i 's/setInterval(loadRecentJobs, [0-9]\+)/setInterval(loadRecentJobs, 30000)/g' app/templates/generator_separate.html

# 2. Добавить кэширование в main файл
cat >> app/main_final_separate.py << 'INNER'

# Оптимизация скорости
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Кэширование статики
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import time

# Добавить заголовки кэширования
@app.middleware("http")
async def add_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=3600"
    return response
INNER

# 3. Оптимизировать импорты в batch_generator.py
cat > app/core/batch_generator_optimized.py << 'INNER'
# Ленивые импорты
import numpy as np

class BatchGenerator:
    def __init__(self, batch_size=10000):
        self.batch_size = batch_size
        self._pl = None
        self._fake = None
    
    @property
    def pl(self):
        if self._pl is None:
            import polars as pl
            self._pl = pl
        return self._pl
    
    @property
    def fake(self):
        if self._fake is None:
            from faker import Faker
            self._fake = Faker()
        return self._fake
INNER

echo "========================================="
echo "✅ ОПТИМИЗАЦИЯ ЗАВЕРШЕНА"
echo "========================================="
