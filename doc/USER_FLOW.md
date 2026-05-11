# 👤 사용자 플로우 (User Flow)

## 1. 전체 사용자 여정 (User Journey)

```mermaid
graph TD
    A["👤 미가입 사용자"] --> B["📱 1. 앱 접속"]
    B --> C{회원가입 필요?}
    C -->|Yes| D["🔐 2. Kakao 소셜 로그인"]
    D --> E["📝 3. 개인정보 입력<br/>전화번호, 닉네임"]
    E --> F["📋 4. 설문조사<br/>학습자 선호도"]
    F --> G["✅ 가입 완료"]
    G --> H["🏠 5. 홈 대시보드"]
    C -->|No| H
    H --> I{"6. 학습 시작"}
    I -->|손가락 문자| J["🖐️ Fingerspell 학습"]
    I -->|단어| K["🔤 Word 학습"]
    I -->|문장| L["💬 Sentence 학습"]
    J --> M["🧺 7. 학습 바구니<br/>즐겨찾기 관리"]
    K --> M
    L --> M
    M --> N["👤 8. 마이페이지<br/>프로필, 통계"]
    N --> O{"계속 학습?"}
    O -->|Yes| H
    O -->|No| P["🚪 9. 로그아웃"]
```

## 2. 상세 플로우별 시나리오

### 시나리오 1: 회원가입 및 초기 설정

```mermaid
graph TD
    A["👤 미가입 사용자가 앱에 접속"] --> B["📱 로그인 페이지"]
    B --> C["🔐 Kakao 로그인 버튼 클릭"]
    C --> D["🔑 Kakao OAuth 인증 페이지<br/>Kakao ID/PW 입력"]
    D --> E["🔌 POST /api/v1/auth/login<br/>authorization_code"]
    E --> F["🔍 Kakao ID 기반 사용자 조회<br/>첫 로그인이면 자동 생성"]
    F --> G["🎫 JWT Token 생성 & 반환<br/>access_token, user_id"]
    G --> H["📝 개인정보 입력 페이지"]
    H --> I["📋 - 전화번호<br/>- 닉네임<br/>- 프로필 사진"]
    I --> J["📤 PUT /api/v1/users/user_id"]
    J --> K["❓ 설문조사 페이지"]
    K --> L["📊 - 학습 목표 선택<br/>- 난이도 선호도<br/>- 학습 시간 설정"]
    L --> M["📤 POST /api/v1/users/user_id/survey"]
    M --> N["✅ 설정 완료<br/>홈 대시보드로 이동"]


### 시나리오 2: 손가락 문자(Fingerspell) 학습

```mermaid
graph TD
    A["🏠 홈 대시보드"] --> B["🖐️ 손가락 문자 학습 선택"]
    B --> C["📋 GET /api/v1/learning/lessons<br/>필터: type=fingerspell"]
    C --> D["📝 Fingerspell 레슨 목록 페이지"]
    D --> E["🎯 특정 레슨 선택<br/>예: A~Z 기초"]
    E --> F["🎥 실시간 인식 페이지"]
    F --> G["📹 - 웹캠 활성화<br/>- MediaPipe 손 추적"]
    G --> H["🔌 WebSocket Connection"]
    H --> I["👐 사용자가 손 모양으로 입력<br/>예: A 손가락 문자 시연"]
    I --> J["⚙️ recon_fingerspell.py"]
    J --> K["🔍 - 프레임 캡처<br/>- MediaPipe 손 포즈 추출<br/>- PyTorch 모델 추론"]
    K --> L["📊 결과 반환<br/>predicted_char, confidence"]
    L --> M["🌐 WebSocket로 실시간 전송"]
    M --> N["📱 Frontend에서 결과 표시"]
    N --> O["✅ - 인식된 문자<br/>- 신뢰도 바<br/>- 정답/오답"]
    O --> P{모든 문자 완료?}
    P -->|No| Q["▶️ 다음 문자"]
    Q --> I
    P -->|Yes| R["💾 POST /api/v1/learning/progress<br/>학습 진도 저장"]
    R --> S["📝 StudyLog 자동 생성<br/>학습 시간, 정확도"]
    S --> T["🎉 완료 축하!"]
    T --> U["📊 학습 통계 페이지"]
    U --> V["🏆 - 정확도 평가<br/>- 소요 시간<br/>- 다음 학습 추천"]
