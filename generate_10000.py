#!/usr/bin/env python3
from app.core.batch_generator import BatchGenerator
import time

print("=" * 70)
print("🚀 ЗАПУСК ГЕНЕРАЦИИ 10,000 ПАЦИЕНТОВ")
print("=" * 70)

start_time = time.time()

# Создаем генератор
generator = BatchGenerator(batch_size=10000)
generator.set_seed(42)

# Генерируем данные
dataset = generator.generate_full_medical_dataset(10000, 50000)

# Сохраняем в JSON
filename = generator.export_to_json(dataset, 'data/generated/medical_dataset_10000.json')

end_time = time.time()
duration = end_time - start_time

print("=" * 70)
print("✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
print("=" * 70)
print(f"📊 Пациентов: {len(dataset['patients'])}")
print(f"📊 Визитов: {len(dataset['visits'])}")
print(f"💾 Файл: {filename}")
print(f"⏱️ Время: {duration:.2f} секунд")
print("=" * 70)
