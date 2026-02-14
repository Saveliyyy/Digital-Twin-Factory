#!/usr/bin/env python3
import sys
import os
import socket
import io
import csv
from datetime import datetime

# Устанавливаем кодировку UTF-8 для вывода
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import uuid
import asyncio

from app.core.batch_generator import BatchGenerator

# Функция для поиска свободного порта
def find_free_port(start_port=8000, max_port=8010):
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

# ============ ИНИЦИАЛИЗАЦИЯ APP ============
app = FastAPI(
    title="Digital Twin Factory",
    description="Фабрика цифровых двойников - генерация синтетических данных с корреляциями",
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем папки
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)
os.makedirs("data/generated", exist_ok=True)
os.makedirs("data/exports", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Хранилище задач
jobs_db = {}
generator = BatchGenerator(batch_size=10000)

# ============ ФУНКЦИЯ ДЛЯ ЧТЕНИЯ HTML ============
def read_html(filename):
    filepath = f"app/templates/{filename}"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return f"<h1>404 - {filename} not found</h1>"

# ============ СОЗДАЕМ ПРОСТОЙ CSS ============
with open("app/static/css/style.css", "w", encoding="utf-8") as f:
    f.write('''
:root {
    --primary: #4361ee;
    --success: #4cc9f0;
    --danger: #f72585;
    --warning: #f8961e;
    --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: var(--gradient);
    min-height: 100vh;
    padding: 20px;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
}

.navbar {
    background: white;
    border-radius: 16px;
    padding: 1rem 2rem;
    margin-bottom: 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.navbar-brand {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary);
    text-decoration: none;
}

.navbar-menu {
    display: flex;
    gap: 1rem;
    list-style: none;
}

.navbar-item a {
    color: #333;
    text-decoration: none;
    padding: 0.5rem 1rem;
}

.navbar-item.active a {
    color: var(--primary);
    font-weight: bold;
}

.card {
    background: white;
    border-radius: 20px;
    padding: 30px;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.card-title {
    font-size: 1.5rem;
    margin-bottom: 20px;
    border-bottom: 2px solid var(--primary);
    padding-bottom: 10px;
}

.btn {
    display: inline-block;
    padding: 12px 30px;
    border: none;
    border-radius: 50px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    background: var(--gradient);
    color: white;
    margin: 5px;
}

.footer {
    text-align: center;
    padding: 30px;
    color: white;
}
''')

# ============ СОЗДАЕМ ПРОСТЫЕ HTML СТРАНИЦЫ ============

# index.html
with open("app/templates/index.html", "w", encoding="utf-8") as f:
    f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Digital Twin Factory</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <nav class="navbar">
            <a href="/" class="navbar-brand">🏭 Digital Twin Factory</a>
            <ul class="navbar-menu">
                <li class="navbar-item active"><a href="/">Главная</a></li>
                <li class="navbar-item"><a href="/generator">Генератор</a></li>
                <li class="navbar-item"><a href="/jobs">Задачи</a></li>
                <li class="navbar-item"><a href="/analytics">Аналитика</a></li>
            </ul>
        </nav>
        
        <div class="card">
            <h1 class="card-title">🏭 Digital Twin Factory</h1>
            <p>Фабрика цифровых двойников — генерация синтетических данных с корреляциями</p>
            <a href="/generator" class="btn">Перейти к генерации</a>
            <a href="/analytics" class="btn">Аналитика</a>
        </div>
    </div>
</body>
</html>''')

# generator.html
with open("app/templates/generator.html", "w", encoding="utf-8") as f:
    f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Генератор</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <nav class="navbar">
            <a href="/" class="navbar-brand">🏭 Digital Twin Factory</a>
            <ul class="navbar-menu">
                <li class="navbar-item"><a href="/">Главная</a></li>
                <li class="navbar-item active"><a href="/generator">Генератор</a></li>
                <li class="navbar-item"><a href="/jobs">Задачи</a></li>
                <li class="navbar-item"><a href="/analytics">Аналитика</a></li>
            </ul>
        </nav>
        
        <div class="card">
            <h1 class="card-title">⚙️ Генератор данных</h1>
            <p>Страница в разработке</p>
        </div>
    </div>
</body>
</html>''')

# jobs.html
with open("app/templates/jobs.html", "w", encoding="utf-8") as f:
    f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Задачи</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <nav class="navbar">
            <a href="/" class="navbar-brand">🏭 Digital Twin Factory</a>
            <ul class="navbar-menu">
                <li class="navbar-item"><a href="/">Главная</a></li>
                <li class="navbar-item"><a href="/generator">Генератор</a></li>
                <li class="navbar-item active"><a href="/jobs">Задачи</a></li>
                <li class="navbar-item"><a href="/analytics">Аналитика</a></li>
            </ul>
        </nav>
        
        <div class="card">
            <h1 class="card-title">📋 Задачи</h1>
            <p>Страница в разработке</p>
        </div>
    </div>
