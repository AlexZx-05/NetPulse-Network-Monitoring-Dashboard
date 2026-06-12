from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.domain.models import Organization, User, UserRole
from app.domain.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.repositories.users import UserRepository


class AuthService:
    def __init__(self, users: UserRepository):
        self.users = users

    def register(self, request: RegisterRequest) -> TokenResponse:
        if self.users.get_by_email(request.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        organization = Organization(name=request.organization_name)
        user = User(
            organization_id=organization.id,
            email=request.email,
            full_name=request.full_name,
            password_hash=hash_password(request.password),
            role=UserRole.owner,
        )
        created = self.users.create_org_owner(organization, user)
        return TokenResponse(
            access_token=create_access_token(created.id, created.organization_id, created.role.value)
        )

    def login(self, request: LoginRequest) -> TokenResponse:
        user = self.users.get_by_email(request.email)
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return TokenResponse(access_token=create_access_token(user.id, user.organization_id, user.role.value))
