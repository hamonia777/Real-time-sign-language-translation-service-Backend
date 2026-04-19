# 가령: 26/04/19 수정내용: 병합으로 날아간 JWT/Kakao/Redis 필드 복구 및 Pydantic V2 문법 적용
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # 팀원분의 Pydantic V2 최신 문법 채택
    model_config = ConfigDict(env_file=".env", case_sensitive=False)
    
    PROJECT_NAME: str = "Sign Language Translator API"
    CORS_ORIGINS: list[str] = ["*"]
    
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str = "3306"
    DB_NAME: str
    
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    KAKAO_REST_API_KEY: str
    KAKAO_REDIRECT_URI: str
    KAKAO_CLIENT_SECRET: str
    
    REDIS_HOST: str
    REDIS_PORT: int = 6379

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()