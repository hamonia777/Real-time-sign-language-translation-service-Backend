# 📡 API Documentation

## 📋 개요

- **Base URL**: `http://localhost:8000`
- **API 버전**: v1
- **인증**: JWT (Bearer Token)
- **Content-Type**: `application/json`
- **문서**: 
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

---

## 🔐 인증 (Authentication)

모든 인증이 필요한 엔드포인트는 다음과 같이 Authorization 헤더를 포함해야 합니다:

```
Authorization: Bearer {access_token}
```

---

## 1️⃣ 사용자 API (Users)

### 1.1 회원가입

**엔드포인트:**
```http
POST /api/v1/users/register
```

**요청 (Request DTO):**
```json
{
  "email": "user@example.com",
  "nickname": "닉네임",
  "phone_number": "010-1234-5678"
}
```

**응답 (Response DTO - 201 Created):**
```json
{
  "message": "회원가입 완료",
  "nickname": "닉네임"
}
```

**에러 응답 (409 Conflict):**
```json
{
  "status": "error",
  "code": "DUPLICATE_NICKNAME",
  "message": "이미 존재하는 닉네임입니다"
}
```

---

### 1.2 Kakao OAuth 로그인

**엔드포인트:**
```http
POST /api/v1/auth/login
```

**요청:**
```json
{
  "access_token": "kakao_access_token"
}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "message": "로그인 성공",
  "email": "user@example.com",
  "is_first": false
}
```

**응답 (첫 로그인 - 200 OK):**
```json
{
  "message": "첫 로그인입니다",
  "email": null,
  "is_first": true
}
```

---

### 1.3 로그아웃

**엔드포인트:**
```http
POST /api/v1/auth/logout
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "message": "로그아웃 완료"
}
```

---

### 1.4 사용자 정보 조회

**엔드포인트:**
```http
GET /api/v1/users/profile
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "user_id": 1,
  "nickname": "사용자닉네임",
  "email": "user@example.com",
  "profile_photo_url": "https://example.com/photo.jpg",
  "created_at": "2024-05-10T12:00:00"
}
```

---

### 1.5 닉네임 변경

**엔드포인트:**
```http
PATCH /api/v1/users/nickname
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**요청 (Request DTO):**
```json
{
  "nickname": "새닉네임"
}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "user_id": 1,
  "nickname": "새닉네임",
  "updated_at": "2024-05-11T15:30:00",
  "nickname_updated_at": "2024-05-11T15:30:00"
}
```

---

### 1.6 닉네임 중복 확인

**엔드포인트:**
```http
GET /api/v1/users/check-nickname?nickname={nickname}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "nickname": "테스트닉네임",
  "is_available": true
}
```

**응답 (중복 - 200 OK):**
```json
{
  "nickname": "테스트닉네임",
  "is_available": false
}
```

---

### 1.7 프로필 사진 목록

**엔드포인트:**
```http
GET /api/v1/users/profile-photos
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "photos": [
    {
      "photo_id": 1,
      "photo_url": "https://example.com/photo1.jpg",
      "name": "기본 프로필 1"
    },
    {
      "photo_id": 2,
      "photo_url": "https://example.com/photo2.jpg",
      "name": "기본 프로필 2"
    }
  ]
}
```

---

### 1.8 프로필 사진 변경

**엔드포인트:**
```http
PATCH /api/v1/users/profile-photo
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**요청 (Request DTO):**
```json
{
  "photo_id": 1
}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "user_id": 1,
  "photo_url": "https://example.com/photo1.jpg",
  "photo_type": "default",
  "updated_at": "2024-05-11T15:30:00"
}
```

---

### 1.9 사용자 랭킹

**엔드포인트:**
```http
GET /api/v1/users/ranking?page=1&limit=10
```

**응답 (Response DTO - 200 OK):**
```json
{
  "rankings": [
    {
      "rank": 1,
      "userId": 5,
      "nickname": "상위사용자",
      "profileImageUrl": "https://example.com/photo.jpg",
      "completedLearningCount": 25
    },
    {
      "rank": 2,
      "userId": 3,
      "nickname": "2위사용자",
      "profileImageUrl": "https://example.com/photo2.jpg",
      "completedLearningCount": 23
    }
  ]
}
```

---

## 2️⃣ 학습 API (Learning)

### 2.1 레슨 목록

**엔드포인트:**
```http
GET /api/v1/learning/lessons?category=basic&level=1&page=1&limit=10
```

**요청 매개변수 (Query Parameters):**
- `category`: 카테고리 (optional)
- `level`: 난이도 (optional)
- `page`: 페이지 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 10)

