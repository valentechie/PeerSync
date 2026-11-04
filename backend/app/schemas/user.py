from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints

BCRYPT_MAX_BYTES = 72


def _lowercase(email: str) -> str:
    return email.lower()


def _fits_bcrypt(password: str) -> str:
    # bcrypt solo admite 72 bytes; se limitan bytes, no caracteres.
    if len(password.encode()) > BCRYPT_MAX_BYTES:
        raise ValueError(f"La contraseña no puede superar {BCRYPT_MAX_BYTES} bytes")
    return password


NormalizedEmail = Annotated[EmailStr, AfterValidator(_lowercase)]


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    email: NormalizedEmail
    password: Annotated[str, Field(min_length=8, repr=False), AfterValidator(_fits_bcrypt)]


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: NormalizedEmail
    # Sin longitud mínima: una contraseña corta es un 401, no un error de validación.
    password: Annotated[str, Field(min_length=1, repr=False), AfterValidator(_fits_bcrypt)]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserRead
