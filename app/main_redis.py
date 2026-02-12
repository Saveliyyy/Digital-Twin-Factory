from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
import uuid
from
from datetime import datetime
import os

from app.workers.celery_app import celery_app
from app.workers.tasks import generate_medical_dataset
from app.core.batch_generator import BatchGenerator

app = FastAPI(
    title="Digital Twin Factory",
    description="Фабрика цифровых двойников с Redis очередью",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
os.makedirs("app/static", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)
os.makedirs("data/generated", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Хранилище заданий
jobs = {}

@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница с дизайном"""
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/v1/health")
async def health():
    """Проверка здоровья сервиса"""
    # Проверяем Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        redis_status = "connected"
    except:
        redis_status = "disconnected"
    
    return {
        "status": "healthy",
        "service": "Digital Twin Factory",
        "version": "2.0.0",
        "redis": redis_status,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/generate/medical")
async def generate_medical(
    patients: int = 10000,
    visits: int = 50000,
    seed: int = 42
):
    """Запуск генерации медицинского датасета через Celery"""
    
    # Создаем задачу в Celery
    task = generate_medical_dataset.delay(patients, visits, seed)
    
    job_id = task.id
    
    # Сохраняем в локальное хранилище
    jobs[job_id] = {
        "task_id": job_id,
        "status": "pending",
        "patients": patients,
        "visits": visits,
        "seed": seed,
        "created_at": datetime.now().isoformat()
    }
    
    # Быстрая статистика для предпросмотра
    generator = BatchGenerator(batch_size=1000)
    generator.set_seed(seed)
    patients_sample = generator.generate_patients(10)
    visits_sample = generator.generate_visits(patients_sample, 20)
    
    diabetic_bmi = patients_sample.filter(pl.col('diabetes') == True)['bmi'].mean() or 0
    non_diabetic_bmi = patients_sample.filter(pl.col('diabetes') == False)['bmi'].mean() or 0
    
    return {
        "success": True,
        "job_id": job_id,
        "message": f"Задача запущена! Генерируется {patients} пациентов и {visits} визитов",
        "statistics": {
            "patients": patients,
            "visits": visits,
            "diabetes_rate": f"{patients_sample['diabetes'].mean():.1%}",
            "average_bmi": round(patients_sample['bmi'].mean(), 1),
            "average_visit_cost": f"${round(visits_sample['cost'].mean(), 2)}",
            "bmi_correlation": {
                "diabetic": round(diabetic_bmi, 1),
                "non_diabetic": round(non_diabetic_bmi, 1),
                "difference": round(diabetic_bmi - non_diabetic_bmi, 1)
            }
        }
    }

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Получение статуса задачи"""
    task = AsyncResult(task_id, app=celery_app)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'meta': {'progress': 0, 'status': 'Ожидание...'}
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'meta': task.info
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'meta': task.result
        }
    elif task.state == 'FAILURE':
        response = {
            'state': task.state,
            'meta': {
                'error': str(task.info),
                'progress': 0,
                'status': 'Ошибка'
            }
        }
    else:
        response = {
            'state': task.state,
            'meta': task.info
        }
    
    return response

@app.get("/api/v1/jobs")
async def list_jobs():
    """Список последних заданий"""
    # Получаем последние 10 заданий
    recent_jobs = list(jobs.values())[-10:]
    
    # Добавляем статусы из Celery
    for job in recent_jobs:
        task = AsyncResult(job['task_id'], app=celery_app)
        job['status'] = task.state.lower()
    
    return recent_jobs[::-1]  # Переворачиваем для отображения последних первыми

@app.get("/api/v1/stats")
async def get_stats():
    """Общая статистика"""
    total_jobs = len(jobs)
    
    # Считаем успешные
    successful = 0
    total_patients = 0
    total_visits = 0
    
    for job_id in jobs:
        task = AsyncResult(job_id, app=celery_app)
        if task.state == 'SUCCESS':
            successful += 1
            if task.result:
                total_patients += task.result.get('patients', 0)
                total_visits += task.result.get('visits', 0)
    
    return {
        "total_jobs": total_jobs,
        "successful_jobs": successful,
        "total_patients": total_patients,
        "total_visits": total_visits,
        "redis_status": "active"
    }

if __name__ == "__main__":
    import uvicorn
    import pl
    
    print("=" * 70)
print("DIGITAL TWIN FACTORY - FULL VERSION")
    print("=" * 70)
    print("FastAPI сервер")
    print("PostgreSQL база данных")
    print("Redis очереди")
    print("Celery воркеры")
    print("Генерация 10,000+ пациентов")
    print("Современный UI дизайн")
    print("=" * 70)
    print("Веб-интерфейс: http://localhost:8000")
    print("Документация API: http://localhost:8000/docs")
    print("Redis: localhost:6379")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
