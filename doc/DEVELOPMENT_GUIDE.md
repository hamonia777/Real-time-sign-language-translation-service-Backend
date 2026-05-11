# 📖 개발 가이드 및 컨벤션

## 1. 코드 구조 및 컨벤션

### 1.1 파일 및 폴더 명명 규칙

```
✅ 올바른 예
- user_routes.py (소문자, 언더스코어)
- UserService.py (클래스명, PascalCase)
- user_dto.py (소문자)
- user_repository.py (소문자)

❌ 잘못된 예
- UserRoutes.py (라우터는 소문자)
- user-routes.py (하이픈 사용)
- UserRoute.py (단수형)
```

### 1.2 Python 코드 스타일

**PEP 8 준수**
```python
# ✅ 올바른 코드
from typing import Optional, List
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(max_length=50)
    nickname: Optional[str] = Field(default=None, max_length=50)
    
    def get_full_profile(self) -> dict:
        \"\"\"사용자 전체 프로필 반환\"\"\"
        return {
            \"id\": self.id,
            \"email\": self.email,
            \"nickname\": self.nickname
        }

# ❌ 잘못된 코드
from typing import *
import sqlmodel  # 왜냐하면 * 사용

class user(SQLModel):  # 클래스명은 PascalCase
    id:int  # 타입 힌트 형식 오류
    email=None  # 필드 정의 방식 오류
```

**줄 길이**: 최대 88자 (Black 스타일)
```python
# ✅ 올바른 형식
def process_learning_data(
    user_id: int,
    lesson_id: int,
    accuracy: float,
    duration: int
) -> dict:
    pass

# ❌ 너무 긴 줄
def process_learning_data(user_id: int, lesson_id: int, accuracy: float, duration: int) -> dict:
    pass
```

### 1.3 Docstring 작성

**Google 스타일 Docstring**
```python
def calculate_accuracy(
    predictions: List[str],
    ground_truth: List[str]
) -> float:
    \"\"\"예측값과 실제값을 비교하여 정확도를 계산합니다.
    
    Args:
        predictions: 모델의 예측 결과 리스트
        ground_truth: 실제 정답 리스트
    
    Returns:
        정확도 (0.0~100.0)
    
    Raises:
        ValueError: 두 리스트의 길이가 다를 때
    
    Examples:
        >>> preds = ['A', 'B', 'A']
        >>> truth = ['A', 'B', 'C']
        >>> accuracy = calculate_accuracy(preds, truth)
        >>> print(f\"{accuracy:.2f}%\")  # 66.67%
    \"\"\"
    if len(predictions) != len(ground_truth):
        raise ValueError(\"예측과 정답의 길이가 일치해야 합니다\")
    
    correct = sum(p == t for p, t in zip(predictions, ground_truth))
    return (correct / len(predictions)) * 100
```

---

## 2. 도메인별 개발 가이드

### 2.1 새로운 도메인 추가하기

**Step 1: 폴더 구조 생성**
```
main/domain/newdomain/
├── __init__.py
├── dto/
│   ├── __init__.py
│   └── newdomain_dto.py
├── entity/
│   ├── __init__.py
│   └── newdomain.py
├── repository/
│   ├── __init__.py
│   └── newdomain_repository.py
├── service/
│   ├── __init__.py
│   └── newdomain_service.py
└── usecase/
    ├── __init__.py
    └── newdomain_usecase.py
```

**Step 2: Entity 정의** (newdomain.py)
```python
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class NewDomain(SQLModel, table=True):
    __tablename__ = \"new_domains\"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key=\"users.id\")
    name: str = Field(max_length=100)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

**Step 3: DTO 정의** (newdomain_dto.py)
```python
from typing import Optional
from pydantic import BaseModel

class NewDomainCreate(BaseModel):
    \"\"\"생성용 DTO\"\"\"
    name: str
    description: Optional[str] = None

class NewDomainUpdate(BaseModel):
    \"\"\"수정용 DTO\"\"\"
    name: Optional[str] = None
    description: Optional[str] = None

class NewDomainResponse(BaseModel):
    \"\"\"응답용 DTO\"\"\"
    id: int
    user_id: int
    name: str
    description: Optional[str]
    created_at: str
