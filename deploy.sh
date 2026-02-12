#!/bin/bash

# Digital Twin Factory - Скрипт деплоя на публичный сервер

echo "=========================================="
echo "🚀 Digital Twin Factory - Деплой"
echo "=========================================="

# Переменные
PROJECT_DIR="/root/digital-twin-factory"
DOMAIN=${1:-"localhost"}
PORT=${2:-"8000"}

# 1. Проверка зависимостей
echo "📦 Проверка зависимостей..."
cd $PROJECT_DIR
source venv/bin/activate
pip install -r requirements.txt

# 2. Создание systemd сервиса
echo "🛠️ Создание systemd сервиса..."
cat > /etc/systemd/system/digital-twin.service << EOL
[Unit]
Description=Digital Twin Factory
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/app/main_full.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# 3. Настройка Nginx
echo "🌐 Настройка Nginx..."
cat > /etc/nginx/sites-available/digital-twin << EOL
server {
    listen 80;
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static {
        alias $PROJECT_DIR/app/static;
    }
    
    location /data {
        alias $PROJECT_DIR/data/generated;
    }
    
    client_max_body_size 100M;
}
EOL

ln -sf /etc/nginx/sites-available/digital-twin /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# 4. Запуск сервиса
echo "▶️ Запуск сервиса..."
systemctl daemon-reload
systemctl enable digital-twin
systemctl restart digital-twin

# 5. Настройка firewall
echo "🛡️ Настройка firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow $PORT/tcp
ufw --force enable

echo "=========================================="
echo "✅ Деплой завершен!"
echo "=========================================="
echo "🌐 Сайт доступен по адресу: http://$DOMAIN"
echo "📊 Статус сервиса: systemctl status digital-twin"
echo "📁 Логи: journalctl -u digital-twin -f"
echo "=========================================="
