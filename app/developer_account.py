from app.models.user import User
import uuid

# Аккаунт разработчика с полным доступом
DEVELOPER_ACCOUNT = {
    "username": "dev_admin",
    "email": "dev@digitaltwin.factory",
    "password": "Dev@123456",
    "full_name": "Developer Admin",
    "tariff_plan": "enterprise"
}

# Функция для создания аккаунта разработчика при запуске
def create_developer_account(users_db, email_db, auth_handler):
    from app.models.user import User
    from datetime import datetime
    import uuid
    
    # Проверяем, существует ли уже аккаунт
    if DEVELOPER_ACCOUNT["username"] in users_db:
        return users_db[DEVELOPER_ACCOUNT["username"]]
    
    # Создаем хеш пароля
    hashed_password = auth_handler.get_password_hash(DEVELOPER_ACCOUNT["password"])
    
    # Создаем пользователя-разработчика
    developer = User(
        id=str(uuid.uuid4()),
        username=DEVELOPER_ACCOUNT["username"],
        email=DEVELOPER_ACCOUNT["email"],
        full_name=DEVELOPER_ACCOUNT["full_name"],
        hashed_password=hashed_password,
        is_active=True,
        is_verified=True,
        is_developer=True,  # Важно!
        tariff_plan=DEVELOPER_ACCOUNT["tariff_plan"],
        tariff_expires=None,  # Бессрочно
        api_calls_remaining=999999,  # Практически бесконечно
        total_generations=0,
        total_patients_generated=0,
        total_visits_generated=0,
        unlimited_access=True,
        developer_permissions={
            "view_all_jobs": True,
            "delete_all_jobs": True,
            "view_all_users": True,
            "unlimited_generation": True,
            "access_dev_panel": True
        },
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Сохраняем
    users_db[developer.username] = developer
    email_db[developer.email] = developer.username
    
    print("\n" + "="*60)
    print("👨‍💻 АККАУНТ РАЗРАБОТЧИКА СОЗДАН")
    print("="*60)
    print(f"Username: {DEVELOPER_ACCOUNT['username']}")
    print(f"Password: {DEVELOPER_ACCOUNT['password']}")
    print(f"Email: {DEVELOPER_ACCOUNT['email']}")
    print("="*60)
    print("✅ Полный доступ ко всем функциям")
    print("✅ Безлимитные генерации")
    print("✅ Все тарифы разблокированы")
    print("="*60 + "\n")
    
    return developer
