import json
import os
import secrets
import bcrypt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
ADMIN_FILE = os.path.join(DATA_DIR, "admin.json")
TOKENS_FILE = os.path.join(DATA_DIR, "tokens.json")


def verify_password(plain: str, hashed: str) -> bool:
    """Проверка пароля через bcrypt"""
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


def load_admin():
    """Загрузить данные админа"""
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # По умолчанию admin/admin
    default = {
        "username": "admin",
        "password_hash": bcrypt.hashpw("admin".encode(), bcrypt.gensalt()).decode(),
        "created_at": datetime.now().isoformat()
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ADMIN_FILE, "w", encoding="utf-8") as f:
        json.dump(default, f, indent=2, ensure_ascii=False)
    return default


def load_tokens():
    """Загрузить refresh токены"""
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_tokens(tokens):
    """Сохранить refresh токены"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(tokens), f)


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=30)
    return jwt.encode(
        {"sub": username, "exp": expire, "type": "access"},
        SECRET_KEY,
        algorithm="HS256"
    )


def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


@router.post("/login")
async def login(request: dict):
    username = request.get("username", "")
    password = request.get("password", "")
    admin = load_admin()

    if username != admin["username"] or not verify_password(password, admin["password_hash"]):
        raise HTTPException(401, "Неверный логин или пароль")

    access = create_access_token(username)
    refresh = create_refresh_token()
    tokens = load_tokens()
    tokens.add(refresh)
    save_tokens(tokens)

    return {"access_token": access, "token_type": "bearer", "refresh": refresh}


@router.post("/refresh")
async def refresh(request: dict):
    refresh_token = request.get("refresh", "")
    tokens = load_tokens()

    if refresh_token not in tokens:
        raise HTTPException(401, "Недействительный refresh токен")

    tokens.remove(refresh_token)
    new_access = create_access_token("admin")
    new_refresh = create_refresh_token()
    tokens.add(new_refresh)
    save_tokens(tokens)

    return {"access_token": new_access, "token_type": "bearer", "refresh": new_refresh}


@router.post("/logout")
async def logout(request: dict = None):
    refresh_token = request.get("refresh", "") if request else ""
    tokens = load_tokens()
    tokens.discard(refresh_token)
    save_tokens(tokens)
    return {"message": "Выход выполнен"}


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(401)
        return payload
    except JWTError:
        raise HTTPException(401, "Недействительный токен")