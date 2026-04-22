# 🤟 REAL-TIME-SIGN-LANGUAGE TRANSLATION SERVICE - Backend API

## 📋 프로젝트 개요

FastAPI 기반의 실시간 수어 번역 서비스 백엔드 API입니다. 
사용자가 수어를 인식하고 학습할 수 있는 통합 플랫폼을 제공합니다.

### 주요 기능
- ✅ **실시간 수어 인식**: 손가락 문자(Fingerspell) 및 단어 수준의 수어 인식
- ✅ **사용자 학습 관리**: 진도상황, 학습 바구니, 학습 로그 관리
- ✅ **개인화 학습**: 사용자별 설문조사 기반 맞춤형 학습 경험
- ✅ **소셜 로그인**: Kakao OAuth 통합
- ✅ **실시간 통신**: WebSocket 지원
- ✅ **API Documentation**: Swagger UI 자동 생성

## 🛠️ 기술 스택

### 코어 프레임워크 & 서버
- **Framework**: FastAPI (0.135.3) - 고성능 Python 웹 프레임워크
- **Server**: Uvicorn (0.42.0) - ASGI 웹 서버
- **ORM**: SQLModel (0.0.38) - Pydantic + SQLAlchemy 통합
- **Database**: MySQL - 관계형 데이터베이스
- **Python**: 3.11+

### 데이터 검증 & 설정
- **pydantic** (2.12.5) - 데이터 검증
- **pydantic-settings** (2.13.1) - 환경 변수 관리
- **SQLAlchemy** (2.0.49) - 데이터베이스 ORM
- **pymysql** (1.1.2) - MySQL 드라이버

### 보안 & 인증
- **python-jose** (3.5.0) - JWT 토큰 생성/검증
- **cryptography** (46.0.6) - 암호화 라이브러리
- **passlib + bcrypt** (1.7.4, 5.0.0) - 비밀번호 안전 해싱
- **python-multipart** (0.0.22) - 파일 업로드 처리

### Machine Learning & 이미지 처리
- **torch** - PyTorch 기반 모델 로딩
- **mediapipe** - 손 포즈 인식
- **opencv-python** - 이미지 처리
- **Pillow** - 이미지 조작
- **numpy** - 수치 계산

### 기타 유틸리티
- **websockets** - 실시간 통신
- **python-dotenv** (1.2.2) - 환경 변수 로딩
- **email-validator** (2.3.0) - 이메일 유효성 검사
- **loguru** (0.7.3) - 고급 로깅
- **redis** - 캐싱 및 세션 관리

## 📦 설치 방법

### 1단계: 프로젝트 클론
```bash
git clone <repository-url>
cd Real-time-sign-language-translation-service-Backend
```

### 2단계: Python 가상환경 생성
```bash
python3 -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3단계: 필수 패키지 설치
```bash
pip install -r requirements.txt
```

### 4단계: 환경 변수 설정
```bash
# .env.example 파일을 복사하여 .env 생성
cp .env.example .env
```

`.env` 파일을 열어 다음 정보를 입력:
```
DB_USER=root
DB_PASSWORD=<your_mysql_password>
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=sign
```

### 5단계: MySQL 데이터베이스 설정(로컬 db로 테스트할때)

#### 옵션 A: 새 사용자 생성 (만약 안될시에 시도해보세요)
```bash
# MySQL에 접속
mysql -u root

# 새 사용자 생성
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON sign.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

그 후 `.env` 파일 수정:
```
DB_USER=app_user
DB_PASSWORD=your_password
```

#### 옵션 B: root 사용자 사용 (WSL/Linux)
```bash
# MySQL에 접속 (비밀번호 없이)
mysql -u root

# root 비밀번호 설정
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_password';
FLUSH PRIVILEGES;
EXIT;
```


## 🚀 실행 방법

### 개발 서버 시작
```bash
uvicorn main.main:app --reload
```

- API 문서: http://127.0.0.1:8000/docs (Swagger UI)
- 대체 문서: http://127.0.0.1:8000/redoc (ReDoc)
- 루트 엔드포인트: http://127.0.0.1:8000/

