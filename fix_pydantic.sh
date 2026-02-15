#!/bin/bash

echo "🔧 Исправление Pydantic V2 предупреждений..."

cd /root/digital-twin-factory

# Заменить .dict() на .model_dump() во всех Python файлах
find app -name "*.py" -exec sed -i 's/\.dict()/.model_dump()/g' {} \;

echo "✅ Готово! Все .dict() заменены на .model_dump()"
