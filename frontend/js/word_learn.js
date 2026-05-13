// UI·타이머: 1번 코드 기준
// WS 모델 연결·top3·hand_detected·score 실시간 처리: 2번 코드 기준
const API_BASE = "/api/v1/learning";
// const API_BASE = "http://127.0.0.1:8080/api/v1/learning";

const PASS_THRESHOLD = 80.0;
const MAX_ATTEMPTS = 3;
// 26/04/19: 프레임 전송 주기 200ms → 100ms
const FRAME_INTERVAL_MS = 100;
// 1번 UI 기준: 원형 SVG 타이머
const RECORD_SECONDS = 10;
const TIMER_CIRCUMFERENCE = 107;

const params = new URLSearchParams(location.search);
const lessonId = parseInt(params.get("lesson_id") || "0", 10);
// 26.05.06: 마이페이지 진행 중 학습에서 진입한 경우 시도 횟수 이어받기
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
  timerInterval: null,   // 1번 기준 원형 타이머
  recording: false,
  hasAnalysisResult: false,
  captureCanvas: null,
};

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[1]) : null;
}

async function init() {
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

  // 단일 지문자(쌍자음/이중모음)는 크게 표시
  if (state.lesson.title.length === 1) {
    document.getElementById("targetCharBig").style.fontSize = "150px";
  }

  await markLearningStarted();
  await loadResumeAttempt();
  bindNav();

  // 5월 11일: 단어 학습 1단계 영상도 sign_video.js에서 설정
  if (typeof setupSignLessonVideo === "function") {
    setupSignLessonVideo(state.lesson).catch((e) => {
      console.warn("학습 영상 설정 실패", e);
    });
  }
}

// 26.05.06: 학습 페이지 진입만 해도 진행 중 학습으로 DB에 기록
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

// 26.05.06: 이어하기 진입 시 기존 attempt 다음 횟수부터 시작
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
  document.getElementById("startRecordBtn").addEventListener("click", onStartRecord);
  document.getElementById("confirmStep3").addEventListener("click", onConfirmStep3);
  document.getElementById("retryBtn").addEventListener("click", () => {
    state.attempt = 1;
    state.maxScore = 0;
    gotoStep(1);
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

  // 1번 기준: 스테퍼 애니메이션
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
    state.hasAnalysisResult = false;
    document.getElementById("scoreVal").textContent = "0점";
    document.getElementById("attemptLabel").textContent = state.attempt;
    document.getElementById("top3Box").innerHTML = "";
    showStartButton(true);
    showConfirmButton(false);
    document.getElementById("startRecordBtn").textContent = "시작";
    document.getElementById("statusLine3").textContent = "시작 버튼을 누르면 녹화가 시작됩니다";
    document.getElementById("statusLine3").style.color = "#6B7280";
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
    if (n === 2) document.getElementById("cameraStatus2").textContent = "카메라 상태 : 실패 (" + e.message + ")";
    if (n === 3) document.getElementById("statusLine3").textContent = "카메라 실패: " + e.message;
  }
}

function stopCamera() {
  if (state.stream) {
    state.stream.getTracks().forEach((t) => t.stop());
    state.stream = null;
  }
}

