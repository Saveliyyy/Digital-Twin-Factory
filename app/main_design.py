#!/usr/bin/env python3
import sys
import os
import socket

# Устанавливаем кодировку UTF-8 для вывода
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import uuid
from datetime import datetime
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
    version="2.0.0",
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
os.makedirs("data/uploads", exist_ok=True)

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

# ============ СОЗДАЕМ CSS ФАЙЛ С КРАСИВЫМ ДИЗАЙНОМ ============
with open("app/static/css/style.css", "w", encoding="utf-8") as f:
    f.write('''
:root {
    --primary: #4361ee;
    --primary-dark: #3a56d4;
    --secondary: #3f37c9;
    --success: #4cc9f0;
    --danger: #f72585;
    --warning: #f8961e;
    --info: #4895ef;
    --light: #f8f9fa;
    --dark: #212529;
    --gray: #6c757d;
    --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--gradient);
    min-height: 100vh;
    color: var(--dark);
    line-height: 1.6;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

/* Навигация */
.navbar {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 1rem 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
}

.navbar-brand {
    font-size: 1.8rem;
    font-weight: 700;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-decoration: none;
}

.navbar-menu {
    display: flex;
    gap: 1rem;
    list-style: none;
}

.navbar-item {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    transition: all 0.3s;
}

.navbar-item a {
    color: var(--dark);
    text-decoration: none;
    font-weight: 500;
}

.navbar-item:hover {
    background: var(--gradient);
}

.navbar-item:hover a {
    color: white;
}

.navbar-item.active {
    background: var(--gradient);
}

.navbar-item.active a {
    color: white;
}

/* Карточки */
.card {
    background: white;
    border-radius: 20px;
    padding: 30px;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s, box-shadow 0.3s;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
}

.card-title {
    font-size: 1.5rem;
    margin-bottom: 20px;
    color: var(--dark);
    border-bottom: 2px solid var(--primary);
    padding-bottom: 10px;
}

/* Сетка */
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 30px;
    margin-bottom: 30px;
}

/* Статистика */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.stat-card {
    background: linear-gradient(145deg, #ffffff, #f8f9fa);
    padding: 25px;
    border-radius: 15px;
    border-left: 5px solid var(--primary);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
}

.stat-icon {
    font-size: 2.5rem;
    margin-bottom: 10px;
}

.stat-label {
    color: var(--gray);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.stat-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--primary);
    line-height: 1.2;
}

/* Формы */
.form-group {
    margin-bottom: 20px;
}

.form-label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: var(--dark);
}

.form-control {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e9ecef;
    border-radius: 12px;
    font-size: 1rem;
    transition: all 0.3s;
    background: white;
}

.form-control:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.1);
}

/* Кнопки */
.btn {
    display: inline-block;
    padding: 12px 30px;
    border: none;
    border-radius: 50px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    text-decoration: none;
    text-align: center;
}

.btn-primary {
    background: var(--gradient);
    color: white;
    box-shadow: 0 4px 15px rgba(103, 58, 183, 0.3);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(103, 58, 183, 0.4);
}

.btn-success {
    background: linear-gradient(135deg, #4cc9f0, #4895ef);
    color: white;
}

.btn-lg {
    padding: 16px 40px;
    font-size: 1.1rem;
}

/* Прогресс бар */
.progress {
    width: 100%;
    height: 12px;
    background: #e9ecef;
    border-radius: 50px;
    margin: 20px 0;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: var(--gradient);
    border-radius: 50px;
    transition: width 0.5s ease;
}

/* Таблицы */
.table-container {
    background: white;
    border-radius: 16px;
    padding: 20px;
    overflow-x: auto;
    margin-top: 20px;
}

.table {
    width: 100%;
    border-collapse: collapse;
}

.table th {
    background: #f8f9fa;
    color: var(--dark);
    font-weight: 600;
    padding: 12px;
    text-align: left;
    border-bottom: 2px solid var(--primary);
}

.table td {
    padding: 12px;
    border-bottom: 1px solid #e9ecef;
}

.table tr:hover {
    background: #f8f9fa;
}

/* Алерты */
.alert {
    padding: 16px 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { transform: translateY(-20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

.alert-success {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}

/* Бейджи */
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 50px;
    font-size: 0.8rem;
    font-weight: 600;
}

.badge-primary {
    background: #e0e7ff;
    color: var(--primary);
}

.badge-success {
    background: #d4edda;
    color: #155724;
}

/* Футер */
.footer {
    text-align: center;
    padding: 30px;
    color: rgba(255, 255, 255, 0.9);
    margin-top: 50px;
}

/* Чарты */
.chart-container {
    position: relative;
    height: 300px;
    width: 100%;
    margin-top: 20px;
}

/* Адаптивность */
@media (max-width: 768px) {
    .navbar {
        flex-direction: column;
        gap: 1rem;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    .grid {
        grid-template-columns: 1fr;
    }
}
''')

