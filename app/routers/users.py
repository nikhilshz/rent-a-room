from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from app.dependencies.database import SessionDep
from app.dependencies.users import UserDep, UserId
from app.errors import USER_NOT_FOUND
from app.models.booking import Booking, BookingPublic
from app.models.room import Room, RoomPublic
from app.models.user import User, UserBase, UserPublic
from app.schemas.query_params import UserSearchParams

router = APIRouter(prefix="/users", tags=["users"])


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
async def get_all_users(
    session: SessionDep, params: Annotated[UserSearchParams, Query()]
):
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


@router.get(
    "/{user_id}/rooms", status_code=status.HTTP_200_OK, response_model=list[RoomPublic]
)
async def get_user_rooms(session: SessionDep, user: UserDep):
    statement = (
        select(Room)
        .join(Booking, col(Booking.room_id) == Room.id)
        .where(col(Booking.user_id) == user.id)
        .order_by(col(Room.id))
        .distinct()
    )

    rooms = await session.exec(statement)
    return rooms.all()
