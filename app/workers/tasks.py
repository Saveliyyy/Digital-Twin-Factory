from app.workers.celery_app import celery_app
from app.core.batch_generator import BatchGenerator
import json
import os
from datetime import datetime
import logging
import polars as pl

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='generate_medical_dataset')
def generate_medical_dataset(self, patients_count, visits_count, seed=42):
    """
    Фоновая задача для генерации медицинского датасета
    """
    task_id = self.request.id
    logger.info(f"Задача {task_id}: Начало генерации {patients_count} пациентов, {visits_count} визитов")
    
    self.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Инициализация генератора...'})
    
    try:
        generator = BatchGenerator(batch_size=10000)
        generator.set_seed(seed)
        
        self.update_state(state='PROGRESS', meta={'progress': 30, 'status': 'Генерация пациентов...'})
        dataset = generator.generate_full_medical_dataset(patients_count, visits_count)
        
        self.update_state(state='PROGRESS', meta={'progress': 70, 'status': 'Сохранение результатов...'})
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"medical_dataset_{timestamp}_p{patients_count}_v{visits_count}.json"
        filepath = os.path.join('data/generated', filename)
        
        os.makedirs('data/generated', exist_ok=True)
        
        # Сохраняем в JSON
        generator.export_to_json(dataset, filepath)
        
        # Статистика
        diabetic_bmi = dataset['patients'].filter(pl.col('diabetes') == True)['bmi'].mean() or 0
        non_diabetic_bmi = dataset['patients'].filter(pl.col('diabetes') == False)['bmi'].mean() or 0
        
        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Готово!'})
        
        return {
            'status': 'success',
            'task_id': task_id,
            'file': filename,
            'filepath': filepath,
            'patients': patients_count,
            'visits': visits_count,
            'statistics': {
                'diabetes_rate': float(dataset['patients']['diabetes'].mean()),
                'avg_bmi': float(dataset['patients']['bmi'].mean()),
                'avg_cost': float(dataset['visits']['cost'].mean()),
                'bmi_correlation': {
                    'diabetic': round(float(diabetic_bmi), 1),
                    'non_diabetic': round(float(non_diabetic_bmi), 1),
                    'difference': round(float(diabetic_bmi - non_diabetic_bmi), 1)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Задача {task_id}: Ошибка - {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise e
