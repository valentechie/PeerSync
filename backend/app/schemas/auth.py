from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints


class DemoLogin(BaseModel):
    # No hay campo de contraseña: en modo demo no se comprueba ni se recibe.
    model_config = ConfigDict(extra="ignore")

    email: Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=1, max_length=320)]


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