// ════════════════════════════════════════════════════════════
//  WebSocket — 2번 코드의 onmessage 로직 그대로 사용
//  (hand_detected 처리 + top3 실시간 갱신 + score 실시간 갱신)
// ════════════════════════════════════════════════════════════
function startWebSocket() {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${location.host}${API_BASE}/ws/word_recognition`;
  state.ws = new WebSocket(url);

  state.ws.onopen = () => {
    document.getElementById("statusLine3").textContent = "준비 완료 — 시작 버튼을 누르세요";
    document.getElementById("statusLine3").style.color = "#6B7280";
  };

  state.ws.onmessage = (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }

    if (msg.type === "error") {
      document.getElementById("statusLine3").textContent = "오류: " + msg.message;
      document.getElementById("statusLine3").style.color = "#550e0d";
      finishWordRecording();
      return;
    }
    if (msg.type !== "prediction") return;
    if (!state.recording) return;

    // ★ 2번 기준: 손 미감지 피드백 (1번에서 누락되어 인식 불가처럼 보이던 원인)
    if (msg.hand_detected === false) {
      state._noHandCount = (state._noHandCount || 0) + 1;
      // 3초(30프레임@100ms) 이상 손 미감지 시 안내 메시지 강화
      if (state._noHandCount > 30) {
        document.getElementById("top3Box").innerHTML =
          "<i>손이 감지되지 않아요.<br>카메라 정면에 손을 크게 보여주세요.</i>";
      } else {
        document.getElementById("top3Box").innerHTML = "<i>손을 감지하는 중...</i>";
      }
      return;
    }
    state._noHandCount = 0; // 손 감지되면 카운터 리셋

    // ★ 2번 기준: segment_top3 또는 top3 모두 처리 → 실시간 top3 갱신
    const predictions = msg.segment_top3 || msg.top3 || [];
    if (predictions.length) {
      const top3Html = predictions
        .map((p, i) => `${i + 1}위 : ${p.label} (${p.prob.toFixed(1)}%)`)
        .join("<br>");
      document.getElementById("top3Box").innerHTML = top3Html;
    }

    // ★ 2번 기준: score를 prediction마다 실시간으로 갱신 (segment 완료 전에도)
    if (typeof msg.score === "number") {
      const score = Math.round(msg.score || 0);
      console.log("받은 score:", score, "maxScore:", state.maxScore);
      if (score > state.maxScore) {
        state.maxScore = score;
        updateGauge(score);
      }
    }

    // ★ 2번 기준: segment_top3가 왔을 때만 녹화 종료 (세그먼트 분석 완료 신호)
    if (msg.segment_top3) {
      finishWordRecording();
      state.hasAnalysisResult = true;
      showStartButton(true);
      showConfirmButton(true);
      document.getElementById("startRecordBtn").textContent = "다시 녹화";
      document.getElementById("statusLine3").textContent = "분석 완료 — 확인 버튼을 누르거나 다시 녹화하세요";
      document.getElementById("statusLine3").style.color = "#2C3E63";
    }
  };

  state.ws.onerror = () => {
    document.getElementById("statusLine3").textContent = "WebSocket 오류";
    document.getElementById("statusLine3").style.color = "#550e0d";
    finishWordRecording();
  };
  state.ws.onclose = () => {
    finishWordRecording();
  };
}

function stopWebSocket() {
  finishWordRecording();
  if (state.ws) { try { state.ws.close(); } catch {} state.ws = null; }
}

// ════════════════════════════════════════════════════════════
//  녹화 제어 — 1번 UI 기준 (원형 SVG 타이머)
// ════════════════════════════════════════════════════════════
function onStartRecord() {
  if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
    alert("WebSocket 연결 대기 중입니다. 잠시 후 다시 시도하세요.");
    return;
  }
  showStartButton(false);
  showConfirmButton(false);
  startWordRecording();
}

function startWordRecording() {
  state.recording = true;
  state.hasAnalysisResult = false;
  state.maxScore = 0;
  updateGauge(0);
  document.getElementById("top3Box").innerHTML = "";
  document.getElementById("statusLine3").textContent = "녹화 중 — 수어를 수행하고 2초간 정지하면 완료됩니다";
  document.getElementById("statusLine3").style.color = "#550e0d";
  startTimer();       // 1번 원형 타이머
  startFrameSender();
}

function finishWordRecording() {
  state.recording = false;
  stopTimer();
  if (state.sendTimer) {
    clearInterval(state.sendTimer);
    state.sendTimer = null;
  }
}

// ════════════════════════════════════════════════════════════
//  프레임 전송 — 2번 기준 (원본 프레임 전송, 품질 0.85)
// ════════════════════════════════════════════════════════════
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
    // 26.05.08: 사용자 화면만 CSS로 반전, 모델에는 원본 프레임 전송
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    // 26/04/19: MediaPipe 손 검출 안정성을 위해 JPEG 품질 0.85
    const b64 = canvas.toDataURL("image/jpeg", 0.85);
    // 26/04/19: Top-3 필터링을 위해 category/subcategory 동반 전송
    state.ws.send(JSON.stringify({
      type: "frame",
      image: b64,
      target: state.lesson.title,
      category: state.lesson.category,
      subcategory: state.lesson.subcategory,
    }));
  }, FRAME_INTERVAL_MS);
}

// ════════════════════════════════════════════════════════════
//  타이머 — 1번 기준 (원형 SVG + 시간 초과 시 자동 확인)
// ════════════════════════════════════════════════════════════
function startTimer() {
  const wrap = document.getElementById("cameraTimerWrap");
  const text = document.getElementById("cameraTimerText");
  const fill = document.getElementById("timerFill");
  if (!wrap) return;

  if (state.timerInterval) clearInterval(state.timerInterval);

  let timerSeconds = RECORD_SECONDS;
  wrap.style.display = "block";

  if (fill) {
    fill.style.transition = "none";
    fill.style.strokeDasharray = TIMER_CIRCUMFERENCE;
    fill.style.strokeDashoffset = "0";
    fill.getBoundingClientRect(); // reflow 강제 (애니메이션 리셋)
  }
  if (text) text.textContent = `${RECORD_SECONDS}s`;

  state.timerInterval = setInterval(() => {
    timerSeconds -= 1;
    if (text) text.textContent = `${timerSeconds}s`;
    if (fill) {
      fill.style.transition = "stroke-dashoffset 1s linear";
      const offset = TIMER_CIRCUMFERENCE * (1 - timerSeconds / RECORD_SECONDS);
      fill.style.strokeDashoffset = offset;
    }
    if (timerSeconds <= 0) {
      stopTimer();
      // 분석 결과(segment_top3)가 왔으면 정상 처리,
      // 없으면 손을 못 찾은 것 → 강제 제출 대신 재시도 유도
      if (state.hasAnalysisResult) {
        onConfirmStep3();
      } else {
        finishWordRecording();
        document.getElementById("statusLine3").textContent = "시간 초과 — 손이 잘 보이도록 다시 시도하세요";
        document.getElementById("statusLine3").style.color = "#550e0d";
        showStartButton(true);
        showConfirmButton(false);
        document.getElementById("startRecordBtn").textContent = "다시 녹화";
      }
    }
  }, 1000);
}

function stopTimer() {
  if (state.timerInterval) {
    clearInterval(state.timerInterval);
    state.timerInterval = null;
  }
  const wrap = document.getElementById("cameraTimerWrap");
  if (wrap) wrap.style.display = "none";
}

// ════════════════════════════════════════════════════════════
//  결과 확인 및 단계 완료
// ════════════════════════════════════════════════════════════
async function onConfirmStep3() {
  // 2번 기준: 분석 완료된 녹화만 시도 횟수에 반영
  if (!state.hasAnalysisResult) {
    alert("분석이 완료된 녹화만 확인할 수 있어요. 다시 녹화해주세요.");
    return;
  }
  finishWordRecording();
  stopWebSocket();

  const score = state.maxScore;
  state.lastScore = score;

  const token = getCookie("access_token");
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const res = await fetch(`${API_BASE}/results`, {
      method: "POST",
      headers: headers,
      body: JSON.stringify({
        lesson_id: lessonId,
        score: score,
        attempt: state.attempt,
      }),
    });
    if (res.status === 401) {
      alert("로그인이 필요합니다.");
      location.href = "login.html";
      return;
    }
    const data = await res.json();
    finishStep3(data);
  } catch (e) {
    finishStep3({
      lesson_id: lessonId,
      score: score,
      is_passed: score >= PASS_THRESHOLD,
      attempt: state.attempt,
    });
  }
}

function finishStep3(result) {
  const failMsg = document.getElementById("failMsg");
  if (!result.is_passed && state.attempt < MAX_ATTEMPTS) {
    if (failMsg) failMsg.style.display = "block";
    state.attempt += 1;
    document.getElementById("attemptLabel").textContent = state.attempt;
    state.maxScore = 0;
    updateGauge(0);
    alert(`점수 ${result.score}점 — 재시도 (${state.attempt}/${MAX_ATTEMPTS})`);
    if (failMsg) failMsg.style.display = "none";
    document.getElementById("top3Box").innerHTML = "";
    showStartButton(true);
    showConfirmButton(false);
    document.getElementById("startRecordBtn").textContent = "시작";
    document.getElementById("statusLine3").textContent = "시작 버튼을 누르면 녹화가 시작됩니다";
    document.getElementById("statusLine3").style.color = "#6B7280";
    startWebSocket();
    return;
  }

  const finalScore = result.score || state.maxScore;
  const doneScoreEl = document.getElementById("doneScore");
  if (doneScoreEl) doneScoreEl.textContent = finalScore;
  if (result.is_passed) markLessonCompleted(lessonId);
  gotoStep(4);
}

function showStartButton(show) {
  const btn = document.getElementById("startRecordBtn");
  if (btn) btn.style.display = show ? "inline-block" : "none";
}

function showConfirmButton(show) {
  const btn = document.getElementById("confirmStep3");
  if (btn) btn.style.display = show ? "inline-block" : "none";
}

function updateGauge(score) {
  const val = document.getElementById("scoreVal");
  if (val) val.textContent = `${score}점`;
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

init();