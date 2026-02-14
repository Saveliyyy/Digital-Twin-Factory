from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class TariffPlan(BaseModel):
    id: str
    name: str
    price_monthly: float
    price_yearly: float
    max_patients_per_month: int
    max_visits_per_month: int
    api_calls_per_month: int
    features: List[str]
    color: str
    is_popular: bool = False
    storage_gb: int
    support_level: str  # basic, priority, dedicated
    export_formats: List[str]  # json, csv, excel, parquet, sql

# Предопределенные тарифы
TARIFFS = {
    "free": TariffPlan(
        id="free",
        name="Бесплатный",
        price_monthly=0,
        price_yearly=0,
        max_patients_per_month=1000,
        max_visits_per_month=5000,
        api_calls_per_month=100,
        features=[
            "До 1,000 пациентов в месяц",
            "До 5,000 визитов в месяц",
            "Базовые корреляции",
            "Экспорт в JSON и CSV",
            "Email поддержка"
        ],
        color="#4b5563",
        is_popular=False,
        storage_gb=1,
        support_level="basic",
        export_formats=["json", "csv"]
    ),
    "basic": TariffPlan(
        id="basic",
        name="Базовый",
        price_monthly=29.99,
        price_yearly=299.99,
        max_patients_per_month=10000,
        max_visits_per_month=50000,
        api_calls_per_month=1000,
        features=[
            "До 10,000 пациентов в месяц",
            "До 50,000 визитов в месяц",
            "Расширенные корреляции",
            "Экспорт в JSON, CSV, Excel",
            "Приоритетная поддержка",
            "История генераций 30 дней"
        ],
        color="#2563eb",
        is_popular=True,
        storage_gb=10,
        support_level="priority",
        export_formats=["json", "csv", "excel"]
    ),
    "pro": TariffPlan(
        id="pro",
        name="Профессиональный",
        price_monthly=99.99,
        price_yearly=999.99,
        max_patients_per_month=100000,
        max_visits_per_month=500000,
        api_calls_per_month=10000,
        features=[
            "До 100,000 пациентов в месяц",
            "До 500,000 визитов в месяц",
            "Все виды корреляций",
            "AI-генерация текста",
            "Экспорт во все форматы",
            "Выделенный менеджер",
            "История генераций 1 год",
            "API доступ"
        ],
        color="#7c3aed",
        is_popular=False,
        storage_gb=100,
        support_level="dedicated",
        export_formats=["json", "csv", "excel", "parquet", "sql"]
    ),
    "enterprise": TariffPlan(
        id="enterprise",
        name="Корпоративный",
        price_monthly=499.99,
        price_yearly=4999.99,
        max_patients_per_month=1000000,
        max_visits_per_month=5000000,
        api_calls_per_month=100000,
        features=[
            "Безлимитные генерации",
            "Индивидуальные корреляции",
            "Выделенные серверы",
            "SLA 99.9%",
            "Интеграция с вашими системами",
            "Обучение команды",
            "Приоритетная разработка"
        ],
        color="#9333ea",
        is_popular=False,
        storage_gb=1000,
        support_level="dedicated",
        export_formats=["json", "csv", "excel", "parquet", "sql", "avro"]
    )
}

def get_tariff_limits(tariff_id: str) -> Dict:
    """Получить лимиты тарифа"""
    tariff = TARIFFS.get(tariff_id, TARIFFS["free"])
    return {
        "max_patients": tariff.max_patients_per_month,
        "max_visits": tariff.max_visits_per_month,
        "api_calls": tariff.api_calls_per_month,
        "storage_gb": tariff.storage_gb,
        "export_formats": tariff.export_formats
    }

def check_user_limits(user, patients_count: int, visits_count: int) -> tuple[bool, str]:
    """Проверить, может ли пользователь выполнить генерацию"""
    limits = get_tariff_limits(user.tariff_plan)
    
    if user.total_patients_generated + patients_count > limits["max_patients"]:
        return False, "Превышен лимит пациентов для вашего тарифа"
    
    if user.total_visits_generated + visits_count > limits["max_visits"]:
        return False, "Превышен лимит визитов для вашего тарифа"
    
    if user.api_calls_remaining <= 0:
        return False, "Исчерпан лимит API вызовов"
    
    return True, "OK"
