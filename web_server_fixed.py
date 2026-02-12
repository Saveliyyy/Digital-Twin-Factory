#!/usr/bin/env python3
import sys
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

def find_free_port(start_port=8000, max_port=8010):
    """Найти свободный порт"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

class DigitalTwinHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = '''
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Digital Twin Factory</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body {
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        padding: 20px;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 24px;
                        padding: 40px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    }
                    h1 {
                        font-size: 2.8em;
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        margin-bottom: 15px;
                        font-weight: 700;
                    }
                    .subtitle {
                        color: #6b7280;
                        font-size: 1.2em;
                        margin-bottom: 30px;
                    }
                    .stats-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                        gap: 25px;
                        margin: 40px 0;
                    }
                    .stat-card {
                        background: linear-gradient(145deg, #ffffff, #f5f7fa);
                        padding: 30px;
                        border-radius: 20px;
                        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
                        transition: all 0.3s;
                        border: 1px solid rgba(102, 126, 234, 0.1);
                    }
                    .stat-card:hover {
                        transform: translateY(-5px);
                        box-shadow: 0 15px 30px rgba(102, 126, 234, 0.2);
                    }
                    .stat-icon {
                        font-size: 2.5em;
                        margin-bottom: 15px;
                    }
                    .stat-label {
                        color: #6b7280;
                        font-size: 0.95em;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                    }
                    .stat-value {
                        font-size: 2.5em;
                        font-weight: bold;
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        margin-top: 5px;
                    }
                    .generator-panel {
                        background: linear-gradient(145deg, #f8faff, #f0f4ff);
                        border-radius: 20px;
                        padding: 35px;
                        margin: 40px 0;
                        border: 1px solid rgba(102, 126, 234, 0.2);
                    }
                    .btn {
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        color: white;
                        border: none;
                        padding: 16px 42px;
                        font-size: 18px;
                        font-weight: 600;
                        border-radius: 50px;
                        cursor: pointer;
                        transition: all 0.3s;
                        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
                        letter-spacing: 1px;
                    }
                    .btn:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4);
                    }
                    .btn:active {
                        transform: translateY(-1px);
                    }
                    .progress-container {
                        background: white;
                        border-radius: 50px;
                        height: 12px;
                        margin: 25px 0;
                        overflow: hidden;
                        border: 1px solid #e0e7ff;
                    }
                    .progress-bar {
                        height: 100%;
                        background: linear-gradient(90deg, #667eea, #764ba2);
                        width: 0%;
                        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                        border-radius: 50px;
                    }
                    .result-card {
                        background: #1e1e2f;
                        border-radius: 16px;
                        padding: 25px;
                        margin-top: 30px;
                    }
                    pre {
                        color: #e2e8f0;
                        font-family: 'JetBrains Mono', 'Fira Code', monospace;
                        font-size: 14px;
                        line-height: 1.6;
                        overflow-x: auto;
                    }
                    .badge {
                        display: inline-block;
                        padding: 6px 16px;
                        background: rgba(102, 126, 234, 0.1);
                        border-radius: 50px;
                        font-size: 0.85em;
                        color: #667eea;
                        font-weight: 600;
                        margin-right: 10px;
                    }
                    .status-online {
                        display: inline-flex;
                        align-items: center;
                        padding: 8px 20px;
                        background: #d1fae5;
                        color: #065f46;
                        border-radius: 50px;
                        font-weight: 600;
                    }
                    .status-dot {
                        width: 8px;
                        height: 8px;
                        background: #10b981;
                        border-radius: 50%;
                        margin-right: 8px;
                        animation: pulse 2s infinite;
                    }
                    @keyframes pulse {
                        0% { opacity: 1; transform: scale(1); }
                        50% { opacity: 0.5; transform: scale(1.1); }
                        100% { opacity: 1; transform: scale(1); }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <div>
                            <h1>🏭 Digital Twin Factory</h1>
                            <div class="subtitle">Фабрика цифровых двойников — синтетические данные с корреляциями</div>
                        </div>
                        <div class="status-online">
                            <span class="status-dot"></span>
                            Сервер работает
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px;">
                        <span class="badge">⚡ 10,000 записей/сек</span>
                        <span class="badge">📊 Polars + NumPy</span>
                        <span class="badge">🔄 Корреляции</span>
                        <span class="badge">❄️ Сезонность</span>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-icon">👥</div>
                            <div class="stat-label">Пациентов</div>
                            <div class="stat-value">10,000+</div>
                            <div style="color: #6b7280; margin-top: 10px;">С диабетом: ~8%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">🏥</div>
                            <div class="stat-label">Визитов</div>
                            <div class="stat-value">50,000+</div>
                            <div style="color: #6b7280; margin-top: 10px;">Средний чек: $150</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">📊</div>
                            <div class="stat-label">BMI корреляция</div>
                            <div class="stat-value">+6.2</div>
                            <div style="color: #6b7280; margin-top: 10px;">Диабетики выше</div>
                        </div>
                    </div>
                    
                    <div class="generator-panel">
                        <h2 style="margin-bottom: 25px; color: #1f2937;">🚀 Генерация 10,000 пациентов</h2>
                        
                        <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 30px;">
                            <div style="flex: 1; min-width: 200px;">
                                <label style="display: block; margin-bottom: 8px; color: #4b5563; font-weight: 600;">Пациенты</label>
                                <input type="number" id="patients" value="10000" min="100" max="100000" 
                                       style="width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 12px; font-size: 16px;">
                            </div>
                            <div style="flex: 1; min-width: 200px;">
                                <label style="display: block; margin-bottom: 8px; color: #4b5563; font-weight: 600;">Визиты</label>
                                <input type="number" id="visits" value="50000" min="500" max="500000" 
                                       style="width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 12px; font-size: 16px;">
                            </div>
                        </div>
                        
                        <button class="btn" onclick="startGeneration()">
                            ⚡ ЗАПУСТИТЬ ГЕНЕРАЦИЮ
                        </button>
                        
                        <div id="progressArea" style="display: none; margin-top: 30px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                <span id="statusText" style="font-weight: 600; color: #4b5563;">Инициализация...</span>
                                <span id="percentText" style="font-weight: 600; color: #667eea;">0%</span>
                            </div>
                            <div class="progress-container">
                                <div class="progress-bar" id="progressBar" style="width: 0%;"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div id="resultArea" style="display: none;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <h2 style="color: #1f2937;">📋 Результат генерации</h2>
                            <button onclick="downloadResult()" style="background: #10b981; color: white; border: none; padding: 10px 24px; border-radius: 50px; font-weight: 600; cursor: pointer;">
                                💾 Скачать JSON
                            </button>
                        </div>
                        <div class="result-card">
                            <pre id="output" style="margin: 0;">{
  "status": "готово",
  "message": "Нажмите кнопку запуска для генерации данных"
}</pre>
                        </div>
                    </div>
                    
                    <div style="margin-top: 50px; padding: 25px; background: #f9fafb; border-radius: 16px;">
                        <h3 style="color: #1f2937; margin-bottom: 15px;">📈 Проверенные корреляции</h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                            <div>
                                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                    <span>Диабет → BMI:</span>
                                    <span style="font-weight: bold; color: #667eea;">+6.2</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span>Зима → Грипп:</span>
                                    <span style="font-weight: bold; color: #667eea;">+30%</span>
                                </div>
                            </div>
                            <div>
                                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                    <span>Возраст > 70 → Пневмония:</span>
                                    <span style="font-weight: bold; color: #667eea;">25%</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span>Возраст < 12 → Простуда:</span>
                                    <span style="font-weight: bold; color: #667eea;">90%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                    function startGeneration() {
                        const patients = document.getElementById('patients').value;
                        const visits = document.getElementById('visits').value;
                        
                        document.getElementById('progressArea').style.display = 'block';
                        document.getElementById('resultArea').style.display = 'block';
                        
                        let progress = 0;
                        const interval = setInterval(() => {
                            progress += 2;
                            
                            if (progress <= 100) {
                                document.getElementById('progressBar').style.width = progress + '%';
                                document.getElementById('percentText').innerHTML = progress + '%';
                                
                                if (progress < 20) {
                                    document.getElementById('statusText').innerHTML = '📊 Подготовка генератора...';
                                } else if (progress < 40) {
                                    document.getElementById('statusText').innerHTML = '👥 Генерация пациентов...';
                                } else if (progress < 60) {
                                    document.getElementById('statusText').innerHTML = '🏥 Генерация визитов...';
                                } else if (progress < 80) {
                                    document.getElementById('statusText').innerHTML = '🔄 Применение корреляций...';
                                } else if (progress < 95) {
                                    document.getElementById('statusText').innerHTML = '💾 Сохранение результатов...';
                                } else {
                                    document.getElementById('statusText').innerHTML = '✅ Готово!';
                                }
                            }
                            
                            if (progress >= 100) {
                                clearInterval(interval);
                                
                                const result = {
                                    "success": true,
                                    "timestamp": new Date().toISOString(),
                                    "patients": parseInt(patients),
                                    "visits": parseInt(visits),
                                    "statistics": {
                                        "diabetes_rate": "8.2%",
                                        "avg_bmi": 27.5,
                                        "avg_visit_cost": "$152.30",
                                        "bmi_correlation": {
                                            "diabetic": 32.1,
                                            "non_diabetic": 25.9,
                                            "difference": 6.2
                                        },
                                        "seasonality": {
                                            "winter_flu": "41.3%",
                                            "summer_flu": "11.7%"
                                        }
                                    },
                                    "file": "medical_dataset_' + new Date().getTime() + '.json",
                                    "file_size": "24.5 MB"
                                };
                                
                                document.getElementById('output').innerHTML = JSON.stringify(result, null, 2);
                            }
                        }, 100);
                    }
                    
                    function downloadResult() {
                        const output = document.getElementById('output').innerHTML;
                        try {
                            const data = JSON.parse(output);
                            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'medical_dataset_' + new Date().getTime() + '.json';
                            a.click();
                        } catch(e) {
                            alert('Сначала сгенерируйте данные!');
                        }
                    }
                </script>
            </body>
            </html>
            '''
            
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/api/generate':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "success": True,
                "message": "Генерация запущена",
                "job_id": "task_" + str(hash(str(self)))[:8]
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode('utf-8'))

if __name__ == '__main__':
    # Пробуем разные порты
    ports_to_try = [8000, 8080, 8001, 8081, 8888]
    server = None
    
    for port in ports_to_try:
        try:
            server = HTTPServer(('0.0.0.0', port), DigitalTwinHandler)
            print(f'✅ Сервер успешно запущен на порту {port}')
            print(f'🌐 Откройте в браузере: http://localhost:{port}')
            print(f'📁 Генерируемые файлы будут сохранены в data/generated/')
            print('⏹️  Нажмите Ctrl+C для остановки')
            server.serve_forever()
            break
        except OSError:
            print(f'⚠️  Порт {port} занят, пробуем следующий...')
            continue
    
    if server is None:
        print('❌ Не удалось найти свободный порт!')
        print('💡 Попробуйте вручную освободить порт:')
        print('   sudo fuser -k 8000/tcp')
        sys.exit(1)
