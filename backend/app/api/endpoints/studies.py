from fastapi import APIRouter, Request

from app.ai.skillswap.studies import FAMILIES, STUDIES, study_label
from app.core.security import CurrentUser, limiter
from app.schemas.people import StudyFamily, StudyOption

router = APIRouter(prefix="/studies", tags=["studies"])


# `request` no se usa aquí, pero slowapi lo exige en la firma.
@router.get("", response_model=list[StudyFamily])
@limiter.limit("60/minute")
def list_studies(request: Request, user: CurrentUser) -> list[StudyFamily]:
    families = [
        StudyFamily(
            name=family,
            studies=[StudyOption(code=s.code, label=study_label(s.code)) for s in STUDIES.values() if s.family == family],
        )
        for family in FAMILIES
    ]
    others = [StudyOption(code=s.code, label=study_label(s.code)) for s in STUDIES.values() if s.family is None]
    return [*families, StudyFamily(name="Other", studies=others)]
