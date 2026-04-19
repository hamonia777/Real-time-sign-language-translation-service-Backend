# 가령: 26/04/19 수정내용: 단어 인식 서비스 신규 추가 (recon_word.py 의 MLP + MotionSeg + DominantTracker 포팅)
"""
단어 수어 실시간 인식 서비스.
- model_word.pt (FrameMLP, 114→N_classes) 를 싱글톤으로 로드
- 프레임 시퀀스를 WordSession 단위로 상태 관리 (모션 세그먼트 + dominant hand 추적)
- 세그먼트가 끝날 때 평균 probability 로 Top-3 + target 점수 산출
"""
from __future__ import annotations

import re
import threading
from collections import Counter, deque
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

_MODEL_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "learning_model"
    / "model_word.pt"
)

HAND_FEAT_DIM = 114


class WordRecognitionService:
    """모델/정규화/mediapipe 는 프로세스 단위로 1회 로드."""

    _instance: "WordRecognitionService | None" = None
    _lock = threading.Lock()

    def __init__(self):
        import torch
        import torch.nn as nn
        import mediapipe as mp

        self.torch = torch
        self.nn = nn
        self.mp = mp

        self.device = torch.device(
            "mps" if torch.backends.mps.is_available() else "cpu"
        )
        print(f"[WordRecognitionService] device={self.device}")
        print(f"[WordRecognitionService] loading model: {_MODEL_PATH}")

        ckpt = torch.load(
            str(_MODEL_PATH), map_location=self.device, weights_only=False
        )
        self.num_classes = ckpt["num_classes"]
        self.input_dim = ckpt.get("input_dim", HAND_FEAT_DIM)
        self.idx_to_label_raw: Dict[int, str] = ckpt["idx_to_label"]

        # 모델 라벨(예: "다시3") → 베이스 단어("다시") 매핑
        self.idx_to_base: Dict[int, str] = {
            i: re.sub(r"\d+$", "", lbl) for i, lbl in self.idx_to_label_raw.items()
        }
        self.base_to_indices: Dict[str, List[int]] = {}
        for i, base in self.idx_to_base.items():
            self.base_to_indices.setdefault(base, []).append(i)

        # 정규화 파라미터
        mean = np.array(ckpt["norm_params"]["mean"]).flatten().astype(np.float32)
        std = np.array(ckpt["norm_params"]["std"]).flatten().astype(np.float32)
        std = np.where(std < 1e-8, 1.0, std)
        self.norm_mean = mean
        self.norm_std = std

        self.model = self._build_model(self.input_dim, self.num_classes)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model = self.model.to(self.device)
        self.model.eval()
        # warmup
        with torch.no_grad():
            dummy = torch.zeros(1, self.input_dim, device=self.device)
            self.model(dummy)

        # mediapipe (프로세스 단위 공유 + lock)
        self.mp_hands = mp.solutions.hands
        self.hands_detector = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._infer_lock = threading.Lock()

        # 가령: 26/04/19 수정내용: 카테고리 별 허용 라벨 세트 구축 (Top-3 필터링용)
        self.category_allowed: Dict[str, set] = self._build_category_allowed()

        print(
            f"[WordRecognitionService] ready. classes={self.num_classes} "
            f"base_labels={len(self.base_to_indices)} "
            f"categories={len(self.category_allowed)}"
        )

    def _build_category_allowed(self) -> Dict[str, set]:
        try:
            from main.domain.learning.service.lesson_service import WORDS_BY_CATEGORY
        except Exception:
            WORDS_BY_CATEGORY = {}

        allowed: Dict[str, set] = {}
        for subcat, words in WORDS_BY_CATEGORY.items():
            s = set()
            for w in words:
                for v in self._target_variants(w):
                    s.add(v)
            allowed[f"word:{subcat}"] = s

        # fingerspell 확장 문자 (word 모델로 인식)
        fs_extended = {"ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ", "ㅘ", "ㅙ", "ㅝ", "ㅞ"}
        allowed["fingerspell:consonant"] = fs_extended
        allowed["fingerspell:vowel"] = fs_extended
        allowed["fingerspell"] = fs_extended
        return allowed

    # 가령: 26/04/19 수정내용: state_dict 키 매칭을 위해 FrameMLP 클래스 구조 (self.net = Sequential) 그대로 복원
    def _build_model(self, input_dim: int, num_classes: int):
        nn = self.nn

        class FrameMLP(nn.Module):
            def __init__(self):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(input_dim, 512),
                    nn.BatchNorm1d(512),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(512, 512),
                    nn.BatchNorm1d(512),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(512, 256),
                    nn.BatchNorm1d(256),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(256, num_classes),
                )

            def forward(self, x):
                return self.net(x)

        return FrameMLP()

    @classmethod
    def instance(cls) -> "WordRecognitionService":
        with cls._lock:
            if cls._instance is None:
                cls._instance = WordRecognitionService()
            return cls._instance

    # ----- hand feature -----
    def _compute_finger_angles(self, pts: np.ndarray) -> np.ndarray:
        fingers = [
            [0, 1, 2, 3, 4],
            [0, 5, 6, 7, 8],
            [0, 9, 10, 11, 12],
            [0, 13, 14, 15, 16],
            [0, 17, 18, 19, 20],
        ]
        angles = []
        for finger in fingers:
            for i in range(len(finger) - 2):
                a, b, c = pts[finger[i]], pts[finger[i + 1]], pts[finger[i + 2]]
                ba, bc = a - b, c - b
                cos = np.dot(ba, bc) / (
                    np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8
                )
                angles.append(float(np.clip(cos, -1, 1)))
        return np.array(angles, dtype=np.float32)

    def detect_hands(self, bgr_frame: np.ndarray):
        """mediapipe 로 손 랜드마크 추출만 수행 (dominant 판별 전 호출)."""
        import cv2

        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        with self._infer_lock:
            return self.hands_detector.process(rgb)

    def extract_hand_rel(self, rh, dominant_label: str) -> np.ndarray | None:
        """114차원 [dominant|support] 특징. 손이 없으면 None."""
        dom = np.zeros(57, dtype=np.float32)
        sup = np.zeros(57, dtype=np.float32)
        has_hand = False

        if rh.multi_hand_landmarks:
            for idx, hlm in enumerate(rh.multi_hand_landmarks):
                lab = rh.multi_handedness[idx].classification[0].label
                pts = np.array(
                    [[lm.x, lm.y] for lm in hlm.landmark], dtype=np.float32
                )
                wrist = pts[0].copy()
                pts = (pts - wrist) / (np.linalg.norm(pts[9] - wrist) + 1e-8)
                feat = np.concatenate([pts.flatten(), self._compute_finger_angles(pts)])

                if lab == dominant_label:
                    dom[:] = feat
                else:
                    sup[:] = feat
                has_hand = True

        return np.concatenate([dom, sup]) if has_hand else None

    # ----- inference -----
    def predict_probs(self, hand_rel: np.ndarray) -> np.ndarray:
        torch = self.torch
        x_n = (hand_rel - self.norm_mean) / self.norm_std
        t = torch.tensor(x_n, dtype=torch.float32).unsqueeze(0).to(self.device)
        with self._infer_lock, torch.no_grad():
            probs = torch.softmax(self.model(t), dim=1)[0].cpu().numpy()
        return probs

    def aggregate_base(self, probs: np.ndarray) -> Dict[str, float]:
        """원 라벨 확률 벡터를 베이스 단어 기준으로 합산."""
        out: Dict[str, float] = {}
        for base, indices in self.base_to_indices.items():
            out[base] = float(probs[indices].sum())
        return out

    def top3_base(self, probs: np.ndarray) -> List[Tuple[str, float]]:
        base = self.aggregate_base(probs)
        return sorted(base.items(), key=lambda x: -x[1])[:3]

    # 가령: 26/04/19 수정내용: target 과 모델 라벨의 표기 차이 (슬래시 / 언더스코어 / 괄호 / 쉼표) 흡수
    @staticmethod
    def _target_variants(target: str) -> List[str]:
        variants = {target}
        if "/" in target:
            parts = [p.strip() for p in target.split("/") if p.strip()]
            variants.update(parts)
            variants.add("_".join(parts))
            if len(parts) == 2:
                variants.add(f"{parts[0]}({parts[1]})")
                variants.add(f"{parts[1]}({parts[0]})")
        if "_" in target:
            parts = [p.strip() for p in target.split("_") if p.strip()]
            variants.update(parts)
            variants.add("/".join(parts))
        m = re.match(r"^(.+?)\((.+?)\)$", target)
        if m:
            a, b = m.group(1), m.group(2)
            variants.update([a, b])
            variants.add(f"{a}/{b}")
            variants.add(f"{a}_{b}")
        if "," in target:
            parts = [p.strip() for p in target.split(",") if p.strip()]
            variants.update(parts)
        return [v for v in variants if v]

    # 가령: 26/04/19 수정내용: 변형 합산(sum) → 최고 매칭(max) 방식으로 변경
    #       — Top-3 에 표시되는 단일 항목 확률과 점수가 일치하도록
    def target_score(self, probs: np.ndarray, target: str) -> float:
        """대상 단어의 확률(0~1). 여러 변형 중 가장 강한 매칭 하나만 선택."""
        base = self.aggregate_base(probs)
        variants = self._target_variants(target)
        best = 0.0
        for v in variants:
            p = base.get(v, 0.0)
            if p > best:
                best = p
        return best