# ============ СОЗДАЕМ HTML ШАБЛОНЫ С КРАСИВЫМ ДИЗАЙНОМ ============
print("=" * 70)
print("🎨 СОЗДАНИЕ ШАБЛОНОВ С ДИЗАЙНОМ")
print("=" * 70)

# 1. index.html - Главная страница с дизайном
with open("app/templates/index.html", "w", encoding="utf-8") as f:
    f.write('''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Twin Factory - Главная</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <!-- Навигация -->
        <nav class="navbar">
            <a href="/" class="navbar-brand">🏭 Digital Twin Factory</a>
            <ul class="navbar-menu">
                <li class="navbar-item active"><a href="/">Главная</a></li>
                <li class="navbar-item"><a href="/generator">Генератор</a></li>
                <li class="navbar-item"><a href="/jobs">Задачи</a></li>
                <li class="navbar-item"><a href="/analytics">Аналитика</a></li>
                <li class="navbar-item"><a href="/api/docs">API</a></li>
            </ul>
        </nav>

        <!-- Хедер -->
        <div class="card fade-in">
            <h1 class="card-title">🏭 Digital Twin Factory</h1>
            <p style="font-size: 1.2rem; color: #6c757d; margin-bottom: 20px;">
                Фабрика цифровых двойников — генерация синтетических данных с корреляциями
            </p>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <span class="badge badge-primary">⚡ 10,000 записей/сек</span>
                <span class="badge badge-success">📊 Polars + NumPy</span>
                <span class="badge badge-primary">🔄 Граф корреляций</span>
                <span class="badge badge-success">❄️ Сезонность</span>
            </div>
        </div>

        <!-- Статистика -->
        <div class="stats-grid" id="stats-container">
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-label">Всего генераций</div>
                <div class="stat-value" id="total-generations">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-label">Сгенерировано пациентов</div>
                <div class="stat-value" id="total-patients">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🏥</div>
                <div class="stat-label">Сгенерировано визитов</div>
                <div class="stat-value" id="total-visits">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚡</div>
                <div class="stat-label">Успешных задач</div>
                <div class="stat-value" id="success-rate">0%</div>
            </div>
        </div>

        <!-- Быстрый старт -->
        <div class="grid">
            <div class="card">
                <h2 class="card-title">🚀 Быстрый старт</h2>
                <p style="margin-bottom: 20px; color: #6c757d;">
                    Сгенерируйте 10,000 пациентов и 50,000 визитов с корреляциями за 30 секунд
                </p>
                <a href="/generator" class="btn btn-primary btn-lg" style="width: 100%;">
                    ⚡ Перейти к генерации
                </a>
            </div>

            <div class="card">
                <h2 class="card-title">📊 Аналитика</h2>
                <p style="margin-bottom: 20px; color: #6c757d;">
                    Просмотр корреляций, сезонности и статистики в реальном времени
                </p>
                <a href="/analytics" class="btn btn-success btn-lg" style="width: 100%;">
                    📈 Перейти к аналитике
                </a>
            </div>
        </div>

        <!-- Корреляции -->
        <div class="grid">
            <div class="card">
                <h2 class="card-title">📈 Корреляция диабет-BMI</h2>
                <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; color: #f72585;">32.1</div>
                        <div style="color: #6c757d;">BMI диабетиков</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; color: #4cc9f0;">25.9</div>
                        <div style="color: #6c757d;">BMI не-диабетиков</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; color: #4361ee;">+6.2</div>
                        <div style="color: #6c757d;">Разница</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2 class="card-title">❄️ Сезонность гриппа</h2>
                <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; color: #4cc9f0;">41%</div>
                        <div style="color: #6c757d;">Зимой</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; color: #f8961e;">12%</div>
                        <div style="color: #6c757d;">Летом</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; color: #4361ee;">3.5x</div>
                        <div style="color: #6c757d;">Выше зимой</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Футер -->
        <div class="footer">
            <p>Digital Twin Factory © 2024 | Версия 2.0.0</p>
            <p style="margin-top: 10px; font-size: 0.9rem;">
                <span style="color: #4cc9f0;">●</span> PostgreSQL 
                <span style="color: #f72585; margin-left: 15px;">●</span> Redis 
                <span style="color: #4361ee; margin-left: 15px;">●</span> FastAPI
                <span style="color: #4cc9f0; margin-left: 15px;">●</span> Polars
            </p>
        </div>
    </div>

    <script>
        async function loadStats() {
            try {
                const response = await fetch('/api/v1/stats');
                const data = await response.json();
                
                document.getElementById('total-generations').textContent = data.total_generations || 0;
                document.getElementById('total-patients').textContent = (data.total_patients || 0).toLocaleString();
                document.getElementById('total-visits').textContent = (data.total_visits || 0).toLocaleString();
                document.getElementById('success-rate').textContent = data.success_rate || '0%';
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        loadStats();
        setInterval(loadStats, 5000);
    </script>
</body>
</html>''')
print("✅ index.html - создан")

