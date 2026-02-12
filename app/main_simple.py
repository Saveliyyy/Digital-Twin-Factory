
# Добавляем страницу аналитики
@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page():
    return read_html("analytics.html")

# Добавляем новые API endpoints для аналитики
@app.get("/api/v1/analytics/correlations")
async def get_correlations():
    """Получить данные о корреляциях для графиков"""
    return {
        "bmi_correlation": {
            "diabetic": 32.1,
            "non_diabetic": 25.9,
            "difference": 6.2
        },
        "seasonality": {
            "winter_flu": 41.3,
            "summer_flu": 11.7
        },
        "age_diagnosis": {
            "child_cold": 90,
            "elderly_pneumonia": 25
        }
    }

@app.get("/api/v1/analytics/demographics")
async def get_demographics():
    """Демографическая статистика"""
    return {
        "age_distribution": [850, 1200, 1800, 2200, 2500, 2100, 1600, 900, 400],
        "gender_ratio": {"male": 48, "female": 52},
        "geography": {
            "urban": 45,
            "suburban": 35,
            "rural": 15,
            "other": 5
        }
    }

@app.get("/api/v1/analytics/quality")
async def get_quality_metrics():
    """Метрики качества данных"""
    return {
        "overall_quality": 98.5,
        "completeness": 99.2,
        "accuracy": 97.8,
        "consistency": 96.5,
        "uniqueness": 100,
        "anomalies": [
            {"type": "extreme_bmi", "count": 5, "description": "BMI > 50"},
            {"type": "pediatric_diabetes", "count": 12, "description": "Диабет 2 типа у детей"},
            {"type": "summer_flu", "count": 3, "description": "Грипп в летние месяцы"}
        ]
    }

@app.get("/api/v1/analytics/predictions")
async def get_predictions():
    """Прогнозы на будущее"""
    return {
        "diabetes": [8.2, 8.5, 8.9, 9.2, 9.6],
        "obesity": [22, 23, 24, 25.5, 27],
        "hypertension": [15, 15.5, 16.2, 16.8, 17.5],
        "years": [2024, 2025, 2026, 2027, 2028]
    }
