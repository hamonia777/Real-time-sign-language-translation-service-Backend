// 가령: 26/04/19 수정내용: 라우터 prefix 가 /api/v1/learning 으로 변경된 것에 맞춰 API_BASE 수정
const API_BASE = "/api/v1/learning";

// 진웅 : live 서버에서는 CORS 문제로 인해 API_BASE 를 상대경로로 설정. 개발 시에는 필요에 따라 주석 처리된 라인을 사용 가능.
// const API_BASE = "http://127.0.0.1:8080/api/v1/learning";

const PASS_THRESHOLD = 80.0;
const MAX_ATTEMPTS = 3;
const FRAME_INTERVAL_MS = 300; // 초당 약 3프레임

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
  captureCanvas: null,
};

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

  bindNav();
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
    gotoStep(1);
  });
}

function gotoStep(n) {
  // cleanup
  if (state.step === 2 || state.step === 3) {
    stopCamera();
  }
  if (state.step === 3) {
    stopWebSocket();
  }

  state.step = n;
  for (let i = 1; i <= 4; i++) {
    document.getElementById(`step${i}`).style.display = i === n ? "block" : "none";
  }
  document.getElementById("pageTitle").textContent = `수어 학습 페이지 - 단계 ${n}`;

  // stepper 상태 업데이트
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
    }
    if (n === 3) {
      document.getElementById("statusLine3").textContent = "카메라 연결됨";
    }
  } catch (e) {
    if (n === 2) {
      document.getElementById("cameraStatus2").textContent = "카메라 상태 : 실패 (" + e.message + ")";
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
      document.getElementById("scoreVal").textContent = score;
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
    ctx.save();
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    ctx.restore();
    const b64 = canvas.toDataURL("image/jpeg", 0.6);
    state.ws.send(JSON.stringify({
      type: "frame",
      image: b64,
      target: state.lesson.title,
    }));
  }, FRAME_INTERVAL_MS);
}

// 가령: 26/04/19 수정내용: access_token 쿠키 읽어 Authorization 헤더로 전송, DB 에 결과 저장 연결
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[1]) : null;
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
      alert("로그인이 필요합니다. 로그인 후 다시 시도해주세요.");
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
  const passed = result.is_passed || state.attempt >= MAX_ATTEMPTS;
  if (!result.is_passed && state.attempt < MAX_ATTEMPTS) {
    state.attempt += 1;
    document.getElementById("attemptLabel").textContent = state.attempt;
    state.maxScore = 0;
    document.getElementById("scoreVal").textContent = "0";
    alert(`점수 ${result.score}점 — 재시도 (${state.attempt}/${MAX_ATTEMPTS})`);
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
