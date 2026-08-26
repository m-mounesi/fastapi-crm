from typing import Optional, TypeVar
from pydantic import BaseModel, Field, field_validator
import re


T = TypeVar("T")  #   use for Generic intput


# Model to Create a User
class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=30,
        description="Username should be between 3 and 30 character",
    )
    password: Optional[str] = Field(
        min_length=8, max_length=30, description="description minimum is 8 character"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        return validate_text(v, "username")


# Model to Login a User
class UserLogin(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=30,
        description="Username should be between 3 and 30 character",
    )
    password: Optional[str] = Field(
        min_length=8, max_length=30, description="description minimum is 8 character"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        return validate_text(v, "username")


# token response model
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


#   Validator function
def validate_text(v: str, field_name: str):
    if re.search(r"[<>{}]", v):
        raise ValueError(f"You cant use <> and {{}} in your {field_name}")

    if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", v):
        raise ValueError("Cant use E-mail")

    if re.search(r"(http|https|ftp)://", v, re.IGNORECASE):
        raise ValueError("Cant use links!")

    return v.strip()
