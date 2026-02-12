#!/usr/bin/env python3
import json
import glob
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

def get_latest_file():
    files = glob.glob('data/generated/medical_dataset_*.json')
    if files:
        return max(files, key=os.path.getctime)
    return None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            latest = get_latest_file()
            html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Digital Twin Factory - Результаты</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial; margin: 20px; background: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                    h1 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
                    .stats { display: grid; grid-template-columns: repeat(3,1fr); gap: 20px; margin: 20px 0; }
                    .card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }
                    .value { font-size: 24px; font-weight: bold; color: #667eea; }
                    pre { background: #1e1e2f; color: white; padding: 15px; border-radius: 5px; overflow: auto; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🏭 Digital Twin Factory - Результаты генерации</h1>
            '''
            
            if latest:
                with open(latest, 'r') as f:
                    data = json.load(f)
                
                html += f'''
                    <div class="stats">
                        <div class="card">
                            <h3>👥 Пациенты</h3>
                            <div class="value">{data.get("total_patients", 0):,}</div>
                        </div>
                        <div class="card">
                            <h3>🏥 Визиты</h3>
                            <div class="value">{data.get("total_visits", 0):,}</div>
                        </div>
                        <div class="card">
                            <h3>📊 Диабет</h3>
                            <div class="value">{data["statistics"]["diabetes"]["percentage"]}%</div>
                        </div>
                    </div>
                    
                    <div class="stats">
                        <div class="card">
                            <h3>📈 BMI диабетиков</h3>
                            <div class="value">{data["statistics"]["bmi"]["diabetic"]}</div>
                        </div>
                        <div class="card">
                            <h3>📉 BMI не-диабетиков</h3>
                            <div class="value">{data["statistics"]["bmi"]["non_diabetic"]}</div>
                        </div>
                        <div class="card">
                            <h3>📊 Разница BMI</h3>
                            <div class="value">+{data["statistics"]["bmi"]["difference"]}</div>
                        </div>
                    </div>
                    
                    <div class="stats">
                        <div class="card">
                            <h3>❄️ Грипп зимой</h3>
                            <div class="value">{data["statistics"]["seasonality"]["winter_flu_percentage"]}%</div>
                        </div>
                        <div class="card">
                            <h3>☀️ Грипп летом</h3>
                            <div class="value">{data["statistics"]["seasonality"]["summer_flu_percentage"]}%</div>
                        </div>
                        <div class="card">
                            <h3>💰 Средний чек</h3>
                            <div class="value">${data["statistics"]["cost"]["average"]}</div>
                        </div>
                    </div>
                    
                    <h2>📋 Пример пациента</h2>
                    <pre>{json.dumps(data["sample_patients"][0], indent=2, ensure_ascii=False)}</pre>
                    
                    <h2>📋 Пример визита</h2>
                    <pre>{json.dumps(data["sample_visits"][0], indent=2, ensure_ascii=False)}</pre>
                    
                    <p><a href="/download" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px;">💾 Скачать полный JSON</a></p>
                '''
            else:
                html += '<p style="color: red;">❌ Нет сгенерированных файлов. Запустите python generate_10000_fixed.py</p>'
            
            html += '</div></body></html>'
            self.wfile.write(html.encode('utf-8'))
        
        elif self.path == '/download':
            latest = get_latest_file()
            if latest:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(latest)}"')
                self.end_headers()
                with open(latest, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()

if __name__ == '__main__':
    port = 8080
    print(f'🌐 Сервер запущен на http://localhost:{port}')
    print(f'📁 Просмотр результатов: http://localhost:{port}')
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()