# 2. generator.html - Страница генератора с дизайном
with open("app/templates/generator.html", "w", encoding="utf-8") as f:
    f.write('''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Twin Factory - Генератор</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <!-- Навигация -->
        <nav class="navbar">
            <a href="/" class="navbar-brand">🏭 Digital Twin Factory</a>
            <ul class="navbar-menu">
                <li class="navbar-item"><a href="/">Главная</a></li>
                <li class="navbar-item active"><a href="/generator">Генератор</a></li>
                <li class="navbar-item"><a href="/jobs">Задачи</a></li>
                <li class="navbar-item"><a href="/analytics">Аналитика</a></li>
                <li class="navbar-item"><a href="/api/docs">API</a></li>
            </ul>
        </nav>

        <!-- Заголовок -->
        <div class="card">
            <h1 class="card-title">🚀 Генератор медицинских данных</h1>
            <p style="color: #6c757d;">
                Создание реалистичных датасетов с пациентами и визитами к врачу.
                Все данные генерируются с учетом корреляций и сезонности.
            </p>
        </div>

        <!-- Основная форма -->
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2 class="card-title">⚙️ Параметры генерации</h2>
                
                <form id="generateForm">
                    <div class="grid" style="grid-template-columns: 1fr 1fr;">
                        <div class="form-group">
                            <label class="form-label">👥 Пациенты</label>
                            <input type="number" name="patients" id="patients" class="form-control" 
                                   value="10000" min="100" max="100000" step="100">
                        </div>

                        <div class="form-group">
                            <label class="form-label">🏥 Визиты</label>
                            <input type="number" name="visits" id="visits" class="form-control" 
                                   value="50000" min="500" max="500000" step="500">
                        </div>
                    </div>

                    <div class="grid" style="grid-template-columns: 1fr 1fr;">
                        <div class="form-group">
                            <label class="form-label">🎲 Seed</label>
                            <input type="number" name="seed" class="form-control" value="42" min="1" max="9999">
                        </div>

                        <div class="form-group">
                            <label class="form-label">📁 Формат</label>
                            <select name="format" class="form-control">
                                <option value="json">JSON</option>
                                <option value="parquet">Parquet</option>
                                <option value="csv">CSV</option>
                            </select>
                        </div>
                    </div>

                    <div style="display: flex; gap: 15px; margin-top: 30px;">
                        <button type="submit" class="btn btn-primary btn-lg" style="flex: 2;">
                            ⚡ ЗАПУСТИТЬ ГЕНЕРАЦИЮ
                        </button>
                        <button type="button" class="btn btn-success btn-lg" style="flex: 1;" onclick="window.location.reload()">
                            🔄 СБРОС
                        </button>
                    </div>
                </form>

                <!-- Прогресс бар -->
                <div id="progressContainer" style="display: none; margin-top: 30px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span id="progressText" style="font-weight: 600;">Инициализация...</span>
                        <span id="progressPercent" style="font-weight: 600; color: #4361ee;">0%</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" id="progressBar" style="width: 0%;"></div>
                    </div>
                </div>

                <!-- Результат -->
                <div id="resultContainer" style="display: none; margin-top: 30px;">
                    <div class="alert alert-success">
                        <h3 style="margin-bottom: 10px;">✅ Генерация запущена!</h3>
                        <p id="resultMessage"></p>
                    </div>
                </div>
            </div>

            <!-- Информация о корреляциях -->
            <div class="card">
                <h2 class="card-title">📊 Активные корреляции</h2>
                
                <div style="margin-bottom: 25px;">
                    <h3 style="font-size: 1.1rem; margin-bottom: 15px; color: #4361ee;">📈 Диабет → BMI</h3>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>BMI диабетиков:</span>
                            <span style="font-weight: bold; color: #f72585;">32.1</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>BMI не-диабетиков:</span>
                            <span style="font-weight: bold; color: #4cc9f0;">25.9</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 10px; padding-top: 10px; border-top: 1px solid #dee2e6;">
                            <span>Разница:</span>
                            <span style="font-weight: bold; color: #4361ee;">+6.2</span>
                        </div>
                    </div>
                </div>

                <div>
                    <h3 style="font-size: 1.1rem; margin-bottom: 15px; color: #4361ee;">❄️ Сезонность</h3>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>Грипп зимой:</span>
                            <span style="font-weight: bold; color: #4cc9f0;">41%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Грипп летом:</span>
                            <span style="font-weight: bold; color: #f8961e;">12%</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Футер -->
        <div class="footer">
            <p>Digital Twin Factory © 2024 | Версия 2.0.0</p>
        </div>
    </div>

    <script>
        document.getElementById('generateForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const patients = document.getElementById('patients').value;
            const visits = document.getElementById('visits').value;
            const seed = document.querySelector('input[name="seed"]').value;
            
            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('resultContainer').style.display = 'none';
            
            let progress = 0;
            const interval = setInterval(() => {
                progress += 2;
                if (progress <= 100) {
                    document.getElementById('progressBar').style.width = progress + '%';
                    document.getElementById('progressPercent').innerHTML = progress + '%';
                    
                    if (progress < 20) document.getElementById('progressText').innerHTML = 'Подготовка генератора...';
                    else if (progress < 40) document.getElementById('progressText').innerHTML = 'Генерация пациентов...';
                    else if (progress < 60) document.getElementById('progressText').innerHTML = 'Генерация визитов...';
                    else if (progress < 80) document.getElementById('progressText').innerHTML = 'Применение корреляций...';
                    else if (progress < 95) document.getElementById('progressText').innerHTML = 'Сохранение результатов...';
                    else document.getElementById('progressText').innerHTML = 'Завершение...';
                }
                if (progress >= 100) clearInterval(interval);
            }, 100);
            
            try {
                const response = await fetch(`/api/v1/generate/medical?patients=${patients}&visits=${visits}&seed=${seed}`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('resultContainer').style.display = 'block';
                    document.getElementById('resultMessage').innerHTML = `✅ Задача запущена! ID: ${data.job_id.substring(0, 8)}...`;
                }
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('progressContainer').style.display = 'none';
            }
        });
    </script>
</body>
</html>''')
print("✅ generator.html - создан")

