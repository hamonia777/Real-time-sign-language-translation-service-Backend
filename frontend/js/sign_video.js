// 가령: 5월 11일 : 수정 내용 - 수어 학습 1단계 영상 연결 로직을 별도 파일로 분리
const SIGN_VIDEO_URLS_URL = "/data/sign_video_urls.json";
const SIGN_VIDEO_PROGRESS_URL = "/data/sign_video_progress.json";
const SIGN_VIDEO_BASE_URL = "/videos";

const signVideoState = {
  urlMap: null,
  progress: null,
};

async function setupSignLessonVideo(lesson) {
  const video = document.getElementById("lessonVideo");
  const targetChar = document.getElementById("targetCharBig");
  const fallback = document.getElementById("videoFallback");
  const playBtn = document.getElementById("videoPlayBtn");
  const videoUrl = await resolveSignLessonVideoUrl(lesson);

  if (!videoUrl) {
    showEmptySignVideo(video, targetChar, fallback);
    return;
  }

  video.src = videoUrl;
  video.style.display = "block";
  targetChar.style.display = "none";
  fallback.style.display = "none";

  // 재생 버튼 표시
  if (playBtn) {
    playBtn.style.display = "flex";
    playBtn.onclick = () => {
      if (video.paused) {
        video.play();
        playBtn.classList.add("playing");
      } else {
        video.pause();
        playBtn.classList.remove("playing");
      }
    };
    // 영상 끝나면 버튼 다시 표시
    video.onended = () => playBtn.classList.remove("playing");
  }

  video.onerror = () => {
    showEmptySignVideo(video, targetChar, fallback);
    if (playBtn) playBtn.style.display = "none";
  };
}

async function resolveSignLessonVideoUrl(lesson) {
  if (!lesson) return "";
  const title = normalizeSignVideoTitle(lesson.title);

  const urlMap = await loadSignVideoUrls();
  const webVideoUrl = findSignVideoUrl(urlMap, title);
  if (webVideoUrl) return webVideoUrl;

  const progress = await loadSignVideoProgress();
  const entry = findSignVideoProgressEntry(progress, title);
  if (entry && entry.status === "success" && entry.path) {
    const fileName = entry.path.replace(/\\/g, "/").split("/").pop();
    if (fileName) return `${SIGN_VIDEO_BASE_URL}/${encodeURIComponent(fileName)}`;
  }

  return lesson.video_url || "";
}

async function loadSignVideoUrls() {
  if (signVideoState.urlMap) return signVideoState.urlMap;

  try {
    const res = await fetch(SIGN_VIDEO_URLS_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    signVideoState.urlMap = await res.json();
  } catch (e) {
    console.warn("웹 영상 URL 매핑 로드 실패", e);
    signVideoState.urlMap = {};
  }
  return signVideoState.urlMap;
}

async function loadSignVideoProgress() {
  if (signVideoState.progress) return signVideoState.progress;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 3000);

  try {
    const res = await fetch(SIGN_VIDEO_PROGRESS_URL, {
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    signVideoState.progress = await res.json();
  } catch (e) {
    console.warn("영상 매핑 로드 실패", e);
    signVideoState.progress = {};
  } finally {
    clearTimeout(timer);
  }
  return signVideoState.progress;
}

function findSignVideoUrl(urlMap, title) {
  if (!urlMap || !title) return "";
  if (urlMap[title]) return normalizeSignVideoUrl(urlMap[title]);

  const parts = title
    .split(/[\/,]/)
    .map((part) => part.trim())
    .filter(Boolean);

  for (const part of parts) {
    if (urlMap[part]) return normalizeSignVideoUrl(urlMap[part]);
  }
  return "";
}

function findSignVideoProgressEntry(progress, title) {
  if (!progress || !title) return null;
  if (progress[title]) return progress[title];

  const parts = title
    .split(/[\/,]/)
    .map((part) => part.trim())
    .filter(Boolean);

  for (const part of parts) {
    if (progress[part]) return progress[part];
  }
  return null;
}

function normalizeSignVideoTitle(title) {
  return title.trim().replace(/[.。．]+$/g, "");
}

function normalizeSignVideoUrl(url) {
  return url.replace(/^http:\/\//, "https://");
}

function showEmptySignVideo(video, targetChar, fallback) {
  video.style.display = "none";
  targetChar.style.display = "none";
  fallback.style.display = "none";
  fallback.textContent = "";
}
