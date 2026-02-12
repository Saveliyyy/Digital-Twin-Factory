#!/usr/bin/env python3
import sys
import os

# Добавляем корневую папку проекта в путь Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import uvicorn
import json
import glob
import uuid
from datetime import datetime
from typing import Optional
import asyncio

# Импортируем наш генератор
from app.core.batch_generator import BatchGenerator

app = FastAPI(
    title="Digital Twin Factory",
    description="Фабрика цифровых двойников - генерация синтетических данных с корреляциями",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем необходимые папки
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)
os.makedirs("data/generated", exist_ok=True)
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Шаблоны
templates = Jinja2Templates(directory="app/templates")

# Хранилище задач
jobs_db = {}
generator = BatchGenerator(batch_size=10000)

# Веб-страницы
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/generator", response_class=HTMLResponse)
async def generator_page(request: Request):
    return templates.TemplateResponse("generator.html", {"request": request})

@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    return templates.TemplateResponse("jobs.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Аналитика</title>
        <link rel="stylesheet" href="/static/css/style.css">
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
                    <li class="navbar-item"><a href="/about">О проекте</a></li>
                </ul>
            </nav>
            <div class="card">
                <h1 class="card-title">📊 Аналитика</h1>
                <p>Страница в разработке</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>О проекте</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <div class="container">
            <nav class="navbar">
                <a href="/" class="navbar-brand">🏭 Digital Twin Factory</a>
                <ul class="navbar-menu">
                    <li class="navbar-item"><a href="/">Главная</a></li>
                    <li class="navbar-item"><a href="/generator">Генератор</a></li>
                    <li class="navbar-item"><a href="/jobs">Задачи</a></li>
                    <li class="navbar-item"><a href="/analytics">Аналитика</a></li>
                    <li class="navbar-item active"><a href="/about">О проекте</a></li>
                </ul>
            </nav>
            <div class="card">
                <h1 class="card-title">📘 О проекте</h1>
                <p><strong>Digital Twin Factory</strong> - система генерации синтетических данных с корреляциями</p>
                <p>Версия: 2.0.0</p>
                <p>Технологии: FastAPI, Polars, NumPy, NetworkX, Redis, PostgreSQL</p>
                <h3>Возможности:</h3>
                <ul>
                    <li>Генерация 10,000+ пациентов за 30 секунд</li>
                    <li>Корреляция диабет-BMI (разница +6.2)</li>
                    <li>Сезонность заболеваний (зимой грипп 40%)</li>
                    <li>Возрастные диагнозы</li>
                    <li>REST API с документацией</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# API endpoints
@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "service": "Digital Twin Factory",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/generate/medical")
async def generate_medical(
    patients: int = 10000,
    visits: int = 50000,
    seed: int = 42
):
    """Запуск генерации медицинского датасета"""
    
    job_id = str(uuid.uuid4())
    
    # Сохраняем задачу
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "patients": patients,
        "visits": visits,
        "seed": seed,
        "created_at": datetime.now().isoformat(),
        "progress": 0,
        "message": "Задача создана"
    }
    
    # Запускаем генерацию в фоне
    asyncio.create_task(run_generation(job_id, patients, visits, seed))
    
    return {
        "success": True,
        "job_id": job_id,
        "message": f"Генерация {patients} пациентов и {visits} визитов запущена"
    }

