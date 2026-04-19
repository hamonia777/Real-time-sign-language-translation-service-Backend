// 가령: 26/04/19 수정내용: 단어 학습 Step 3 에 model_word.pt WebSocket 연결 + 세그먼트 기반 채점 구현
// 가령: 26/04/19 수정내용: 시작 버튼으로 녹화 트리거 / 녹화 중에는 예측 숨기고 진행바 표시
const API_BASE = "/api/v1/learning";

// 진웅 : live 서버에서는 CORS 문제로 인해 API_BASE 를 상대경로로 설정. 개발 시에는 필요에 따라 주석 처리된 라인을 사용 가능.
// const API_BASE = "http://127.0.0.1:8080/api/v1/learning"; 
const PASS_THRESHOLD = 80.0;
const MAX_ATTEMPTS = 3;
// 가령: 26/04/19 수정내용: 인식률 개선을 위해 프레임 전송 주기 200ms → 100ms (5fps → 10fps)
const FRAME_INTERVAL_MS = 100;
const RECORD_MAX_MS = 10000; // 최대 녹화 시간 (진행바 전체)

const params = new URLSearchParams(location.search);
const lessonId = parseInt(params.get("lesson_id") || "0", 10);

const state = {
  lesson: null,
  step: 1,
  attempt: 1,
  lastScore: 0,
  maxScore: 0,
  stream: null,
  ws: null,
  sendTimer: null,
  progressTimer: null,
  recordStartAt: 0,
  recording: false,
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

  // 가령: 26/04/19 수정내용: 단일 지문자(쌍자음/이중모음) 는 크게 표시
  if (state.lesson.title.length === 1) {
    document.getElementById("targetCharBig").style.fontSize = "150px";
  }

  bindNav();
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

  state.step = n;
  for (let i = 1; i <= 4; i++) {
    document.getElementById(`step${i}`).style.display = i === n ? "block" : "none";
  }
  document.getElementById("pageTitle").textContent = `단어 학습 페이지 - 단계 ${n}`;

  const nodes = document.querySelectorAll("#stepper .node");
  const lines = document.querySelectorAll("#stepper .line");
  nodes.forEach((node, i) => {
    node.classList.remove("active", "done");
    if (i + 1 < n) node.classList.add("done");
    else if (i + 1 === n) node.classList.add("active");
  });
  lines.forEach((line, i) => {
    line.classList.toggle("done", i + 1 < n);
  });

  if (n === 2) startCameraForStep(2);
  if (n === 3) {
    state.maxScore = 0;
    document.getElementById("scoreVal").textContent = "0";
    document.getElementById("attemptLabel").textContent = state.attempt;
    document.getElementById("top3Box").innerHTML = "";
    setProgress(0);
    showProgress(false);
    showStartButton(true);
    showConfirmButton(false);
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
    if (n === 2) document.getElementById("cameraStatus2").textContent = "카메라 상태 : 정상";
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
      document.getElementById("statusLine3").style.color = "#c33";
      stopRecording();
      return;
    }
    if (msg.type !== "prediction") return;

    if (!state.recording) return; // 녹화 중이 아니면 무시

    // 세그먼트 완료 → 결과 표시
    if (msg.segment_top3) {
      stopRecording();
      const top3Html = msg.segment_top3
        .map((p, i) => `${i + 1}위 : ${p.label} (${p.prob.toFixed(1)}%)`)
        .join("<br>");
      document.getElementById("top3Box").innerHTML = top3Html;

      if (typeof msg.score === "number") {
        const score = Math.round(msg.score);
        if (score > state.maxScore) {
          state.maxScore = score;
          document.getElementById("scoreVal").textContent = score;
        }
      }

      showConfirmButton(true);
      showStartButton(true); // 다시 시도 가능
      document.getElementById("startRecordBtn").textContent = "다시 녹화";
      document.getElementById("statusLine3").textContent = "분석 완료 — 확인 버튼을 누르거나 다시 녹화하세요";
      document.getElementById("statusLine3").style.color = "#2C3E63";
    }
  };

  state.ws.onerror = () => {
    document.getElementById("statusLine3").textContent = "WebSocket 오류";
    document.getElementById("statusLine3").style.color = "#c33";
    stopRecording();
  };
  state.ws.onclose = () => {
    stopRecording();
  };
}

function stopWebSocket() {
  stopRecording();
  if (state.ws) { try { state.ws.close(); } catch {} state.ws = null; }
}

