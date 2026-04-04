# REAL-TIME-SIGN-LANGUAGE 백엔드 프로젝트

## 📋 프로젝트 개요

FastAPI 기반의 실시간 수어 번역 서비스 백엔드 API

## 🛠️ 기술 스택

### 주요 패키지
- **Framework**: FastAPI - 고성능 Python 웹 프레임워크
- **Server**: Uvicorn - ASGI 웹 서버
- **ORM**: SQLModel - Pydantic + SQLAlchemy 통합
- **Database**: MySQL - 관계형 데이터베이스
- **Python**: 3.12+

### 보안 & 인증(추후 추가 예정)
- **python-jose**: JWT 토큰 생성/검증
- **cryptography**: 암호화 라이브러리
- **passlib + bcrypt**: 비밀번호 안전 해싱

### 기타 필수 패키지(추후 추가 예정)
- **python-multipart**: 파일 업로드 처리
- **email-validator**: 이메일 유효성 검사
- **python-dotenv**: 환경 변수 관리
- **loguru**: 고급 로깅

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

```text
main/
├── api/                    # API 라우팅 계층
│   ├── router.py           # 메인 라우터
│   └── user/
│       └── user_routes.py  # 사용자 엔드포인트
├── domain/                 # 도메인 계층
│   └── user/
│       ├── dto/            # Data Transfer Objects
│       ├── entity/         # 데이터베이스 모델
│       ├── repository/     # 리포지토리 인터페이스
│       ├── service/        # 비즈니스 로직
│       └── usecase/        # 유스케이스
├── core/                   # 공통 설정
│   ├── config.py           # 환경 설정
│   └── database.py         # 데이터 베이스 관리 코드
└── main.py                 # FastAPI 앱 진입점

## 🔧 환경 설정 파일

### .env 파일
프로젝트 루트 디렉토리에 `.env` 파일을 생성하세요:

```bash
DB_USER=app_user
DB_PASSWORD=your_secure_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=sign
```

## 📝 API 엔드포인트

### 회원가입
- **URL**: `POST /users/sign-up`
- **요청 본문**:
```json
{
  "email": "user@example.com",
  "nickname": "사용자닉네임",
  "phone_number": "010-1234-5678"
}
```
- **응답**:
```json
{
  "message": "회원가입이 완료되었습니다.",
  "nickname": "사용자닉네임"
}
```

## ⚠️ 트러블슈팅

### MySQL 연결 오류 (Access Denied)
```
ERROR 1698 (28000): Access denied for user 'root'@'localhost'
```

비밀번호나 그런건 문제가 없을텐데 계속 연결이 거부되는 상황이 발생

알아보니 윈도우 사용자일 경우 socket authentication을 사용해서 비밀번호 인증이 안 되는 경우가 있다함

두가지 방법으로 해결 가능

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