async def run_generation(job_id: str, patients: int, visits: int, seed: int):
    """Фоновая генерация данных"""
    try:
        jobs_db[job_id]["progress"] = 10
        jobs_db[job_id]["message"] = "Инициализация генератора..."
        
        generator.set_seed(seed)
        
        jobs_db[job_id]["progress"] = 30
        jobs_db[job_id]["message"] = "Генерация пациентов..."
        
        dataset = generator.generate_full_medical_dataset(patients, visits)
        
        jobs_db[job_id]["progress"] = 70
        jobs_db[job_id]["message"] = "Генерация визитов..."
        
        # Сохраняем результат
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"medical_dataset_{timestamp}.json"
        filepath = os.path.join("data/generated", filename)
        
        # Конвертируем datetime в строки
        patients_list = dataset['patients'].to_dicts()
        visits_list = dataset['visits'].to_dicts()
        
        for visit in visits_list:
            if 'date' in visit and visit['date']:
                if hasattr(visit['date'], 'isoformat'):
                    visit['date'] = visit['date'].isoformat()
                else:
                    visit['date'] = str(visit['date'])
        
        # Сохраняем в JSON
        output = {
            'generated_at': datetime.now().isoformat(),
            'job_id': job_id,
            'total_patients': len(patients_list),
            'total_visits': len(visits_list),
            'patients': patients_list[:100],  # Сохраняем только первые 100 для примера
            'visits': visits_list[:200]       # Сохраняем только первые 200 для примера
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        jobs_db[job_id]["progress"] = 100
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["completed_at"] = datetime.now().isoformat()
        jobs_db[job_id]["result_url"] = f"/api/v1/datasets/{job_id}"
        jobs_db[job_id]["file"] = filename
        jobs_db[job_id]["message"] = "Готово!"
        
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)
        jobs_db[job_id]["completed_at"] = datetime.now().isoformat()
        jobs_db[job_id]["message"] = f"Ошибка: {str(e)}"
        print(f"Error in generation {job_id}: {e}")
        import traceback
        traceback.print_exc()

@app.get("/api/v1/jobs")
async def list_jobs():
    """Список задач"""
    jobs_list = list(jobs_db.values())
    jobs_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return jobs_list[:50]

@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: str):
    """Детали задачи"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_db[job_id]

@app.delete("/api/v1/jobs/{job_id}")
async def delete_job(job_id: str):
    """Удаление задачи"""
    if job_id in jobs_db:
        del jobs_db[job_id]
    return {"success": True}

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Статус задачи для совместимости"""
    if task_id in jobs_db:
        job = jobs_db[task_id]
        return {
            "state": "SUCCESS" if job["status"] == "completed" else 
                    "FAILURE" if job["status"] == "failed" else
                    "PROGRESS",
            "meta": {
                "progress": job.get("progress", 0),
                "status": job.get("message", job["status"])
            }
        }
    return {"state": "PENDING", "meta": {"progress": 0, "status": "Waiting"}}

@app.get("/api/v1/stats")
async def get_stats():
    """Статистика"""
    completed = [j for j in jobs_db.values() if j["status"] == "completed"]
    total_patients = sum(j.get("patients", 0) for j in completed)
    total_visits = sum(j.get("visits", 0) for j in completed)
    
    return {
        "total_generations": len(jobs_db),
        "successful_jobs": len(completed),
        "total_patients": total_patients,
        "total_visits": total_visits,
        "success_rate": f"{(len(completed)/len(jobs_db)*100 if jobs_db else 0):.1f}%"
    }

@app.get("/api/v1/datasets/{job_id}")
async def download_dataset(job_id: str):
    """Скачать датасет"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    if "file" not in job:
        raise HTTPException(status_code=404, detail="File not found")
    
    filepath = os.path.join("data/generated", job["file"])
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        filepath,
        media_type="application/json",
        filename=job["file"]
    )

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 DIGITAL TWIN FACTORY - ПОЛНАЯ ВЕРСИЯ 2.0.0")
    print("=" * 70)
    print("✅ Веб-интерфейс: http://localhost:8000")
    print("✅ Генератор: http://localhost:8000/generator")
    print("✅ Задачи: http://localhost:8000/jobs")
    print("✅ API документация: http://localhost:8000/api/docs")
    print("=" * 70)
    print(f"📁 Данные сохраняются в: {os.path.abspath('data/generated')}")
    print("=" * 70)
    
    uvicorn.run(
        "app.main_full:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
