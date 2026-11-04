from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import OperationalError

from app.api.router import api_router
from app.core.config import get_settings
from app.core.security import limiter

app = FastAPI(title="PeerSync API")
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    # La respuesta por defecto de FastAPI repite el valor recibido (`input`),
    # lo que devolvería el token de Google en claro.
    errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse({"detail": errors}, status.HTTP_422_UNPROCESSABLE_CONTENT)


@app.exception_handler(RateLimitExceeded)
def handle_rate_limit(_: Request, __: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        {"detail": "Demasiadas peticiones, inténtalo de nuevo en un minuto"},
        status.HTTP_429_TOO_MANY_REQUESTS,
    )


@app.exception_handler(OperationalError)
def handle_database_unavailable(_: Request, __: OperationalError) -> JSONResponse:
    return JSONResponse(
        {"detail": "Servicio no disponible temporalmente"},
        status.HTTP_503_SERVICE_UNAVAILABLE,
    )


app.include_router(api_router)
