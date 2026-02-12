.PHONY: help install init-db run test clean

help:
@echo "========================================="
@echo "Digital Twin Factory - Makefile"
@echo "========================================="
@echo ""
@echo "Доступные команды:"
@echo "  make install     - Установка зависимостей"
@echo "  make init-db     - Инициализация базы данных"
@echo "  make run         - Запуск FastAPI сервера"
@echo "  make test        - Запуск тестовой генерации"
@echo "  make clean       - Очистка временных файлов"
@echo ""

install:
pip install --upgrade pip
pip install -r requirements.txt

init-db:
python scripts/init_db.py

run:
export PYTHONIOENCODING=utf-8; \
export LANG=en_US.UTF-8; \
export LC_ALL=en_US.UTF-8; \
python app/main.py

test:
export PYTHONIOENCODING=utf-8; \
python scripts/test_generation.py

clean:
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
