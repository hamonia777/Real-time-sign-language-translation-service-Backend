# 📚 프로젝트 개요

## 프로젝트 이름
**Real-time Sign Language Translation Service - Backend API**

## 프로젝트 목표

실시간 수어(수화) 번역 및 학습 플랫폼을 제공하여:
- ✅ 청각 장애인의 **자립적 학습** 지원
- ✅ 비장애인의 **수어 이해 증진**
- ✅ 기술과 교육의 접목으로 **접근성 향상**
- ✅ AI 기반 **개인화 학습** 제공

## 주요 기능

### 1. 실시간 수어 인식
- **손가락 문자(Fingerspell)**: A~Z 손 모양 인식
- **단어 인식**: 일상용어, 음식, 동물 등 단어 수준의 수어 인식
- **문장 인식**: 여러 단어를 연결한 문장 인식
- **기술**: PyTorch 딥러닝 + MediaPipe 손 추적

### 2. 개인화 학습 시스템
- 사용자 설문조사 기반 맞춤형 학습 경로
- 3단계 학습 (손가락 문자 → 단어 → 문장)
- 학습 진도 추적
- 학습 통계 및 분석

### 3. 사용자 관리
- Kakao OAuth 기반 소셜 로그인
- 사용자 프로필 관리
- 학습 기록 저장
- 학습 바구니 (즐겨찾기)

### 4. 실시간 통신
- WebSocket 지원 (실시간 수어 인식 결과 전송)
- 양방향 통신

### 5. 데이터 기반 인사이트
- 사용자별 학습 통계
- 정확도 추적
- 학습 시간 측정
- 진도 현황 분석

## 기술 스택

### Backend Framework
| 항목 | 기술 | 버전 |
|------|------|------|
| 웹 프레임워크 | FastAPI | 0.135.3 |
| 웹 서버 | Uvicorn | 0.42.0 |
| ORM | SQLModel | 0.0.38 |
| 데이터 검증 | Pydantic | 2.12.5 |
| 인증 | JWT + Kakao OAuth | - |

### 데이터베이스
| 항목 | 기술 | 용도 |
|------|------|------|
| 주 데이터베이스 | MySQL | 사용자, 레슨, 학습 진도 저장 |
| 캐시 | Redis | 세션, 자주 접근 데이터 캐싱 |
| 마이그레이션 | Alembic | 데이터베이스 버전 관리 |

### 머신러닝 & 컴퓨터 비전
| 항목 | 기술 | 용도 |
|------|------|------|
| 딥러닝 | PyTorch 2.9.1 | 수어 모델 로드 및 추론 |
| 손 추적 | MediaPipe 0.10.21 | 손 포즈 추정 |
| 이미지 처리 | OpenCV 4.11 | 비디오 프레임 처리 |
| 수치 계산 | NumPy 1.26.4 | 행렬 연산 |

### 보안 & 인증
| 항목 | 기술 |
|------|------|
| 비밀번호 해싱 | bcrypt 5.0.0 |
| 암호화 | cryptography 46.0.6 |
| JWT 토큰 | python-jose 3.5.0 |
| 이메일 검증 | email-validator 2.3.0 |

### 추가 라이브러리
| 항목 | 기술 | 용도 |
|------|------|------|
| 환경 변수 | python-dotenv | .env 파일 로드 |
| 로깅 | Loguru | 고급 로깅 |
| 스케줄링 | APScheduler 3.10.4 | 정기 작업 (배치 작업) |
| 웹소켓 | websockets 12.0 | 실시간 통신 |
| HTTP 클라이언트 | httpx | 외부 API 호출 |

## 프로젝트 구조

