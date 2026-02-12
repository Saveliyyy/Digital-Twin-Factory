#!/usr/bin/env python3
import polars as pl
import numpy as np
from faker import Faker
import uuid
from datetime import datetime, timedelta
import random

print("=" * 60)
print("ТЕСТ ГЕНЕРАЦИИ ДАННЫХ")
print("=" * 60)

# Устанавливаем seed
np.random.seed(42)
random.seed(42)
Faker.seed(42)
fake = Faker()

# Генерируем пациентов
n_patients = 100
patients = []

print(f"\n1. Генерация {n_patients} пациентов...")

for i in range(n_patients):
    diabetes = random.random() < 0.08
    bmi = round(random.uniform(28, 40) if diabetes else random.uniform(18.5, 35), 1)
    
    patient = {
        'id': str(uuid.uuid4()),
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'age': random.randint(18, 90),
        'gender': random.choice(['Male', 'Female']),
        'height': round(random.uniform(150, 190), 1),
        'weight': round(random.uniform(50, 100), 1),
        'diabetes': diabetes,
        'bmi': bmi
    }
    patients.append(patient)

print(f"   Создано: {len(patients)} пациентов")
print(f"   Диабет: {sum(p['diabetes'] for p in patients)} чел. ({sum(p['diabetes'] for p in patients)/len(patients):.1%})")

# Генерируем визиты
n_visits = 500
visits = []

print(f"\n2. Генерация {n_visits} визитов...")

for i in range(n_visits):
    patient = random.choice(patients)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    date = datetime(2024, month, day)
    
    # Сезонность
    if month in [11, 12, 1, 2]:
        diagnosis = random.choices(
            ['Flu', 'Cold', 'Pneumonia', 'Bronchitis'],
            weights=[0.4, 0.3, 0.2, 0.1]
        )[0]
    else:
        diagnosis = random.choices(
            ['Flu', 'Cold', 'Allergy', 'Hypertension', 'Arthritis'],
            weights=[0.1, 0.3, 0.25, 0.2, 0.15]
        )[0]
    
    # Корреляция с диабетом
    if patient['diabetes'] and random.random() < 0.6:
        diagnosis = 'Diabetes'
    
    # Корреляция с возрастом
    if patient['age'] > 70 and random.random() < 0.25:
        diagnosis = 'Pneumonia'
    elif patient['age'] < 12 and random.random() < 0.9:
        diagnosis = 'Cold'
    
    visit = {
        'id': str(uuid.uuid4()),
        'patient_id': patient['id'],
        'date': date.isoformat(),
        'diagnosis': diagnosis,
        'cost': round(random.uniform(50, 300), 2)
    }
    visits.append(visit)

print(f"   Создано: {len(visits)} визитов")

# Статистика
diabetic_patients = [p for p in patients if p['diabetes']]
non_diabetic_patients = [p for p in patients if not p['diabetes']]

diabetic_bmi = sum(p['bmi'] for p in diabetic_patients) / len(diabetic_patients) if diabetic_patients else 0
non_diabetic_bmi = sum(p['bmi'] for p in non_diabetic_patients) / len(non_diabetic_patients) if non_diabetic_patients else 0

winter_visits = [v for v in visits if int(v['date'].split('-')[1]) in [11, 12, 1, 2]]
summer_visits = [v for v in visits if int(v['date'].split('-')[1]) in [6, 7, 8]]

winter_flu = sum(1 for v in winter_visits if v['diagnosis'] == 'Flu') / len(winter_visits) if winter_visits else 0
summer_flu = sum(1 for v in summer_visits if v['diagnosis'] == 'Flu') / len(summer_visits) if summer_visits else 0

print("\n" + "=" * 60)
print("СТАТИСТИКА")
print("=" * 60)

print(f"\nПАЦИЕНТЫ:")
print(f"   Всего: {len(patients)}")
print(f"   Средний возраст: {sum(p['age'] for p in patients)/len(patients):.0f} лет")
print(f"   Диабет: {len(diabetic_patients)} чел. ({len(diabetic_patients)/len(patients):.1%})")

print(f"\nКОРРЕЛЯЦИЯ BMI:")
print(f"   BMI диабетиков: {diabetic_bmi:.1f}")
print(f"   BMI не-диабетиков: {non_diabetic_bmi:.1f}")
print(f"   Разница: {diabetic_bmi - non_diabetic_bmi:.1f}")

print(f"\nВИЗИТЫ:")
print(f"   Всего: {len(visits)}")
print(f"   Средняя стоимость: ${sum(v['cost'] for v in visits)/len(visits):.2f}")

print(f"\nСЕЗОННОСТЬ:")
print(f"   Грипп зимой: {winter_flu:.1%} ({len(winter_visits)} визитов)")
print(f"   Грипп летом: {summer_flu:.1%} ({len(summer_visits)} визитов)")

print("\n" + "=" * 60)
print("ТЕСТ УСПЕШНО ВЫПОЛНЕН")
print("=" * 60)

# Сохраняем в файл
import json
with open('test_output.json', 'w', encoding='utf-8') as f:
    json.dump({
        'patients': patients[:10],
        'visits': visits[:20],
        'statistics': {
            'patients': len(patients),
            'visits': len(visits),
            'diabetes_rate': f"{len(diabetic_patients)/len(patients):.1%}",
            'bmi_correlation': {
                'diabetic': round(diabetic_bmi, 1),
                'non_diabetic': round(non_diabetic_bmi, 1),
                'difference': round(diabetic_bmi - non_diabetic_bmi, 1)
            },
            'seasonality': {
                'winter_flu': f"{winter_flu:.1%}",
                'summer_flu': f"{summer_flu:.1%}"
            }
        }
    }, f, indent=2, ensure_ascii=False)

print(f"\nДанные сохранены в test_output.json")
