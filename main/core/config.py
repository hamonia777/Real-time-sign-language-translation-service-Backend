from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sign Language Translator API"
    CORS_ORIGINS: list[str] = ["*"]
    
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str = "3306"
    DB_NAME: str

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"

settings = Settings()