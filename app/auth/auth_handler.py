from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Секретный ключ для JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Настройки для паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки для почты
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "your-email@gmail.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "your-password")
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Обрезаем пароль до 72 символов для bcrypt
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_verification_token():
    return secrets.token_urlsafe(32)

def send_verification_email(email: str, token: str, username: str, industry: str = "healthcare"):
    """Отправка письма с подтверждением с учетом отрасли"""
    try:
        verification_link = f"http://localhost:8000/verify-email?token={token}"
        
        # Индустриальные иконки
        industry_icons = {
            "healthcare": "🏥",
            "finance": "💰",
            "retail": "🛍️",
            "manufacturing": "🏭",
            "telecom": "📱",
            "transport": "🚚",
            "energy": "⚡",
            "education": "🎓",
            "marketing": "📊",
            "hr": "👥"
        }
        
        icon = industry_icons.get(industry, "🏭")
        
        print("\n" + "="*60)
        print(f"{icon} ПОДТВЕРЖДЕНИЕ РЕГИСТРАЦИИ - {industry.upper()}")
        print("="*60)
        print(f"Email: {email}")
        print(f"Пользователь: {username}")
        print(f"Отрасль: {industry}")
        print(f"Ссылка: {verification_link}")
        print("="*60 + "\n")
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False

def send_password_reset_email(email: str, token: str, username: str):
    """Отправка письма для сброса пароля"""
    try:
        reset_link = f"http://localhost:8000/reset-password?token={token}"
        print("\n" + "="*60)
        print("🔐 СБРОС ПАРОЛЯ")
        print("="*60)
        print(f"Email: {email}")
        print(f"Пользователь: {username}")
        print(f"Ссылка: {reset_link}")
        print("="*60 + "\n")
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False
