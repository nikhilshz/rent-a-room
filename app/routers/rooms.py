from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import col, exists, func, select

from app.dependencies.database import SessionDep
from app.dependencies.rooms import RoomDep
from app.errors import SERVICE_UNDER_MAINTENANCE
from app.models.booking import Booking
from app.models.room import Room, RoomBase, RoomPublic, RoomUpdate
from app.schemas.query_params import RoomSearchParams

# router = APIRouter(prefix="/rooms", tags=["rooms"])
router = APIRouter()


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
async def get_rooms(session: SessionDep, params: Annotated[RoomSearchParams, Query()]):
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


@router.get("/booked", status_code=status.HTTP_200_OK, response_model=list[RoomPublic])
async def get_booked_rooms(session: SessionDep):
    room_has_bookings = exists().where(col(Booking.room_id) == Room.id)
    statement = select(Room).where(room_has_bookings).order_by(col(Room.id))
    result = await session.exec(statement)
    rooms = result.all()
    return rooms


@router.get(
    "/unbooked", status_code=status.HTTP_200_OK, response_model=list[RoomPublic]
)
async def get_unbooked_rooms(session: SessionDep):
    room_does_not_have_bookings = ~exists().where(col(Booking.room_id) == Room.id)
    statement = select(Room).where(room_does_not_have_bookings).order_by(col(Room.id))
    result = await session.exec(statement)
    rooms = result.all()
    return rooms


class RoomWithBookingCount(RoomPublic):
    booking_count: int


@router.get(
    "/stats", status_code=status.HTTP_200_OK, response_model=list[RoomWithBookingCount]
)
async def get_rooms_stats(session: SessionDep):
    statement = (
        select(Room, func.count(col(Booking.id).label("booking_count")))
        .outerjoin(Booking, col(Booking.room_id) == Room.id)
        .group_by(col(Room.id))
        .order_by(Room.id)
    )

    result = await session.exec(statement)
    data = result.all()

    return [
        RoomWithBookingCount(**room.model_dump(), booking_count=booking_count)
        for room, booking_count in data
    ]


@router.get(
    "/booked-between", status_code=status.HTTP_200_OK, response_model=list[RoomPublic]
)
async def get_rooms_booked_between(session: SessionDep, start_date: str, end_date: str):
    # statement = select(Room).join(Booking, col(Booking.room_id) == Room.id)
    statement = (
        select(Room)
        .join(Booking)
        .where(col(Booking.check_in) >= start_date)
        .where(col(Booking.check_out) <= end_date)
        .distinct()
        .order_by(col(Room.id))
    )

    result = await session.exec(statement)
    rooms = result.all()
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