```

## 📂 프로젝트 구조 (Project Structure)

Real-time-sign-language-translation-service-Backend/
├── main/                           # 백엔드 애플리케이션
│   ├── api/                        # API 라우팅 계층
│   │   ├── router.py               # 메인 라우터
│   │   └── user/
│   │       ├── user_routes.py      # 사용자 관련 엔드포인트
│   │   └── learning/
│   │       └── learning_routes.py  # 학습 관련 엔드포인트
│   │
│   ├── core/                       # 핵심 설정 및 유틸리티
│   │   ├── config.py               # 환경 설정 (DB, JWT, OAuth 등)
│   │   ├── database.py             # 데이터베이스 연결 관리
│   │   ├── redis_client.py         # Redis 캐싱
│   │   └── security.py             # 보안 및 인증 로직
│   │
│   ├── domain/                     # 도메인 계층 (비즈니스 로직)
│   │   ├── user/                   # 사용자 도메인
│   │   │   ├── dto/                # Data Transfer Objects
│   │   │   ├── entity/             # 데이터베이스 모델
│   │   │   ├── repository/         # 데이터 접근 계층
│   │   │   ├── service/            # 비즈니스 로직
│   │   │   └── usecase/            # 유스케이스
│   │   │
│   │   ├── learning/               # 학습 도메인
│   │   │   ├── dto/                # DTO (lesson, recognition 등)
│   │   │   ├── entity/             # Lesson 엔티티
│   │   │   ├── repository/
│   │   │   ├── service/            # 수어 인식 서비스
│   │   │   └── usecase/
│   │   │
│   │   ├── Inquiry/                # 문의 도메인
│   │   ├── LearningBasket/         # 학습 바구니
│   │   ├── LessonWordMapping/      # 레슨-단어 매핑
│   │   ├── StudyLog/               # 학습 로그
│   │   ├── UserLessonProgress/     # 사용자 학습 진도
│   │   └── UserSurveyProfiles/     # 사용자 설문 정보
│   │
│   ├── learning_model/             # 머신러닝 모델
│   │   ├── model_fingerspell.pt    # 손가락 문자 인식 모델
│   │   ├── model_word.pt           # 단어 수어 인식 모델
│   │   ├── recon_fingerspell.py    # 손가락 문자 인식 로직
│   │   └── recon_word.py           # 단어 수어 인식 로직
│   │
│   └── main.py                     # FastAPI 애플리케이션 진입점
│
├── frontend/                       # 프론트엔드 정적 파일
│   ├── html/                       # HTML 페이지
│   │   ├── home.html               # 메인 페이지
│   │   ├── login.html              # 로그인 페이지
│   │   ├── register.html           # 회원가입 페이지
│   │   ├── learning.html           # 학습 페이지
│   │   ├── sign_learn.html         # 수어 학습 상세 페이지
│   │   ├── search.html             # 검색 페이지
│   │   ├── mypage.html             # 마이페이지
│   │   └── support.html            # 지원 페이지
│   ├── css/                        # 스타일시트
│   └── js/                         # 프론트엔드 스크립트
│       └── ... (각 페이지별 동작 로직)
│
├── alembic/                        # 데이터베이스 마이그레이션
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── .env                            # 환경 변수 (Git 제외)
├── .env.example                    # 환경 변수 예시
├── requirements.txt                # Python 의존성
├── alembic.ini                     # Alembic 설정
└── README.md                       # 이 파일
```
### 도메인 아키텍처 설명

프로젝트는 **계층화 아키텍처(Layered Architecture)**를 따릅니다:

1. **API 계층** (`api/`): HTTP 요청 처리 및 라우팅
2. **도메인 계층** (`domain/`): 비즈니스 로직 구현
   - **Entity**: 데이터베이스 모델
   - **DTO**: 요청/응답 데이터 구조
   - **Repository**: 데이터 접근
   - **Service**: 비즈니스 로직
   - **UseCase**: 고수준 비즈니스 프로세스
3. **핵심 계층** (`core/`): DB, 환경 설정, 보안



## � 환경 설정 

### .env 파일 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하세요:


## 🚀 실행 방법

### 개발 서버 시작
```bash
uvicorn main.main:app --reload
```

**API 문서 접근:**
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 데이터베이스 스키마

