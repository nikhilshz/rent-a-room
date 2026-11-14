from typing import Annotated, Literal

from fastapi import APIRouter, Cookie, Header, Response, status
from pydantic import BaseModel, Field

router = APIRouter()


class AppHeaders(BaseModel):
    user_agent: str | None


class AppCookies(BaseModel):
    theme: Literal["light", "dark"] = Field(
        default="dark",
        description="Preferred display theme",
        examples=["light", "dark"],
    )
    language: Literal["en", "es", "fr"] = Field(
        default="en",
        description="Preferred language",
        examples=["en", "es", "fr"],
    )


@router.get("/", status_code=status.HTTP_200_OK)
def root(
    app_cookies: Annotated[AppCookies, Cookie()],
    app_headers: Annotated[AppHeaders, Header()] = None,
):
    greetings = {
        "en": "Welcome to rent a room",
        "es": "Bienvenaidofgnoebneoitbnh",
        "fr": "tefbklnteinthp",
    }

    greeting = greetings.get(app_cookies.language)
    return {"message": greeting, "user_agent": app_headers.user_agent}


@router.get("/preferences", status_code=status.HTTP_200_OK, tags=["preferences"])
def set_preferences(response: Response):
    app_cookies = AppCookies()
    response.set_cookie(key="theme", value=app_cookies.theme)
    response.set_cookie(key="language", value=app_cookies.language)
    return {"messege": "Preferenced updated"}
