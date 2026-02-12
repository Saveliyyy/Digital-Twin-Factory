from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import datetime

app = FastAPI(title="Digital Twin Factory")

@app.get("/", response_class=HTMLResponse)
async def root():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Digital Twin Factory</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial; margin: 40px; background: #f0f2f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            h1 {{ color: #1a73e8; }}
            .status {{ background: #e8f0fe; padding: 20px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Digital Twin Factory</h1>
            <div class="status">
                <h2>Статус: ONLINE</h2>
                <p>Сервер успешно запущен!</p>
                <p>Время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>FastAPI версия: 0.104.1</p>
            </div>
            <p>API документация: <a href="/docs">/docs</a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Digital Twin Factory"}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("DIGITAL TWIN FACTORY - ЗАПУСК")
    print("=" * 60)
    print("Сервер запущен: http://localhost:8000")
    print("Документация:  http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
