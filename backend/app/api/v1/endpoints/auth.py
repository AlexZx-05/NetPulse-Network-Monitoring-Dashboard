from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.schemas import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.api.deps import CurrentUser, get_current_user
from app.repositories.users import UserRepository
from app.services.auth_service import AuthService

router = APIRouter()


def auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, service: AuthService = Depends(auth_service)) -> TokenResponse:
    return service.register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, service: AuthService = Depends(auth_service)) -> TokenResponse:
    return service.login(payload)


@router.get("/me", response_model=UserRead)
def me(current: CurrentUser = Depends(get_current_user)):
    return current.user
