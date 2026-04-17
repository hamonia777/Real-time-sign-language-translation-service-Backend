from abc import ABC, abstractmethod
from sqlmodel import Session
from fastapi import Depends

from main.core.database import get_db
from main.domain.UserSurveyProfiles.entity.user_survey_profiles import UserSurveyProfile

class SurveyRepository(ABC):
    @abstractmethod
    async def save(self, survey: UserSurveyProfile) -> UserSurveyProfile:
        pass

class SqlSurveyRepository(SurveyRepository):
    def __init__(self, db: Session):
        self.db = db

    async def save(self, survey: UserSurveyProfile) -> UserSurveyProfile:
        merged_survey = self.db.merge(survey)
        self.db.commit()
        return merged_survey

def get_survey_repository(db: Session = Depends(get_db)) -> SurveyRepository:
    return SqlSurveyRepository(db)