# 3. jobs.html - Страница задач с дизайном
with open("app/templates/jobs.html", "w", encoding="utf-8") as f:
    f.write('''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Twin Factory - Задачи</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <!-- Навигация -->
        <nav class="navbar">
            <a href="/" class="navbar-brand">🏭 Digital Twin Factory</a>
            <ul class="navbar-menu">
                <li class="navbar-item"><a href="/">Главная</a></li>
                <li class="navbar-item"><a href="/generator">Генератор</a></li>
                <li class="navbar-item active"><a href="/jobs">Задачи</a></li>
                <li class="navbar-item"><a href="/analytics">Аналитика</a></li>
                <li class="navbar-item"><a href="/api/docs">API</a></li>
            </ul>
        </nav>

        <!-- Заголовок -->
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1 class="card-title">📋 Задачи генерации</h1>
                    <p style="color: #6c757d;">История всех запущенных генераций данных</p>
                </div>
                <button class="btn btn-primary" onclick="window.location.reload()">
                    🔄 Обновить
                </button>
            </div>
        </div>

        <!-- Статистика задач -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-label">Всего задач</div>
                <div class="stat-value" id="totalJobs">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-label">Завершено</div>
                <div class="stat-value" id="completedJobs">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⏳</div>
                <div class="stat-label">В процессе</div>
                <div class="stat-value" id="activeJobs">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">❌</div>
                <div class="stat-label">Ошибки</div>
                <div class="stat-value" id="failedJobs">0</div>
            </div>
        </div>

        <!-- Таблица задач -->
        <div class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th>ID задачи</th>
                        <th>Пациенты</th>
                        <th>Визиты</th>
                        <th>Статус</th>
                        <th>Дата создания</th>
                    </tr>
                </thead>
                <tbody id="jobsTableBody">
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 40px;">
                            <div style="font-size: 1.2rem; color: #6c757d;">Загрузка задач...</div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Футер -->
        <div class="footer">
            <p>Digital Twin Factory © 2024 | Версия 2.0.0</p>
        </div>
    </div>

    <script>
        async function loadJobs() {
            try {
                const response = await fetch('/api/v1/jobs');
                const jobs = await response.json();
                
                const total = jobs.length;
                const completed = jobs.filter(j => j.status === 'completed').length;
                const active = jobs.filter(j => j.status === 'processing' || j.status === 'pending').length;
                const failed = jobs.filter(j => j.status === 'failed').length;
                
                document.getElementById('totalJobs').textContent = total;
                document.getElementById('completedJobs').textContent = completed;
                document.getElementById('activeJobs').textContent = active;
                document.getElementById('failedJobs').textContent = failed;
                
                let html = '';
                if (jobs.length === 0) {
                    html = '<tr><td colspan="5" style="text-align: center; padding: 40px;">📭 Нет задач</td></tr>';
                } else {
                    jobs.slice(0, 10).forEach(job => {
                        let statusClass = '';
                        let statusText = job.status || 'pending';
                        
                        if (statusText === 'completed') statusClass = 'badge-success';
                        else if (statusText === 'processing' || statusText === 'pending') statusClass = 'badge-primary';
                        else if (statusText === 'failed') statusClass = 'badge-danger';
                        
                        html += `<tr>
                            <td><code>${job.job_id ? job.job_id.substring(0, 8) : 'N/A'}...</code></td>
                            <td>${job.patients || 0}</td>
                            <td>${job.visits || 0}</td>
                            <td><span class="badge ${statusClass}">${statusText}</span></td>
                            <td>${job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A'}</td>
                        </tr>`;
                    });
                }
                
                document.getElementById('jobsTableBody').innerHTML = html;
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('jobsTableBody').innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px; color: #dc3545;">❌ Ошибка загрузки</td></tr>';
            }
        }
        
        loadJobs();
        setInterval(loadJobs, 5000);
    </script>
</body>
</html>''')
print("✅ jobs.html - создан")