**응답 (Response DTO - 200 OK):**
```json
{
  "total_count": 50,
  "items": [
    {
      "lesson_id": 1,
      "title": "안녕하세요",
      "category": "기초",
      "subcategory": "인사",
      "level": 1,
      "video_url": "https://example.com/video1.mp4",
      "thumbnail_url": "https://example.com/thumb1.jpg"
    },
    {
      "lesson_id": 2,
      "title": "감사합니다",
      "category": "기초",
      "subcategory": "인사",
      "level": 1,
      "video_url": "https://example.com/video2.mp4",
      "thumbnail_url": "https://example.com/thumb2.jpg"
    }
  ]
}
```

---

### 2.2 레슨 상세 조회

**엔드포인트:**
```http
GET /api/v1/learning/lessons/{lesson_id}
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "lesson_id": 1,
  "title": "안녕하세요",
  "description": "인사 표현을 배웁니다",
  "category": "기초",
  "subcategory": "인사",
  "level": 1,
  "video_url": "https://example.com/video1.mp4",
  "thumbnail_url": "https://example.com/thumb1.jpg",
  "duration": 120,
  "pass_threshold": 80.0
}
```

---

### 2.3 학습 시작

**엔드포인트:**
```http
POST /api/v1/learning/start
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**요청 (Request DTO):**
```json
{
  "lesson_id": 1
}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "lesson_id": 1,
  "status": "in_progress",
  "attempt": 1
}
```

---

### 2.4 학습 결과 저장

**엔드포인트:**
```http
POST /api/v1/learning/save-result
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**요청 (Request DTO):**
```json
{
  "lesson_id": 1,
  "score": 85.5,
  "attempt": 1
}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "lesson_id": 1,
  "score": 85.5,
  "is_passed": true,
  "attempt": 1,
  "pass_threshold": 80.0
}
```

---

### 2.5 학습 진도 조회

**엔드포인트:**
```http
GET /api/v1/learning/progress
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "completed_count": 15,
  "in_progress_count": 3,
  "completed": [
    {
      "lesson_id": 1,
      "title": "안녕하세요",
      "category": "기초",
      "subcategory": "인사",
      "level": 1,
      "status": "completed",
      "attempt": 2,
      "progress_percent": 100,
      "updated_at": "2024-05-10T18:00:00"
    }
  ],
  "in_progress": [
    {
      "lesson_id": 5,
      "title": "숫자",
      "category": "기초",
      "subcategory": "숫자",
      "level": 1,
      "status": "in_progress",
      "attempt": 1,
      "progress_percent": 45,
      "updated_at": "2024-05-11T10:30:00"
    }
  ]
}
```

---

### 2.6 문장 학습 조회

**엔드포인트:**
```http
GET /api/v1/learning/sentences/{sentence_id}
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "sentence_id": 1,
  "sentence_title": "오늘 날씨가 좋네요",
  "words": [
    {
      "word_order": 1,
      "lesson_id": 10,
      "title": "오늘"
    },
    {
      "word_order": 2,
      "lesson_id": 11,
      "title": "날씨"
    },
    {
      "word_order": 3,
      "lesson_id": 12,
      "title": "좋다"
    }
  ]
}
```

---

## 3️⃣ 수어 인식 API (Recognition)

### 3.1 손가락 문자(Fingerspell) 인식

**엔드포인트:**
```http
POST /api/v1/recognition/fingerspell
```

**헤더:**
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**요청:**
```
file: <video_file>
```

**응답 (Response DTO - 200 OK):**
```json
{
  "recognized_text": "HELLO",
  "confidence": 0.92,
  "details": [
    {
      "character": "H",
      "confidence": 0.95
    },
    {
      "character": "E",
      "confidence": 0.90
    }
  ]
}
```

---

### 3.2 단어 수어 인식

**엔드포인트:**
```http
POST /api/v1/recognition/word
```

**헤더:**
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**요청:**
```
file: <video_file>
```

**응답 (Response DTO - 200 OK):**
```json
{
  "recognized_word": "안녕하세요",
  "lesson_id": 1,
  "confidence": 0.88,
  "is_correct": true
}
```

---

## 4️⃣ 검색 API (Search)

### 4.1 수어 검색

**엔드포인트:**
```http
GET /api/v1/search?q=안녕&type=lesson&page=1&limit=10
```

**요청 매개변수:**
- `q`: 검색어 (필수)
- `type`: 검색 타입 (lesson, sentence, word) (optional)
- `page`: 페이지 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 10)

**응답 (Response DTO - 200 OK):**
```json
{
  "total_count": 12,
  "items": [
    {
      "id": 1,
      "title": "안녕하세요",
      "type": "lesson",
      "category": "기초",
      "level": 1,
      "thumbnail_url": "https://example.com/thumb1.jpg"
    },
    {
      "id": 5,
      "title": "안녕",
      "type": "word",
      "category": "기초",
      "level": 1,
      "video_url": "https://example.com/video5.mp4"
    }
  ]
}
```

