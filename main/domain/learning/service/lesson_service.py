from pathlib import Path
from typing import List, Optional

from fastapi import Depends, HTTPException

from main.domain.learning.entity.lesson import Lesson
from main.domain.learning.repository.lesson_repository import (
    LessonRepository,
    get_lesson_repository,
)
# 가령: 260422: 수정 내용 - 문장 시드(seed_sentences) 에서 lesson_word_mappings 를 사용하기 위해 repository import
from main.domain.LessonWordMapping.entity.lesson_word_mapping import LessonWordMapping
from main.domain.LessonWordMapping.repository.lesson_word_mapping_repository import (
    LessonWordMappingRepository,
    get_lesson_word_mapping_repository,
)


KOREAN_CONSONANTS = [
    "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ",
    "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
    # 가령: 26/04/19 수정내용: model_word.pt 에 포함된 쌍자음 5개 추가 (실제로는 지문자)
    "ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ",
]

KOREAN_VOWELS = [
    "ㅏ", "ㅑ", "ㅓ", "ㅕ", "ㅗ", "ㅛ", "ㅜ",
    "ㅠ", "ㅡ", "ㅣ", "ㅐ", "ㅒ", "ㅔ", "ㅖ",
    # 가령: 26/04/19 수정내용: model_word.pt 에 포함된 이중모음 4개 추가 (실제로는 지문자)
    "ㅘ", "ㅙ", "ㅝ", "ㅞ",
    # 가령: 26/04/19 수정내용: model_fingerspell.pt 가 지원하지만 DB 에 없던 모음 3개 추가
    "ㅚ", "ㅟ", "ㅢ",
]