```

### 시나리오 3: 단어(Word) 학습

```mermaid
graph TD
    A["🏠 홈 대시보드"] --> B["🔤 단어 학습 선택"]
    B --> C["📋 GET /api/v1/learning/lessons<br/>필터: type=word"]
    C --> D["🎯 Word 레슨 목록 페이지"]
    D --> E["예시 레슨:<br/>일상용어, 음식, 동물, 감정"]
    E --> F["📌 레슨 선택<br/>예: 일상용어"]
    F --> G["🎓 GET /api/v1/learning<br/>lesson/lesson_id"]
    G --> H["🔤 단어 목록 페이지"]
    H --> I["🎬 각 단어의 영상/이미지<br/>클릭하여 상세 페이지로"]
    I --> J["📝 단어 상세 페이지"]
    J --> K["📺 - 수어 시범 영상 재생<br/>- 단어 뜻 설명<br/>- 예문"]
    K --> L["🎬 실시간 인식 시작"]
    L --> M["👐 사용자가 수어로 표현<br/>웹캠으로 시연"]
    M --> N["⚙️ recon_word.py"]
    N --> O["🔍 - 비디오 프레임 수집<br/>- MediaPipe 손 추적<br/>- PyTorch 단어 모델 추론<br/>- 신뢰도 계산"]
    O --> P["📊 결과 반환<br/>word, confidence, accuracy"]
    P --> Q{정확도 확인}
    Q -->|>80% 정답| R["✅ 정답"]
    Q -->|<80% 오답| S["❌ 재시도"]
    S --> T["🎬 다시 시범 영상 보기"]
    T --> U{재시도?}
    U -->|Yes| M
    U -->|No| V["⏭️ SKIP"]
    R --> W["▶️ 다음 단어"]
    V --> W
    W --> X{모든 단어 완료?}
    X -->|No| H
    X -->|Yes| Y["💾 학습 진도 저장"]
    Y --> Z["🏆 동기 획득"]
    Z --> AA["📝 학습 기록 생성"]
    AA --> AB["🎉 완료"]
```

### 시나리오 4: 문장(Sentence) 학습

```mermaid
graph TD
    A["🏠 홈 대시보드"] --> B["💬 문장 학습 선택"]
    B --> C["📋 GET /api/v1/learning/lessons<br/>필터: type=sentence"]
    C --> D["🎯 Sentence 레슨 목록"]
    D --> E["예시 레슨:<br/>인사말, 자기소개, 일상 대화"]
    E --> F["📌 문장 선택"]
    F --> G["📝 문장 상세 페이지"]
    G --> H["🎬 - 문장 뜻<br/>- 수어 시범 영상 전체<br/>- 각 단어별 분해 영상"]
    H --> I["▶️ 시범 영상 재생"]
    I --> J["👐 사용자가 전체 문장을<br/>수어로 표현<br/>웹캠으로 촬영"]
    J --> K["⚙️ recon_video.py"]
    K --> L["🔍 - 전체 영상 프레임 수집<br/>- 각 구간별 단어 인식<br/>- 전체 문장 순서 검증"]
    L --> M["📊 정확도 계산<br/>단어별 정확도 평균"]
    M --> N["📈 결과<br/>accuracy, word_scores"]
    N --> O{정확도 확인}
    O -->|> 70% 통과| P["✅ 통과"]
    O -->|≤ 70% 재시도| Q["❌ 재시도"]
    Q --> R["💡 피드백 제공<br/>어려운 부분 표시"]
    R --> S{다시 시도?}
    S -->|Yes| J
    S -->|No| T["⏭️ SKIP"]
    P --> U["▶️ 다음 문장 또는 완료"]
    T --> U