# =============================================================================
# Per-connection state
# =============================================================================
class DominantTracker:
    def __init__(self, decay: float = 0.97):
        self.decay = decay
        self.motion = {"Left": 0.0, "Right": 0.0}
        self.prev: Dict[str, np.ndarray | None] = {"Left": None, "Right": None}

    def update(self, rh) -> str:
        present = set()
        if rh.multi_hand_landmarks:
            for idx, hlm in enumerate(rh.multi_hand_landmarks):
                lab = rh.multi_handedness[idx].classification[0].label
                wrist = np.array(
                    [hlm.landmark[0].x, hlm.landmark[0].y], dtype=np.float32
                )
                if self.prev[lab] is not None:
                    m = float(np.linalg.norm(wrist - self.prev[lab]))
                    self.motion[lab] = (
                        self.decay * self.motion[lab] + (1 - self.decay) * m * 100
                    )
                self.prev[lab] = wrist
                present.add(lab)

        for lab in ("Left", "Right"):
            if lab not in present:
                self.motion[lab] *= self.decay
        return "Left" if self.motion["Left"] > self.motion["Right"] else "Right"


class MotionSeg:
    """손 모션 시작/종료 감지."""

    def __init__(
        self, thr: float = 0.015, min_f: int = 5, max_f: int = 50, cool: int = 10, smooth_w: int = 5
    ):
        self.thr, self.min_f, self.max_f, self.cool = thr, min_f, max_f, cool
        self.active = False
        self.count = 0
        self.still = 0
        self.prev: np.ndarray | None = None
        self.motion_buf: deque = deque(maxlen=smooth_w)

    def step(self, hand_feat: np.ndarray | None) -> str:
        motion = 0.0
        if self.prev is not None and hand_feat is not None:
            motion = float(np.linalg.norm(hand_feat - self.prev))
        if hand_feat is not None:
            self.prev = hand_feat.copy()
        self.motion_buf.append(motion if hand_feat is not None else 0.0)
        avg_motion = float(np.mean(self.motion_buf))
        moving = hand_feat is not None and avg_motion > self.thr
        no_hand = hand_feat is None

        if not self.active:
            if moving:
                self.active, self.count, self.still = True, 1, 0
            return "idle"

        self.count += 1
        self.still = 0 if (moving and not no_hand) else self.still + 1
        timeout = self.count >= self.max_f
        settled = self.still >= self.cool and self.count >= self.min_f
        if timeout or settled:
            self.active, self.count, self.still = False, 0, 0
            return "ready"
        return "collecting"


