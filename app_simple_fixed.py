from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uuid
from datetime import datetime
import os

app = FastAPI(title="Digital Twin Factory")

# Static files
os.makedirs("app/static", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)

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
                font-family: 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 25px;
                font-size: 16px;
                cursor: pointer;
                margin: 10px 0;
                text-decoration: none;
                display: inline-block;
            }
            .success {
                background: #d4edda;
                color: #155724;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏭 Digital Twin Factory</h1>
            <p>Сервис генерации синтетических данных с корреляциями</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3>✅ Статус: ONLINE</h3>
                <p>Сервер успешно запущен!</p>
                <p>Версия: 1.0.0</p>
                <p>Время: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
            </div>
            
            <a href="/docs" class="btn">📚 Документация API</a>
            <a href="/generate-test" class="btn">🚀 Тест генерации</a>
            
            <div class="success" id="result" style="display: none;"></div>
        </div>
        
        <script>
            async function testGeneration() {
                try {
                    const response = await fetch('/generate-test');
                    const data = await response.json();
                    document.getElementById('result').style.display = 'block';
                    document.getElementById('result').innerHTML = 
                        '✅ Генерация: ' + data.patients + ' пациентов, ' + 
                        data.visits + ' визитов<br>' +
                        '📊 Диабет: ' + (data.stats?.diabetes_rate || 'N/A');
                } catch(e) {
                    alert('Ошибка: ' + e.message);
                }
            }
        </script>
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
    import random
    import uuid
    
    random.seed(42)
    
    patients = []
    for i in range(10):
        diabetes = random.random() < 0.08
        patients.append({
            "id": str(uuid.uuid4()),
            "age": random.randint(18, 90),
            "diabetes": diabetes,
            "bmi": round(random.uniform(28, 40) if diabetes else random.uniform(18.5, 35), 1)
        })
    
    diabetes_rate = sum(p['diabetes'] for p in patients) / len(patients)
    
    return {
        "status": "success",
        "patients": len(patients),
        "visits": 20,
        "stats": {
            "diabetes_rate": f"{diabetes_rate:.1%}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 Digital Twin Factory - Упрощенная версия")
    print("=" * 60)
    print("Сервер запущен: http://localhost:8000")
    print("Документация: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