```
Root/
├── main/                          # 메인 백엔드 코드
│   ├── __init__.py
│   ├── main.py                   # FastAPI 앱 설정
│   ├── api/                      # 라우터 계층
│   │   ├── router.py            # 메인 라우터
│   │   ├── user/
│   │   ├── learning/
│   │   ├── survey/
│   │   ├── profile/
│   │   └── search/
│   ├── core/                     # 인프라 계층
│   │   ├── config.py           # 설정
│   │   ├── database.py         # DB 연결
│   │   ├── security.py         # JWT, 암호화
│   │   ├── redis_client.py     # Redis 클라이언트
│   │   ├── scheduler.py        # 백그라운드 작업
│   │   ├── email_notification.py
│   │   └── kakao_notification.py
│   ├── domain/                  # 도메인 계층 (비즈니스 로직)
│   │   ├── user/
│   │   ├── learning/
│   │   ├── UserSurveyProfiles/
│   │   ├── UserLessonProgress/
│   │   ├── LearningBasket/
│   │   ├── StudyLog/
│   │   ├── Search/
│   │   ├── ProfilePhoto/
│   │   └── Inquiry/
│   └── learning_model/          # ML 모델 계층
│       ├── model_fingerspell.pt
│       ├── model_word.pt
│       ├── model_video.pt
│       ├── recon_fingerspell.py
│       ├── recon_word.py
│       └── recon_video.py
├── frontend/                     # 프론트엔드 정적 파일
│   ├── html/                    # HTML 페이지
│   ├── css/                     # 스타일시트
│   ├── js/                      # 자바스크립트
│   └── images/                  # 이미지 및 업로드 폴더
├── alembic/                     # 데이터베이스 마이그레이션
│   ├── versions/               # 마이그레이션 스크립트
│   └── env.py
├── doc/                         # 문서 (지금 작성 중)
├── requirements.txt            # Python 의존성
├── .env                        # 환경 변수
└── README.md                   # 프로젝트 README
```

## 도메인 구조 (Domain-Driven Design)

각 도메인은 클린 아키텍처 원칙을 따릅니다:

```
{Domain}/
├── __init__.py
├── dto/                  # Data Transfer Objects (요청/응답 데이터)
│   └── {entity}_dto.py
├── entity/               # Domain Models (비즈니스 엔티티)
│   └── {entity}.py
├── repository/           # Data Access Layer (데이터 접근)
│   └── {entity}_repository.py
├── service/              # Business Logic (비즈니스 로직)
│   └── {entity}_service.py
└── usecase/              # Use Cases (응용 시나리오)
    └── {entity}_usecase.py
```

### 도메인별 설명

#### User (사용자)
- **역할**: 사용자 계정, 인증, 프로필 관리
- **주요 필드**: id, kakao_id, email, nickname, phone_num, profile_image_url
- **관계**: 여러 학습 기록, 바구니, 진도 정보

#### Learning (학습)
- **역할**: 레슨, 단어, 문장 관리
- **주요 필드**: id, title, description, type, difficulty_level
- **타입**: 손가락 문자(Fingerspell), 단어(Word), 문장(Sentence)

#### UserLessonProgress (학습 진도)
- **역할**: 사용자별 레슨 진행 상황 추적
- **주요 필드**: user_id, lesson_id, progress, completed_at, accuracy

#### LearningBasket (학습 바구니)
- **역할**: 사용자의 즐겨찾기 관리
- **주요 필드**: user_id, lesson_id, word_id, created_at

#### UserSurveyProfile (설문 프로필)
- **역할**: 사용자 설문조사 응답 저장 및 개인화
- **주요 필드**: user_id, learning_goal, preferred_difficulty, study_time

#### StudyLog (학습 기록)
- **역할**: 각 학습 세션 기록
- **주요 필드**: user_id, lesson_id, duration, accuracy, start_time, end_time

#### Search (검색)
- **역할**: 검색 기능 및 히스토리
- **주요 필드**: user_id, query, result_count, searched_at

#### ProfilePhoto (프로필 사진)
- **역할**: 사용자 프로필 사진 관리
- **주요 필드**: user_id, image_url, uploaded_at

#### Inquiry (문의)
- **역할**: 사용자 1:1 문의 관리
- **주요 필드**: user_id, title, content, status, created_at

## 핵심 API 엔드포인트

### 사용자 (User)
```
POST   /api/v1/users/register        회원가입
POST   /api/v1/auth/login            카카오 로그인
GET    /api/v1/users/me              현재 사용자 정보
PUT    /api/v1/users/{user_id}       사용자 정보 수정
DELETE /api/v1/users/{user_id}       회원탈퇴
```

### 학습 (Learning)
```
GET    /api/v1/learning/lessons      레슨 목록
GET    /api/v1/learning/lesson/{id}  레슨 상세
POST   /api/v1/learning/progress     학습 진도 저장
GET    /api/v1/learning/progress     학습 진도 조회
```

### 학습 바구니 (Basket)
```
GET    /api/v1/learning/basket       바구니 목록
POST   /api/v1/learning/basket       항목 추가
DELETE /api/v1/learning/basket/{id}  항목 삭제
```

### 설문 (Survey)
```
POST   /api/v1/users/{user_id}/survey     설문 응답 저장
GET    /api/v1/users/{user_id}/survey     설문 프로필 조회
```

### 프로필 (Profile)
```
GET    /api/v1/profile/{user_id}     프로필 조회
POST   /api/v1/profile/photo         사진 업로드
```

