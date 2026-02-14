#!/usr/bin/env python3
import sys
import os
import socket
from datetime import datetime, timedelta
import uuid
import asyncio

# Устанавливаем кодировку UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
import uvicorn
import jwt

# Импортируем наши модули
from app.auth import auth_handler
from app.models.user import User, UserCreate, UserLogin, UserResponse, Token
from app.models.tariffs import TARIFFS, get_tariff_limits, check_user_limits
from app.core.batch_generator import BatchGenerator
from app.developer_account import create_developer_account, DEVELOPER_ACCOUNT

# Функция поиска свободного порта
def find_free_port(start_port=8000, max_port=8010):
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

# ============ ИНИЦИАЛИЗАЦИЯ APP ============
app = FastAPI(
    title="Digital Twin Factory",
    description="Фабрика цифровых двойников - генерация синтетических данных с корреляциями",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем папки
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)
os.makedirs("app/templates/auth", exist_ok=True)
os.makedirs("app/templates/dashboard", exist_ok=True)
os.makedirs("data/generated", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ============ ХРАНИЛИЩА ДАННЫХ ============
users_db = {}  # username -> User
email_db = {}  # email -> username
tokens_db = {}  # token -> username
jobs_db = {}  # job_id -> job

generator = BatchGenerator(batch_size=10000)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

# Создаем аккаунт разработчика при запуске
developer = create_developer_account(users_db, email_db, auth_handler)

# ============ ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ============
def get_user_by_username(username: str):
    return users_db.get(username)

def get_user_by_email(email: str):
    username = email_db.get(email)
    if username:
        return users_db.get(username)
    return None

def create_user(user_data: UserCreate):
    if user_data.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if user_data.email in email_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth_handler.get_password_hash(user_data.password)
    verification_token = auth_handler.create_verification_token()
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        verification_token=verification_token,
        is_developer=False
    )
    
    users_db[user.username] = user
    email_db[user.email] = user.username
    tokens_db[verification_token] = user.username
    
    auth_handler.send_verification_email(user.email, verification_token, user.username)
    
    return user

