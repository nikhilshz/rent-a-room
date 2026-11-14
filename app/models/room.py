from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.booking import Booking


# Base model class - shared fields for all representation of a room
# Write creating using POSt
# Data coming in
class RoomBase(SQLModel):
    name: str = Field()
    price_per_night: int = Field()
    bedrooms: float = Field(multiple_of=0.5)
    bathrooms: float = Field(multiple_of=0.5)


# For communication with DB
# Room table model- maps to the "rooms" database model
class Room(RoomBase, table=True):
    __tablename__: str = "rooms"

    id: int | None = Field(default=None, primary_key=True)

    bookings: list["Booking"] = Relationship(
        back_populates="room",
        cascade_delete=True,
    )


# Room response model - the payload to send back to the client
# Guranteed to have ID for the room(room must exist)
# Data going out
class RoomPublic(RoomBase):
    id: int = Field()


# Room update Model - all fields can be optional coz we fallback to None
# for patch
class RoomUpdate(SQLModel):
    name: str | None = None
    price_per_night: int | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