### 검색 (Search)
```
GET    /api/v1/search?q=keyword      검색 실행
GET    /api/v1/search/history        검색 히스토리
```

## 실행 환경 요구사항

### 필수
- **Python**: 3.11+ (권장: 3.11)
  > ⚠️ **주의**: Python 3.13 이상에서는 MediaPipe 0.10.22+에서 mp.solutions가 제거되어 손가락 문자 인식이 실패할 수 있습니다.
  > 권장 설정: `conda create -n py311_env python=3.11`

- **MySQL**: 5.7+ 또는 8.0+
- **Redis**: 5.0+

### 개발 환경 설정

1. **Python 환경 생성**
```bash
conda create -n py311_env python=3.11
conda activate py311_env
```

2. **의존성 설치**
```bash
pip install -r requirements.txt
```

3. **환경 변수 설정** (.env 파일)
```env
# 데이터베이스
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=sign_language_db

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Kakao OAuth
KAKAO_REST_API_KEY=your_kakao_key
KAKAO_REDIRECT_URI=http://localhost:8000/api/v1/auth/login/callback
KAKAO_CLIENT_SECRET=your_kakao_secret

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Email
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

4. **데이터베이스 초기화**
```bash
# 마이그레이션 생성
alembic upgrade head

# 테이블 자동 생성 (FastAPI 시작 시)
python -m uvicorn main.main:app --reload
```

5. **서버 실행**
```bash
uvicorn main.main:app --reload --host 0.0.0.0 --port 8000
```

6. **API 문서 확인**
```
http://localhost:8000/docs (Swagger UI)
http://localhost:8000/redoc (ReDoc)
```

## 주요 특징

### 1. 클린 아키텍처
- **계층 분리**: API → Domain → Database
- **의존성 주입**: 느슨한 결합
- **테스트 용이**: 각 계층 독립적 테스트 가능

### 2. 타입 안전성
- **Pydantic**: 모든 데이터 검증
- **SQLModel**: ORM + 타입 힌트
- **Python 3.11+**: 향상된 타입 힌팅

### 3. 실시간 통신
- **WebSocket**: 실시간 수어 인식 결과 전송
- **양방향 통신**: 클라이언트-서버 양쪽에서 데이터 송수신

### 4. 머신러닝 통합
- **PyTorch 모델**: 사전 학습된 수어 인식 모델
- **MediaPipe**: 실시간 손 추적
- **최적화된 추론**: GPU 지원 (가능시)

### 5. 확장 가능성
- **마이크로서비스 준비**: 각 도메인 독립화 가능
- **API 버전 관리**: /api/v1/ 경로 사용
- **플러그인 아키텍처**: 새로운 도메인 쉽게 추가 가능

## 보안

### 인증 & 인가
- **JWT 토큰 기반**: 상태 비저장(Stateless) 인증
- **Kakao OAuth**: 소셜 로그인으로 보안 강화
- **토큰 만료**: 자동 갱신 메커니즘

### 데이터 보호
- **bcrypt**: 비밀번호 단방향 해싱
- **HTTPS**: 암호화된 전송 (프로덕션)
- **CORS 설정**: 허용된 도메인만 접근 가능

### 입력 검증
- **Pydantic**: 모든 입력 데이터 타입 검증
- **SQL 인젝션 방지**: SQLModel ORM 사용
- **Rate Limiting**: (추가 설정 가능)

## 성능 최적화

### 캐싱
- **Redis**: 자주 접근하는 데이터 캐싱
- **데이터베이스 쿼리**: 인덱스 최적화

### 비동기 처리
- **FastAPI**: 기본적으로 비동기 지원
- **APScheduler**: 백그라운드 작업 비동기 처리

## 모니터링 & 로깅

### 로깅 (Loguru)
```python
from loguru import logger

logger.info("사용자 로그인: {user_id}", user_id=user_id)
logger.error("데이터베이스 오류", exc_info=True)
```

### 성능 모니터링
- 응답 시간 추적
- 에러율 모니터링
- 리소스 사용량 확인

## 배포

### 프로덕션 체크리스트
- [ ] .env 파일에서 SECRET_KEY 변경
- [ ] CORS_ORIGINS을 실제 프론트엔드 URL로 설정
- [ ] MySQL, Redis 비밀번호 설정
- [ ] 모니터링 도구 설정


## 개발 로드맵

### 현재
✅ 기본 사용자 관리
✅ 레슨 및 단어 관리
✅ 실시간 수어 인식
✅ 학습 진도 추적

## 연락처

- 개발팀: dev@example.com
- 문제 보고: issues@example.com
