// 가령: 260422: 수정 내용 - 문장 학습 페이지 신규 JS. word_learn.js 의 단일 단어 루프를 N개 단어 + 1개 문장 흐름으로 확장
// 26.05.07 : 가령 : 수정 내용 - Step 4 문장 인식은 model_video.pt 문장 모델 WebSocket으로 연결
// 가령: 260422: 수정 내용 - 단어 학습 60점 통과 기준 제거 (단어는 연습용, 문장만 60점 기준 적용)
const API_BASE = "/api/v1/learning";
const SENTENCE_PASS_THRESHOLD = 60.0;
const FRAME_INTERVAL_MS = 100;
// 26.05.06 : 가령 : 수정 내용 - 서버 분석 완료 여유 확보를 위해 녹화 제한 10초 → 15초
const RECORD_MAX_MS = 15000;
const RECORD_SECONDS = RECORD_MAX_MS / 1000;
const TIMER_CIRCUMFERENCE = 107;
const STEP_TITLES = {
  1: "영상 시청",
  2: "환경 세팅",
  3: "수어 실습",
  4: "문장 실습",
  5: "학습 완료",
};

const params = new URLSearchParams(location.search);
const sentenceId = parseInt(params.get("lesson_id") || "0", 10);
// 26.05.06 : 가령 : 수정 내용 - 마이페이지 진행 중 학습에서 진입한 경우 시도 횟수 이어받기
const shouldResume = params.get("resume") === "1";

const state = {
  sentence: null,             // { sentence_id, sentence_title, words: [{word_order, lesson_id, title}] }
  step: 1,
  previewWordIdx: 0,          // Step 1 단어 확인에서 넘기는 현재 단어 인덱스
  previewVideoToken: 0,       // Step 1 영상 비동기 갱신 순서 보장용
  currentWordIdx: 0,          // Step 3 진행 중 0..words.length-1
  attempt: 1,                 // 현재 단어의 시도 횟수
  attemptSentence: 1,         // Step 4 문장 시도 횟수
  wordScores: [],             // 단어별 최고 점수 (length = words.length)
  sentenceScore: 0,
  sentenceDetected: [],
  sentenceMatched: [],
  sentenceTop3: [],
  maxScore: 0,
  stream: null,
  ws: null,
  sentenceWs: null,
  sendTimer: null,
  sentenceSendTimer: null,
  sentenceRecordTimer: null,
  progressTimer: null,
  timerInterval: null,
  sentenceTimerInterval: null,
  stepperTimer: null,
  recordStartAt: 0,
  sentenceRecordStartAt: 0,
  recording: false,
  sentenceRecording: false,
  sentenceWaitingResult: false,
  hasAnalysisResult: false,
  hasSentenceAnalysisResult: false,
  captureCanvas: null,
  sentenceCaptureCanvas: null,
};

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[1]) : null;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function init() {
  const mainEl = document.querySelector('.learning-main');
  if (mainEl) mainEl.classList.add('practice-mode');
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
  document.getElementById("sentenceSide").textContent = state.sentence.sentence_title;
  renderPreviewWord();
  renderSentenceVideoList();

  // Step 4 화면
  document.getElementById("targetSentence4").textContent = state.sentence.sentence_title;
  document.getElementById("doneSentence").textContent = state.sentence.sentence_title;
  renderWordChips("wordChipRow", 0, 0);
  renderWordChips("sentenceChipRow", 0, state.sentence.words.length);

  await markLearningStarted();
  await loadResumeAttempt();
  bindNav();
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
      body: JSON.stringify({ lesson_id: sentenceId }),
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
      (item) => Number(item.lesson_id) === Number(sentenceId)
    );
    if (!progress) return;

    state.attemptSentence = Math.min((progress.attempt || 0) + 1, 3);
    const attemptEl = document.getElementById("attemptLabel4");
    if (attemptEl) attemptEl.textContent = state.attemptSentence;
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
  document.getElementById("backTo3From4").addEventListener("click", () => gotoStep(3));
  document.getElementById("startSentenceRecordBtn").addEventListener("click", onStartSentenceRecord);
  document.getElementById("confirmSentenceBtn").addEventListener("click", onConfirmSentence);
  document.getElementById("retryBtn").addEventListener("click", () => {
    state.previewWordIdx = 0;
    state.currentWordIdx = 0;
    state.attempt = 1;
    state.attemptSentence = 1;
    state.maxScore = 0;
    state.wordScores = new Array(state.sentence.words.length).fill(0);
    state.sentenceScore = 0;
    gotoStep(1);
  });
}