def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return None
    if not auth_handler.verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, auth_handler.SECRET_KEY, algorithms=[auth_handler.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
    except:
        return None
    
    return get_user_by_username(username)

async def get_current_developer(token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not user.is_developer:
        raise HTTPException(status_code=403, detail="Developer access required")
    return user

# ============ API АУТЕНТИФИКАЦИИ ============
@app.post("/api/v1/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    try:
        user = create_user(user_data)
        return {"message": "User created successfully. Please check your email for verification."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    if not user.is_verified and user.username != DEVELOPER_ACCOUNT["username"]:
        user.is_verified = True
        user.is_active = True
    
    access_token_expires = timedelta(minutes=auth_handler.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_handler.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user.dict())
    )

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UserResponse(**current_user.dict())

@app.get("/api/v1/auth/verify")
async def verify_email(token: str):
    username = tokens_db.get(token)
    if not username:
        return HTMLResponse(content="<h1>Invalid or expired token</h1>")
    
    user = users_db.get(username)
    if not user:
        return HTMLResponse(content="<h1>User not found</h1>")
    
    user.is_verified = True
    user.is_active = True
    
    return HTMLResponse(content="<h1>Email verified successfully! You can now login.</h1>")

# ============ API ТАРИФОВ ============
@app.get("/api/v1/tariffs")
async def get_tariffs():
    return list(TARIFFS.values())

@app.get("/api/v1/tariffs/{tariff_id}")
async def get_tariff(tariff_id: str):
    return TARIFFS.get(tariff_id, TARIFFS["free"])

@app.get("/api/v1/tariffs/limits/{tariff_id}")
async def get_tariff_limits_endpoint(tariff_id: str):
    return get_tariff_limits(tariff_id)

# ============ API ГЕНЕРАЦИИ ============
@app.post("/api/v1/generate/medical")
async def generate_medical(
    patients: int = 10000,
    visits: int = 50000,
    seed: int = 42,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not current_user.is_developer:
        can_proceed, message = check_user_limits(current_user, patients, visits)
        if not can_proceed:
            raise HTTPException(status_code=403, detail=message)
    
    job_id = str(uuid.uuid4())
    
    jobs_db[job_id] = {
        "job_id": job_id,
        "user_id": current_user.id,
        "username": current_user.username,
        "status": "processing",
        "patients": patients,
        "visits": visits,
        "seed": seed,
        "created_at": datetime.now().isoformat()
    }
    
    current_user.total_generations += 1
    current_user.total_patients_generated += patients
    current_user.total_visits_generated += visits
    if not current_user.is_developer:
        current_user.api_calls_remaining -= 1
    
    asyncio.create_task(run_generation(job_id, patients, visits, seed))
    
    return {"success": True, "job_id": job_id}

async def run_generation(job_id, patients, visits, seed):
    try:
        generator.set_seed(seed)
        dataset = generator.generate_full_medical_dataset(patients, visits)
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["completed_at"] = datetime.now().isoformat()
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)

@app.get("/api/v1/jobs")
async def list_jobs(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if current_user.is_developer:
        user_jobs = list(jobs_db.values())
    else:
        user_jobs = [job for job in jobs_db.values() if job.get("user_id") == current_user.id]
    
    user_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return user_jobs[:50]

@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: str, current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if current_user.is_developer:
        return job
    
    if job.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return job

@app.get("/api/v1/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "total_generations": current_user.total_generations,
        "total_patients": current_user.total_patients_generated,
        "total_visits": current_user.total_visits_generated,
        "api_calls_remaining": current_user.api_calls_remaining if not current_user.is_developer else "unlimited",
        "is_developer": current_user.is_developer
    }

# ============ API ДЛЯ РАЗРАБОТЧИКА ============
@app.get("/api/v1/admin/users")
async def get_all_users(dev: User = Depends(get_current_developer)):
    users_list = []
    for user in users_db.values():
        users_list.append({
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "is_verified": user.is_verified,
            "total_generations": user.total_generations,
            "tariff_plan": user.tariff_plan,
            "is_developer": user.is_developer
        })
    return users_list

@app.get("/api/v1/admin/stats")
async def get_admin_stats(dev: User = Depends(get_current_developer)):
    total_users = len(users_db)
    verified_users = sum(1 for u in users_db.values() if u.is_verified)
    developer_count = sum(1 for u in users_db.values() if u.is_developer)
    total_generations = sum(u.total_generations for u in users_db.values())
    total_patients = sum(u.total_patients_generated for u in users_db.values())
    total_visits = sum(u.total_visits_generated for u in users_db.values())
    
    return {
        "total_users": total_users,
        "verified_users": verified_users,
        "developer_count": developer_count,
        "total_generations": total_generations,
        "total_patients": total_patients,
        "total_visits": total_visits,
        "jobs_count": len(jobs_db),
        "completed_jobs": sum(1 for j in jobs_db.values() if j.get("status") == "completed"),
        "failed_jobs": sum(1 for j in jobs_db.values() if j.get("status") == "failed"),
        "system_version": "3.0.0",
        "environment": "development"
    }

@app.post("/api/v1/admin/generate/unlimited")
async def generate_unlimited(
    patients: int = 100000,
    visits: int = 500000,
    dev: User = Depends(get_current_developer)
):
    job_id = str(uuid.uuid4())
    
    jobs_db[job_id] = {
        "job_id": job_id,
        "user_id": dev.id,
        "username": dev.username,
        "status": "processing",
        "patients": patients,
        "visits": visits,
        "created_at": datetime.now().isoformat(),
        "unlimited": True
    }
    
    asyncio.create_task(run_generation(job_id, patients, visits, 42))
    
    return {"success": True, "job_id": job_id, "message": f"Generating {patients} patients and {visits} visits"}

@app.delete("/api/v1/admin/jobs/all")
async def delete_all_jobs(dev: User = Depends(get_current_developer)):
    global jobs_db
    jobs_db = {}
    return {"message": "All jobs deleted successfully"}

# ============ ВЕБ-СТРАНИЦЫ ============
def read_html(filename):
    filepath = f"app/templates/{filename}"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return f"<h1>File {filename} not found</h1>"

@app.get("/", response_class=HTMLResponse)
async def index():
    return read_html("index_dark.html")

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return read_html("auth/register.html")

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return read_html("auth/login.html")

# ============ РАЗДЕЛЬНЫЕ СТРАНИЦЫ ============
@app.get("/generator", response_class=HTMLResponse)
async def generator_page():
    return read_html("generator_separate.html")

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page():
    return read_html("analytics_separate.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    return read_html("dashboard/enhanced.html")

@app.get("/developer", response_class=HTMLResponse)
async def developer_page():
    return read_html("developer.html")

@app.get("/tariffs", response_class=HTMLResponse)
async def tariffs_page():
    return read_html("tariffs.html")

@app.get("/verify-email")
async def verify_email_page(token: str):
    return RedirectResponse(url=f"/api/v1/auth/verify?token={token}")

# ============ API ДЛЯ АНАЛИТИКИ ============
@app.get("/api/v1/analytics/data")
async def get_analytics_data():
    """Данные для графиков аналитики"""
    return {
        "bmi": {
            "labels": ["Диабетики", "Не-диабетики"],
            "values": [32.1, 25.9],
            "colors": ["#f72585", "#4cc9f0"]
        },
        "seasonality": {
            "months": ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"],
            "flu": [42, 40, 30, 20, 15, 10, 8, 9, 15, 25, 35, 41],
            "cold": [35, 33, 32, 30, 28, 25, 22, 23, 26, 30, 33, 36]
        },
        "diagnosis": {
            "labels": ["Простуда", "Грипп", "Гипертония", "Диабет", "Артрит"],
            "values": [30, 25, 18, 15, 12],
            "colors": ["#4cc9f0", "#f72585", "#f8961e", "#4361ee", "#3f37c9"]
        },
        "costs": {
            "labels": ["Пневмония", "Диабет", "Гипертония", "Грипп", "Простуда"],
            "values": [350, 280, 200, 120, 80]
        }
    }

# ============ ЗАПУСК ============
if __name__ == "__main__":
    port = find_free_port(8000)
    
    if port:
        print("=" * 80)
        print("🚀 DIGITAL TWIN FACTORY - РАЗДЕЛЬНЫЕ СТРАНИЦЫ")
        print("=" * 80)
        print(f"📌 Адрес: http://localhost:{port}")
        print(f"🏠 Главная: http://localhost:{port}/")
        print(f"📝 Регистрация: http://localhost:{port}/register")
        print(f"🔐 Вход: http://localhost:{port}/login")
        print(f"🚀 Генератор: http://localhost:{port}/generator")
        print(f"📊 Аналитика: http://localhost:{port}/analytics")
        print(f"👤 Личный кабинет: http://localhost:{port}/dashboard")
        print(f"👨‍💻 Разработчик: http://localhost:{port}/developer")
        print(f"💰 Тарифы: http://localhost:{port}/tariffs")
        print(f"📚 API Docs: http://localhost:{port}/api/docs")
        print("=" * 80)
        print("👑 АККАУНТ РАЗРАБОТЧИКА:")
        print(f"  Username: {DEVELOPER_ACCOUNT['username']}")
        print(f"  Password: {DEVELOPER_ACCOUNT['password']}")
        print("=" * 80)
        
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        print("❌ Нет свободных портов")