```

**Step 4: Repository 정의** (newdomain_repository.py)
```python
from typing import Optional, List
from sqlmodel import Session, select
from main.domain.newdomain.entity.newdomain import NewDomain

class NewDomainRepository:
    \"\"\"NewDomain 데이터 접근 계층\"\"\"
    
    @staticmethod
    def create(session: Session, new_domain: NewDomain) -> NewDomain:
        \"\"\"새로운 데이터 생성\"\"\"
        session.add(new_domain)
        session.commit()
        session.refresh(new_domain)
        return new_domain
    
    @staticmethod
    def get_by_id(session: Session, id: int) -> Optional[NewDomain]:
        \"\"\"ID로 조회\"\"\"
        return session.get(NewDomain, id)
    
    @staticmethod
    def get_by_user(session: Session, user_id: int) -> List[NewDomain]:
        \"\"\"사용자별 조회\"\"\"
        statement = select(NewDomain).where(NewDomain.user_id == user_id)
        return session.exec(statement).all()
    
    @staticmethod
    def update(session: Session, id: int, **kwargs) -> Optional[NewDomain]:
        \"\"\"데이터 수정\"\"\"
        new_domain = session.get(NewDomain, id)
        if not new_domain:
            return None
        
        for key, value in kwargs.items():
            setattr(new_domain, key, value)
        
        session.add(new_domain)
        session.commit()
        session.refresh(new_domain)
        return new_domain
    
    @staticmethod
    def delete(session: Session, id: int) -> bool:
        \"\"\"데이터 삭제\"\"\"
        new_domain = session.get(NewDomain, id)
        if not new_domain:
            return False
        
        session.delete(new_domain)
        session.commit()
        return True
```

**Step 5: UseCase 정의** (newdomain_usecase.py)
```python
from typing import Optional, List
from sqlmodel import Session
from main.domain.newdomain.entity.newdomain import NewDomain
from main.domain.newdomain.repository.newdomain_repository import NewDomainRepository
from main.domain.newdomain.dto.newdomain_dto import (
    NewDomainCreate,
    NewDomainUpdate,
    NewDomainResponse
)

class NewDomainUseCase:
    \"\"\"NewDomain 비즈니스 로직\"\"\"
    
    def __init__(self, session: Session):
        self.session = session
        self.repository = NewDomainRepository()
    
    def create_new_domain(
        self,
        user_id: int,
        dto: NewDomainCreate
    ) -> NewDomainResponse:
        \"\"\"새로운 항목 생성\"\"\"
        new_domain = NewDomain(
            user_id=user_id,
            name=dto.name,
            description=dto.description
        )
        created = self.repository.create(self.session, new_domain)
        return self._to_response(created)
    
    def get_new_domain(self, id: int) -> Optional[NewDomainResponse]:
        \"\"\"항목 조회\"\"\"
        new_domain = self.repository.get_by_id(self.session, id)
        return self._to_response(new_domain) if new_domain else None
    
    def _to_response(self, entity: NewDomain) -> NewDomainResponse:
        \"\"\"Entity를 Response DTO로 변환\"\"\"
        return NewDomainResponse(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at.isoformat()
        )
```

**Step 6: Router 정의** (api/newdomain/newdomain_routes.py)
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from main.core.database import get_session
from main.core.security import get_current_user
from main.domain.newdomain.dto.newdomain_dto import (
    NewDomainCreate,
    NewDomainResponse
)
from main.domain.newdomain.usecase.newdomain_usecase import NewDomainUseCase

router = APIRouter()

@router.post(\"/\", response_model=NewDomainResponse, status_code=status.HTTP_201_CREATED)
async def create_new_domain(
    dto: NewDomainCreate,
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    \"\"\"새로운 항목 생성\"\"\"
    usecase = NewDomainUseCase(session)
    return usecase.create_new_domain(current_user.id, dto)

@router.get(\"/{id}\", response_model=NewDomainResponse)
async def get_new_domain(
    id: int,
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    \"\"\"항목 조회\"\"\"
    usecase = NewDomainUseCase(session)
    new_domain = usecase.get_new_domain(id)
    
    if not new_domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=\"항목을 찾을 수 없습니다\"
        )
    
    return new_domain
```