```

### 시나리오 5: 학습 바구니 (Learning Basket)

```mermaid
graph TD
    A["📚 각 학습 페이지에서"] --> B["⭐ 즐겨찾기 버튼 클릭"]
    B --> C["📤 POST /api/v1/learning/basket<br/>lesson_id, word_id"]
    C --> D["💾 LearningBasket 데이터 생성<br/>저장됨"]
    D --> E["✅ 즐겨찾기 완료"]
    E --> F{"마이페이지 또는<br/>홈에서 학습 바구니<br/>탭 클릭?"}
    F -->|Yes| G["📤 GET /api/v1/learning/basket<br/>저장된 즐겨찾기 목록"]
    G --> H["🧺 학습 바구니 페이지"]
    H --> I["📋 - 저장된 모든 항목 표시<br/>- 재학습 버튼<br/>- 삭제 버튼"]
    I --> J{항목 선택}
    J -->|재학습| K["▶️ 선택한 항목 학습 시작"]
    J -->|삭제| L["🗑️ 항목 제거"]
```

### 시나리오 6: 마이페이지 (My Page)

```mermaid
graph TD
    A["📱 메인 메뉴에서"] --> B["👤 마이페이지 클릭"]
    B --> C["📤 GET /api/v1/users/me<br/>마이페이지 정보 로드"]
    C --> D["👤 마이페이지"]
    D --> E["👤 프로필 섹션"]
    D --> F["📊 학습 통계 섹션"]
    D --> G["⚙️ 설정 섹션"]
    D --> H["🔗 기타"]
    E --> E1["📸 프로필 사진<br/>닉네임<br/>이메일<br/>전화번호<br/>[프로필 수정]<br/>[사진 변경]<br/>[비밀번호 변경]"]
    F --> F1["⏱️ 총 학습 시간<br/>📚 완료한 레슨 수<br/>📈 평균 정확도<br/>📅 최근 학습 날짜<br/>🔥 연속 학습 일수"]
    G --> G1["🔔 알림 설정<br/>💬 카톡 알림 활성화<br/>📊 난이도 설정"]
    H --> H1["❌ 계정 삭제<br/>🚪 로그아웃"]
    E1 --> I{선택}
    F1 --> I
    G1 --> I
    H1 --> I
    I -->|프로필 수정| J["✏️ PUT /api/v1/users"]
    I -->|사진 업로드| K["📸 POST /upload"]
    I -->|알림 설정| L["🔔 설정 적용"]
    I -->|로그아웃| M["🚪 로그아웃"]
    J --> N["✅ 업데이트 완료"]
    K --> N
    L --> N
    M --> O["📱 로그인 페이지"]
```

## 3. 검색 및 발견 (Search & Discovery)

```mermaid
graph TD
    A["🔍 검색 창에 단어 입력<br/>예: 안녕하세요"] --> B["📤 GET /api/v1/search?q=keyword<br/>검색 실행"]
    B --> C["🎯 검색 결과 반환"]
    C --> D["📋 - 매칭 단어 목록<br/>- 관련 레슨<br/>- 검색 히스토리 자동 저장"]
    D --> E["🌐 검색 결과 페이지"]
    E --> F["👆 검색 결과 표시<br/>클릭하여 상세 페이지로"]
    F --> G["📤 GET /api/v1/search/history<br/>이전 검색어 조회"]
```

---

## 4. 상태 관리 (State Management)

### 세션 상태
```mermaid
graph LR
    A["🔓 로그인 전"] --> B["📱 로그인 페이지 표시<br/>보호된 리소스 접근 불가"]
    C["🔐 로그인 후"] --> D["🎫 JWT Token 저장<br/>LocalStorage"]
    D --> E["🌐 모든 요청에 JWT 포함<br/>Authorization: Bearer token"]
    F["⏰ 토큰 만료"] --> G{갱신 가능?}
    G -->|Yes| H["🔄 자동 갱신 시도"]
    H --> E
    G -->|No| I["🔐 재로그인 요청"]
