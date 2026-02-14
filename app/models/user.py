from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool = False
    is_verified: bool = False
    is_developer: bool = False  # Добавляем поле для разработчика
    verification_token: Optional[str] = None
    reset_token: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Статистика пользователя
    total_generations: int = 0
    total_patients_generated: int = 0
    total_visits_generated: int = 0
    
    # Тарифный план
    tariff_plan: str = "free"  # free, basic, pro, enterprise
    tariff_expires: Optional[datetime] = None
    api_calls_remaining: int = 100  # Для бесплатного тарифа
    
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
    created_at: datetime
    tariff_plan: str
    tariff_expires: Optional[datetime]
    
    # Статистика
    total_generations: int
    total_patients_generated: int
    total_visits_generated: int
    api_calls_remaining: int
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None