**Step 7: 라우터 통합** (api/router.py)
```python
from main.api.newdomain import newdomain_routes

api_router.include_router(
    newdomain_routes.router,
    prefix=\"/api/v1/newdomains\",
    tags=[\"NewDomains\"],
)
```

---

## 3. 데이터베이스 작업

### 3.1 마이그레이션 생성

```bash
# 자동 마이그레이션 생성
alembic revision --autogenerate -m \"새 테이블 추가\"

# 생성된 파일 확인
cat alembic/versions/xxx_새_테이블_추가.py

# 적용
alembic upgrade head
```

### 3.2 복잡한 쿼리 작성

```python
from sqlmodel import Session, select, func
from main.domain.user.entity.user import User
from main.domain.study_log.entity.study_log import StudyLog

def get_user_statistics(session: Session, user_id: int) -> dict:
    \"\"\"사용자의 학습 통계 조회\"\"\"
    
    # 총 학습 시간
    total_duration_result = session.exec(
        select(func.sum(StudyLog.duration)).where(
            StudyLog.user_id == user_id
        )
    ).first()
    total_duration = total_duration_result or 0
    
    # 평균 정확도
    avg_accuracy = session.exec(
        select(func.avg(StudyLog.accuracy)).where(
            StudyLog.user_id == user_id
        )
    ).first() or 0
    
    # 총 학습 세션 수
    session_count = session.exec(
        select(func.count(StudyLog.id)).where(
            StudyLog.user_id == user_id
        )
    ).first() or 0
    
    return {
        \"total_duration_hours\": total_duration / 3600,
        \"average_accuracy\": avg_accuracy,
        \"total_sessions\": session_count
    }
```

---

## 4. 에러 처리

### 4.1 커스텀 예외 정의

```python
# main/core/exceptions.py
class AppException(Exception):
    \"\"\"기본 애플리케이션 예외\"\"\"
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ResourceNotFoundError(AppException):
    \"\"\"리소스를 찾을 수 없음\"\"\"
    def __init__(self, resource_type: str, resource_id: int):
        super().__init__(
            code=\"NOT_FOUND\",
            message=f\"{resource_type}(ID: {resource_id})을 찾을 수 없습니다\",
            status_code=404
        )

class DuplicateDataError(AppException):
    \"\"\"중복 데이터 오류\"\"\"
    def __init__(self, field: str, value: str):
        super().__init__(
            code=\"DUPLICATE_DATA\",
            message=f\"{field}이 이미 존재합니다: {value}\",
            status_code=409
        )
```

### 4.2 예외 처리기

```python
# main/main.py에 추가
from main.core.exceptions import AppException
from fastapi import FastAPI
from fastapi.responses import JSONResponse

@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            \"status\": \"error\",
            \"code\": exc.code,
            \"message\": exc.message
        }
    )
```

---

## 5. 로깅

### 5.1 로거 설정

```python
# main/core/logger.py
from loguru import logger
import sys

logger.remove()  # 기본 핸들러 제거

# 콘솔 로깅
logger.add(
    sys.stdout,
    format=\"<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>\",
    level=\"INFO\"
)

# 파일 로깅
logger.add(
    \"logs/app_{time:YYYY-MM-DD}.log\",
    rotation=\"00:00\",  # 매일 자정에 새 파일
    retention=\"7 days\",  # 7일간 보관
    level=\"DEBUG\"
)

# 에러 로깅
logger.add(
    \"logs/error_{time:YYYY-MM-DD}.log\",
    level=\"ERROR\"
)
```

### 5.2 로깅 사용

```python
from main.core.logger import logger

def create_user(user_data: dict) -> User:
    logger.info(f\"사용자 생성 시작: {user_data.get('email')}\")
    try:
        user = User(**user_data)
        session.add(user)
        session.commit()
        logger.info(f\"사용자 생성 완료: user_id={user.id}\")
        return user
    except Exception as e:
        logger.error(f\"사용자 생성 실패: {str(e)}\", exc_info=True)
        raise
```

---

## 6. 테스트 작성