/* ──────────────────────────────────────────────────────────────
          혜미 추가 : 문장 구성 단어 리스트 관련 함수 시작
  ─────────────────────────────────────────────────────────────── */
async function renderSentenceVideoList() {
  const container = document.getElementById("sentenceVideoList");
  if (!container || !state.sentence?.words) return;

  container.innerHTML = state.sentence.words
    .map((word, idx) => `
      <button class="sentence-video-card" type="button" data-word-index="${idx}">
        <div class="sentence-video-thumb">
          <span>수어 영상 보이는 곳</span>
        </div>
        <div class="sentence-video-title">${escapeHtml(word.title)}</div>
      </button>
    `)
    .join("");

  container.querySelectorAll(".sentence-video-card").forEach((card) => {
    card.addEventListener("click", () => {
      selectPreviewWord(Number(card.dataset.wordIndex || 0));
    });
  });

  await Promise.all(
    state.sentence.words.map(async (word, idx) => {
      const card = container.querySelector(`[data-word-index="${idx}"]`);
      const thumb = card?.querySelector(".sentence-video-thumb");
      if (!thumb || typeof resolveSignLessonVideoUrl !== "function") return;

      const videoUrl = await resolveSignLessonVideoUrl({
        title: word.title,
        video_url: word.video_url || "",
      });
      if (!videoUrl) return;

      thumb.innerHTML = "";
      const video = document.createElement("video");
      video.src = videoUrl;
      video.muted = true;
      video.playsInline = true;
      video.preload = "metadata";
      thumb.appendChild(video);
    })
  );

  updateSentenceVideoListActive();
}

function updateSentenceVideoListActive() {
  const container = document.getElementById("sentenceVideoList");
  if (!container) return;
  container.querySelectorAll(".sentence-video-card").forEach((card) => {
    card.classList.toggle(
      "active",
      Number(card.dataset.wordIndex || 0) === state.previewWordIdx
    );
  });
}

function selectPreviewWord(idx) {
  state.previewWordIdx = Math.max(0, Math.min(state.sentence.words.length - 1, idx));
  renderPreviewWord();
}

// 가령: 5월 11일 : 수정 내용 - Step 1 단어 확인에서 수어 어순 단어를 하나씩 넘겨 표시
function renderPreviewWord() {
  const words = state.sentence.words;
  const current = words[state.previewWordIdx];

  document.getElementById("sentenceBig").textContent = "수어 영상 보이는 곳";
  document.getElementById("wordOrderBox").innerHTML = words
    .map((w, idx) => {
      const text = `${idx + 1}. ${escapeHtml(w.title)}`;
      return idx === state.previewWordIdx
        ? `<span class="word-order-current">${text}</span>`
        : text;
    })
    .join("<br>");
  updatePreviewWordVideo(current);
  updateSentenceVideoListActive();
}

// 가령: 5월 11일 : 수정 내용 - 문장 단어 확인에서 현재 단어별 연결 영상 표시
async function updatePreviewWordVideo(word) {
  const video = document.getElementById("sentenceWordVideo");
  const token = ++state.previewVideoToken;

  if (!video || typeof resolveSignLessonVideoUrl !== "function") {
    return;
  }

  video.pause();
  video.removeAttribute("src");
  video.load();
  video.style.display = "none";
  document.getElementById("sentenceBig").style.display = "block";

  const videoUrl = await resolveSignLessonVideoUrl({
    title: word.title,
    video_url: word.video_url || "",
  });

  if (token !== state.previewVideoToken) return;
  if (!videoUrl) return;

  video.src = videoUrl;
  video.style.display = "block";
  document.getElementById("sentenceBig").style.display = "none";
  video.load();
  video.onerror = () => {
    if (token === state.previewVideoToken) {
      video.style.display = "none";
      document.getElementById("sentenceBig").style.display = "block";
    }
  };
}
/* ───────────────────────────────────────────────────────────
          혜미 추가 : 문장 구성 단어 리스트 관련 함수 끝
  ──────────────────────────────────────────────────────────── */