# 가령: 26/04/19 수정내용: 단어를 카테고리별로 분류한 맵으로 교체. 카테고리는 subcategory 컬럼에 저장.
WORDS_BY_CATEGORY = {
    "greeting": [  # 인사·기본표현
        "안녕하세요", "저는", "입니다", "감사합니다", "반갑습니다",
        "질문", "답변", "다시", "이해", "맞다", "맞다,사실", "말씀",
        "틀리다", "모르다", "괜찮다", "아니다", "있다", "없다", "알다",
        "왜냐하면", "같다", "요약", "확인", "허용", "승인", "마지막",
    ],
    "family": [  # 사람·가족·관계
        "가족", "친구", "사람", "사랑", "아버지/아빠", "어머니/엄마",
        "언니/누나", "형/오빠", "남동생", "여동생", "할머니", "할아버지",
        "남편", "아내", "아이", "아들", "딸", "나라", "농인", "장애인",
        # 가령: 260422: 수정 내용 - 문장 학습 시드(sentences.txt) 단어 추가
        "상대",
    ],
    "emotion": [  # 감정·기분
        "기쁘다", "슬프다", "화나다", "무섭다", "당황", "행복", "우울",
        "긴장", "다정", "다행", "부끄럽다", "부럽다", "서운하다", "신나다",
        "지루하다", "피곤", "힘들다", "이별", "극복", "반성", "좋다", "싫다",
        "만족", "반려(거절)", "예쁘다/멋지다", "귀엽다", "뜨겁다", "기분",
        "모습", "후회", "차별", "편하다",
        # 가령: 260422: 수정 내용 - 문장 학습 시드(sentences.txt) 단어 추가
        "신뢰",
    ],
    "body": [  # 신체·건강
        "눈(신체)", "다리(신체)", "발(신체)", "손", "입", "귀", "머리",
        "무릎", "코", "어깨", "얼굴", "감기", "건강", "알레르기", "무증상",
        "수술", "약", "약국", "병원", "기침", "아프다", "마음", "쌀밥",
    ],
    "job": [  # 직업
        "가수", "간호사", "교수", "선생님", "변호사", "경찰", "군인", "기자",
        "농부", "과학자", "근로자", "근무하다", "의사", "미용사", "소방원",
        "판사", "조종사", "요리사", "운동선수", "화가", "사장", "학생",
        # 가령: 260422: 수정 내용 - 문장 학습 시드(sentences.txt) 단어 추가. "프로그래머" 는 동의어로 매핑 처리(시드 단계)
        "개발자",
    ],
    "nature": [  # 자연·날씨·계절
        "산", "바다", "강", "숲", "바위", "하늘", "호수", "섬", "구름",
        "비", "바람", "봄", "여름", "가을", "겨울", "계절", "날씨", "꽃",
        "나무", "무지개", "별", "동굴", "번개", "안개", "돌",
    ],
    "thing": [  # 사물·음식·기기
        "책", "컴퓨터", "노트북", "신발", "옷", "우유", "커피", "빵", "사과",
        "우산", "핸드폰", "휴대폰", "카메라", "돈", "의자", "종이", "책상",
        "텔레비전", "선물", "색깔", "표정", "표", "그림", "사진", "영화",
        "노래", "영상", "소리", "냉장고", "수어", "음식", "사전", "상", "상식",
        "안경", "시험", "약속", "이름", "전화", "전화번호", "주사", "영수증",
        "비행기", "버스", "기차", "가방", "창문", "편의점", "승용차", "과일",
        "생일", "물",
        # 가령: 260422: 수정 내용 - 문장 학습 시드(sentences.txt) 단어 추가
        "웹사이트",
    ],
    "action": [  # 동작·상태
        "가다", "오다", "가르치다", "배우다", "가져가다", "기다리다", "끝나다",
        "돕다", "듣다", "마시다", "먹다", "받다", "보다", "빌리다", "사다",
        "쉽다", "어렵다", "씻다", "일어나다", "잊다", "자다", "주다", "찾다",
        "팔다", "걷다", "고르다", "고치다", "그리다", "나가다", "넣다", "놀다",
        "닫다", "던지다", "들어가다", "만들다", "믿다", "부르다", "비싸다",
        "빠르다", "서다", "싸우다", "시작하다", "싸다(cheap)", "쓰다(글)", "앉다",
        "약하다", "열다", "읽다", "잡다", "적다(write)", "졸업하다", "타다",
        "필요하다", "느리다", "무겁다", "작다", "짧다", "조용하다", "천천히",
        "크다", "항상", "혼자", "웃다", "울다", "만나다", "말하다", "맡다",
        "멈추다", "바꾸다, 변경", "부탁", "가끔", "예전", "그냥", "다르다",
        "새롭다", "변화", "이루다", "전달", "준비,챙기다", "추가", "실시간",
        "설명", "소개", "발표", "연결", "연락", "도움", "도입", "일하다",
        "잃다", "입다", "뛰어나다", "나누다", "겪다", "장점", "하다", "내용",
        "문제", "방법", "기능", "공유", "계약", "광고", "뒤쪽", "많다", "적다",
        "어떻게",
        # 가령: 260422: 수정 내용 - 문장 학습 시드(sentences.txt) 단어 추가
        "꿈꾸다", "묻다", "성장", "노력", "서로", "해결", "같이", "인정", "원하다", "보여주다",
    ],
    "place": [  # 장소·시간
        "집", "학교", "화장실", "회사", "도서관", "교실", "공원", "마을",
        "동물원", "식당", "은행", "법원", "역(지하철)", "고등학교", "중학교",
        "초등학교", "대학교", "앞", "옆", "여기", "세계", "국가", "지역",
        "장소", "문화", "휴일", "치과", "오늘", "오전", "오후", "저녁",
        "아침", "지금", "언제", "어제", "내일", "월(달)", "년(해)", "시간",
        "누구", "어디", "출장", "전공",
        # 가령: 260422: 수정 내용 - 문장 학습 시드(sentences.txt) 단어 추가
        "매일",
    ],
    "study": [  # 학업·업무·숫자·기타
        "공부,학업", "주제", "이유", "정보", "데이터", "보안", "복구", "대회",
        "직업", "월급", "변호사", "경찰", "기자", "결산", "결제", "검토",
        "토론", "추진", "팀", "품질", "세금", "거래", "위자료", "퇴직금",
        "대출금", "등록비", "연차", "취소", "순서", "협의", "하나(1)", "둘(2)",
        "셋(3)", "넷(4)", "다섯(5)", "여섯(6)", "일곱(7)", "여덟(8)", "아홉(9)",
        "열(10)", "숫자", "통계", "감속", "쉬다", "휴가", "복지", "부서",
        "화면", "나중에", "송금", "번개",
        # 가령: 260422: 수정 내용 - 문장 학습 시드(sentences.txt) 단어 추가
        "경험", "결과", "의견", "능력",
    ],
}

