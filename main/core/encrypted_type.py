from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from main.core.config import settings


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    return Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())


class EncryptedText(TypeDecorator):
    """DB 에 암호화된 문자열로 저장하고, 읽을 때 자동으로 복호화하는 컬럼 타입.

    저장 전 암호화 / 조회 후 복호화가 SQLAlchemy 레벨에서 이루어지므로
    호출하는 쪽 코드는 평문 문자열을 그대로 다루면 된다.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return _fernet().encrypt(value.encode("utf-8")).decode("ascii")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
        except InvalidToken:
            # 암호화 도입 전에 저장된 평문 값. 다음 저장 시 암호화되며, 일괄 변환은 scripts/encrypt_legacy_kakao_tokens.py 로 한다.
            return value