```

### 학습 진도 상태
```mermaid
graph TD
    A["📚 학습 진도 상태"] --> B["🔲 시작 안 함<br/>progress = null"]
    A --> C["⏳ 진행 중<br/>progress = user_id, lesson_id<br/>current_word_index"]
    A --> D["✅ 완료<br/>progress = completed_at<br/>accuracy"]
    A --> E["⏸️ 미완료 중단<br/>progress = last_position<br/>timestamp"]
```

---

## 5. 에러 처리 (Error Handling)

```mermaid
graph TD
    A["👤 사용자 액션"] --> B["🌐 API 요청 실패"]
    B --> C["📊 에러 코드 분류"]
    C --> D["❌ 400: 잘못된 요청"]
    C --> E["🔐 401: 인증 실패<br/>토큰 만료"]
    C --> F["🚫 403: 권한 없음"]
    C --> G["🔍 404: 리소스 없음"]
    C --> H["⚡ 409: 충돌<br/>중복 데이터"]
    C --> I["⚠️ 500: 서버 오류"]
    D --> J["💬 에러 메시지 표시<br/>알림창"]
    E --> J
    F --> J
    G --> J
    H --> J
    I --> J
    J --> K["🔘 - 사용자 친화적 메시지<br/>- 재시도 버튼<br/>- 홈으로 돌아가기"]
```

---

## 6. 통지 및 피드백

### 학습 완료 통지
```mermaid
graph TD
    A["✅ 학습 완료"] --> B["🎉 축하 메시지 표시"]
    B --> C["📊 정확도 %"]
    B --> D["⏱️ 소요 시간"]
    B --> E["🎯 다음 추천 학습"]
    B --> F["📤 공유하기 옵션"]
    C --> G["📝 StudyLog 생성"]
    D --> G
    E --> G
    F --> G
    G --> H{카톡 알림?}
    H -->|Yes| I["💬 Kakao 카톡 알림 전송"]
```

### 목표 달성 알림
```mermaid
graph TD
    A["🎯 특정 조건 충족"] --> B["조건 체크"]
    B --> C["⏱️ 일일 학습 시간 도달"]
    B --> D["🔥 연속 학습 일수 달성"]
    B --> E["🏆 모든 레슨 완료"]
    B --> F["📈 특정 정확도 달성"]
    C --> G["🏅 배지 또는 동기 부여 메시지<br/>표시"]
    D --> G
    E --> G
    F --> G
    G --> H{알림 전송?}
    H -->|Yes| I["💬 카톡 또는<br/>이메일 알림 전송"]
```

---

## 7. 로그아웃 및 세션 종료

```mermaid
graph TD
    A["👤 사용자가<br/>[로그아웃] 클릭"] --> B["🗑️ JWT Token 삭제<br/>LocalStorage에서 제거"]
    B --> C["🗑️ Redis 세션 정보 삭제<br/>optional"]
    C --> D["📱 로그인 페이지로 리다이렉트"]
    D --> E["✨ - 모든 입력 필드 초기화"]
```

---

## 8. 오프라인 처리 (Offline Handling)

```mermaid
graph TD
    A["🌐 네트워크 끊김 감지"] --> B["💾 현재 상태 로컬 저장"]
    B --> C["🔹 - 진행 중인 학습 위치<br/>- 입력된 데이터"]
    A --> D["🔄 네트워크 복구 감지"]
    D --> E["🔄 로컬 데이터 서버와 동기화"]
    E --> F["📤 - 학습 진도 업로드<br/>- StudyLog 생성"]
    F --> G["✅ 정상 작동 재개"]
```
