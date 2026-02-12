#!/usr/bin/env python3
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class RealDataHandler(BaseHTTPRequestHandler):
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
                <title>Digital Twin Factory - РЕАЛЬНЫЕ ДАННЫЕ</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Arial, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 20px;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 20px;
                        padding: 30px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    }
                    h1 {
                        color: #333;
                        border-bottom: 3px solid #667eea;
                        padding-bottom: 10px;
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
                        border-left: 5px solid #667eea;
                    }
                    .stat-value {
                        font-size: 2.2em;
                        font-weight: bold;
                        color: #667eea;
                    }
                    .success-badge {
                        background: #10b981;
                        color: white;
                        padding: 10px 20px;
                        border-radius: 50px;
                        display: inline-block;
                        margin-bottom: 20px;
                    }
                    pre {
                        background: #1e1e2f;
                        color: #fff;
                        padding: 20px;
                        border-radius: 10px;
                        overflow: auto;
                        font-size: 14px;
                    }
                    .btn {
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        color: white;
                        border: none;
                        padding: 12px 30px;
                        border-radius: 50px;
                        cursor: pointer;
                        text-decoration: none;
                        display: inline-block;
                        margin: 10px 5px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <span class="success-badge">✅ РЕАЛЬНЫЕ ДАННЫЕ ЗАГРУЖЕНЫ</span>
                    <h1>🏭 Digital Twin Factory</h1>
                    <p>Фабрика цифровых двойников — синтетические данные с корреляциями</p>
                    
                    <div id="stats"></div>
                    <div id="samples"></div>
                </div>

                <script>
                    async function loadData() {
                        try {
                            const response = await fetch('/data');
                            const data = await response.json();
                            
                            // Статистика
                            document.getElementById('stats').innerHTML = `
                                <div class="stats-grid">
                                    <div class="stat-card">
                                        <div style="color: #666;">👥 Пациенты</div>
                                        <div class="stat-value">${data.total_patients}</div>
                                    </div>
                                    <div class="stat-card">
                                        <div style="color: #666;">🏥 Визиты</div>
                                        <div class="stat-value">${data.total_visits}</div>
                                    </div>
                                    <div class="stat-card">
                                        <div style="color: #666;">📊 Диабет</div>
                                        <div class="stat-value">${data.statistics.diabetes.percentage}%</div>
                                    </div>
                                    <div class="stat-card">
                                        <div style="color: #666;">📈 BMI диабетиков</div>
                                        <div class="stat-value">${data.statistics.bmi.diabetic}</div>
                                    </div>
                                    <div class="stat-card">
                                        <div style="color: #666;">📉 BMI не-диабетиков</div>
                                        <div class="stat-value">${data.statistics.bmi.non_diabetic}</div>
                                    </div>
                                    <div class="stat-card">
                                        <div style="color: #666;">📊 Разница BMI</div>
                                        <div class="stat-value">+${data.statistics.bmi.difference}</div>
                                    </div>
                                </div>
                            `;
                            
                            // Примеры пациентов
                            let patientsHtml = '<h2>📋 Примеры пациентов</h2><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">';
                            data.sample_patients.slice(0, 6).forEach(p => {
                                patientsHtml += `
                                    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
                                        <strong>${p.first_name} ${p.last_name}</strong><br>
                                        Возраст: ${p.age}<br>
                                        Пол: ${p.gender}<br>
                                        Диабет: ${p.diabetes ? '✅' : '❌'}<br>
                                        BMI: ${p.bmi}
                                    </div>
                                `;
                            });
                            patientsHtml += '</div>';
                            document.getElementById('samples').innerHTML = patientsHtml;
                            
                        } catch(e) {
                            console.error(e);
                        }
                    }
                    loadData();
                </script>
            </body>
            </html>
            '''
            self.wfile.write(html.encode('utf-8'))
        
        elif self.path == '/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Загружаем последний файл
            import glob
            files = glob.glob('/root/digital-twin-factory/data/generated/medical_dataset_*.json')
            if files:
                latest = max(files, key=os.path.getctime)
                with open(latest, 'r') as f:
                    data = json.load(f)
                self.wfile.write(json.dumps(data).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({'error': 'No data'}).encode('utf-8'))
        
        elif self.path == '/download':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Disposition', 'attachment; filename="medical_data.json"')
            self.end_headers()
            
            files = glob.glob('/root/digital-twin-factory/data/generated/medical_dataset_*.json')
            if files:
                latest = max(files, key=os.path.getctime)
                with open(latest, 'rb') as f:
                    self.wfile.write(f.read())

if __name__ == '__main__':
    port = 8080
    print('=' * 70)
    print('✅ Digital Twin Factory - СЕРВЕР РЕАЛЬНЫХ ДАННЫХ')
    print('=' * 70)
    print(f'🌐 Откройте в браузере: http://localhost:{port}')
    print(f'📁 Данные загружены из: /root/digital-twin-factory/data/generated/')
    print('=' * 70)
    
    # Проверяем наличие файлов
    import glob
    files = glob.glob('/root/digital-twin-factory/data/generated/medical_dataset_*.json')
    if files:
        latest = max(files, key=os.path.getctime)
        print(f'✅ Найден файл: {os.path.basename(latest)}')
        with open(latest, 'r') as f:
            data = json.load(f)
            print(f'👥 Пациентов: {data.get("total_patients", "N/A")}')
            print(f'🏥 Визитов: {data.get("total_visits", "N/A")}')
    else:
        print('❌ Файлы не найдены!')
    
    print('=' * 70)
    HTTPServer(('0.0.0.0', port), RealDataHandler).serve_forever()