</body>
</html>''')

# analytics.html
with open("app/templates/analytics_final.html", "w", encoding="utf-8") as f:
    f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Аналитика</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
    <div class="container">
        <nav class="navbar">
            <a href="/" class="navbar-brand">🏭 Digital Twin Factory</a>
            <ul class="navbar-menu">
                <li class="navbar-item"><a href="/">Главная</a></li>
                <li class="navbar-item"><a href="/generator">Генератор</a></li>
                <li class="navbar-item"><a href="/jobs">Задачи</a></li>
                <li class="navbar-item active"><a href="/analytics">Аналитика</a></li>
            </ul>
        </nav>

        <div class="card">
            <h1 class="card-title">📊 Аналитика</h1>
            <p>Визуализация корреляций, финансовая аналитика и экспорт данных</p>
        </div>

        <div class="card">
            <h2 class="card-title">💰 Финансовая аналитика</h2>
            <canvas id="revenueChart" style="height: 300px; width: 100%;"></canvas>
        </div>

        <div class="card">
            <h2 class="card-title">📈 Визуализация корреляций</h2>
            <canvas id="correlationChart" style="height: 300px; width: 100%;"></canvas>
        </div>

        <div class="card">
            <h2 class="card-title">📋 Экспорт данных</h2>
            <button class="btn" onclick="exportData('json')">JSON</button>
            <button class="btn" onclick="exportData('csv')">CSV</button>
            <button class="btn" onclick="exportData('sql')">SQL</button>
        </div>
    </div>

    <script>
        // Revenue Chart
        new Chart(document.getElementById('revenueChart'), {
            type: 'bar',
            data: {
                labels: ['Пневмония', 'Диабет', 'Гипертония', 'Грипп', 'Простуда'],
                datasets: [{
                    label: 'Выручка ($)',
                    data: [350, 280, 200, 120, 80],
                    backgroundColor: ['#f72585', '#f8961e', '#4cc9f0', '#4361ee', '#3f37c9']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });

        // Correlation Chart
        new Chart(document.getElementById('correlationChart'), {
            type: 'bar',
            data: {
                labels: ['Диабетики', 'Не-диабетики'],
                datasets: [{
                    data: [32.1, 25.9],
                    backgroundColor: ['#f72585', '#4cc9f0']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });

        function exportData(format) {
            alert('Экспорт в ' + format.toUpperCase() + ' будет доступен в следующем обновлении');
        }
    </script>
</body>
</html>''')

# ============ ВЕБ-СТРАНИЦЫ ============
@app.get("/", response_class=HTMLResponse)
async def index():
    return read_html("index.html")

@app.get("/generator", response_class=HTMLResponse)
async def generator_page():
    return read_html("generator.html")

@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page():
    return read_html("jobs.html")

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page():
    return read_html("analytics_final.html")

# ============ API ENDPOINTS ============
@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "service": "Digital Twin Factory", "version": "2.1.0"}

@app.get("/api/v1/stats")
async def get_stats():
    return {
        "total_generations": len(jobs_db),
        "successful_jobs": len([j for j in jobs_db.values() if j.get("status") == "completed"]),
        "total_patients": sum(j.get("patients", 0) for j in jobs_db.values()),
        "total_visits": sum(j.get("visits", 0) for j in jobs_db.values())
    }

@app.post("/api/v1/generate/medical")
async def generate_medical(patients: int = 10000, visits: int = 50000, seed: int = 42):
    job_id = str(uuid.uuid4())
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "patients": patients,
        "visits": visits,
        "seed": seed,
        "created_at": datetime.now().isoformat()
    }
    return {"success": True, "job_id": job_id}

@app.get("/api/v1/jobs")
async def list_jobs():
    return list(jobs_db.values())[-50:]

# ============ ЗАПУСК ============
if __name__ == "__main__":
    port = find_free_port(8000)
    
    if port:
        print("=" * 70)
        print("🚀 DIGITAL TWIN FACTORY - ЗАПУЩЕН")
        print("=" * 70)
        print(f"📌 Адрес: http://localhost:{port}")
        print(f"🏠 Главная: http://localhost:{port}/")
        print(f"⚙️  Генератор: http://localhost:{port}/generator")
        print(f"📋 Задачи: http://localhost:{port}/jobs")
        print(f"📊 Аналитика: http://localhost:{port}/analytics")
        print("=" * 70)
        
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        print("❌ Нет свободных портов")
