from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field, StringConstraints, field_validator
from sqlmodel import col, select

from app.dependencies.database import SessionDep
from app.dependencies.rooms import RoomDep
from app.errors import SERVICE_UNDER_MAINTENANCE
from app.models.room import Room, RoomBase, RoomPublic, RoomUpdate

# router = APIRouter(prefix="/rooms", tags=["rooms"])
router = APIRouter()


class SearchQueryParams(BaseModel):
    max_price: int | None = Field(
        default=None, ge=10, le=10_000, examples=[100, 2000, 10_000]
    )

    search: Annotated[str | None, StringConstraints(to_lower=True)] = Field(
        default=None,
        min_length=3,
        max_length=10,
        title="Search term",
        description="Provide a keyword to look for within the room's title",
        examples=["sunny", "bedroom", "house"],
    )

    limit: int = Field(default=10, ge=1, le=100)

    offset: int = Field(default=0, ge=0)

    @field_validator("search")
    @classmethod
    def fail_if_funny(cls, search: str):
        if "lol" in search.lower():
            raise ValueError("No funny business allowed")
        return search


MAINTENANCE_MODE = False


def check_maintenance_mode():
    if MAINTENANCE_MODE:
        raise SERVICE_UNDER_MAINTENANCE


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=RoomPublic,
    dependencies=[Depends(check_maintenance_mode)],
)
async def create_room(session: SessionDep, room: RoomBase):
    print("PAYLOAD:", room)

    validated_room = Room.model_validate(room)

    print("VALIDATED ROOM:", validated_room)
    session.add(validated_room)
    await session.commit()
    await session.refresh(validated_room)
    return validated_room


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[RoomPublic],
    summary="List all available rooms",
    description="Return all rooms, Supports filtering by price and search term",
    response_description="a list of all rooms matching the filter criteria",
)
async def get_rooms(session: SessionDep, params: Annotated[SearchQueryParams, Query()]):
    statement = select(Room)

    if params.max_price:
        statement = statement.where(Room.price_per_night <= params.max_price)

    if params.search:
        # statement = statement.where(func.lower(Room.name).contains(params.search))
        statement = statement.where(col(Room.name).ilike(f"%{params.search}%"))

    statement = (
        statement.limit(params.limit).offset(params.offset).order_by(col(Room.id))
    )
    # rooms = await session.exec(statement).all()
    rooms = (await session.exec(statement)).all()
    return rooms


@router.get(
    "/{room_id}",
    status_code=status.HTTP_200_OK,
    response_model=RoomPublic,
)
# async def get_room(room: RoomDep) -> Room:
def get_room(room: RoomDep) -> Room:
    return room


@router.patch(
    "/{room_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_maintenance_mode)],
)
async def update_room(
    session: SessionDep, room: RoomDep, room_payload: RoomUpdate
) -> Room:
    room_payload_without_default_values = room_payload.model_dump(exclude_unset=True)
    room.sqlmodel_update(room_payload_without_default_values)
    session.add(room)
    await session.commit()
    await session.refresh(room)
    return room


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_200_OK,
    response_model=RoomPublic,
    dependencies=[Depends(check_maintenance_mode)],
)
async def delete_room(session: SessionDep, room: RoomDep):
    await session.delete(room)
    await session.commit()
    return room
