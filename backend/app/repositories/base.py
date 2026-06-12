from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class TenantRepository(Generic[ModelT]):
    def __init__(self, db: Session, model: type[ModelT]):
        self.db = db
        self.model = model

    def get(self, organization_id: UUID, entity_id: UUID) -> ModelT | None:
        stmt = select(self.model).where(
            self.model.organization_id == organization_id,
            self.model.id == entity_id,
        )
        return self.db.scalar(stmt)

    def list(self, organization_id: UUID, limit: int = 100) -> list[ModelT]:
        stmt = select(self.model).where(self.model.organization_id == organization_id).limit(limit)
        return list(self.db.scalars(stmt))

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
