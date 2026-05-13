// 가령: 26/04/19 수정내용: 라우터 prefix 가 /api/v1/learning 으로 변경된 것에 맞춰 API_BASE 수정
const API_BASE = "/api/v1/learning";

// 진웅 : live 서버에서는 CORS 문제로 인해 API_BASE 를 상대경로로 설정. 개발 시에는 필요에 따라 주석 처리된 라인을 사용 가능.
// const API_BASE = "http://127.0.0.1:8080/api/v1/learning";

const PASS_THRESHOLD = 80.0;
const MAX_ATTEMPTS = 3;
const FRAME_INTERVAL_MS = 300; // 초당 약 3프레임

const params = new URLSearchParams(location.search);
const lessonId = parseInt(params.get("lesson_id") || "0", 10);
// 26.05.06 : 가령 : 수정 내용 - 마이페이지 진행 중 학습에서 진입한 경우 시도 횟수 이어받기
const shouldResume = params.get("resume") === "1";

const state = {
  lesson: null,
  step: 1,
  attempt: 1,
  lastScore: 0,
  maxScore: 0,
  stream: null,
  ws: null,
  sendTimer: null,
  captureCanvas: null,
};

async function init() {
  const mainEl = document.querySelector('.learning-main');
  if (mainEl) mainEl.classList.add('practice-mode');
  if (!lessonId) {
    alert("lesson_id 가 없습니다.");
    location.href = "learning.html";
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/lessons/${lessonId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    state.lesson = await res.json();
  } catch (e) {
    alert("레슨 로드 실패: " + e.message);
    return;
  }

  document.getElementById("targetCharBig").textContent = state.lesson.title;
  document.getElementById("targetCharSide").textContent = state.lesson.title;
  document.getElementById("targetChar3").textContent = state.lesson.title;
  document.getElementById("doneChar").textContent = state.lesson.title;

  await markLearningStarted();
  await loadResumeAttempt();
  bindNav();

  // 가령: 5월 11일 : 수정 내용 - 1단계 학습 영상을 sign_video.js에서 설정
  if (typeof setupSignLessonVideo === "function") {
    setupSignLessonVideo(state.lesson).catch((e) => {
      console.warn("학습 영상 설정 실패", e);
    });
  }
}

// 26.05.06 : 가령 : 수정 내용 - 학습 페이지 진입만 해도 진행 중 학습으로 DB에 기록
async function markLearningStarted() {
  const token = getCookie("access_token");
  if (!token) return;

  try {
    await fetch(`${API_BASE}/progress/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ lesson_id: lessonId }),
    });
  } catch (e) {
    console.warn("학습 시작 기록 실패", e);
  }
}

// 26.05.06 : 가령 : 수정 내용 - 이어하기 진입 시 기존 attempt 다음 횟수부터 시작
async function loadResumeAttempt() {
  if (!shouldResume) return;
  const token = getCookie("access_token");
  if (!token) return;

  try {
    const res = await fetch(`${API_BASE}/my-progress`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;

    const data = await res.json();
    const progress = (data.in_progress || []).find(
      (item) => Number(item.lesson_id) === Number(lessonId)
    );
    if (!progress) return;

    state.attempt = Math.min((progress.attempt || 0) + 1, MAX_ATTEMPTS);
    const attemptEl = document.getElementById("attemptLabel");
    if (attemptEl) attemptEl.textContent = state.attempt;
  } catch (e) {
    console.warn("진행 상태 불러오기 실패", e);
  }
}

function bindNav() {
  document.getElementById("toStep2").addEventListener("click", () => gotoStep(2));
  document.getElementById("backTo1").addEventListener("click", () => gotoStep(1));
  document.getElementById("toStep3").addEventListener("click", () => gotoStep(3));
  document.getElementById("backTo2").addEventListener("click", () => gotoStep(2));
  document.getElementById("confirmStep3").addEventListener("click", onConfirmStep3);
  document.getElementById("retryBtn").addEventListener("click", () => {
    state.attempt = 1;
    state.maxScore = 0;
    state.step = 1;
    for (let i = 1; i <= 4; i++) {
      document.getElementById(`step${i}`).style.display = i === 1 ? "block" : "none";
    }

    const nodes = document.querySelectorAll("#stepper .node");
    const lines = document.querySelectorAll("#stepper .line");

    lines.forEach((line) => {
      line.style.transition = "none";
      line.classList.remove("done");
    });

    nodes.forEach((node, i) => {
      node.querySelector(".dot").style.transition = "none";
      node.classList.remove("active", "done");
      if (i === 0) node.classList.add("active");
    });

    // reflow 후 transition 복구
    document.querySelector("#stepper").getBoundingClientRect();

    lines.forEach((line) => line.style.transition = "");
    nodes.forEach((node) => node.querySelector(".dot").style.transition = "");
  });
}

function gotoStep(n) {
  if (state.step === 2 || state.step === 3) stopCamera();
  if (state.step === 3) stopWebSocket();

  const prev = state.step;
  state.step = n;

  for (let i = 1; i <= 4; i++) {
    document.getElementById(`step${i}`).style.display = i === n ? "block" : "none";
  }

  const nodes = document.querySelectorAll("#stepper .node");
  const lines = document.querySelectorAll("#stepper .line");

if (n > prev) {
    lines.forEach((line, i) => {
      line.classList.toggle("done", i + 1 < n);
    });
    setTimeout(() => {
      nodes.forEach((node, i) => {
        node.classList.remove("active");
        if (i + 1 < n) node.classList.add("done");
        else if (i + 1 === n) node.classList.add("active");
        else node.classList.remove("done");
      });
    }, 200);
  } else {
    nodes.forEach((node, i) => {
      node.classList.remove("active");
      if (i + 1 < n) node.classList.add("done");
      else if (i + 1 === n) node.classList.add("active");
      else node.classList.remove("done");
    });
    setTimeout(() => {
      lines.forEach((line, i) => {
        line.classList.toggle("done", i + 1 < n);
      });
    }, 200);
  }

  if (n === 2) startCameraForStep(2);
  if (n === 3) {
    state.maxScore = 0;
    document.getElementById("scoreVal").textContent = "0";
    document.getElementById("attemptLabel").textContent = state.attempt;
    startCameraForStep(3).then(() => startWebSocket());
  }
}

async function startCameraForStep(n) {
  try {
    state.stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
      audio: false,
    });
    const video = document.getElementById(`video${n}`);
    video.srcObject = state.stream;
    if (n === 2) {
      document.getElementById("cameraStatus2").textContent = "카메라 상태 : 정상";
      const checkBtn = document.getElementById("cameraCheckBtn");
      if (checkBtn) {
        checkBtn.onclick = async () => {
          document.getElementById("cameraStatus2").textContent = "카메라 상태 : 확인 중...";
          stopCamera();
          await startCameraForStep(2);
        };
      }
    }
    if (n === 3) {
      document.getElementById("statusLine3").textContent = "카메라 연결됨";
    }
  } catch (e) {
    if (n === 2) {
      document.getElementById("cameraStatus2").textContent = "카메라 상태 : 연결 실패";
    }
    if (n === 3) {
      document.getElementById("statusLine3").textContent = "카메라 실패: " + e.message;
    }
  }
}

function stopCamera() {
  if (state.stream) {
    state.stream.getTracks().forEach((t) => t.stop());
    state.stream = null;
  }
}

// 진웅 : WebSocket 연결 로직 개선. API_BASE 에 따라 ws/wss 프로토콜 자동 선택
// function startWebSocket() {  
//   const wsUrl = API_BASE.replace(/^http/, 'ws') + "/ws/recognition";
//   state.ws = new WebSocket(wsUrl);

//   state.ws.onopen = () => {

function startWebSocket() {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${location.host}${API_BASE}/ws/recognition`;
  state.ws = new WebSocket(url);

  state.ws.onopen = () => {
    document.getElementById("statusLine3").textContent = "WebSocket 연결됨 — 손을 카메라에 보여주세요";
    startTimer(); 
    startFrameSender();
  };
  state.ws.onmessage = (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }
    if (msg.type === "error") {
      document.getElementById("statusLine3").textContent = "오류: " + msg.message;
      return;
    }
    if (msg.type !== "prediction") return;

    if (!msg.hand_detected) {
      document.getElementById("top3Box").innerHTML = "<i>손을 감지하는 중...</i>";
      return;
    }

    const top3Html = msg.top3
      .map((p, i) => `${i + 1}위 : ${p.label} (${p.prob.toFixed(1)}%)`)
      .join("<br>");
    document.getElementById("top3Box").innerHTML = top3Html;

    const score = Math.round(msg.score || 0);
    if (score > state.maxScore) {
      state.maxScore = score;
      updateGauge(score); 
    }
  };
  state.ws.onerror = () => {
    document.getElementById("statusLine3").textContent = "WebSocket 오류";
  };
  state.ws.onclose = () => {
    if (state.sendTimer) {
      clearInterval(state.sendTimer);
      state.sendTimer = null;
    }
  };
}

function stopWebSocket() {
  stopTimer(); 
  if (state.sendTimer) {
    clearInterval(state.sendTimer);
    state.sendTimer = null;
  }
  if (state.ws) {
    try { state.ws.close(); } catch {}
    state.ws = null;
  }
}

function startFrameSender() {
  const video = document.getElementById("video3");
  if (!state.captureCanvas) {
    state.captureCanvas = document.createElement("canvas");
    state.captureCanvas.width = 640;
    state.captureCanvas.height = 480;
  }
  const canvas = state.captureCanvas;
  const ctx = canvas.getContext("2d");

  state.sendTimer = setInterval(() => {
    if (!state.ws || state.ws.readyState !== WebSocket.OPEN) return;
    if (!video.videoWidth) return;
    // 26.05.06 : 가령 : 수정 내용 - 사용자 화면은 CSS로만 반전하고 서버 전송 프레임은 원본 방향 유지
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    // 26.05.07 : 가령 : 수정 내용 - 지문자 손가락 윤곽 보존을 위해 JPEG 품질 0.6 → 0.85
    const b64 = canvas.toDataURL("image/jpeg", 0.85);
    state.ws.send(JSON.stringify({
      type: "frame",
      image: b64,
      target: state.lesson.title,
      // 26.05.07 : 가령 : 수정 내용 - 지문자 자음/모음 후보군 필터링을 위해 subcategory 전달
      subcategory: state.lesson.subcategory,
    }));
  }, FRAME_INTERVAL_MS);
}

// 가령: 26/04/19 수정내용: access_token 쿠키 읽어 Authorization 헤더로 전송, DB 에 결과 저장 연결
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[1]) : null;
}

