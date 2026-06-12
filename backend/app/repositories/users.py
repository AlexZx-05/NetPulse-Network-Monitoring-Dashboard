from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Organization, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def create_org_owner(self, organization: Organization, user: User) -> User:
        self.db.add(organization)
        self.db.flush()
        user.organization_id = organization.id
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
