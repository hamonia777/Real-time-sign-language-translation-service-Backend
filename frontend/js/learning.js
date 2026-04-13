const API_BASE = "/api/learning";

async function loadLessons() {
  try {
    const res = await fetch(`${API_BASE}/lessons?category=fingerspell`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    render(data.items);
  } catch (e) {
    console.error(e);
    document.getElementById("consonantList").innerHTML =
      '<p style="color:#c33;grid-column:1/-1;padding:10px;">레슨 불러오기 실패. "DB 시드 초기화" 를 먼저 눌러주세요.</p>';
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

function render(items) {
  const consonantBox = document.getElementById("consonantList");
  const vowelBox = document.getElementById("vowelList");
  consonantBox.innerHTML = "";
  vowelBox.innerHTML = "";

  const completed = getCompletedSet();

  for (const item of items) {
    const a = document.createElement("a");
    a.className = "lesson-card";
    if (completed.has(item.lesson_id)) {
      a.classList.add("completed");
    }
    a.href = `sign_learn.html?lesson_id=${item.lesson_id}`;
    a.textContent = item.title;
    if (item.subcategory === "vowel") {
      vowelBox.appendChild(a);
    } else {
      consonantBox.appendChild(a);
    }
  }
}

async function seed() {
  const btn = document.getElementById("seedBtn");
  btn.disabled = true;
  btn.textContent = "시드 중...";
  try {
    const res = await fetch(`${API_BASE}/seed/fingerspell`, { method: "POST" });
    const data = await res.json();
    alert(data.message || "완료");
    await loadLessons();
  } catch (e) {
    alert("시드 실패: " + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "DB 시드 초기화";
  }
}

document.getElementById("seedBtn").addEventListener("click", seed);
loadLessons();