async function onConfirmStep3() {
  stopTimer();
  stopWebSocket();

  const score = state.maxScore;
  state.lastScore = score;

  // 통과 여부는 클라이언트에서 즉시 판단
  const isPassed = score >= PASS_THRESHOLD;

  // 서버 저장은 백그라운드에서 (화면 전환 안 기다림)
  const token = getCookie("access_token");
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  fetch(`${API_BASE}/results`, {
    method: "POST",
    headers: headers,
    body: JSON.stringify({
      lesson_id: lessonId,
      score: score,
      attempt: state.attempt,
    }),
  }).catch((e) => console.warn("결과 저장 실패", e));

  // 화면 전환은 즉시
  finishStep3({ score, is_passed: isPassed, attempt: state.attempt });
}

function finishStep3(result) {
  const failMsg = document.getElementById('failMsg');
  const isPassed = result.is_passed;

  if (!isPassed && state.attempt < MAX_ATTEMPTS) {
    if (failMsg) failMsg.style.display = 'block';
    state.attempt += 1;
    document.getElementById("attemptLabel").textContent = state.attempt;
    state.maxScore = 0;
    document.getElementById("scoreVal").textContent = "0점";
    updateGauge(0);
    alert(`점수 ${result.score}점 — 재시도 (${state.attempt}/${MAX_ATTEMPTS})`);
    if (failMsg) failMsg.style.display = 'none';

    startWebSocket();
    return;
  }

  const finalScore = result.score || state.maxScore;
  const doneScoreEl = document.getElementById("doneScore");
  if (doneScoreEl) doneScoreEl.textContent = finalScore;

  if (isPassed) markLessonCompleted(lessonId);

  // 3초 후 완료 화면으로 전환
  setTimeout(() => gotoStep(4), 2000);
}