function onStartRecord() {
  if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
    alert("WebSocket 연결 대기 중입니다. 잠시 후 다시 시도하세요.");
    return;
  }
  state.recording = true;
  state.recordStartAt = Date.now();
  document.getElementById("top3Box").innerHTML = "";
  showProgress(true);
  setProgress(0);
  showStartButton(false);
  showConfirmButton(false);
  document.getElementById("statusLine3").textContent = "🔴 녹화 중 — 수어를 수행하고 2초간 정지하면 완료됩니다";
  document.getElementById("statusLine3").style.color = "#c7541f";
  startFrameSender();
  startProgressAnimation();
}

function stopRecording() {
  state.recording = false;
  if (state.sendTimer) { clearInterval(state.sendTimer); state.sendTimer = null; }
  if (state.progressTimer) { clearInterval(state.progressTimer); state.progressTimer = null; }
  showProgress(false);
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
    ctx.save();
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    ctx.restore();
    // 가령: 26/04/19 수정내용: MediaPipe 손 검출 안정성을 위해 JPEG 품질 0.6 → 0.85
    const b64 = canvas.toDataURL("image/jpeg", 0.85);
    // 가령: 26/04/19 수정내용: Top-3 를 카테고리 내부로 필터링하기 위해 category/subcategory 동반 전송
    state.ws.send(JSON.stringify({
      type: "frame",
      image: b64,
      target: state.lesson.title,
      category: state.lesson.category,
      subcategory: state.lesson.subcategory,
    }));
  }, FRAME_INTERVAL_MS);
}

function startProgressAnimation() {
  state.progressTimer = setInterval(() => {
    const elapsed = Date.now() - state.recordStartAt;
    const pct = Math.min(100, (elapsed / RECORD_MAX_MS) * 100);
    setProgress(pct, elapsed);
    if (elapsed >= RECORD_MAX_MS) {
      // 최대 시간 초과 — 녹화 강제 종료
      stopRecording();
      document.getElementById("statusLine3").textContent = "시간 초과 — 다시 시도하세요";
      document.getElementById("statusLine3").style.color = "#c33";
      showStartButton(true);
      document.getElementById("startRecordBtn").textContent = "다시 녹화";
    }
  }, 150);
}

// 가령: 26/04/19 수정내용: 진행바에 경과 시간 텍스트 표시 추가
function setProgress(pct, elapsedMs) {
  document.getElementById("progressBar").style.width = pct + "%";
  if (typeof elapsedMs === "number") {
    const sec = (elapsedMs / 1000).toFixed(1);
    const total = (RECORD_MAX_MS / 1000).toFixed(1);
    document.getElementById("progressTime").textContent = `${sec} / ${total} 초`;
  }
}
function showProgress(show) {
  document.getElementById("progressWrap").style.display = show ? "block" : "none";
  document.getElementById("progressTime").style.display = show ? "block" : "none";
}
function showStartButton(show) {
  document.getElementById("startRecordBtn").style.display = show ? "inline-block" : "none";
}
function showConfirmButton(show) {
  document.getElementById("confirmStep3").style.display = show ? "inline-block" : "none";
}

async function onConfirmStep3() {
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
  if (!result.is_passed && state.attempt < MAX_ATTEMPTS) {
    state.attempt += 1;
    document.getElementById("attemptLabel").textContent = state.attempt;
    state.maxScore = 0;
    document.getElementById("scoreVal").textContent = "0";
    alert(`점수 ${result.score}점 — 재시도 (${state.attempt}/${MAX_ATTEMPTS})`);
    // Step 3 재진입 상태로 초기화
    document.getElementById("top3Box").innerHTML = "";
    showConfirmButton(false);
    showStartButton(true);
    document.getElementById("startRecordBtn").textContent = "시작";
    document.getElementById("statusLine3").textContent = "시작 버튼을 누르면 녹화가 시작됩니다";
    document.getElementById("statusLine3").style.color = "#6B7280";
    return;
  }

  document.getElementById("doneScore").textContent = result.score;
  const msg = result.is_passed
    ? "축하합니다!<br>학습을 완료했습니다!"
    : `3회 시도 완료<br>최고 점수: ${result.score}점`;
  document.getElementById("completeMsg").innerHTML = msg;
  markLessonCompleted(lessonId);
  gotoStep(4);
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
