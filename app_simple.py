from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import uuid
import random
from datetime import datetime
import json

app = FastAPI(title="Digital Twin Factory")

@app.get("/", response_class=HTMLResponse)
async def root():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Digital Twin Factory</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                color: #333;
            }
            h1 { color: #667eea; }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 5px;
            }
            pre {
                background: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
                overflow: auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Digital Twin Factory</h1>
            <p>Сервис работает! Версия 1.0.0</p>
            <a href="/docs" class="btn">Документация API</a>
            <a href="/generate-test" class="btn">Тестовая генерация</a>
            <h2>Статус:</h2>
            <pre>Сервер запущен: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</pre>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Digital Twin Factory"}

@app.get("/generate-test")
async def generate_test():
    """Быстрая тестовая генерация"""
    
    random.seed(42)
    
    # Пациенты
    patients = []
    for i in range(10):
        diabetes = random.random() < 0.08
        patients.append({
            "id": str(uuid.uuid4()),
            "age": random.randint(18, 90),
            "gender": random.choice(["Male", "Female"]),
            "diabetes": diabetes,
            "bmi": round(random.uniform(28, 40) if diabetes else random.uniform(18.5, 35), 1)
        })
    
    # Визиты
    visits = []
    for i in range(20):
        patient = random.choice(patients)
        month = random.randint(1, 12)
        
        if month in [11, 12, 1, 2]:
            diagnosis = random.choice(["Flu", "Cold", "Pneumonia"])
        else:
            diagnosis = random.choice(["Cold", "Allergy", "Hypertension"])
        
        visits.append({
            "id": str(uuid.uuid4()),
            "patient_id": patient["id"],
            "date": f"2024-{month:02d}-{random.randint(1,28):02d}",
            "diagnosis": diagnosis,
            "cost": round(random.uniform(50, 300), 2)
        })
    
    return {
        "status": "success",
        "patients": len(patients),
        "visits": len(visits),
        "sample": {
            "patients": patients[:3],
            "visits": visits[:5]
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Запуск Digital Twin Factory")
    print("=" * 60)
    print("http://localhost:8000")
    print("http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