function markLessonCompleted(id) {
  try {
    const key = "learning_completed_lessons";
    const raw = localStorage.getItem(key);
    const set = new Set(raw ? JSON.parse(raw) : []);
    set.add(id);
    localStorage.setItem(key, JSON.stringify([...set]));
  } catch (e) {
    console.warn("completed 저장 실패", e);
  }
}

const RECORD_SECONDS = 10;
const TIMER_CIRCUMFERENCE = 107;
let timerInterval = null;
let timerSeconds = RECORD_SECONDS;

function startTimer() {
  const wrap = document.getElementById('cameraTimerWrap');
  const text = document.getElementById('cameraTimerText');
  const fill = document.getElementById('timerFill');
  if (!wrap) return;

  if (timerInterval) clearInterval(timerInterval);

  timerSeconds = RECORD_SECONDS;
  wrap.style.display = 'block';

  if (fill) {
    fill.style.transition = 'none';
    fill.style.strokeDasharray = TIMER_CIRCUMFERENCE;
    fill.style.strokeDashoffset = '0';
    fill.getBoundingClientRect();
  }

  if (text) text.textContent = RECORD_SECONDS + 's';

  // tick()을 즉시 호출하지 않고 interval만 등록 → 10초 정확히 보장
  timerInterval = setInterval(() => {
    timerSeconds--;
    if (text) text.textContent = timerSeconds + 's';
    if (fill) {
      fill.style.transition = 'stroke-dashoffset 1s linear';
      const offset = TIMER_CIRCUMFERENCE * (1 - timerSeconds / RECORD_SECONDS);
      fill.style.strokeDashoffset = offset;
    }
    if (timerSeconds <= 0) {
      stopTimer();
      onConfirmStep3(); // .click() 대신 직접 호출
    }
  }, 1000);
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
  const wrap = document.getElementById('cameraTimerWrap');
  if (wrap) wrap.style.display = 'none';
}

function updateGauge(score) {
  const val = document.getElementById('scoreVal');
  if (val) val.textContent = score + '점';
}
init();
