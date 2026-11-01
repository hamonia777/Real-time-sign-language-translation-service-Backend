"""암호화 도입 이전에 평문으로 저장된 카카오 토큰을 암호화한다.

사용법 (프로젝트 루트에서 실행, .env 필요):
    python -m scripts.encrypt_legacy_kakao_tokens

이미 암호화된 값(Fernet 토큰은 'gAAAAA' 로 시작)은 건너뛴다. 여러 번 실행해도 안전하다.
"""

from sqlalchemy import text
from sqlmodel import Session

from main.core.database import engine
from main.core.encrypted_type import EncryptedText

FERNET_PREFIX = "gAAAAA"
COLUMNS = ("kakao_access_token", "kakao_refresh_token")


def main() -> None:
    encrypt = EncryptedText().process_bind_param
    updated = 0

    with Session(engine) as session:
        rows = session.execute(text("SELECT id, kakao_access_token, kakao_refresh_token FROM users")).all()
        for user_id, access_token, refresh_token in rows:
            changes = {}
            for column, value in zip(COLUMNS, (access_token, refresh_token)):
                if value and not value.startswith(FERNET_PREFIX):
                    changes[column] = encrypt(value, None)
            if changes:
                assignments = ", ".join(f"{column} = :{column}" for column in changes)
                session.execute(text(f"UPDATE users SET {assignments} WHERE id = :id"), {**changes, "id": user_id})
                updated += 1
        session.commit()

    print(f"암호화 완료: {updated}명의 토큰을 변환했습니다.")


if __name__ == "__main__":
    main()