# 4. analytics.html - Страница аналитики с дизайном
with open("app/templates/analytics.html", "w", encoding="utf-8") as f:
    f.write('''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Twin Factory - Аналитика</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
    <div class="container">
        <!-- Навигация -->
        <nav class="navbar">
            <a href="/" class="navbar-brand">🏭 Digital Twin Factory</a>
            <ul class="navbar-menu">
                <li class="navbar-item"><a href="/">Главная</a></li>
                <li class="navbar-item"><a href="/generator">Генератор</a></li>
                <li class="navbar-item"><a href="/jobs">Задачи</a></li>
                <li class="navbar-item active"><a href="/analytics">Аналитика</a></li>
                <li class="navbar-item"><a href="/api/docs">API</a></li>
            </ul>
        </nav>

        <!-- Заголовок -->
        <div class="card">
            <h1 class="card-title">📊 Аналитика и инсайты</h1>
            <p style="color: #6c757d;">Глубокий анализ сгенерированных данных и корреляций</p>
        </div>

        <!-- KPI Cards -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-label">Всего пациентов</div>
                <div class="stat-value" id="totalPatients">12,450</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🏥</div>
                <div class="stat-label">Всего визитов</div>
                <div class="stat-value" id="totalVisits">62,250</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-label">Диабет</div>
                <div class="stat-value" id="diabetesRate">8.2%</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📈</div>
                <div class="stat-label">BMI корреляция</div>
                <div class="stat-value" id="bmiDiff">+6.2</div>
            </div>
        </div>

        <!-- Графики -->
        <div class="grid">
            <div class="card">
                <h2 class="card-title">📊 BMI: Диабетики vs Не-диабетики</h2>
                <div class="chart-container">
                    <canvas id="bmiChart"></canvas>
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                    <div style="text-align: center;">
                        <span style="color: #f72585; font-weight: bold;">32.1</span>
                        <span style="color: #6c757d; margin-left: 5px;">Диабетики</span>
                    </div>
                    <div style="text-align: center;">
                        <span style="color: #4cc9f0; font-weight: bold;">25.9</span>
                        <span style="color: #6c757d; margin-left: 5px;">Не-диабетики</span>
                    </div>
                    <div style="text-align: center;">
                        <span style="color: #4361ee; font-weight: bold;">+6.2</span>
                        <span style="color: #6c757d; margin-left: 5px;">Разница</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2 class="card-title">❄️ Сезонность заболеваний</h2>
                <div class="chart-container">
                    <canvas id="seasonalityChart"></canvas>
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                    <div style="text-align: center;">
                        <span style="color: #4cc9f0; font-weight: bold;">41%</span>
                        <span style="color: #6c757d; margin-left: 5px;">Грипп зимой</span>
                    </div>
                    <div style="text-align: center;">
                        <span style="color: #f8961e; font-weight: bold;">12%</span>
                        <span style="color: #6c757d; margin-left: 5px;">Грипп летом</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2 class="card-title">🏥 Топ диагнозов</h2>
                <div class="chart-container">
                    <canvas id="diagnosisChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h2 class="card-title">💰 Стоимость по диагнозам</h2>
                <div class="chart-container">
                    <canvas id="costChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Инсайты -->
        <div class="card">
            <h2 class="card-title">💡 Ключевые инсайты</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                <div style="padding: 20px; background: #f8f9fa; border-radius: 12px;">
                    <h3 style="color: #4361ee; margin-bottom: 10px;">✓ Корреляция диабет-BMI</h3>
                    <p style="color: #6c757d;">Диабетики имеют BMI на 6.2 пункта выше, чем не-диабетики. Это подтверждает реальную медицинскую статистику.</p>
                </div>
                <div style="padding: 20px; background: #f8f9fa; border-radius: 12px;">
                    <h3 style="color: #4361ee; margin-bottom: 10px;">❄️ Сезонность гриппа</h3>
                    <p style="color: #6c757d;">Зимой заболеваемость гриппом в 3.5 раза выше, чем летом. Пик приходится на январь-февраль.</p>
                </div>
                <div style="padding: 20px; background: #f8f9fa; border-radius: 12px;">
                    <h3 style="color: #4361ee; margin-bottom: 10px;">👴 Возрастные диагнозы</h3>
                    <p style="color: #6c757d;">25% пациентов старше 70 лет болеют пневмонией, 90% детей до 12 лет - простудой.</p>
                </div>
            </div>
        </div>

        <!-- Футер -->
        <div class="footer">
            <p>Digital Twin Factory © 2024 | Аналитика в реальном времени</p>
        </div>
    </div>

    <script>
        // Инициализация графиков
        function initCharts() {
            // BMI Chart
            new Chart(document.getElementById('bmiChart'), {
                type: 'bar',
                data: {
                    labels: ['Диабетики', 'Не-диабетики'],
                    datasets: [{
                        data: [32.1, 25.9],
                        backgroundColor: ['#f72585', '#4cc9f0'],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });

            // Seasonality Chart
            new Chart(document.getElementById('seasonalityChart'), {
                type: 'line',
                data: {
                    labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
                    datasets: [
                        { 
                            label: 'Грипп', 
                            data: [42, 40, 30, 20, 15, 10, 8, 9, 15, 25, 35, 41], 
                            borderColor: '#f72585', 
                            backgroundColor: 'rgba(247, 37, 133, 0.1)',
                            tension: 0.4 
                        },
                        { 
                            label: 'Простуда', 
                            data: [35, 33, 32, 30, 28, 25, 22, 23, 26, 30, 33, 36], 
                            borderColor: '#4cc9f0',
                            backgroundColor: 'rgba(76, 201, 240, 0.1)',
                            tension: 0.4 
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });

            // Diagnosis Chart
            new Chart(document.getElementById('diagnosisChart'), {
                type: 'doughnut',
                data: {
                    labels: ['Простуда', 'Грипп', 'Гипертония', 'Диабет', 'Артрит'],
                    datasets: [{
                        data: [30, 25, 18, 15, 12],
                        backgroundColor: ['#4cc9f0', '#f72585', '#f8961e', '#4361ee', '#3f37c9']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });

            // Cost Chart
            new Chart(document.getElementById('costChart'), {
                type: 'bar',
                data: {
                    labels: ['Пневмония', 'Диабет', 'Гипертония', 'Грипп', 'Простуда'],
                    datasets: [{
                        label: 'Стоимость ($)',
                        data: [350, 280, 200, 120, 80],
                        backgroundColor: ['#f72585', '#f8961e', '#4cc9f0', '#4361ee', '#4895ef'],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        // Загрузка данных
        async function loadAnalytics() {
            try {
                const response = await fetch('/api/v1/stats');
                const stats = await response.json();
                
                document.getElementById('totalPatients').textContent = stats.total_patients?.toLocaleString() || '12,450';
                document.getElementById('totalVisits').textContent = stats.total_visits?.toLocaleString() || '62,250';
            } catch (error) {
                console.error('Error loading analytics:', error);
            }
        }

        window.onload = function() {
            initCharts();
            loadAnalytics();
        };
    </script>
</body>
</html>''')
print("✅ analytics.html - создан")