주요 테이블:
- **users**: 사용자 정보
- **lessons**: 수어 레슨
- **study_logs**: 학습 로그
- **user_lesson_progress**: 사용자 학습 진度
- **learning_basket**: 학습 바구니
- **user_survey_profiles**: 사용자 설문 정보
- **inquiries**: 사용자 문의

## ⚠️ 트러블슈팅

### 1. MySQL 연결 오류 (Access Denied)
```
ERROR 1698 (28000): Access denied for user 'root'@'localhost'
```

**해결 방법:**
Windows 사용자의 경우 socket authentication으로 인해 비밀번호 인증이 실패할 수 있습니다.

**옵션 A: 새로운 사용자 생성**
```bash
# MySQL에 접속
mysql -u root

# 새 사용자 생성
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON sign.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

그 후 `.env` 파일 수정:
```env
DB_USER=app_user
DB_PASSWORD=your_password
```

**옵션 B: root 사용자 인증 변경 (WSL/Linux)**
```bash
# MySQL에 접속
mysql -u root

# root 비밀번호 설정
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_password';
FLUSH PRIVILEGES;
EXIT;
```

### 2. 포트 이미 사용 중 (Port already in use)
```
OSError: [Errno 48] Address already in use
```

**해결 방법:**
```bash
# 다른 포트로 실행
uvicorn main.main:app --reload --port 8001

# 또는 기존 프로세스 종료
# Windows PowerShell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force

# Linux/macOS
lsof -ti:8000 | xargs kill -9
```

### 3. PyTorch/MediaPipe 설치 오류
대용량 라이브러리(torch, mediapipe)로 인한 설치 문제가 발생하는 경우:

```bash
# 캐시 초기화 후 재설치
pip install --no-cache-dir -r requirements.txt

# 또는 개별 설치
pip install --no-cache-dir torch
pip install --no-cache-dir mediapipe
```

### 4. Redis 연결 오류
Redis가 설치되지 않았거나 실행 중이지 않은 경우:

```bash
# Redis 설치 (Linux/macOS)
brew install redis

# Redis 실행
redis-server

# Windows는 Docker 또는 WSL 사용 권장
```

## 📋 요구사항

- Python 3.11 이상
- MySQL 5.7 이상
- Redis 5.0 이상 (옵션)
- 최소 4GB RAM (PyTorch 모델 로딩)

## 🔐 보안 주의사항

- `.env` 파일은 자격 증명을 포함하므로 Git에 커밋하지 마세요
- `JWT_SECRET_KEY`는 강력한 무작위 문자열을 사용하세요
- 프로덕션 환경에서는 CORS 설정을 제한하세요

## 📚 추가 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLModel 문서](https://sqlmodel.tiangolo.com/)
- [MediaPipe 문서](https://mediapipe.dev/)

## 👨‍💻 개발팀

이 프로젝트는 실시간 수어 번역 서비스를 제공하기 위해 만들어졌습니다.

## 📄 라이선스

이 프로젝트의 라이선스는 [프로젝트 라이선스]를 참고하세요.


1. SOCKET으로 로컬 연결
 mysql -u root -e "SELECT VERSION();"  # 비밀번호 없이 연결됨

2. 앱에서 사용할 별도 사용자 생성

# MySQL에 root로 접속
mysql -u root

# 새 사용자 생성
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'AApolk147!!';
GRANT ALL PRIVILEGES ON sign.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;

### ModuleNotFoundError
```bash
# 가상환경 활성화 확인
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate     # Windows

# 패키지 재설치
pip install -r requirements.txt
```

## 📚 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangeous.io/)
- [SQLModel 공식 문서](https://sqlmodel.tiangeous.dev/)
- [Pydantic 공식 문서](https://docs.pydantic.dev/)

- [FAST API 튜토리얼](https://m.blog.naver.com/sodaincan7/223214093562)
- [클린코드 기반 레이아웃 구조](https://devocean.sk.com/blog/techBoardDetail.do?ID=166993&boardType=techBlog)
- [라우터 전략](https://brotherdan.tistory.com/40)
- [SQL 연결 참고](https://jaeseo0519.tistory.com/392)
