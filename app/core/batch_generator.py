"""
Пакетный генератор данных с поддержкой корреляций.
Генерирует данные батчами по 10,000 записей.
"""
import polars as pl
import numpy as np
from faker import Faker
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import random
import logging

logger = logging.getLogger(__name__)
fake = Faker(['en_US'])

class BatchGenerator:
    """
    Генератор данных, работающий батчами.
    Оптимизирован для генерации больших объемов данных.
    """
    
    def __init__(self, batch_size: int = 10000):
        self.batch_size = batch_size
        self.seed = None
        
    def set_seed(self, seed: int):
        """Установка seed для воспроизводимости"""
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
        Faker.seed(seed)
    
    def generate_patients(self, count: int = 10000) -> pl.DataFrame:
        """
        Генерация пациентов с реалистичными характеристиками.
        """
        logger.info(f"Генерация {count} пациентов...")
        
        all_patients = []
        remaining = count
        
        while remaining > 0:
            batch_count = min(self.batch_size, remaining)
            
            # Генерируем базовые поля
            diabetes = np.random.random(batch_count) < 0.08
            
            # BMI с корреляцией
            bmi = np.zeros(batch_count)
            for i in range(batch_count):
                if diabetes[i]:
                    bmi[i] = np.random.normal(32, 4)
                else:
                    bmi[i] = np.random.normal(26, 5)
                bmi[i] = np.clip(bmi[i], 16, 50)
            
            batch_data = {
                'id': [str(uuid.uuid4()) for _ in range(batch_count)],
                'first_name': [fake.first_name() for _ in range(batch_count)],
                'last_name': [fake.last_name() for _ in range(batch_count)],
                'age': np.random.normal(45, 18, batch_count).astype(int),
                'gender': np.random.choice(['Male', 'Female'], batch_count, p=[0.48, 0.52]),
                'height': np.random.normal(170, 10, batch_count).round(1),
                'weight': np.random.normal(75, 15, batch_count).round(1),
                'diabetes': diabetes.tolist(),
                'bmi': bmi.round(1).tolist(),
                'hypertension': np.random.random(batch_count) < 0.15,
            }
            
            # Клиппинг значений
            batch_data['age'] = np.clip(batch_data['age'], 0, 100).tolist()
            batch_data['height'] = np.clip(batch_data['height'], 140, 210).tolist()
            batch_data['weight'] = np.clip(batch_data['weight'], 40, 150).tolist()
            
            # Корреляция возраста и гипертонии
            age_array = np.array(batch_data['age'])
            hypertension_array = np.array(batch_data['hypertension'])
            elderly_mask = age_array > 60
            if np.sum(elderly_mask) > 0:
                elderly_prob = np.random.random(np.sum(elderly_mask)) < 0.4
                hypertension_array[elderly_mask] = elderly_prob
            batch_data['hypertension'] = hypertension_array.tolist()
            
            batch_df = pl.DataFrame(batch_data)
            all_patients.append(batch_df)
            remaining -= batch_count
        
        patients_df = pl.concat(all_patients) if len(all_patients) > 1 else all_patients[0]
        logger.info(f"Сгенерировано {len(patients_df)} пациентов")
        return patients_df
    
    def generate_visits(self, patients_df: pl.DataFrame, count: int = 50000) -> pl.DataFrame:
        """
        Генерация визитов к врачу с привязкой к пациентам.
        """
        logger.info(f"Генерация {count} визитов...")
        
        patient_ids = patients_df['id'].to_list()
        n_patients = len(patient_ids)
        
        # Создаем словари для быстрого доступа к данным пациентов
        patient_ages = {}
        patient_diabetes = {}
        for row in patients_df.to_dicts():
            patient_ages[row['id']] = row['age']
            patient_diabetes[row['id']] = row['diabetes']
        
        all_visits = []
        remaining = count
        
        while remaining > 0:
            batch_count = min(self.batch_size, remaining)
            
            # Распределяем визиты по пациентам
            parent_indices = np.random.choice(n_patients, size=batch_count)
            assigned_parent_ids = [patient_ids[i] for i in parent_indices]
            
            # Генерируем даты (2023-2024)
            start_date = datetime(2023, 1, 1)
            end_date = datetime(2024, 12, 31)
            date_range = (end_date - start_date).days
            
            dates = []
            months = []
            for _ in range(batch_count):
                days_offset = np.random.randint(0, date_range)
                date = start_date + timedelta(days=days_offset)
                dates.append(date)
                months.append(date.month)
            
            # Базовые диагнозы
            diagnoses = []
            for month in months:
                if month in [11, 12, 1, 2]:  # Зима
                    diag = np.random.choice(
                        ['Flu', 'Cold', 'Pneumonia', 'Bronchitis'],
                        p=[0.4, 0.3, 0.2, 0.1]
                    )
                else:  # Лето
                    diag = np.random.choice(
                        ['Cold', 'Allergy', 'Hypertension', 'Arthritis', 'Flu'],
                        p=[0.3, 0.25, 0.2, 0.15, 0.1]
                    )
                diagnoses.append(diag)
            
            # Получаем данные пациентов для корреляций
            patient_ages_batch = [patient_ages.get(pid, 45) for pid in assigned_parent_ids]
            patient_diabetes_batch = [patient_diabetes.get(pid, False) for pid in assigned_parent_ids]
            
            # Корреляция с диабетом
            for i in range(batch_count):
                if patient_diabetes_batch[i] and np.random.random() < 0.6:
                    diagnoses[i] = 'Diabetes'
            
            # Корреляция с возрастом
            for i in range(batch_count):
                age = patient_ages_batch[i]
                if age > 70 and np.random.random() < 0.25:
                    diagnoses[i] = 'Pneumonia'
                elif age < 12 and np.random.random() < 0.9:
                    diagnoses[i] = 'Cold'
            
            # Стоимость визита
            costs = np.random.normal(150, 80, batch_count)
            costs = np.clip(costs, 30, 500).round(2)
            
            batch_data = {
                'id': [str(uuid.uuid4()) for _ in range(batch_count)],
                'patient_id': assigned_parent_ids,
                'date': dates,
                'diagnosis': diagnoses,
                'cost': costs.tolist(),
                'follow_up': np.random.random(batch_count) < 0.15,
            }
            
            batch_df = pl.DataFrame(batch_data)
            all_visits.append(batch_df)
            remaining -= batch_count
        
        visits_df = pl.concat(all_visits) if len(all_visits) > 1 else all_visits[0]
        logger.info(f"Сгенерировано {len(visits_df)} визитов")
        return visits_df
    
    def generate_full_medical_dataset(self, n_patients: int = 10000, n_visits: int = 50000) -> Dict[str, pl.DataFrame]:
        """
        Генерация полного медицинского датасета.
        """
        logger.info("=" * 60)
        logger.info("НАЧАЛО ГЕНЕРАЦИИ МЕДИЦИНСКОГО ДАТАСЕТА")
        logger.info(f"Пациентов: {n_patients}, Визитов: {n_visits}")
        logger.info("=" * 60)
        
        if self.seed:
            np.random.seed(self.seed)
            random.seed(self.seed)
        
        patients_df = self.generate_patients(n_patients)
        visits_df = self.generate_visits(patients_df, n_visits)
        
        # Статистика
        diabetes_rate = patients_df['diabetes'].mean()
        avg_bmi = patients_df['bmi'].mean()
        avg_cost = visits_df['cost'].mean()
        
        diabetic_patients = patients_df.filter(pl.col('diabetes') == True)
        non_diabetic_patients = patients_df.filter(pl.col('diabetes') == False)
        
        diabetic_bmi = diabetic_patients['bmi'].mean() if len(diabetic_patients) > 0 else 0
        non_diabetic_bmi = non_diabetic_patients['bmi'].mean() if len(non_diabetic_patients) > 0 else 0
        
        logger.info("=" * 60)
        logger.info("СТАТИСТИКА ГЕНЕРАЦИИ:")
        logger.info(f"Пациентов: {len(patients_df)}")
        logger.info(f"Визитов: {len(visits_df)}")
        logger.info(f"Диабет: {diabetes_rate:.1%}")
        logger.info(f"Средний BMI: {avg_bmi:.1f}")
        logger.info(f"BMI диабетиков: {diabetic_bmi:.1f}")
        logger.info(f"BMI не-диабетиков: {non_diabetic_bmi:.1f}")
        logger.info(f"Разница BMI: {diabetic_bmi - non_diabetic_bmi:.1f}")
        logger.info(f"Средняя стоимость визита: ${avg_cost:.2f}")
        logger.info("=" * 60)
        
        return {
            'patients': patients_df,
            'visits': visits_df
        }
    
    def export_to_json(self, dataset: Dict[str, pl.DataFrame], filepath: str):
        """Экспорт датасета в JSON"""
        import json
        
        patients_list = dataset['patients'].to_dicts()
        visits_list = dataset['visits'].to_dicts()
        
        for visit in visits_list:
            if 'date' in visit and visit['date']:
                if hasattr(visit['date'], 'isoformat'):
                    visit['date'] = visit['date'].isoformat()
                else:
                    visit['date'] = str(visit['date'])
        
        output = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'seed': self.seed,
                'patients_count': len(patients_list),
                'visits_count': len(visits_list)
            },
            'patients': patients_list,
            'visits': visits_list
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Датасет сохранен в {filepath}")
        return filepath