# 중복 시 먼저 등장한 카테고리 우선 — 단어 한 개당 하나의 subcategory 로 매핑되도록 평탄화
def _build_word_map():
    m = {}
    for cat, words in WORDS_BY_CATEGORY.items():
        for w in words:
            w = w.strip()
            if w and w not in m:
                m[w] = cat
    return m

WORD_CATEGORY_MAP = _build_word_map()


# 가령: 260422: 수정 내용 - 문장(sentences.txt) 단어 → 기존 word lesson title 동의어 매핑 (시드 시점에 정규화)
SENTENCE_WORD_ALIASES = {
    "저": "저는",
    "나": "저는",
    "감사": "감사합니다",
    "프로그래머": "개발자",
}


# 가령: 260422: 수정 내용 - sentences.txt 절대 경로 (lesson_service.py 위치 기준)
SENTENCES_TXT_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "learning_model" / "sentences.txt"
)


class LessonService:
    # 가령: 260422: 수정 내용 - 문장 시드를 위해 LessonWordMappingRepository 추가 주입
    def __init__(
        self,
        repo: LessonRepository = Depends(get_lesson_repository),
        mapping_repo: LessonWordMappingRepository = Depends(get_lesson_word_mapping_repository),
    ):
        self.repo = repo
        self.mapping_repo = mapping_repo

    def get_lesson(self, lesson_id: int) -> Lesson:
        lesson = self.repo.find_by_id(lesson_id)
        if lesson is None:
            raise HTTPException(status_code=404, detail="lesson not found")
        return lesson

    def list_by_category(self, category: str) -> List[Lesson]:
        return self.repo.find_by_category(category)

    def seed_fingerspell(self) -> dict:
        inserted = 0
        skipped = 0

        for title in KOREAN_CONSONANTS:
            if self.repo.find_by_title_and_category(title, "fingerspell"):
                skipped += 1
                continue
            self.repo.save(
                Lesson(
                    title=title,
                    category="fingerspell",
                    subcategory="consonant",
                    level=1,
                    video_url="",
                    thumbnail_url=None,
                )
            )
            inserted += 1

        for title in KOREAN_VOWELS:
            if self.repo.find_by_title_and_category(title, "fingerspell"):
                skipped += 1
                continue
            self.repo.save(
                Lesson(
                    title=title,
                    category="fingerspell",
                    subcategory="vowel",
                    level=1,
                    video_url="",
                    thumbnail_url=None,
                )
            )
            inserted += 1

        total = len(KOREAN_CONSONANTS) + len(KOREAN_VOWELS)
        return {"inserted": inserted, "skipped": skipped, "total": total}

    # 가령: 26/04/19 수정내용: 단어 시드 + 기존 row 의 subcategory 를 WORD_CATEGORY_MAP 로 UPDATE 하도록 변경
    def seed_words(self) -> dict:
        inserted = 0
        updated = 0
        skipped = 0

        for title, subcat in WORD_CATEGORY_MAP.items():
            existing = self.repo.find_by_title_and_category(title, "word")
            if existing is not None:
                if existing.subcategory != subcat:
                    existing.subcategory = subcat
                    self.repo.save(existing)
                    updated += 1
                else:
                    skipped += 1
                continue
            self.repo.save(
                Lesson(
                    title=title,
                    category="word",
                    subcategory=subcat,
                    level=1,
                    video_url="",
                    thumbnail_url=None,
                )
            )
            inserted += 1

        return {
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "total": len(WORD_CATEGORY_MAP),
        }

    # 가령: 260422: 수정 내용 - sentences.txt 를 읽어 문장 lesson(category=sentence) + lesson_word_mappings 시드
    def seed_sentences(self) -> dict:
        if not SENTENCES_TXT_PATH.exists():
            raise HTTPException(
                status_code=404,
                detail=f"sentences.txt not found at {SENTENCES_TXT_PATH}",
            )

        inserted_sentences = 0
        skipped_sentences = 0
        inserted_mappings = 0
        deleted_mappings = 0
        missing_words: List[str] = []  # "{문장}: {단어}" 포맷, lesson 매칭 실패한 단어 추적
        total_lines = 0

        for raw_line in SENTENCES_TXT_PATH.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue

            words_part, sentence_part = line.split("=", 1)
            sign_words = [w.strip() for w in words_part.split(",") if w.strip()]
            sentence_title = sentence_part.strip()
            if not sentence_title or not sign_words:
                continue
            total_lines += 1

            # 문장 lesson upsert (있으면 재사용 + 기존 매핑 정리)
            sentence_lesson = self.repo.find_by_title_and_category(sentence_title, "sentence")
            if sentence_lesson is None:
                sentence_lesson = self.repo.save(
                    Lesson(
                        title=sentence_title,
                        category="sentence",
                        subcategory="business",
                        level=1,
                        video_url="",
                        thumbnail_url=None,
                    )
                )
                inserted_sentences += 1
            else:
                skipped_sentences += 1
                deleted_mappings += self.mapping_repo.delete_by_sentence_id(sentence_lesson.id)

            # 수어 어순대로 매핑 생성 (word_order = 1..N)
            for order, sign_word in enumerate(sign_words, start=1):
                canonical = SENTENCE_WORD_ALIASES.get(sign_word, sign_word)
                word_lesson = self.repo.find_by_title_and_category(canonical, "word")
                if word_lesson is None:
                    missing_words.append(f"{sentence_title}: {sign_word}(→{canonical})")
                    continue
                self.mapping_repo.save(
                    LessonWordMapping(
                        sentence_lesson_id=sentence_lesson.id,
                        word_lesson_id=word_lesson.id,
                        word_order=order,
                    )
                )
                inserted_mappings += 1

        return {
            "inserted_sentences": inserted_sentences,
            "skipped_sentences": skipped_sentences,
            "inserted_mappings": inserted_mappings,
            "deleted_mappings": deleted_mappings,
            "missing_words": missing_words,
            "total_lines": total_lines,
        }

    # 가령: 260422: 수정 내용 - 문장 학습 페이지용. 문장 lesson + 수어어순 단어 lesson 목록 한 번에 조회
    def get_sentence_with_words(self, sentence_id: int) -> dict:
        sentence = self.repo.find_by_id(sentence_id)
        if sentence is None or sentence.category != "sentence":
            raise HTTPException(status_code=404, detail="sentence lesson not found")

        mappings = self.mapping_repo.find_by_sentence_id(sentence_id)
        words = []
        for m in mappings:
            word_lesson = self.repo.find_by_id(m.word_lesson_id)
            if word_lesson is None:
                continue
            words.append({
                "word_order": m.word_order,
                "lesson_id": word_lesson.id,
                "title": word_lesson.title,
            })
        return {
            "sentence_id": sentence.id,
            "sentence_title": sentence.title,
            "words": words,
        }
