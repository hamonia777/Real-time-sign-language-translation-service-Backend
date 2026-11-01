# 카카오 토큰 DB 암호화

## 1. 배경

카카오 로그인 후 발급되는 `access_token`과 `refresh_token`은 `users` 테이블에 저장되어 카카오 API(알림 발송 등)를 대신 호출하는 데 쓰입니다. 이 값이 DB에 평문으로 있으면, DB가 유출되는 순간 모든 사용자의 카카오 계정으로 API 호출이 가능해집니다.

이를 막기 위해 DB에 저장할 때 암호화하고, 읽을 때 복호화하도록 바꿨습니다.

## 2. 설계

| 항목 | 선택 | 이유 |
|---|---|---|
| 암호화 방식 | `cryptography`의 **Fernet** (AES-128-CBC + HMAC-SHA256) | 인증된 암호화(무결성 검증 포함), 표준 라이브러리 수준으로 검증됨, 이미 `requirements.txt`에 포함 |
| 적용 위치 | SQLAlchemy **TypeDecorator** (`EncryptedText`) | 저장/조회 시 자동 처리되므로 라우터·유스케이스 코드를 수정하지 않아도 됨 |
| 키 관리 | 환경변수 `TOKEN_ENCRYPTION_KEY` | 코드와 DB에 키를 두지 않음. 운영 환경에서는 `.env` 또는 시크릿 매니저로 주입 |
| 스키마 | 기존 `TEXT` 컬럼 그대로 사용 | 테이블 구조 변경 없이 적용 가능 |

## 3. 구성 파일

- `main/core/encrypted_type.py`: `EncryptedText` 타입 정의
- `main/domain/user/entity/user.py`: `kakao_access_token`, `kakao_refresh_token` 컬럼에 `EncryptedText` 적용
- `main/core/config.py`: `TOKEN_ENCRYPTION_KEY` 설정 추가 (필수값)
- `scripts/encrypt_legacy_kakao_tokens.py`: 암호화 도입 전 평문 토큰을 일괄 변환하는 스크립트
- `tests/test_token_encryption.py`: 암·복호화 단위 테스트

## 4. 동작 방식

1. **저장 시**: 평문 토큰 → Fernet 암호화 → `gAAAAA...` 형태의 문자열로 DB 저장
2. **조회 시**: DB 값 → Fernet 복호화 → 평문으로 애플리케이션에 전달
3. **기존 평문 데이터**: 복호화가 실패하면(평문이면) 그대로 반환합니다. 다음 저장 때 자동으로 암호화되고, 아래 스크립트로 한 번에 변환할 수도 있습니다.

## 5. 키 생성과 설정

```bash
# 키 생성 (한 번만 실행하고 안전한 곳에 보관)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

`.env`에 추가합니다.

```
TOKEN_ENCRYPTION_KEY=<생성된 키>
```

> **주의**
> - 키를 잃어버리면 기존 토큰을 복호화할 수 없습니다. 사용자가 카카오 로그인을 다시 해야 합니다.
> - 키를 바꾸면 기존 데이터도 복호화되지 않습니다. 키 교체가 필요하면 먼저 모든 토큰을 복호화한 뒤 새 키로 다시 암호화해야 합니다.
> - 키는 저장소에 커밋하지 않습니다 (`.env`는 `.gitignore`에 포함).

## 6. 기존 데이터 변환

```bash
python -m scripts.encrypt_legacy_kakao_tokens
```

- 평문으로 남아 있는 토큰만 암호화합니다.
- 이미 암호화된 값은 건너뛰므로 여러 번 실행해도 안전합니다.
- **운영 DB에 실행하기 전에 백업을 먼저 받으세요.**

## 7. 검증

- 단위 테스트: 암호화 결과가 평문과 다름, 복호화하면 원래 값으로 돌아옴, `None` 처리, 평문 호환 (7개 테스트 중 암호화 관련 3개)
- 실제 ORM 검증: 메모리 SQLite에 저장 후 원시 SQL로 조회하면 `gAAAAA...` 암호문이 보이고, ORM으로 읽으면 평문이 나옴을 확인
- 변환 스크립트 검증: 평문 행을 넣고 실행하면 암호화되며, 두 번째 실행은 0건 변환

## 8. 한계와 후속 과제

- 암호화 키는 여전히 환경변수에 있으므로, 서버 자체가 침해되면 키도 함께 노출될 수 있습니다. 운영 단계에서는 AWS KMS, GCP Secret Manager 같은 시크릿 매니저 사용을 권장합니다.
- 키 교체(rotation) 절차는 아직 자동화되어 있지 않습니다. `MultiFernet`을 쓰면 여러 키를 동시에 두고 점진적으로 교체할 수 있습니다.
- 애플리케이션 로그에 토큰이 출력되지 않는지 별도로 점검이 필요합니다.
