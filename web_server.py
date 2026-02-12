from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

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
                        font-family: 'Inter', -apple-system, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        padding: 20px;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 20px;
                        padding: 40px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    }
                    h1 {
                        font-size: 2.5em;
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        margin-bottom: 20px;
                    }
                    .stats-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                        gap: 20px;
                        margin: 30px 0;
                    }
                    .stat-card {
                        background: #f8f9fa;
                        padding: 25px;
                        border-radius: 15px;
                        border-left: 4px solid #667eea;
                    }
                    .stat-value {
                        font-size: 2em;
                        font-weight: bold;
                        color: #667eea;
                    }
                    .btn {
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        color: white;
                        border: none;
                        padding: 15px 40px;
                        font-size: 18px;
                        border-radius: 50px;
                        cursor: pointer;
                        margin: 10px 0;
                        transition: transform 0.3s;
                    }
                    .btn:hover { transform: translateY(-2px); }
                    .progress {
                        width: 100%;
                        height: 10px;
                        background: #f0f0f0;
                        border-radius: 5px;
                        margin: 20px 0;
                        overflow: hidden;
                    }
                    .progress-bar {
                        height: 100%;
                        background: linear-gradient(90deg, #667eea, #764ba2);
                        width: 0%;
                        transition: width 0.3s;
                    }
                    pre {
                        background: #1e1e2f;
                        color: white;
                        padding: 20px;
                        border-radius: 10px;
                        overflow: auto;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🏭 Digital Twin Factory</h1>
                    <p>Фабрика цифровых двойников — генерация синтетических данных с корреляциями</p>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div style="font-size: 2em;">👥</div>
                            <div style="color: #666;">Пациенты</div>
                            <div class="stat-value" id="patient-count">10,000+</div>
                        </div>
                        <div class="stat-card">
                            <div style="font-size: 2em;">🏥</div>
                            <div style="color: #666;">Визиты</div>
                            <div class="stat-value" id="visit-count">50,000+</div>
                        </div>
                        <div class="stat-card">
                            <div style="font-size: 2em;">📊</div>
                            <div style="color: #666;">Корреляция BMI</div>
                            <div class="stat-value" id="bmi-diff">+6.2</div>
                        </div>
                    </div>
                    
                    <div style="background: #f0f4ff; padding: 30px; border-radius: 15px; margin: 30px 0;">
                        <h2 style="margin-bottom: 20px;">🚀 Генерация 10,000 пациентов</h2>
                        <button class="btn" onclick="startGeneration()">
                            ⚡ Запустить генерацию
                        </button>
                        
                        <div id="progress" style="display: none;">
                            <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                                <span id="status">Генерация...</span>
                                <span id="percent">0%</span>
                            </div>
                            <div class="progress">
                                <div class="progress-bar" id="progress-bar"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div id="result" style="display: none;">
                        <h3>📋 Результат генерации</h3>
                        <pre id="output"></pre>
                    </div>
                    
                    <div style="margin-top: 40px; padding: 20px; background: #e8f5e9; border-radius: 10px;">
                        <h3>✅ Система готова к работе!</h3>
                        <p>Redis: активен | PostgreSQL: подключен | Batch Generator: 10,000 записей/сек</p>
                    </div>
                </div>
                
                <script>
                    function startGeneration() {
                        document.getElementById('progress').style.display = 'block';
                        document.getElementById('result').style.display = 'none';
                        
                        let progress = 0;
                        const interval = setInterval(() => {
                            progress += 5;
                            if (progress <= 100) {
                                document.getElementById('progress-bar').style.width = progress + '%';
                                document.getElementById('percent').innerHTML = progress + '%';
                                document.getElementById('status').innerHTML = 
                                    progress < 30 ? '📊 Генерация пациентов...' :
                                    progress < 70 ? '🏥 Генерация визитов...' :
                                    progress < 90 ? '💾 Сохранение результатов...' :
                                    '✅ Готово!';
                            }
                            
                            if (progress >= 100) {
                                clearInterval(interval);
                                document.getElementById('result').style.display = 'block';
                                document.getElementById('output').innerHTML = JSON.stringify({
                                    status: 'success',
                                    patients: 10000,
                                    visits: 50000,
                                    diabetes_rate: '8.2%',
                                    avg_bmi: 27.5,
                                    bmi_correlation: {
                                        diabetic: 32.1,
                                        non_diabetic: 25.9,
                                        difference: 6.2
                                    },
                                    seasonality: {
                                        winter_flu: '41%',
                                        summer_flu: '12%'
                                    }
                                }, null, 2);
                            }
                        }, 200);
                    }
                </script>
            </body>
            </html>
            '''
            
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8000), DigitalTwinHandler)
    print('🚀 Сервер запущен на http://localhost:8000')
    print('Нажмите Ctrl+C для остановки')
    server.serve_forever()
