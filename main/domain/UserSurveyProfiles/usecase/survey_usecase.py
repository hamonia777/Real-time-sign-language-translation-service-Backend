from fastapi import Depends
from main.domain.UserSurveyProfiles.dto.survey_request_dto import SurveyRequestDto
from main.domain.UserSurveyProfiles.entity.user_survey_profiles import UserSurveyProfile
from main.domain.UserSurveyProfiles.repository.survey_repository import SurveyRepository, get_survey_repository

class SurveyUseCase:
    def __init__(self, survey_repo: SurveyRepository = Depends(get_survey_repository)):
        self.survey_repo = survey_repo

    async def execute(self, user_id: int, req: SurveyRequestDto):
        new_survey = UserSurveyProfile(
            user_id=user_id,
            level=req.signLanguageLevel,
            type=req.communicationType,
            difficulty=req.learningDifficulty
        )
        await self.survey_repo.save(new_survey)

        return {"msg": "설문 정보 저장 완료"}