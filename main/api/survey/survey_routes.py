import httpx
from fastapi import APIRouter, Depends, Response, HTTPException
from fastapi.responses import RedirectResponse
from main.core.config import settings
from main.domain.user.dto.user_request_dto import UserSignUpRequestDto
from main.domain.UserSurveyProfiles.dto.survey_request_dto import SurveyRequestDto
from main.domain.UserSurveyProfiles.usecase.survey_usecase import SurveyUseCase
from main.core.security import get_current_user_id

router = APIRouter()

@router.post("/profile/survey")
async def submit_survey(
    survey_req: SurveyRequestDto,
    usecase: SurveyUseCase = Depends(),
    user_id: int = Depends(get_current_user_id)
):
    result = await usecase.execute(user_id, survey_req)
    return result