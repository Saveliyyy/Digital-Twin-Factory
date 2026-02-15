from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

# Список доступных направлений
INDUSTRIES = [
    {"id": "healthcare", "name": "Здравоохранение", "icon": "🏥", "color": "#f72585"},
    {"id": "finance", "name": "Финансы и банкинг", "icon": "💰", "color": "#f8961e"},
    {"id": "retail", "name": "Ритейл и E-commerce", "icon": "🛍️", "color": "#4cc9f0"},
    {"id": "manufacturing", "name": "Промышленность", "icon": "🏭", "color": "#4361ee"},
    {"id": "telecom", "name": "Телекоммуникации", "icon": "📱", "color": "#3f37c9"},
    {"id": "transport", "name": "Транспорт и логистика", "icon": "🚚", "color": "#f9844a"},
    {"id": "energy", "name": "Энергетика", "icon": "⚡", "color": "#ffd166"},
    {"id": "education", "name": "Образование", "icon": "🎓", "color": "#06d6a0"},
    {"id": "marketing", "name": "Маркетинг и реклама", "icon": "📊", "color": "#118ab2"},
    {"id": "hr", "name": "HR и рекрутинг", "icon": "👥", "color": "#ef476f"},
]

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool = False
    is_verified: bool = False
    is_developer: bool = False
    industry: str = "healthcare"  # Выбранное направление
    industry_data: Dict[str, Any] = Field(default_factory=dict)  # Данные по направлению
    verification_token: Optional[str] = None
    reset_token: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Статистика пользователя
    total_generations: int = 0
    total_records_generated: int = 0
    favorite_datasets: List[str] = Field(default_factory=list)
    
    # Тарифный план
    tariff_plan: str = "free"
    tariff_expires: Optional[datetime] = None
    api_calls_remaining: int = 100
    
    # Дополнительные поля для разработчика
    unlimited_access: bool = False
    developer_permissions: Dict[str, bool] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    industry: str = "healthcare"  # Поле для выбора направления

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    is_developer: bool
    industry: str
    created_at: datetime
    tariff_plan: str
    tariff_expires: Optional[datetime]
    
    # Статистика
    total_generations: int
    total_records_generated: int
    api_calls_remaining: int
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class IndustryResponse(BaseModel):
    id: str
    name: str
    icon: str
    color: str