### 6.1 단위 테스트

```python
# tests/test_user_usecase.py
import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool
from main.domain.user.entity.user import User
from main.domain.user.usecase.user_usecase import UserUseCase

@pytest.fixture(name=\"session\")
def session_fixture():
    \"\"\"테스트용 임시 데이터베이스\"\"\"
    engine = create_engine(
        \"sqlite://\",
        connect_args={\"check_same_thread\": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_create_user(session: Session):
    \"\"\"사용자 생성 테스트\"\"\"
    usecase = UserUseCase(session)
    user_data = {
        \"email\": \"test@example.com\",
        \"nickname\": \"testuser\"
    }
    
    user = usecase.create_user(user_data)
    
    assert user.email == \"test@example.com\"
    assert user.nickname == \"testuser\"

def test_get_user(session: Session):
    \"\"\"사용자 조회 테스트\"\"\"
    usecase = UserUseCase(session)
    
    # 사용자 생성
    user = User(email=\"test@example.com\", nickname=\"testuser\")
    session.add(user)
    session.commit()
    
    # 조회
    retrieved = usecase.get_user(user.id)
    
    assert retrieved is not None
    assert retrieved.email == \"test@example.com\"
```

### 6.2 통합 테스트

```python
# tests/test_user_api.py
from fastapi.testclient import TestClient
from main.main import app

client = TestClient(app)

def test_register_user():
    \"\"\"사용자 등록 API 테스트\"\"\"
    response = client.post(
        \"/api/v1/users/register\",
        json={
            \"email\": \"newuser@example.com\",
            \"nickname\": \"newuser\"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data[\"status\"] == \"success\"
    assert data[\"data\"][\"email\"] == \"newuser@example.com\"
```

---

## 7. 성능 최적화

### 7.1 데이터베이스 쿼리 최적화

```python
# ❌ N+1 문제
users = session.exec(select(User)).all()
for user in users:
    lessons = session.exec(
        select(Lesson).where(Lesson.user_id == user.id)
    ).all()  # 각 사용자마다 쿼리 발생

# ✅ JOIN 사용
from sqlalchemy.orm import joinedload

users = session.exec(
    select(User).options(joinedload(User.lessons))
).unique().all()
```

### 7.2 캐싱

```python
from main.core.redis_client import redis_client
import json

def get_lessons_cached(lesson_type: str) -> list:
    \"\"\"캐시된 레슨 조회\"\"\"
    cache_key = f\"lessons:{lesson_type}\"
    
    # 캐시 확인
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 데이터베이스 조회
    lessons = session.exec(
        select(Lesson).where(Lesson.type == lesson_type)
    ).all()
    
    # 캐시 저장 (1시간)
    redis_client.setex(
        cache_key,
        3600,
        json.dumps([lesson.dict() for lesson in lessons])
    )
    
    return lessons
```

---

## 8. 보안

### 8.1 입력 검증

```python
from pydantic import BaseModel, Field, validator

class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=50)
    nickname: str = Field(..., min_length=2, max_length=50)
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('유효한 이메일이 아닙니다')
        return v
    
    @validator('nickname')
    def validate_nickname(cls, v):
        if not v.isalnum():
            raise ValueError('닉네임은 영숫자만 가능합니다')
        return v
```

### 8.2 권한 검증

```python
from fastapi import HTTPException, status

def check_user_ownership(user_id: int, current_user_id: int):
    \"\"\"사용자 소유권 확인\"\"\"
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=\"이 리소스에 접근할 권한이 없습니다\"
        )
```

---

## 9. 커밋 메시지 컨벤션

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 스타일 수정 (PEP 8 등)
- `refactor`: 코드 리팩토링
- `perf`: 성능 개선
- `test`: 테스트 추가/수정
- `chore`: 빌드, 의존성 등 수정

**예제**:
```
feat(learning): 실시간 수어 인식 API 추가

- WebSocket 엔드포인트 구현
- MediaPipe 통합
- 손 포즈 인식 알고리즘 적용

Closes #123
```

---

## 10. 참고 자료

- [PEP 8 - Python Code Style](https://www.python.org/dev/peps/pep-0008/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/deployment/concepts/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