---

## 5️⃣ 설문 API (Survey)

### 5.1 설문 조회

**엔드포인트:**
```http
GET /api/v1/survey/questions
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "survey_id": 1,
  "questions": [
    {
      "question_id": 1,
      "question_text": "학습 목표는 무엇인가요?",
      "question_type": "single_choice",
      "options": [
        {"option_id": 1, "text": "일상 회화"},
        {"option_id": 2, "text": "전문 지식"},
        {"option_id": 3, "text": "모두 배우고 싶음"}
      ]
    }
  ]
}
```

---

### 5.2 설문 응답 저장

**엔드포인트:**
```http
POST /api/v1/survey/responses
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**요청 (Request DTO):**
```json
{
  "survey_id": 1,
  "answers": [
    {
      "question_id": 1,
      "selected_option_ids": [1]
    },
    {
      "question_id": 2,
      "selected_option_ids": [3, 4]
    }
  ]
}
```

**응답 (Response DTO - 201 Created):**
```json
{
  "message": "설문 완료",
  "survey_id": 1,
  "completed_at": "2024-05-11T15:30:00"
}
```

---

## 6️⃣ 학습 바구니 API (Learning Basket)

### 6.1 바구니 조회

**엔드포인트:**
```http
GET /api/v1/basket
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "total_count": 5,
  "items": [
    {
      "basket_item_id": 1,
      "lesson_id": 1,
      "title": "안녕하세요",
      "category": "기초",
      "level": 1,
      "added_at": "2024-05-11T10:00:00"
    }
  ]
}
```

---

### 6.2 바구니에 추가

**엔드포인트:**
```http
POST /api/v1/basket
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**요청 (Request DTO):**
```json
{
  "lesson_id": 1
}
```

**응답 (Response DTO - 201 Created):**
```json
{
  "message": "바구니에 추가되었습니다",
  "basket_item_id": 1,
  "lesson_id": 1
}
```

---

### 6.3 바구니에서 제거

**엔드포인트:**
```http
DELETE /api/v1/basket/{basket_item_id}
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답 (Response DTO - 204 No Content):**
```
(응답 없음)
```

---

## 7️⃣ 문의 API (Inquiry)

### 7.1 문의 목록

**엔드포인트:**
```http
GET /api/v1/inquiries?page=1&limit=10
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답 (Response DTO - 200 OK):**
```json
{
  "total_count": 8,
  "items": [
    {
      "inquiry_id": 1,
      "title": "로그인이 안 됩니다",
      "category": "기술적문제",
      "status": "pending",
      "created_at": "2024-05-10T12:00:00"
    }
  ]
}
```

---

### 7.2 문의 작성

**엔드포인트:**
```http
POST /api/v1/inquiries
```

**헤더:**
```
Authorization: Bearer {access_token}
```

**요청 (Request DTO):**
```json
{
  "title": "로그인이 안 됩니다",
  "content": "Kakao 로그인 버튼을 클릭해도 진행되지 않습니다",
  "category": "기술적문제"
}
```

**응답 (Response DTO - 201 Created):**
```json
{
  "message": "문의가 접수되었습니다",
  "inquiry_id": 1,
  "created_at": "2024-05-11T15:30:00"
}
```

---

## 🔴 에러 응답 포맷

모든 에러 응답은 다음 포맷을 따릅니다:

```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "에러 메시지",
  "details": {
    "field": "추가 정보"
  }
}
```

### HTTP 상태 코드

| 코드 | 설명 |
|------|------|
| 200 | OK - 성공 |
| 201 | Created - 리소스 생성됨 |
| 204 | No Content - 응답 없음 |
| 400 | Bad Request - 잘못된 요청 |
| 401 | Unauthorized - 인증 실패 |
| 403 | Forbidden - 권한 없음 |
| 404 | Not Found - 리소스 없음 |
| 409 | Conflict - 중복/충돌 |
| 500 | Internal Server Error - 서버 오류 |

---

## 📝 공통 응답 패턴

### 성공 응답 (페이지네이션 포함)

```json
{
  "total_count": 50,
  "items": [...],
  "next_cursor": 11
}
```

### 성공 응답 (단일 리소스)

```json
{
  "message": "요청 성공",
  "data": {...}
}
```

---

## 🔄 WebSocket API

### 실시간 수어 인식

**엔드포인트:**
```
ws://localhost:8000/ws/recognition/{user_id}?token={access_token}
```

**메시지 형식:**
```json
{
  "type": "frame",
  "data": "base64_encoded_image_data"
}
```

**응답:**
```json
{
  "type": "result",
  "recognized": "단어",
  "confidence": 0.92
}
```