function renderWordChips(containerId, activeIdx, doneCount) {
  const container = document.getElementById(containerId);
  if (!container || !state.sentence?.words) return;

  container.innerHTML = state.sentence.words
    .map((word, idx) => {
      const classes = ["sentence-word-chip"];
      if (idx < doneCount) classes.push("done");
      if (idx === activeIdx) classes.push("active");
      return `<span class="${classes.join(" ")}">${escapeHtml(word.title)}</span>`;
    })
    .join("");
}

function gotoStep(n) {
  if (state.step === 2 || state.step === 3 || state.step === 4) stopCamera();
  if (state.step === 3) stopWebSocket();
  if (state.step === 4) stopSentenceWebSocket();

  const prev = state.step;
  state.step = n;
  for (let i = 1; i <= 5; i++) {
    document.getElementById(`step${i}`).style.display = i === n ? "block" : "none";
  }
  document.getElementById("pageTitle").textContent = `문장 학습 페이지 - ${STEP_TITLES[n]}`;

  updateStepper(n, prev);

  if (n === 2) startCameraForStep(2);
  if (n === 3) {
    setupStep3ForCurrentWord();
    startCameraForStep(3).then(() => startWebSocket());
  }
  if (n === 4) {
    document.getElementById("attemptLabel4").textContent = state.attemptSentence;
    document.getElementById("scoreVal4").textContent = "0";
    document.getElementById("sentenceTop3Box").innerHTML = "";
    renderWordChips("sentenceChipRow", 0, state.sentence.words.length);
    state.sentenceTop3 = [];
    state.sentenceWaitingResult = false;
    document.getElementById("startSentenceRecordBtn").style.display = "inline-block";
    document.getElementById("confirmSentenceBtn").style.display = "none";
    document.getElementById("statusLine4").textContent = "학습한 단어를 어순에 맞게 이어서 문장으로 표현해주세요.";
    document.getElementById("statusLine4").style.color = "#6B7280";
    startCameraForStep(4).then(() => startSentenceWebSocket());
  }
  if (n === 5) {
    finishLearning();
  }
}

function updateStepper(nextStep, prevStep) {
  const nodes = document.querySelectorAll("#stepper .node");
  const lines = document.querySelectorAll("#stepper .line");

  if (state.stepperTimer) {
    clearTimeout(state.stepperTimer);
    state.stepperTimer = null;
  }

  const applyNodes = () => {
    nodes.forEach((node, i) => {
      node.classList.remove("active", "done");
      if (i + 1 < nextStep) node.classList.add("done");
      else if (i + 1 === nextStep) node.classList.add("active");
    });
  };

  const applyLines = () => {
    lines.forEach((line, i) => {
      line.classList.toggle("done", i + 1 < nextStep);
    });
  };

  if (nextStep > prevStep) {
    applyLines();
    state.stepperTimer = setTimeout(applyNodes, 200);
    return;
  }

  applyNodes();
  state.stepperTimer = setTimeout(applyLines, 200);
}

