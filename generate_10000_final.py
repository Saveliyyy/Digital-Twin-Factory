#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.batch_generator import BatchGenerator
import time
import json
from datetime import datetime

# АБСОЛЮТНЫЙ ПУТЬ - ФАЙЛ БУДЕТ ТОЧНО ЗДЕСЬ!
OUTPUT_DIR = "/root/digital-twin-factory/data/generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("🚀 ЗАПУСК ГЕНЕРАЦИИ 10,000 ПАЦИЕНТОВ")
print("=" * 70)
print(f"📁 Файлы будут сохранены в: {OUTPUT_DIR}")
print("=" * 70)

start_time = time.time()

try:
    # Создаем генератор
    generator = BatchGenerator(batch_size=10000)
    generator.set_seed(42)
    
    print("⏳ Генерация данных... Это займет около 30-60 секунд")
    
    # Генерируем данные
    dataset = generator.generate_full_medical_dataset(10000, 50000)
    
    # Конвертируем Polars DataFrame в список словарей
    patients_list = dataset['patients'].to_dicts()
    visits_list = dataset['visits'].to_dicts()
    
    print(f"✅ Сгенерировано {len(patients_list)} пациентов")
    print(f"✅ Сгенерировано {len(visits_list)} визитов")
    
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
    
    # Формируем имя файла
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"medical_dataset_{timestamp}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    print(f"⏳ Сохранение в файл: {filepath}")
    
    # СОХРАНЯЕМ В JSON
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
        'sample_patients': patients_list[:20],
        'sample_visits': visits_list[:50]
    }
    
    # Сохраняем файл
    with open(filepath, 'w', encoding='utf-8') as f:
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
    print(f"💾 Файл: {filepath}")
    print(f"📁 Размер: {os.path.getsize(filepath) / 1024 / 1024:.1f} MB")
    print(f"⏱️ Время: {duration:.2f} секунд")
    print("=" * 70)
    
    # СОЗДАЕМ ССЫЛКУ НА ПОСЛЕДНИЙ ФАЙЛ
    latest_link = os.path.join(OUTPUT_DIR, "latest.json")
    if os.path.exists(latest_link):
        os.remove(latest_link)
    os.symlink(filename, latest_link)
    print(f"🔗 Ссылка: {latest_link} -> {filename}")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