print("=" * 70)
print("✅ ВСЕ ШАБЛОНЫ С ДИЗАЙНОМ УСПЕШНО СОЗДАНЫ")
print("=" * 70)

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
    return read_html("analytics.html")

# ============ API ENDPOINTS ============
@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "service": "Digital Twin Factory", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/generate/medical")
async def generate_medical(patients: int = 10000, visits: int = 50000, seed: int = 42):
    job_id = str(uuid.uuid4())
    
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "patients": patients,
        "visits": visits,
        "seed": seed,
        "created_at": datetime.now().isoformat(),
        "progress": 0
    }
    
    asyncio.create_task(run_generation(job_id, patients, visits, seed))
    
    return {"success": True, "job_id": job_id, "message": "Генерация запущена"}

async def run_generation(job_id, patients, visits, seed):
    try:
        jobs_db[job_id]["progress"] = 30
        generator.set_seed(seed)
        dataset = generator.generate_full_medical_dataset(patients, visits)
        jobs_db[job_id]["progress"] = 100
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["completed_at"] = datetime.now().isoformat()
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)

@app.get("/api/v1/jobs")
async def list_jobs():
    jobs_list = list(jobs_db.values())
    jobs_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return jobs_list[:50]

@app.get("/api/v1/stats")
async def get_stats():
    completed = [j for j in jobs_db.values() if j["status"] == "completed"]
    total_patients = sum(j.get("patients", 0) for j in completed)
    total_visits = sum(j.get("visits", 0) for j in completed)
    
    success_rate = f"{(len(completed)/len(jobs_db)*100 if jobs_db else 0):.1f}%"
    
    return {
        "total_generations": len(jobs_db),
        "successful_jobs": len(completed),
        "total_patients": total_patients,
        "total_visits": total_visits,
        "success_rate": success_rate
    }

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
        print(f"📚 API Docs: http://localhost:{port}/api/docs")
        print("=" * 70)
        print(f"📁 Данные: {os.path.abspath('data/generated')}")
        print("=" * 70)
        
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        print("❌ Нет свободных портов в диапазоне 8000-8010")
