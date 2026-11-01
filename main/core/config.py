# 가령: 26/04/19 수정내용: 병합으로 날아간 JWT/Kakao/Redis 필드 복구 및 Pydantic V2 문법 적용
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=False)
    
    PROJECT_NAME: str = "Sign Language Translator API"
    # 하위 경로 배포 시 앞에 붙는 경로 (예: "/sign"). 로컬은 빈 값.
    APP_BASE_PATH: str = ""
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

    # 카카오 토큰 등 DB 저장 민감정보 암호화 키 (Fernet). 생성: Fernet.generate_key()
    TOKEN_ENCRYPTION_KEY: str

    REDIS_HOST: str
    REDIS_PORT: int = 6379

    EMAIL_SENDER: str = ""
    EMAIL_PASSWORD: str = ""

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()