class WordSession:
    """WebSocket 연결 당 하나씩 생성. 모션 상태와 세그먼트 누적."""

    def __init__(self, service: WordRecognitionService):
        self.service = service
        self.dom_trk = DominantTracker()
        # 가령: 26/04/19 수정내용: JPEG 압축 손실로 모션값이 깎이는 것을 보정해 thr 0.008 → 0.003
        #       (min_f=10 → 1초, max_f=100 → 10초, cool=20 → 2초)
        self.seg = MotionSeg(thr=0.003, min_f=10, max_f=100, cool=20, smooth_w=5)
        self.seg_probs: List[np.ndarray] = []
        self.live_window: deque = deque(maxlen=10)
        # 가령: 26/04/19 수정내용: 세그먼트 중 target 의 최고 점수를 추적 (한 프레임이라도 맞으면 반영)
        self.seg_max_target_score: float = 0.0

    # 가령: 26/04/19 수정내용: category/subcategory 를 받아 Top-3 를 해당 카테고리 라벨로 필터링
    def process_frame(
        self,
        bgr_frame: np.ndarray,
        target: str | None,
        category: str | None = None,
        subcategory: str | None = None,
    ) -> dict:
        rh = self.service.detect_hands(bgr_frame)
        dom_label = self.dom_trk.update(rh)
        hand_rel = self.service.extract_hand_rel(rh, dominant_label=dom_label)

        result: dict = {
            "hand_detected": hand_rel is not None,
            "motion": None,
        }

        if hand_rel is not None:
            probs = self.service.predict_probs(hand_rel)
            base = self.service.aggregate_base(probs)
            top_lbl, top_conf = max(base.items(), key=lambda x: x[1])
            self.live_window.append((top_lbl, top_conf))

            if self.seg.active:
                self.seg_probs.append(probs)
                # 가령: 26/04/19 수정내용: 세그먼트 중 프레임 별 target 점수 중 최고값 추적
                if target:
                    cur = self.service.target_score(probs, target) * 100.0
                    if cur > self.seg_max_target_score:
                        self.seg_max_target_score = cur

            if len(self.live_window) >= 3:
                majority_lbl = Counter(l for l, _ in self.live_window).most_common(1)[0][0]
                majority_conf = float(
                    np.mean([c for l, c in self.live_window if l == majority_lbl])
                )
                result["live_label"] = majority_lbl
                result["live_conf"] = majority_conf * 100.0

        motion_state = self.seg.step(hand_rel)
        result["motion"] = motion_state

        # 가령: 26/04/19 수정내용: 점수와 Top-3 를 모두 "프레임별 최고값(peak)" 으로 일치시킴
        #       + 타겟의 카테고리에 속한 라벨로만 Top-3 필터링
        if motion_state == "ready" and self.seg_probs:
            peak_base: Dict[str, float] = {}
            for p in self.seg_probs:
                base_p = self.service.aggregate_base(p)
                for lbl, v in base_p.items():
                    if v > peak_base.get(lbl, 0.0):
                        peak_base[lbl] = v

            allowed: set | None = None
            if category and subcategory:
                allowed = self.service.category_allowed.get(f"{category}:{subcategory}")
            if allowed is None and category:
                allowed = self.service.category_allowed.get(category)
            if allowed:
                peak_base = {l: v for l, v in peak_base.items() if l in allowed}

            top3 = sorted(peak_base.items(), key=lambda x: -x[1])[:3]
            result["segment_top3"] = [
                {"label": l, "prob": round(p * 100.0, 2)} for l, p in top3
            ]
            if target:
                score = self.seg_max_target_score
                result["score"] = round(score, 2)
                result["is_passed"] = score >= 80.0
                result["target"] = target
            self.seg_probs.clear()
            self.seg_max_target_score = 0.0

        return result
