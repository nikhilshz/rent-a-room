from typing import Annotated

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field, StringConstraints, field_validator
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from app.dependencies.database import SessionDep
from app.dependencies.users import UserDep, UserId
from app.errors import USER_NOT_FOUND
from app.models.booking import BookingPublic
from app.models.user import User, UserBase, UserPublic

router = APIRouter(prefix="/users", tags=["users"])


class SearchQueryParams(BaseModel):
    name: Annotated[str | None, StringConstraints(to_lower=True)] = Field(
        default=None,
        min_length=2,
        max_length=10,
    )
    limit: int = Field(default=10, ge=1, le=100)

    offset: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def fail_if_funny(cls, name: str | None):
        if name is not None and "lol" in name.lower():
            raise ValueError("No funny business allowed")
        return name


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserPublic)
async def create_user(session: SessionDep, user: UserBase):
    validated_user = User.model_validate(user)
    session.add(validated_user)
    await session.commit()
    await session.refresh(validated_user)
    return validated_user


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List all available users",
    response_model=list[UserPublic],
)
async def get_users(session: SessionDep, params: Annotated[SearchQueryParams, Query()]):
    statement = select(User)

    if params.name:
        statement = statement.where(col(User.name).ilike(f"%{params.name}%"))

    statement = (
        statement.limit(params.limit).offset(params.offset).order_by(col(User.id))
    )
    users = (await session.exec(statement)).all()
    return users


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserPublic)
async def get_user(user: UserDep):
    return user


@router.get(
    "/{user_id}/bookings",
    status_code=status.HTTP_200_OK,
    response_model=list[BookingPublic],
)
async def get_user_bookings(session: SessionDep, user_id: UserId):
    user = await session.get(
        User, user_id, options=[selectinload(User.bookings)]
    )  # 2 SQL queries, selectinload for one to many associations
    if not user:
        raise USER_NOT_FOUND
    return user.bookings