// 가령: 260422: 수정 내용 - 시도 횟수 표시 제거 (단어는 점수 제한 없이 한 번 인식 후 다음으로)
// 가령: 260422: 수정 내용 - 점수 UI 제거에 따라 scoreVal DOM 접근 삭제 (state.maxScore 는 내부 추적용으로 유지)
function setupStep3ForCurrentWord() {
  const w = state.sentence.words[state.currentWordIdx];
  document.getElementById("wordIndexLabel").textContent =
    `${state.currentWordIdx + 1}/${state.sentence.words.length}`;
  document.getElementById("targetChar3").textContent = w.title;
  renderWordChips("wordChipRow", state.currentWordIdx, state.currentWordIdx);
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
      document.getElementById("statusLine3").style.color = "#7d2523";
      stopRecording();
      return;
    }
    if (msg.type !== "prediction") return;
    if (!state.recording) return;

    if (msg.segment_top3) {
      stopRecording();
      state.hasAnalysisResult = true;
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
    document.getElementById("statusLine3").style.color = "#7d2523";
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

// 26.05.07 : 가령 : 수정 내용 - 문장 학습 Step 4 전체 영상 인식 WebSocket 연결
function startSentenceWebSocket() {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${location.host}${API_BASE}/ws/video_recognition`;
  state.sentenceWs = new WebSocket(url);

  state.sentenceWs.onopen = () => {
    document.getElementById("statusLine4").textContent = "준비 완료 — 시작 버튼을 누르세요";
    document.getElementById("statusLine4").style.color = "#6B7280";
  };
  state.sentenceWs.onmessage = (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }

    if (msg.type === "error") {
      document.getElementById("statusLine4").textContent = "오류: " + msg.message;
      document.getElementById("statusLine4").style.color = "#7d2523";
      stopSentenceRecording();
      return;
    }

    if (msg.type === "sentence_status") {
      if (!state.sentenceRecording) return;
      if (!msg.hand_detected) {
        document.getElementById("statusLine4").textContent = "손을 감지하는 중...";
        return;
      }
      if (typeof msg.buffer_count === "number") {
        document.getElementById("statusLine4").textContent =
          `녹화 중 — 수집 프레임 ${msg.buffer_count}개`;
      }
      return;
    }

    if (msg.type === "sentence_result") {
      state.sentenceWaitingResult = false;
      state.hasSentenceAnalysisResult = true;
      state.sentenceScore = Math.round(msg.score || 0);
      state.sentenceTop3 = msg.top3 || [];
      renderSentenceResult(msg);
    }
  };
  state.sentenceWs.onerror = () => {
    document.getElementById("statusLine4").textContent = "WebSocket 오류";
    document.getElementById("statusLine4").style.color = "#7d2523";
    stopSentenceRecording();
  };
  state.sentenceWs.onclose = () => stopSentenceRecording();
}

function stopSentenceWebSocket() {
  stopSentenceRecording();
  if (state.sentenceWs) { try { state.sentenceWs.close(); } catch {} state.sentenceWs = null; }
}

function onStartSentenceRecord() {
  if (!state.sentenceWs || state.sentenceWs.readyState !== WebSocket.OPEN) {
    alert("WebSocket 연결 대기 중입니다. 잠시 후 다시 시도하세요.");
    return;
  }
  state.sentenceRecording = true;
  state.hasSentenceAnalysisResult = false;
  state.sentenceScore = 0;
  state.sentenceDetected = [];
  state.sentenceMatched = [];
  state.sentenceTop3 = [];
  state.sentenceWaitingResult = false;
  state.sentenceRecordStartAt = Date.now();
  state.sentenceWs.send(JSON.stringify({
    type: "reset",
    target_sentence: state.sentence.sentence_title,
  }));
  document.getElementById("scoreVal4").textContent = "0";
  document.getElementById("sentenceTop3Box").innerHTML = "";
  setSentenceProgress(0);
  startSentenceTimer();
  showSentenceProgress(true);
  document.getElementById("startSentenceRecordBtn").style.display = "none";
  document.getElementById("confirmSentenceBtn").style.display = "none";
  document.getElementById("statusLine4").textContent = "녹화 중 — 문장을 수어 어순대로 수행하세요.";
  document.getElementById("statusLine4").style.color = "#7d2523";
  startSentenceFrameSender();
  state.sentenceRecordTimer = setInterval(() => {
    const elapsed = Date.now() - state.sentenceRecordStartAt;
    const pct = Math.min(100, (elapsed / RECORD_MAX_MS) * 100);
    setSentenceProgress(pct, elapsed);
    if (elapsed >= RECORD_MAX_MS) {
      finishSentenceRecording();
    }
  }, 150);
}

function finishSentenceRecording() {
  state.sentenceRecording = false;
  state.sentenceWaitingResult = true;
  if (state.sentenceSendTimer) { clearInterval(state.sentenceSendTimer); state.sentenceSendTimer = null; }
  if (state.sentenceRecordTimer) { clearInterval(state.sentenceRecordTimer); state.sentenceRecordTimer = null; }
  stopSentenceTimer();
  showSentenceProgress(false);

  document.getElementById("statusLine4").textContent = "녹화 완료 — 문장을 분석 중입니다.";
  document.getElementById("statusLine4").style.color = "#2C3E63";

  if (state.sentenceWs && state.sentenceWs.readyState === WebSocket.OPEN) {
    state.sentenceWs.send(JSON.stringify({
      type: "finish",
      target_sentence: state.sentence.sentence_title,
    }));
  } else {
    state.sentenceWaitingResult = false;
    document.getElementById("startSentenceRecordBtn").style.display = "inline-block";
    document.getElementById("startSentenceRecordBtn").textContent = "다시 녹화";
    document.getElementById("statusLine4").textContent = "WebSocket 연결이 끊겼습니다. 다시 시도하세요.";
    document.getElementById("statusLine4").style.color = "#7d2523";
  }
}

function renderSentenceResult(msg) {
  document.getElementById("scoreVal4").textContent = state.sentenceScore;

  const top3Html = state.sentenceTop3.length
    ? state.sentenceTop3
        .map((p, i) => `${i + 1}위 : ${escapeHtml(p.label)} (${Number(p.prob || 0).toFixed(1)}%)`)
        .join("<br>")
    : "판독 후보 없음";

  const matched = msg.matched_label
    ? `정답 라벨 : ${escapeHtml(msg.matched_label)}`
    : "정답 라벨 : 모델 후보에서 찾지 못함";

  // 26.05.07 : 가령 : 수정 내용 - 문장 학습 Step 4는 15초 녹화 종료 후 전체 문장 Top-3를 표시
  document.getElementById("sentenceTop3Box").innerHTML =
    `정답 점수 : ${state.sentenceScore}점<br>${matched}<br>${top3Html}`;
  document.getElementById("startSentenceRecordBtn").style.display = "inline-block";
  document.getElementById("startSentenceRecordBtn").textContent = "다시 녹화";
  document.getElementById("confirmSentenceBtn").style.display = "inline-block";
  document.getElementById("statusLine4").textContent = "분석 완료 — 확인 버튼을 누르거나 다시 녹화하세요.";
  document.getElementById("statusLine4").style.color = "#2C3E63";
}

function stopSentenceRecording() {
  state.sentenceRecording = false;
  state.sentenceWaitingResult = false;
  if (state.sentenceSendTimer) { clearInterval(state.sentenceSendTimer); state.sentenceSendTimer = null; }
  if (state.sentenceRecordTimer) { clearInterval(state.sentenceRecordTimer); state.sentenceRecordTimer = null; }
  stopSentenceTimer();
  showSentenceProgress(false);
}

function setSentenceProgress(pct, elapsedMs) {
  const bar = document.getElementById("progressBar4");
  if (bar) bar.style.width = pct + "%";
  if (typeof elapsedMs === "number") {
    const sec = (elapsedMs / 1000).toFixed(1);
    const total = (RECORD_MAX_MS / 1000).toFixed(1);
    const time = document.getElementById("progressTime4");
    if (time) time.textContent = `${sec} / ${total} 초`;
  }
}

function showSentenceProgress(show) {
  const wrap = document.getElementById("progressWrap4");
  const time = document.getElementById("progressTime4");
  if (wrap) wrap.style.display = show ? "block" : "none";
  if (time) time.style.display = show ? "block" : "none";
}

function startSentenceFrameSender() {
  const video = document.getElementById("video4");
  if (!state.sentenceCaptureCanvas) {
    state.sentenceCaptureCanvas = document.createElement("canvas");
    state.sentenceCaptureCanvas.width = 640;
    state.sentenceCaptureCanvas.height = 480;
  }
  const canvas = state.sentenceCaptureCanvas;
  const ctx = canvas.getContext("2d");
  state.sentenceSendTimer = setInterval(() => {
    if (!state.sentenceWs || state.sentenceWs.readyState !== WebSocket.OPEN) return;
    if (!video.videoWidth) return;
    // 26.05.07 : 가령 : 수정 내용 - 화면만 CSS로 반전하고 문장 모델에는 원본 프레임 전송
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const b64 = canvas.toDataURL("image/jpeg", 0.85);
    state.sentenceWs.send(JSON.stringify({
      type: "frame",
      image: b64,
      target_sentence: state.sentence.sentence_title,
    }));
  }, FRAME_INTERVAL_MS);
}

function onStartRecord() {
  if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
    alert("WebSocket 연결 대기 중입니다. 잠시 후 다시 시도하세요.");
    return;
  }
  state.recording = true;
  state.hasAnalysisResult = false;
  state.recordStartAt = Date.now();
  document.getElementById("top3Box").innerHTML = "";
  showProgress(true);
  setProgress(0);
  startTimer();
  showStartButton(false);
  showConfirmButton(false);
  document.getElementById("statusLine3").textContent = "녹화 중 — 수어를 수행하고 2초간 정지하면 완료됩니다";
  document.getElementById("statusLine3").style.color = "#7d2523";
  startFrameSender();
  startProgressAnimation();
}

function stopRecording() {
  state.recording = false;
  if (state.sendTimer) { clearInterval(state.sendTimer); state.sendTimer = null; }
  if (state.progressTimer) { clearInterval(state.progressTimer); state.progressTimer = null; }
  stopTimer();
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
    // 26.05.08 : 가령 : 수정 내용 - 문장 3단계 단어 학습도 서버에는 원본 프레임 전송
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const b64 = canvas.toDataURL("image/jpeg", 0.85);
    const w = state.sentence.words[state.currentWordIdx];
    state.ws.send(JSON.stringify({
      type: "frame",
      image: b64,
      target: w.title,
      category: "word",
      // 26.05.07 : 가령 : 수정 내용 - 문장 학습 Step 3에서는 현재 학습 중인 정답 단어만 인식 후보로 전송
      allowed_targets: [w.title],
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
      state.hasAnalysisResult = false;
      document.getElementById("statusLine3").textContent = "시간 초과 — 다시 시도하세요";
      document.getElementById("statusLine3").style.color = "#7d2523";
      showStartButton(true);
      showConfirmButton(false);
      document.getElementById("startRecordBtn").textContent = "다시 녹화";
    }
  }, 150);
}

function setProgress(pct, elapsedMs) {
  const bar = document.getElementById("progressBar");
  if (bar) bar.style.width = pct + "%";
  if (typeof elapsedMs === "number") {
    const sec = (elapsedMs / 1000).toFixed(1);
    const total = (RECORD_MAX_MS / 1000).toFixed(1);
    const time = document.getElementById("progressTime");
    if (time) time.textContent = `${sec} / ${total} 초`;
  }
}
function showProgress(show) {
  const wrap = document.getElementById("progressWrap");
  const time = document.getElementById("progressTime");
  if (wrap) wrap.style.display = show ? "block" : "none";
  if (time) time.style.display = show ? "block" : "none";
}
function showStartButton(show) {
  document.getElementById("startRecordBtn").style.display = show ? "inline-block" : "none";
}
function showConfirmButton(show) {
  document.getElementById("confirmStep3").style.display = show ? "inline-block" : "none";
}

function startTimer() {
  startCircleTimer({
    intervalKey: "timerInterval",
    wrapId: "cameraTimerWrap",
    textId: "cameraTimerText",
    fillId: "timerFill",
  });
}

function stopTimer() {
  stopCircleTimer({
    intervalKey: "timerInterval",
    wrapId: "cameraTimerWrap",
  });
}

function startSentenceTimer() {
  startCircleTimer({
    intervalKey: "sentenceTimerInterval",
    wrapId: "sentenceCameraTimerWrap",
    textId: "sentenceCameraTimerText",
    fillId: "sentenceTimerFill",
  });
}

function stopSentenceTimer() {
  stopCircleTimer({
    intervalKey: "sentenceTimerInterval",
    wrapId: "sentenceCameraTimerWrap",
  });
}

function startCircleTimer({ intervalKey, wrapId, textId, fillId }) {
  const wrap = document.getElementById(wrapId);
  const text = document.getElementById(textId);
  const fill = document.getElementById(fillId);
  if (!wrap) return;

  if (state[intervalKey]) clearInterval(state[intervalKey]);

  let secondsLeft = RECORD_SECONDS;
  wrap.style.display = "block";

  if (fill) {
    fill.style.transition = "none";
    fill.style.strokeDasharray = TIMER_CIRCUMFERENCE;
    fill.style.strokeDashoffset = "0";
    fill.getBoundingClientRect();
  }
  if (text) text.textContent = `${secondsLeft}s`;

  state[intervalKey] = setInterval(() => {
    secondsLeft -= 1;
    if (text) text.textContent = `${Math.max(secondsLeft, 0)}s`;
    if (fill) {
      fill.style.transition = "stroke-dashoffset 1s linear";
      fill.style.strokeDashoffset =
        TIMER_CIRCUMFERENCE * (1 - Math.max(secondsLeft, 0) / RECORD_SECONDS);
    }
    if (secondsLeft <= 0 && state[intervalKey]) {
      clearInterval(state[intervalKey]);
      state[intervalKey] = null;
    }
  }, 1000);
}

function stopCircleTimer({ intervalKey, wrapId }) {
  if (state[intervalKey]) {
    clearInterval(state[intervalKey]);
    state[intervalKey] = null;
  }
  const wrap = document.getElementById(wrapId);
  if (wrap) wrap.style.display = "none";
}

// 가령: 260422: 수정 내용 - 단어는 인식만 하고 점수 제한 없이 다음으로 넘어가도록 변경 (재시도 루프 제거)
function onConfirmStep3() {
  // 26.05.06 : 가령 : 수정 내용 - 시간 초과된 녹화는 다음 단계와 시도 흐름에 반영하지 않음
  if (!state.hasAnalysisResult) {
    alert("분석이 완료된 녹화만 다음 단계에 반영됩니다.");
    return;
  }

  const score = state.maxScore;
  // 점수는 참고용으로 누적만 (최고점)
  if (score > state.wordScores[state.currentWordIdx]) {
    state.wordScores[state.currentWordIdx] = score;
  }
  // 점수 무관 다음 단어로
  state.currentWordIdx += 1;

  if (state.currentWordIdx >= state.sentence.words.length) {
    renderWordChips("wordChipRow", state.sentence.words.length - 1, state.sentence.words.length);
    gotoStep(4);
  } else {
    renderWordChips("wordChipRow", state.currentWordIdx, state.currentWordIdx);
    setupStep3ForCurrentWord();
  }
}

// 26.05.07 : 가령 : 수정 내용 - Step 4 문장 전체 영상 인식 결과로 완료/재시도 판단
function onConfirmSentence() {
  if (!state.hasSentenceAnalysisResult) {
    alert("분석이 완료된 녹화만 문장 학습 결과에 반영됩니다.");
    return;
  }

  const passed = state.sentenceScore >= SENTENCE_PASS_THRESHOLD;
  if (!passed && state.attemptSentence < 3) {
    state.attemptSentence += 1;
    document.getElementById("attemptLabel4").textContent = state.attemptSentence;
    state.sentenceScore = 0;
    state.hasSentenceAnalysisResult = false;
    document.getElementById("scoreVal4").textContent = "0";
    document.getElementById("sentenceTop3Box").innerHTML = "";
    document.getElementById("startSentenceRecordBtn").style.display = "inline-block";
    document.getElementById("startSentenceRecordBtn").textContent = "다시 녹화";
    document.getElementById("confirmSentenceBtn").style.display = "none";
    document.getElementById("statusLine4").textContent =
      `점수가 부족합니다. 다시 시도하세요. (${state.attemptSentence}/3)`;
    document.getElementById("statusLine4").style.color = "#7d2523";
    return;
  }

  gotoStep(5);
}

// 가령: 260422: 수정 내용 - 단어 점수 통과 기준 제거. 문장 점수 60점 만으로 통과 판정
async function finishLearning() {
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
  await saveSentenceResult(state.sentenceScore);
  markLessonCompleted(sentenceId);
}

async function saveSentenceResult(score) {
  const token = getCookie("access_token");
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const res = await fetch(`${API_BASE}/results`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        lesson_id: sentenceId,
        score,
        attempt: state.attemptSentence,
      }),
    });
    if (res.status === 401) {
      alert("로그인이 필요합니다.");
      location.href = "login.html";
    }
  } catch (e) {
    console.warn("문장 학습 결과 저장 실패", e);
  }
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

