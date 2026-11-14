from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator


class UserSearchParams(BaseModel):
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


class RoomSearchParams(BaseModel):
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
    def fail_if_funny(cls, search: str | None):
        if search is not None and "lol" in search.lower():
            raise ValueError("No funny business allowed")
        return search
