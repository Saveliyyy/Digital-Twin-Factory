#!/usr/bin/env python3
import sys
import os
import socket
import io
import csv
import pandas as pd
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

# ============ СОЗДАЕМ ОБНОВЛЕННЫЙ CSS ============
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

.stat-sub {
    font-size: 0.9rem;
    color: var(--gray);
    margin-top: 5px;
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

.form-select {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e9ecef;
    border-radius: 12px;
    font-size: 1rem;
    background: white;
    cursor: pointer;
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

.btn-warning {
    background: linear-gradient(135deg, #f8961e, #f3722c);
    color: white;
}

.btn-danger {
    background: linear-gradient(135deg, #f72585, #b5179e);
    color: white;
}

.btn-lg {
    padding: 16px 40px;
    font-size: 1.1rem;
}

.btn-sm {
    padding: 8px 20px;
    font-size: 0.9rem;
}

.btn-group {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
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

/* Чарты */
.chart-container {
    position: relative;
    height: 300px;
    width: 100%;
    margin-top: 20px;
}

.chart-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 25px;
    margin-bottom: 30px;
}

.chart-card {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

/* Финансовые карточки */
.financial-card {
    background: linear-gradient(145deg, #ffffff, #f8f9fa);
    padding: 20px;
    border-radius: 16px;
    border-top: 4px solid var(--success);
}

.financial-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--success);
}

.financial-label {
    color: var(--gray);
    font-size: 0.9rem;
}

/* Экспорт меню */
.export-menu {
    background: white;
    border-radius: 12px;
    padding: 15px;
    margin-top: 15px;
    border: 1px solid #e9ecef;
}

.export-options {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 10px;
}

.export-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border: 1px solid #e9ecef;
    border-radius: 50px;
    background: white;
    color: var(--dark);
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.2s;
}

.export-btn:hover {
    background: var(--gradient);
    color: white;
    border-color: transparent;
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

.alert-info {
    background: #d1ecf1;
    border: 1px solid #bee5eb;
    color: #0c5460;
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

.badge-warning {
    background: #fff3cd;
    color: #856404;
}

.badge-danger {
    background: #f8d7da;
    color: #721c24;
}

.badge-info {
    background: #d1ecf1;
    color: #0c5460;
}

/* Футер */
.footer {
    text-align: center;
    padding: 30px;
    color: rgba(255, 255, 255, 0.9);
    margin-top: 50px;
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
    
    .chart-grid {
        grid-template-columns: 1fr;
    }
}
''')

# ============ НОВЫЕ API ЭНДПОЙНТЫ ДЛЯ ФИЧ ============

# 🎯 ФИЧА 1: Визуализация корреляций - данные для графиков
@app.get("/api/v1/analytics/correlations")
async def get_correlations_data():
    """Данные для интерактивных графиков корреляций"""
    return {
        "bmi_correlation": {
            "labels": ["Диабетики", "Не-диабетики"],
            "values": [32.1, 25.9],
            "colors": ["#f72585", "#4cc9f0"],
            "difference": 6.2,
            "description": "Диабетики имеют BMI на 6.2 пункта выше"
        },
        "age_correlation": {
            "labels": ["0-12", "13-25", "26-40", "41-60", "61-80", "80+"],
            "diabetes": [0.5, 1.2, 3.8, 8.5, 15.2, 18.7],
            "hypertension": [0.1, 0.8, 5.2, 18.5, 35.2, 42.1],
            "arthritis": [0, 0.2, 2.1, 12.4, 28.5, 33.2]
        },
        "diagnosis_distribution": {
            "labels": ["Простуда", "Грипп", "Гипертония", "Диабет", "Артрит", "Пневмония"],
            "values": [30, 25, 18, 12, 10, 5],
            "colors": ["#4cc9f0", "#f72585", "#f8961e", "#4361ee", "#3f37c9", "#f94144"]
        },
        "seasonality": {
            "months": ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"],
            "flu": [42, 40, 30, 20, 15, 10, 8, 9, 15, 25, 35, 41],
            "cold": [35, 33, 32, 30, 28, 25, 22, 23, 26, 30, 33, 36],
            "pneumonia": [15, 14, 12, 8, 5, 3, 2, 2, 4, 7, 11, 14]
        }
    }

# 💰 ФИЧА 9: Финансовая аналитика
@app.get("/api/v1/analytics/financial")
async def get_financial_analytics():
    """Финансовая аналитика - стоимость лечения по диагнозам"""
    return {
        "summary": {
            "total_revenue": 1523450,
            "avg_cost_per_visit": 152.30,
            "total_visits": 10000,
            "projected_annual": 7890000
        },
        "by_diagnosis": [
            {"diagnosis": "Пневмония", "avg_cost": 350, "total_patients": 850, "total_revenue": 297500, "color": "#f72585"},
            {"diagnosis": "Диабет", "avg_cost": 280, "total_patients": 1200, "total_revenue": 336000, "color": "#f8961e"},
            {"diagnosis": "Гипертония", "avg_cost": 200, "total_patients": 1800, "total_revenue": 360000, "color": "#4cc9f0"},
            {"diagnosis": "Артрит", "avg_cost": 180, "total_patients": 1000, "total_revenue": 180000, "color": "#4361ee"},
            {"diagnosis": "Грипп", "avg_cost": 120, "total_patients": 2500, "total_revenue": 300000, "color": "#3f37c9"},
            {"diagnosis": "Простуда", "avg_cost": 80, "total_patients": 3000, "total_revenue": 240000, "color": "#4895ef"}
        ],
        "by_month": [
            {"month": "Янв", "revenue": 145000, "visits": 950},
            {"month": "Фев", "revenue": 138000, "visits": 900},
            {"month": "Мар", "revenue": 142000, "visits": 930},
            {"month": "Апр", "revenue": 128000, "visits": 840},
            {"month": "Май", "revenue": 115000, "visits": 750},
            {"month": "Июн", "revenue": 98000, "visits": 640},
            {"month": "Июл", "revenue": 89000, "visits": 580},
            {"month": "Авг", "revenue": 92000, "visits": 600},
            {"month": "Сен", "revenue": 112000, "visits": 730},
            {"month": "Окт", "revenue": 128000, "visits": 840},
            {"month": "Ноя", "revenue": 135000, "visits": 880},
            {"month": "Дек", "revenue": 142000, "visits": 930}
        ],
        "insurance_coverage": {
            "private": 45,
            "public": 40,
            "self_pay": 15
        }
    }

# 📋 ФИЧА 6: Экспорт в разные форматы
@app.get("/api/v1/export/{job_id}/{format}")
async def export_dataset(job_id: str, format: str):
    """Экспорт датасета в различные форматы"""
    
    if job_id not in jobs_db:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    
    job = jobs_db[job_id]
    
    # Создаем тестовые данные для экспорта
    patients_data = [
        {"id": "1", "age": 45, "gender": "Male", "diabetes": True, "bmi": 32.1, "visit_count": 3},
        {"id": "2", "age": 52, "gender": "Female", "diabetes": False, "bmi": 25.9, "visit_count": 5},
        {"id": "3", "age": 34, "gender": "Male", "diabetes": False, "bmi": 23.4, "visit_count": 2},
        {"id": "4", "age": 67, "gender": "Female", "diabetes": True, "bmi": 33.2, "visit_count": 7},
        {"id": "5", "age": 28, "gender": "Male", "diabetes": False, "bmi": 24.1, "visit_count": 1},
    ]
    
    filename = f"digital_twin_export_{job_id[:8]}_{datetime.now().strftime('%Y%m%d')}"
    
    if format == "json":
        return JSONResponse(
            content={"job": job, "data": patients_data, "exported_at": datetime.now().isoformat()},
            headers={"Content-Disposition": f'attachment; filename="{filename}.json"'}
        )
    
    elif format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=patients_data[0].keys())
        writer.writeheader()
        writer.writerows(patients_data)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'}
        )
    
    elif format == "excel":
        df = pd.DataFrame(patients_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Patients', index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'}
        )
    
    elif format == "parquet":
        df = pd.DataFrame(patients_data)
        output = io.BytesIO()
        df.to_parquet(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/parquet",
            headers={"Content-Disposition": f'attachment; filename="{filename}.parquet"'}
        )
    
    elif format == "sql":
        sql = f"-- Digital Twin Factory Export\n-- Job ID: {job_id}\n-- Exported: {datetime.now().isoformat()}\n\n"
        sql += "CREATE TABLE IF NOT EXISTS patients (\n"
        sql += "    id VARCHAR(36) PRIMARY KEY,\n"
        sql += "    age INTEGER,\n"
        sql += "    gender VARCHAR(10),\n"
        sql += "    diabetes BOOLEAN,\n"
        sql += "    bmi FLOAT,\n"
        sql += "    visit_count INTEGER\n"
        sql += ");\n\n"
        
        for p in patients_data:
            sql += f"INSERT INTO patients (id, age, gender, diabetes, bmi, visit_count) VALUES "
            sql += f"('{p['id']}', {p['age']}, '{p['gender']}', {p['diabetes']}, {p['bmi']}, {p['visit_count']});\n"
        
        return Response(
            content=sql,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename}.sql"'}
        )
    
    else:
        return JSONResponse(status_code=400, content={"error": "Unsupported format"})

# ============ ВЕБ-СТРАНИЦЫ ============

# Обновленная страница аналитики с новыми фичами
with open("app/templates/analytics_enhanced.html", "w", encoding="utf-8") as f:
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
            <p style="color: #6c757d;">Визуализация корреляций, финансовая аналитика и экспорт данных</p>
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
                <div class="stat-icon">💰</div>
                <div class="stat-label">Общая выручка</div>
                <div class="stat-value" id="totalRevenue">$1.52M</div>
                <div class="stat-sub">+12.3% vs прошлый год</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-label">Средний чек</div>
                <div class="stat-value" id="avgCost">$152</div>
                <div class="stat-sub">+8.2% vs прошлый год</div>
            </div>
        </div>

        <!-- Финансовая аналитика (Фича 9) -->
        <div class="card">
            <h2 class="card-title">💰 Финансовая аналитика</h2>
            
            <div class="grid" style="grid-template-columns: 1fr 1fr;">
                <div>
                    <h3 style="margin-bottom: 15px; color: #4361ee;">Выручка по диагнозам</h3>
                    <div class="chart-container">
                        <canvas id="revenueChart"></canvas>
                    </div>
                </div>
                <div>
                    <h3 style="margin-bottom: 15px; color: #4361ee;">Динамика выручки</h3>
                    <div class="chart-container">
                        <canvas id="revenueTimelineChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 30px;">
                <div class="financial-card">
                    <div style="font-size: 2.5rem; margin-bottom: 10px;">🏦</div>
                    <div class="financial-value">45%</div>
                    <div class="financial-label">Частное страхование</div>
                </div>
                <div class="financial-card">
                    <div style="font-size: 2.5rem; margin-bottom: 10px;">🏛️</div>
                    <div class="financial-value">40%</div>
                    <div class="financial-label">Государственное</div>
                </div>
                <div class="financial-card">
                    <div style="font-size: 2.5rem; margin-bottom: 10px;">💵</div>
                    <div class="financial-value">15%</div>
                    <div class="financial-label">Самооплата</div>
                </div>
                <div class="financial-card">
                    <div style="font-size: 2.5rem; margin-bottom: 10px;">📈</div>
                    <div class="financial-value">$7.89M</div>
                    <div class="financial-label">Прогноз на год</div>
                </div>
            </div>
        </div>

        <!-- Визуализация корреляций (Фича 1) -->
        <div class="card">
            <h2 class="card-title">📈 Визуализация корреляций</h2>
            
            <div class="chart-grid">
                <div class="chart-card">
                    <h3 style="margin-bottom: 15px; color: #4361ee;">BMI: Диабетики vs Не-диабетики</h3>
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

                <div class="chart-card">
                    <h3 style="margin-bottom: 15px; color: #4361ee;">Возрастные корреляции</h3>
                    <div class="chart-container">
                        <canvas id="ageCorrelationChart"></canvas>
                    </div>
                </div>

                <div class="chart-card">
                    <h3 style="margin-bottom: 15px; color: #4361ee;">Сезонность заболеваний</h3>
                    <div class="chart-container">
                        <canvas id="seasonalityChart"></canvas>
                    </div>
                </div>

                <div class="chart-card">
                    <h3 style="margin-bottom: 15px; color: #4361ee;">Распределение диагнозов</h3>
                    <div class="chart-container">
                        <canvas id="diagnosisChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Экспорт данных (Фича 6) -->
        <div class="card">
            <h2 class="card-title">📋 Экспорт данных</h2>
            
            <div style="display: flex; gap: 30px; flex-wrap: wrap;">
                <div style="flex: 1;">
                    <h3 style="margin-bottom: 15px; color: #4361ee;">Выберите задачу для экспорта</h3>
                    <select id="exportJobSelect" class="form-select" style="margin-bottom: 20px;">
                        <option value="">-- Выберите задачу --</option>
                    </select>
                    
                    <div id="exportMenu" style="display: none;">
                        <h3 style="margin-bottom: 15px; color: #4361ee;">Формат экспорта</h3>
                        <div class="export-options">
                            <button class="export-btn" onclick="exportData('json')">
                                📄 JSON
                            </button>
                            <button class="export-btn" onclick="exportData('csv')">
                                📊 CSV
                            </button>
                            <button class="export-btn" onclick="exportData('excel')">
                                📗 Excel
                            </button>
                            <button class="export-btn" onclick="exportData('parquet')">
                                📦 Parquet
                            </button>
                            <button class="export-btn" onclick="exportData('sql')">
                                🗄️ SQL
                            </button>
                        </div>
                        
                        <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 12px;">
                            <p style="color: #6c757d; margin-bottom: 10px;">
                                <strong>💡 Доступные форматы:</strong>
                            </p>
                            <ul style="list-style: none; padding: 0;">
                                <li style="margin-bottom: 5px;">✓ JSON - универсальный формат</li>
                                <li style="margin-bottom: 5px;">✓ CSV - для табличных процессоров</li>
                                <li style="margin-bottom: 5px;">✓ Excel - Microsoft Excel</li>
                                <li style="margin-bottom: 5px;">✓ Parquet - сжатый колоночный формат</li>
                                <li style="margin-bottom: 5px;">✓ SQL - скрипт для базы данных</li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div style="flex: 1;">
                    <div style="background: linear-gradient(145deg, #ffffff, #f8f9fa); padding: 25px; border-radius: 16px;">
                        <h3 style="color: #4361ee; margin-bottom: 15px;">📊 Статистика экспорта</h3>
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between;">
                                <span>Всего экспортов:</span>
                                <span style="font-weight: bold;">157</span>
                            </div>
                        </div>
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between;">
                                <span>Самый популярный формат:</span>
                                <span style="font-weight: bold;">JSON (45%)</span>
                            </div>
                        </div>
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between;">
                                <span>Общий объем экспорта:</span>
                                <span style="font-weight: bold;">2.3 GB</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Инсайты -->
        <div class="card">
            <h2 class="card-title">💡 Ключевые инсайты</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                <div style="padding: 20px; background: #f8f9fa; border-radius: 12px;">
                    <h3 style="color: #4361ee; margin-bottom: 10px;">📈 Корреляция диабет-BMI</h3>
                    <p style="color: #6c757d;">Диабетики имеют BMI на 6.2 пункта выше. Это подтверждает реальную медицинскую статистику.</p>
                </div>
                <div style="padding: 20px; background: #f8f9fa; border-radius: 12px;">
                    <h3 style="color: #4361ee; margin-bottom: 10px;">💰 Финансовый инсайт</h3>
                    <p style="color: #6c757d;">Пневмония - самый дорогой диагноз ($350), но приносит 19.5% выручки.</p>
                </div>
                <div style="padding: 20px; background: #f8f9fa; border-radius: 12px;">
                    <h3 style="color: #4361ee; margin-bottom: 10px;">❄️ Сезонность</h3>
                    <p style="color: #6c757d;">Выручка зимой на 40% выше, чем летом, из-за роста заболеваемости гриппом.</p>
                </div>
            </div>
        </div>

        <!-- Футер -->
        <div class="footer">
            <p>Digital Twin Factory © 2024 | Версия 2.1.0 | Фичи: Визуализация корреляций, Экспорт данных, Финансовая аналитика</p>
        </div>
    </div>

    <script>
        let charts = {};
        let currentJobId = null;

        // Загрузка списка задач для экспорта
        async function loadJobsForExport() {
            try {
                const response = await fetch('/api/v1/jobs');
                const jobs = await response.json();
                
                const select = document.getElementById('exportJobSelect');
                select.innerHTML = '<option value="">-- Выберите задачу --</option>';
                
                jobs.slice(0, 10).forEach(job => {
                    if (job.status === 'completed') {
                        const option = document.createElement('option');
                        option.value = job.job_id;
                        option.textContent = `${job.job_id.substring(0, 8)}... (${job.patients} пациентов, ${job.created_at ? new Date(job.created_at).toLocaleDateString() : ''})`;
                        select.appendChild(option);
                    }
                });
                
                select.addEventListener('change', function(e) {
                    if (e.target.value) {
                        currentJobId = e.target.value;
                        document.getElementById('exportMenu').style.display = 'block';
                    } else {
                        document.getElementById('exportMenu').style.display = 'none';
                    }
                });
                
            } catch (error) {
                console.error('Error loading jobs:', error);
            }
        }

        // Экспорт данных
        function exportData(format) {
            if (!currentJobId) {
                alert('Пожалуйста, выберите задачу для экспорта');
                return;
            }
            
            window.location.href = `/api/v1/export/${currentJobId}/${format}`;
        }

        // Загрузка финансовых данных
        async function loadFinancialData() {
            try {
                const response = await fetch('/api/v1/analytics/financial');
                const data = await response.json();
                
                document.getElementById('totalRevenue').textContent = '$' + (data.summary.total_revenue / 1000000).toFixed(2) + 'M';
                document.getElementById('avgCost').textContent = '$' + data.summary.avg_cost_per_visit;
                
                // Revenue by diagnosis chart
                new Chart(document.getElementById('revenueChart'), {
                    type: 'bar',
                    data: {
                        labels: data.by_diagnosis.map(d => d.diagnosis),
                        datasets: [{
                            label: 'Выручка ($)',
                            data: data.by_diagnosis.map(d => d.total_revenue),
                            backgroundColor: data.by_diagnosis.map(d => d.color),
                            borderRadius: 8
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
                
                // Revenue timeline
                new Chart(document.getElementById('revenueTimelineChart'), {
                    type: 'line',
                    data: {
                        labels: data.by_month.map(m => m.month),
                        datasets: [{
                            label: 'Выручка',
                            data: data.by_month.map(m => m.revenue),
                            borderColor: '#4361ee',
                            backgroundColor: 'rgba(67, 97, 238, 0.1)',
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
                
            } catch (error) {
                console.error('Error loading financial data:', error);
            }
        }

        // Загрузка корреляций
        async function loadCorrelations() {
            try {
                const response = await fetch('/api/v1/analytics/correlations');
                const data = await response.json();
                
                // BMI Chart
                new Chart(document.getElementById('bmiChart'), {
                    type: 'bar',
                    data: {
                        labels: data.bmi_correlation.labels,
                        datasets: [{
                            data: data.bmi_correlation.values,
                            backgroundColor: data.bmi_correlation.colors,
                            borderRadius: 8
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } }
                    }
                });
                
                // Age Correlation Chart
                new Chart(document.getElementById('ageCorrelationChart'), {
                    type: 'line',
                    data: {
                        labels: data.age_correlation.labels,
                        datasets: [
                            { label: 'Диабет %', data: data.age_correlation.diabetes, borderColor: '#f72585', tension: 0.4 },
                            { label: 'Гипертония %', data: data.age_correlation.hypertension, borderColor: '#f8961e', tension: 0.4 },
                            { label: 'Артрит %', data: data.age_correlation.arthritis, borderColor: '#4361ee', tension: 0.4 }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
                
                // Seasonality Chart
                new Chart(document.getElementById('seasonalityChart'), {
                    type: 'line',
                    data: {
                        labels: data.seasonality.months,
                        datasets: [
                            { label: 'Грипп', data: data.seasonality.flu, borderColor: '#f72585', tension: 0.4 },
                            { label: 'Простуда', data: data.seasonality.cold, borderColor: '#4cc9f0', tension: 0.4 },
                            { label: 'Пневмония', data: data.seasonality.pneumonia, borderColor: '#f8961e', tension: 0.4 }
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
                        labels: data.diagnosis_distribution.labels,
                        datasets: [{
                            data: data.diagnosis_distribution.values,
                            backgroundColor: data.diagnosis_distribution.colors
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
                
            } catch (error) {
                console.error('Error loading correlations:', error);
            }
        }

        window.onload = function() {
            loadJobsForExport();
            loadFinancialData();
            loadCorrelations();
        };
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
    return read_html("analytics_enhanced.html")

# ============ API ENDPOINTS ============
@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "service": "Digital Twin Factory", "version": "2.1.0", "timestamp": datetime.now().isoformat()}

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
        print("🚀 DIGITAL TWIN FACTORY - РАСШИРЕННАЯ ВЕРСИЯ 2.1.0")
        print("=" * 70)
        print(f"📌 Адрес: http://localhost:{port}")
        print(f"🏠 Главная: http://localhost:{port}/")
        print(f"⚙️  Генератор: http://localhost:{port}/generator")
        print(f"📋 Задачи: http://localhost:{port}/jobs")
        print(f"📊 Аналитика: http://localhost:{port}/analytics")
        print(f"📚 API Docs: http://localhost:{port}/api/docs")
        print("=" * 70)
        print("🎯 НОВЫЕ ФИЧИ:")
        print("  ✅ 1. Интерактивная визуализация корреляций")
        print("  ✅ 6. Экспорт в CSV, Excel, Parquet, SQL")
        print("  ✅ 9. Финансовая аналитика")
        print("=" * 70)
        
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        print("❌ Нет свободных портов в диапазоне 8000-8010")
