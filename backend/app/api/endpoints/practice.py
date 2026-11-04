from fastapi import APIRouter, HTTPException, Request, status

from app.ai import llm_client
from app.ai.practice import coach
from app.core.security import CurrentUser, limiter
from app.schemas.practice import PracticeQuestion, PracticeRequest

router = APIRouter(prefix="/practice", tags=["practice"])


# `request` no se usa aquí, pero slowapi lo exige en la firma.
# El límite es por IP y protege el gasto en Gemini, porque cualquiera puede entrar.
@router.post("/next", response_model=PracticeQuestion)
@limiter.limit("30/minute")
def next_question(request: Request, data: PracticeRequest, user: CurrentUser) -> PracticeQuestion:
    history = [coach.Turn(turn.role, turn.content) for turn in data.history]
    try:
        return PracticeQuestion(question=coach.next_question(data.topic, history))
    except llm_client.LLMNotConfiguredError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "El entrenamiento con IA aún no está configurado"
        ) from exc
    except llm_client.LLMUnavailableError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "La IA no está disponible ahora. Inténtalo de nuevo en un momento"
        ) from exc
    except llm_client.LLMEmptyResponseError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "La IA no pudo responder a eso. Prueba a decirlo de otra forma"
        ) from exc
