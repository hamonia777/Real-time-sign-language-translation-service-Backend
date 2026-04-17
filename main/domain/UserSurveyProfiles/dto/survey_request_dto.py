from pydantic import BaseModel, EmailStr, Field

class SurveyRequestDto(BaseModel):
    signLanguageLevel: int
    communicationType: str
    learningDifficulty: str
