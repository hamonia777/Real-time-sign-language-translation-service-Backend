// 가령: 260422: 수정 내용 - 문장 학습 페이지 신규 JS. word_learn.js 의 단일 단어 루프를 N개 단어 + 1개 문장 흐름으로 확장
// Phase 3 작업 (model_video.pt 연결) 전까지 Step 4(문장 인식) 는 임시 통과 처리 버튼으로 대체
// 가령: 260422: 수정 내용 - 단어 학습 60점 통과 기준 제거 (단어는 연습용, 문장만 60점 기준 적용)
const API_BASE = "/api/v1/learning";
const SENTENCE_PASS_THRESHOLD = 60.0;
const FRAME_INTERVAL_MS = 100;
const RECORD_MAX_MS = 10000;

const params = new URLSearchParams(location.search);
const sentenceId = parseInt(params.get("lesson_id") || "0", 10);

const state = {
  sentence: null,             // { sentence_id, sentence_title, words: [{word_order, lesson_id, title}] }
  step: 1,
  currentWordIdx: 0,          // Step 3 진행 중 0..words.length-1
  attempt: 1,                 // 현재 단어의 시도 횟수
  attemptSentence: 1,         // Step 4 문장 시도 횟수
  wordScores: [],             // 단어별 최고 점수 (length = words.length)
  sentenceScore: 0,
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
  if (!sentenceId) {
    alert("lesson_id 가 없습니다.");
    location.href = "learning.html";
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/sentences/${sentenceId}/words`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    state.sentence = await res.json();
  } catch (e) {
    alert("문장 로드 실패: " + e.message);
    return;
  }

  if (!state.sentence.words || state.sentence.words.length === 0) {
    alert("이 문장에 매핑된 단어가 없습니다. 시드를 다시 확인하세요.");
    return;
  }

  state.wordScores = new Array(state.sentence.words.length).fill(0);

  // Step 1 화면 채우기
  document.getElementById("sentenceBig").textContent = state.sentence.sentence_title;
  document.getElementById("sentenceSide").textContent = state.sentence.sentence_title;
  document.getElementById("wordOrderBox").innerHTML = state.sentence.words
    .map((w) => `${w.word_order}. ${w.title}`)
    .join("<br>");

  // Step 4 화면
  document.getElementById("targetSentence4").textContent = state.sentence.sentence_title;
  document.getElementById("doneSentence").textContent = state.sentence.sentence_title;

  bindNav();
}

function bindNav() {
  document.getElementById("toStep2").addEventListener("click", () => gotoStep(2));
  document.getElementById("backTo1").addEventListener("click", () => gotoStep(1));
  document.getElementById("toStep3").addEventListener("click", () => gotoStep(3));
  document.getElementById("backTo2").addEventListener("click", () => gotoStep(2));
  document.getElementById("startRecordBtn").addEventListener("click", onStartRecord);
  document.getElementById("confirmStep3").addEventListener("click", onConfirmStep3);
  document.getElementById("backTo3From4").addEventListener("click", () => gotoStep(3));
  document.getElementById("passSentenceBtn").addEventListener("click", onPassSentence);
  document.getElementById("retryBtn").addEventListener("click", () => {
    state.currentWordIdx = 0;
    state.attempt = 1;
    state.attemptSentence = 1;
    state.maxScore = 0;
    state.wordScores = new Array(state.sentence.words.length).fill(0);
    state.sentenceScore = 0;
    gotoStep(1);
  });
}

function gotoStep(n) {
  if (state.step === 2 || state.step === 3 || state.step === 4) stopCamera();
  if (state.step === 3) stopWebSocket();

  state.step = n;
  for (let i = 1; i <= 5; i++) {
    document.getElementById(`step${i}`).style.display = i === n ? "block" : "none";
  }
  document.getElementById("pageTitle").textContent = `문장 학습 페이지 - 단계 ${n}`;

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
    setupStep3ForCurrentWord();
    startCameraForStep(3).then(() => startWebSocket());
  }
  if (n === 4) {
    document.getElementById("attemptLabel4").textContent = state.attemptSentence;
    document.getElementById("scoreVal4").textContent = "0";
    startCameraForStep(4);
  }
  if (n === 5) {
    finishLearning();
  }
}

// 가령: 260422: 수정 내용 - 시도 횟수 표시 제거 (단어는 점수 제한 없이 한 번 인식 후 다음으로)
// 가령: 260422: 수정 내용 - 점수 UI 제거에 따라 scoreVal DOM 접근 삭제 (state.maxScore 는 내부 추적용으로 유지)
function setupStep3ForCurrentWord() {
  const w = state.sentence.words[state.currentWordIdx];
  document.getElementById("wordIndexLabel").textContent =
    `${state.currentWordIdx + 1}/${state.sentence.words.length}`;
  document.getElementById("targetChar3").textContent = w.title;
  state.maxScore = 0;
  document.getElementById("top3Box").innerHTML = "";
  setProgress(0);
  showProgress(false);
  showStartButton(true);
  showConfirmButton(false);
  document.getElementById("startRecordBtn").textContent = "시작";
  document.getElementById("statusLine3").textContent = "시작 버튼을 누르면 인식이 시작됩니다 (점수 무관, 확인 시 다음 단어)";
  document.getElementById("statusLine3").style.color = "#6B7280";
}

// 가령: 260422: 수정 내용 - 단어 어순 미니 스테퍼 UI 제거에 따라 renderWordMiniStepper 함수 삭제

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
    if (!state.recording) return;

    if (msg.segment_top3) {
      stopRecording();
      const top3Html = msg.segment_top3
        .map((p, i) => `${i + 1}위 : ${p.label} (${p.prob.toFixed(1)}%)`)
        .join("<br>");
      document.getElementById("top3Box").innerHTML = top3Html;

      // 가령: 260422: 수정 내용 - 점수 UI 제거에 따라 DOM 갱신 삭제 (state.maxScore 만 내부 추적)
      if (typeof msg.score === "number") {
        const score = Math.round(msg.score);
        if (score > state.maxScore) state.maxScore = score;
      }

      showConfirmButton(true);
      showStartButton(true);
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
    const b64 = canvas.toDataURL("image/jpeg", 0.85);
    const w = state.sentence.words[state.currentWordIdx];
    state.ws.send(JSON.stringify({
      type: "frame",
      image: b64,
      target: w.title,
      category: "word",
      // subcategory 는 서버 측 카테고리 필터에 사용. 단어 학습과 동일한 동작을 위해 omit (전체 word 모델 라벨 대상)
    }));
  }, FRAME_INTERVAL_MS);
}

function startProgressAnimation() {
  state.progressTimer = setInterval(() => {
    const elapsed = Date.now() - state.recordStartAt;
    const pct = Math.min(100, (elapsed / RECORD_MAX_MS) * 100);
    setProgress(pct, elapsed);
    if (elapsed >= RECORD_MAX_MS) {
      stopRecording();
      document.getElementById("statusLine3").textContent = "시간 초과 — 다시 시도하세요";
      document.getElementById("statusLine3").style.color = "#c33";
      showStartButton(true);
      document.getElementById("startRecordBtn").textContent = "다시 녹화";
    }
  }, 150);
}

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

// 가령: 260422: 수정 내용 - 단어는 인식만 하고 점수 제한 없이 다음으로 넘어가도록 변경 (재시도 루프 제거)
function onConfirmStep3() {
  const score = state.maxScore;
  // 점수는 참고용으로 누적만 (최고점)
  if (score > state.wordScores[state.currentWordIdx]) {
    state.wordScores[state.currentWordIdx] = score;
  }
  // 점수 무관 다음 단어로
  state.currentWordIdx += 1;

  if (state.currentWordIdx >= state.sentence.words.length) {
    gotoStep(4);
  } else {
    setupStep3ForCurrentWord();
  }
}

// 가령: 260422: 수정 내용 - Step 4 임시 통과 버튼. Phase 3 에서 model_video.pt WebSocket 연결로 교체 예정
function onPassSentence() {
  // 임시: 80점으로 통과 처리. 실제 인식 연결 시 score 는 모델 응답에서 받음
  state.sentenceScore = 80;
  document.getElementById("scoreVal4").textContent = state.sentenceScore;
  gotoStep(5);
}

// 가령: 260422: 수정 내용 - 단어 점수 통과 기준 제거. 문장 점수 60점 만으로 통과 판정
function finishLearning() {
  const wordAvg = state.wordScores.length
    ? Math.round(state.wordScores.reduce((a, b) => a + b, 0) / state.wordScores.length)
    : 0;
  document.getElementById("doneWordAvg").textContent = wordAvg;
  document.getElementById("doneSentenceScore").textContent = state.sentenceScore;
  const sentencePassed = state.sentenceScore >= SENTENCE_PASS_THRESHOLD;
  const msg = sentencePassed
    ? "축하합니다!<br>문장 학습을 완료했습니다!"
    : `학습 종료<br>문장 점수 ${state.sentenceScore}점 (통과 기준 ${SENTENCE_PASS_THRESHOLD}점)`;
  document.getElementById("completeMsg").innerHTML = msg;
  markLessonCompleted(sentenceId);
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
