from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
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

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()