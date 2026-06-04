# 📚 프로젝트 문서 가이드


## 🛠️ Tech Stack (기술 스택)

#### 🌐 Backend Framework & Server
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=for-the-badge&logo=uvicorn&logoColor=white)](https://www.uvicorn.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)

#### 🗄️ Database & ORM
[![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![SQLAlchemy](https://img.shields.io/badge/SQLModel_(Alchemy)-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://sqlmodel.tiangolo.com/)

#### 🧠 Machine Learning & Computer Vision
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-00B0FF?style=for-the-badge&logo=google&logoColor=white)](https://mediapipe.dev/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)

#### 🔐 Security, Auth & Real-time
[![JSON Web Tokens](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)](https://jwt.io/)
[![Kakao Auth](https://img.shields.io/badge/Kakao%20OAuth-FFCD00?style=for-the-badge&logo=kakao&logoColor=black)](https://developers.kakao.com/)
[![WebSockets](https://img.shields.io/badge/WebSockets-010101?style=for-the-badge&logo=socket.io&logoColor=white)](https://websockets.readthedocs.io/)

#### 📦 Language & Environment
[![Python 3.11](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Anaconda](https://img.shields.io/badge/Conda-44A833?style=for-the-badge&logo=anaconda&logoColor=white)](https://docs.conda.io/)


## 📖 문서 목차

### 1. 📋 [프로젝트 개요](doc/PROJECT_OVERVIEW.md)
**프로젝트의 전체 개요 및 핵심 정보**

- 🎯 프로젝트 목표 및 주요 기능
- 🛠️ 기술 스택 상세 정보
- 📁 프로젝트 구조 및 파일 구성
- 🏗️ 도메인 구조 (Domain-Driven Design)
- 🔑 핵심 API 엔드포인트 목록
- 📊 주요 특징 및 이점


---

### 2. 🏗️ [서비스 아키텍처](doc/SERVICE_ARCHITECTURE.md)
**시스템 아키텍처 및 계층 설계**

- 🎨 전체 시스템 아키텍처 다이어그램
- 📦 계층별 설명 (API, Domain, ML, Data)
- 🔄 주요 데이터 흐름 (Flow)
- 🔐 보안 아키텍처 및 인증 구조
- 📈 확장 가능성 및 스케일링
- 💡 기술 스택 매핑


---

### 3. 👤 [사용자 플로우](doc/USER_FLOW.md)
**사용자 여정과 상호작용 흐름**

- 📍 전체 사용자 여정 (User Journey)
- 🔐 회원가입 및 로그인 플로우
- 📚 학습 시나리오 (손가락 문자, 단어, 문장)
- 🎯 학습 바구니 관리
- 👤 마이페이지 기능
- 🔍 검색 및 발견
- ⚠️ 에러 처리 및 예외 상황


---

### 4. 🗄️ [데이터베이스 스키마](doc/DATABASE_SCHEMA.md)
**데이터베이스 설계 및 테이블 정보**

- 📊 전체 테이블 목록 및 설명
- 🔑 상세 테이블 스키마
- 🔗 테이블 관계도 (ER Diagram)
- 📈 주요 SQL 쿼리 예제
- ⚡ 인덱싱 전략
- 📦 마이그레이션 가이드
- 💾 백업 전략


---

### 5. 📡 [API 문서](doc/API_DOCUMENTATION.md)
**REST API 상세 명세**

- 🌐 API 기본 정보 및 인증
- 👤 사용자 관리 API
- 📚 학습 관리 API
- 🎁 학습 바구니 API
- 📋 설문 조사 API
- 👁️ 프로필 관리 API
- 🔍 검색 API
- 🔌 WebSocket API (실시간 통신)
- 🐛 에러 코드 및 대응
- 📝 cURL/JavaScript 사용 예제


### 6. 📖 [개발 가이드 및 컨벤션](doc/DEVELOPMENT_GUIDE.md)
**코딩 스타일, 패턴, 모범 사례**

- 📝 코드 구조 및 명명 컨벤션
- 🎯 Python 코드 스타일 (PEP 8)
- 📚 Docstring 작성 방법
- 🏛️ 도메인별 개발 가이드
- 💾 데이터베이스 작업
- ⚠️ 에러 처리 및 로깅
- 🧪 테스트 작성
- ⚡ 성능 최적화
- 🔐 보안 모범 사례
- 💬 Git 커밋 컨벤션

---

## 📚 문서별 상세 내용

### PROJECT_OVERVIEW.md
```
총 페이지: ~30장
- 프로젝트 소개 (1-2장)
- 기술 스택 상세 (5-10장)
- 프로젝트 구조 (5-8장)
- 도메인 구조 (5-8장)
- 핵심 API (3-5장)
- 실행 환경 (5-7장)
```

### SERVICE_ARCHITECTURE.md
```
총 페이지: ~20장
- 아키텍처 다이어그램 (5-7장)
- 계층별 설명 (8-10장)
- 데이터 흐름 (3-5장)
- 보안 구조 (3-5장)
```

### USER_FLOW.md
```
총 페이지: ~25장
- 사용자 여정 (3-5장)
- 상세 플로우 (15-20장)
- 상태 관리 (2-3장)
- 에러 처리 (2-3장)
```

### DATABASE_SCHEMA.md
```
총 페이지: ~30장
- 테이블 목록 (2-3장)
- 상세 스키마 (20-25장)
- 관계도 (2-3장)
- 쿼리 예제 (3-5장)
```

### API_DOCUMENTATION.md
```
총 페이지: ~40장
- 기본 정보 (2-3장)
- 사용자 API (3-5장)
- 학습 API (3-5장)
- 기타 API (10-15장)
- 예제 (5-10장)
```


### DEVELOPMENT_GUIDE.md
```
총 페이지: ~40장
- 코드 스타일 (5-8장)
- 도메인 개발 (10-15장)
- DB 작업 (5-8장)
- 에러 처리 (3-5장)
- 테스트 (5-8장)
- 최적화 (3-5장)
- 보안 (2-3장)
```

---

## 🔍 문서 검색 팁

### 특정 기능 찾기
- \"회원가입 플로우\" → USER_FLOW.md, API_DOCUMENTATION.md
- \"학습 데이터 저장\" → DATABASE_SCHEMA.md, API_DOCUMENTATION.md
- \"실시간 수어 인식\" → SERVICE_ARCHITECTURE.md, USER_FLOW.md
- \"WebSocket\" → API_DOCUMENTATION.md, USER_FLOW.md

### 특정 기술 찾기
- \"MySQL\" → DATABASE_SCHEMA.md, SETUP_AND_DEPLOYMENT.md
- \"JWT 인증\" → SERVICE_ARCHITECTURE.md, API_DOCUMENTATION.md
- \"성능 최적화\" → DEVELOPMENT_GUIDE.md, SERVICE_ARCHITECTURE.md


---

## 📞 추가 지원

### 문서 관련 문의
- 문서에 오류가 있거나 개선할 점이 있으면 Pull Request 제출
- 특정 주제에 대한 추가 문서가 필요하면 Issue 생성

---

## 📈 문서 업데이트 이력

| 날짜 | 작성자 | 내용 | 비고 |
|------|--------|------|------|
| 2024-05-10 | 개발팀 | 초기 문서 작성 | v1.0 |
| | | | |

---

## ✅ 문서 체크리스트

### 신규 기능 추가 시
- [ ] API 명세 추가 (API_DOCUMENTATION.md)
- [ ] 데이터베이스 스키마 업데이트 (DATABASE_SCHEMA.md)
- [ ] 개발 가이드 업데이트 (DEVELOPMENT_GUIDE.md)
- [ ] 사용자 플로우 업데이트 (USER_FLOW.md)
- [ ] 아키텍처 다이어그램 업데이트 (SERVICE_ARCHITECTURE.md)

### 배포 전
- [ ] API 문서 최신화 확인
- [ ] 데이터베이스 마이그레이션 문서 작성
- [ ] 배포 가이드 검토
- [ ] 주요 변경사항 문서화

### 분기별
- [ ] 전체 문서 검토 및 개선
- [ ] 버전 업데이트 확인
- [ ] 오래된 정보 제거
- [ ] 새로운 기능 추가 문서화

---

## 📚 관련 리소스

### 공식 문서
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [SQLModel 문서](https://sqlmodel.tiangolo.com/)
- [MediaPipe 문서](https://mediapipe.dev/)
- [PyTorch 문서](https://pytorch.org/)

### 개발 자료
- GitHub 저장소: [repository_url]
- 이슈 트래킹: [issues_url]
- 프로젝트 보드: [projects_url]

---

**마지막 업데이트**: 2024년 5월 10일
**버전**: 1.0
**상태**: 작성 중 🔄
