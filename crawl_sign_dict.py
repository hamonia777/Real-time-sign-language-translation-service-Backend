"""
한국수어사전 영상 URL 크롤링 스크립트
사용법:
  테스트: python crawl_sign_dict.py --video 먹다
  전체:   python crawl_sign_dict.py
"""

import json, time, sys, re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

BASE_URL = "https://sldict.korean.go.kr"
DELAY    = 2.0
OUT_FILE = "sign_words_video.json"

# 전체 단어 목록 (lessons 테이블 기준 436개)
DB_WORDS = [
    # fingerspell - consonant
    "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ",
    "ㄲ","ㄸ","ㅃ","ㅆ","ㅉ",
    # fingerspell - vowel
    "ㅏ","ㅑ","ㅓ","ㅕ","ㅗ","ㅛ","ㅜ","ㅠ","ㅡ","ㅣ","ㅐ","ㅒ","ㅔ","ㅖ",
    "ㅘ","ㅙ","ㅝ","ㅞ",
    # word - greeting
    "안녕하세요","저는","입니다","감사합니다","질문","다시","이해","맞다",
    "말씀","틀리다","반갑습니다","모르다","괜찮다","답변","마지막","맞다,사실",
    "아니다","왜냐하면","요약","허용","확인","알다","없다","있다","같다","승인",
    # word - family
    "남동생","어머니","언니","여동생","할머니","할아버지","형","친구",
    "농인","아버지","가족","남편","딸","사람","아들","아이","아내","사랑",
    "장애인","나라","숲",
    # word - emotion
    "좋다","싫다","귀엽다","기쁘다","뜨겁다","슬프다","화나다","힘들다",
    "긴장","다행","다정","당황","만족","무섭다","부끄럽다","부럽다",
    "서운하다","신나다","우울","이별","지루하다","차별","극복","편하다",
    "피곤","행복","후회","기분","모습","반성","반려",
    # word - body
    "병원","아프다","약","약국","알레르기","감기","건강","기침","얼굴",
    "귀","눈","다리","머리","무릎","발","손","어깨","입","코","수술","마음",
    "무증상","쌀밥",
    # word - job
    "선생님","교수","근로자","의사","학생","가수","간호사","경찰","과학자",
    "군인","기자","농부","미용사","변호사","사장","소방원","요리사","운동선수",
    "조종사","판사","화가",
    # word - nature
    "날씨","바다","산","가을","겨울","계절","봄","여름","꽃","강","구름",
    "나무","무지개","바람","바위","번개","별","비","섬","안개","하늘","호수",
    "돌","동굴","숲",
    # word - thing
    "가방","돈","빵","사과","물","우산","우유","안경","책","커피","컴퓨터",
    "신발","사전","수어","영상","옷","과일","냉장고","노래","버스","비행기",
    "사진","색깔","생일","선물","소리","승용차","의자","이름","종이","창문",
    "책상","텔레비전","편의점","그림","기차","영화","음식","약속","전화번호",
    "카메라","표","표정","영수증","주사","전화","화면","노트북","상","상식","핸드폰",
    # word - action
    "적다","많다","가다","가르치다","기다리다","끝나다","돕다","듣다","마시다",
    "먹다","받다","배우다","보다","빌리다","사다","팔다","씻다","일어나다",
    "잊다","자다","주다","찾다","가끔","가져가다","그냥","기능","나누다",
    "내용","다르다","도움","도입","말하다","만나다","멈추다","문제","바꾸다",
    "발표","방법","변화","소개","실시간","연결","연락","이루다","일하다",
    "잃다","입다","장점","전달","준비","추가","걷다","고르다","고치다",
    "그리다","나가다","넣다","놀다","닫다","들어가다","만들다","믿다","부르다",
    "부탁","서다","싸우다","시작하다","앉다","약하다","열다","읽다","잡다",
    "적다","졸업하다","타다","필요하다","느리다","무겁다","작다","짧다",
    "조용하다","천천히","크다","항상","혼자","웃다","울다","계약","공유",
    "광고","겪다","새롭다","설명","예전","이유",
    # word - place
    "내일","도서관","식당","어디","여기","오늘","오전","오후","저녁","지금",
    "집","학교","아침","어제","언제","역","옆","앞","화장실","회사","년",
    "누구","뒤쪽","시간","월","대학교","법원","은행","장소","중학교","초등학교",
    "고등학교","공원","교실","국가","마을","문화","세계","동물원","지역","출장",
    "치과","전공","대회","매일",
    # word - study
    "나중에","공부","나중에","넷","다섯","데이터","둘","셋","순서","쉬다",
    "아홉","여덟","여섯","열","일곱","하나","숫자","거래","검토","토론",
    "결산","결제","대출금","보안","복구","복지","부서","세금","송금","연차",
    "월급","위자료","이유","정보","주제","추진","취소","팀","통계","품질",
    "휴가","감속","등록비","직업","협의","퇴직금",
]

# 중복 제거
DB_WORDS = list(dict.fromkeys(DB_WORDS))


def init_driver():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)


def crawl_word(driver, keyword):
    try:
        driver.get(f"{BASE_URL}/front/search/searchAllList.do?searchKeyword={keyword}")
        time.sleep(DELAY)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        cid, ctype = None, None
        for a in soup.select("a"):
            href = a.get("href", "")
            m = re.search(r"fnSearchContentsView\('(\d+)',\s*'(\w+)'", href)
            if m:
                cid, ctype = m.group(1), m.group(2)
                break

        if not cid:
            return None

        detail_url = f"{BASE_URL}/front/sign/signContentsView.do?origin_no={cid}&top_category={ctype}&category=&searchKeyword={keyword}&searchCondition=&search_gubun=&museum_no=0&current_pos=0"
        driver.get(detail_url)
        time.sleep(DELAY)

        detail_soup = BeautifulSoup(driver.page_source, "html.parser")
        for source in detail_soup.select("source"):
            src = source.get("src", "")
            if src.endswith(".mp4") and "multimedia_files" in src:
                return src

        return None

    except Exception as e:
        print(f"오류: {e}")
        return None


def test_video(keyword):
    print(f"'{keyword}' 테스트 중...")
    driver = init_driver()
    try:
        url = crawl_word(driver, keyword)
        print(f"✅ {url}" if url else "❌ 없음")
    finally:
        driver.quit()


def crawl_all():
    try:
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            results = json.load(f)
        done_words = {r["word"] for r in results}
        print(f"기존 {len(results)}개 발견, 이어서 진행...\n")
    except:
        results = []
        done_words = set()

    failed = []
    driver = init_driver()

    try:
        remaining = [w for w in DB_WORDS if w not in done_words]
        print(f"총 {len(DB_WORDS)}개 중 남은 단어: {len(remaining)}개\n")

        for i, word in enumerate(remaining):
            print(f"[{i+1}/{len(remaining)}] '{word}'...", end=" ", flush=True)
            video_url = crawl_word(driver, word)

            if video_url:
                results.append({"word": word, "video_url": video_url})
                print("✅")
            else:
                failed.append(word)
                print("❌")

            if (i + 1) % 50 == 0:
                with open(OUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"\n💾 중간저장 ({len(results)}개)\n")

    finally:
        driver.quit()

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 완료! 성공: {len(results)}개 / 실패: {len(failed)}개")
    if failed:
        print(f"실패: {failed}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--video":
        test_video(sys.argv[2] if len(sys.argv) > 2 else "먹다")
    else:
        crawl_all()