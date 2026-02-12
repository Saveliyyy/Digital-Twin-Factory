#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.batch_generator import BatchGenerator
import time
import json
from datetime import datetime

print("=" * 70)
print("🚀 ЗАПУСК ГЕНЕРАЦИИ 10,000 ПАЦИЕНТОВ")
print("=" * 70)

start_time = time.time()

# Создаем папку для данных
os.makedirs('data/generated', exist_ok=True)

# Создаем генератор
generator = BatchGenerator(batch_size=10000)
generator.set_seed(42)

# Генерируем данные
dataset = generator.generate_full_medical_dataset(10000, 50000)

# Формируем имя файла
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f'data/generated/medical_dataset_{timestamp}.json'

# Конвертируем Polars DataFrame в список словарей
patients_list = dataset['patients'].to_dicts()
visits_list = dataset['visits'].to_dicts()

# Конвертируем datetime в строки
for visit in visits_list:
    if 'date' in visit and visit['date']:
        if hasattr(visit['date'], 'isoformat'):
            visit['date'] = visit['date'].isoformat()
        else:
            visit['date'] = str(visit['date'])

# Вычисляем статистику
diabetes_count = sum(1 for p in patients_list if p.get('diabetes', False))
diabetes_rate = (diabetes_count / len(patients_list)) * 100 if patients_list else 0

# BMI корреляция
diabetic_patients = [p for p in patients_list if p.get('diabetes', False)]
non_diabetic_patients = [p for p in patients_list if not p.get('diabetes', False)]

diabetic_bmi = sum(p.get('bmi', 0) for p in diabetic_patients) / len(diabetic_patients) if diabetic_patients else 0
non_diabetic_bmi = sum(p.get('bmi', 0) for p in non_diabetic_patients) / len(non_diabetic_patients) if non_diabetic_patients else 0
avg_bmi = sum(p.get('bmi', 0) for p in patients_list) / len(patients_list)

# Стоимость визитов
avg_cost = sum(v.get('cost', 0) for v in visits_list) / len(visits_list) if visits_list else 0

# Сезонность
winter_visits = []
summer_visits = []
for v in visits_list:
    if 'date' in v:
        try:
            month = int(v['date'].split('-')[1])
            if month in [11, 12, 1, 2]:
                winter_visits.append(v)
            elif month in [6, 7, 8]:
                summer_visits.append(v)
        except:
            pass

winter_flu = sum(1 for v in winter_visits if v.get('diagnosis') == 'Flu') / len(winter_visits) * 100 if winter_visits else 0
summer_flu = sum(1 for v in summer_visits if v.get('diagnosis') == 'Flu') / len(summer_visits) * 100 if summer_visits else 0

# СОХРАНЯЕМ В JSON С ПРАВИЛЬНОЙ СТРУКТУРОЙ
output = {
    'generated_at': datetime.now().isoformat(),
    'seed': 42,
    'total_patients': len(patients_list),
    'total_visits': len(visits_list),
    'statistics': {
        'diabetes': {
            'count': diabetes_count,
            'percentage': round(diabetes_rate, 1)
        },
        'bmi': {
            'average': round(avg_bmi, 1),
            'diabetic': round(diabetic_bmi, 1),
            'non_diabetic': round(non_diabetic_bmi, 1),
            'difference': round(diabetic_bmi - non_diabetic_bmi, 1)
        },
        'cost': {
            'average': round(avg_cost, 2)
        },
        'seasonality': {
            'winter_flu_percentage': round(winter_flu, 1),
            'summer_flu_percentage': round(summer_flu, 1),
            'winter_visits': len(winter_visits),
            'summer_visits': len(summer_visits)
        }
    },
    'sample_patients': patients_list[:20],  # Первые 20 пациентов
    'sample_visits': visits_list[:50]       # Первые 50 визитов
}

# Сохраняем файл
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

end_time = time.time()
duration = end_time - start_time

print("=" * 70)
print("✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
print("=" * 70)
print(f"📊 Пациентов: {len(patients_list)}")
print(f"📊 Визитов: {len(visits_list)}")
print(f"📈 Диабет: {diabetes_count} чел. ({diabetes_rate:.1f}%)")
print(f"📊 BMI диабетиков: {diabetic_bmi:.1f}")
print(f"📊 BMI не-диабетиков: {non_diabetic_bmi:.1f}")
print(f"📈 Разница BMI: {diabetic_bmi - non_diabetic_bmi:.1f}")
print(f"❄️ Грипп зимой: {winter_flu:.1f}% ({len(winter_visits)} визитов)")
print(f"☀️ Грипп летом: {summer_flu:.1f}% ({len(summer_visits)} визитов)")
print(f"💾 Файл: {filename}")
print(f"📁 Размер: {os.path.getsize(filename) / 1024 / 1024:.1f} MB")
print(f"⏱️ Время: {duration:.2f} секунд")
print("=" * 70)

# Создаем symlink к последнему файлу
latest_link = 'data/generated/latest.json'
if os.path.exists(latest_link):
    os.remove(latest_link)
os.symlink(os.path.basename(filename), latest_link)
print(f"🔗 Ссылка: {latest_link} -> {os.path.basename(filename)}")
print("=" * 70)
