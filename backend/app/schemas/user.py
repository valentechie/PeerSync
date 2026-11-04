from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class GoogleLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # ID token que entrega Google Identity Services al navegador.
    credential: Annotated[str, Field(min_length=1, max_length=4096, repr=False)]


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
