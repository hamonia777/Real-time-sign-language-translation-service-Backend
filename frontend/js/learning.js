// 가령: 26/04/19 수정내용: 라우터 prefix 가 /api/v1/learning 으로 변경된 것에 맞춰 API_BASE 수정
// 가령: 26/04/19 수정내용: DB 시드 초기화 버튼/기능 제거 (seed 함수 및 클릭 핸들러 삭제)
// 가령: 26/04/19 수정내용: 단어 학습 섹션 카테고리 탭 + 단어 렌더링 로직 추가
const API_BASE = "/api/v1/learning";

// 가령: 26/04/19 수정내용: fingerspell 모델이 못 알아듣는 쌍자음/이중모음은 word 모델(word_learn.html)로 라우팅
const WORD_MODEL_FS_CHARS = new Set(["ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ", "ㅘ", "ㅙ", "ㅝ", "ㅞ"]);

const WORD_CATEGORIES = [
  { key: "greeting", label: "인사·표현" },
  { key: "family", label: "사람·가족" },
  { key: "emotion", label: "감정" },
  { key: "body", label: "신체·건강" },
  { key: "job", label: "직업" },
  { key: "nature", label: "자연" },
  { key: "thing", label: "사물" },
  { key: "action", label: "동작" },
  { key: "place", label: "장소·시간" },
  { key: "study", label: "학업·업무·숫자" },
];

let allWords = [];
let activeCategory = WORD_CATEGORIES[0].key;

async function loadLessons() {
  try {
    const res = await fetch(`${API_BASE}/lessons?category=fingerspell`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderFingerspell(data.items);
  } catch (e) {
    console.error(e);
    document.getElementById("consonantList").innerHTML =
      '<p style="color:#c33;grid-column:1/-1;padding:10px;">레슨 불러오기 실패.</p>';
  }
}

async function loadWords() {
  try {
    const res = await fetch(`${API_BASE}/lessons?category=word`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    allWords = data.items;
    renderTabs();
    renderWords();
  } catch (e) {
    console.error(e);
    document.getElementById("wordList").innerHTML =
      '<p style="color:#c33;grid-column:1/-1;padding:10px;">단어 목록 불러오기 실패.</p>';
  }
}

function getCompletedSet() {
  try {
    const raw = localStorage.getItem("learning_completed_lessons");
    return new Set(raw ? JSON.parse(raw) : []);
  } catch {
    return new Set();
  }
}

function renderFingerspell(items) {
  const consonantBox = document.getElementById("consonantList");
  const vowelBox = document.getElementById("vowelList");
  consonantBox.innerHTML = "";
  vowelBox.innerHTML = "";

  const completed = getCompletedSet();

  for (const item of items) {
    const a = document.createElement("a");
    a.className = "lesson-card";
    if (completed.has(item.lesson_id)) a.classList.add("completed");
    const page = WORD_MODEL_FS_CHARS.has(item.title) ? "word_learn.html" : "sign_learn.html";
    a.href = `${page}?lesson_id=${item.lesson_id}`;
    a.textContent = item.title;
    if (item.subcategory === "vowel") vowelBox.appendChild(a);
    else consonantBox.appendChild(a);
  }
}

function renderTabs() {
  const tabBox = document.getElementById("wordTabs");
  tabBox.innerHTML = "";
  for (const cat of WORD_CATEGORIES) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "word-tab" + (cat.key === activeCategory ? " active" : "");
    btn.textContent = cat.label;
    btn.addEventListener("click", () => {
      activeCategory = cat.key;
      renderTabs();
      renderWords();
    });
    tabBox.appendChild(btn);
  }
}

function renderWords() {
  const box = document.getElementById("wordList");
  box.innerHTML = "";
  const completed = getCompletedSet();
  const filtered = allWords.filter((w) => w.subcategory === activeCategory);

  if (filtered.length === 0) {
    box.innerHTML =
      '<p style="color:#8c93a8;grid-column:1/-1;padding:10px;">이 카테고리의 단어가 없습니다. 시드 API 를 먼저 호출하세요.</p>';
    return;
  }

  for (const item of filtered) {
    const a = document.createElement("a");
    a.className = "lesson-card word-card";
    if (completed.has(item.lesson_id)) a.classList.add("completed");
    a.href = `word_learn.html?lesson_id=${item.lesson_id}`;
    a.textContent = item.title;
    box.appendChild(a);
  }
}

loadLessons();
loadWords();
