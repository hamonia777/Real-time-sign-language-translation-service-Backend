"""
지문자 실시간 인식 서비스.
- 학습된 .pt 모델 로드
- BGR 프레임 -> mediapipe 키포인트 추출 -> Top-3 예측 반환
- WebSocket 요청 처리 시 싱글톤으로 재사용
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import List, Tuple

import numpy as np

POSE_DIM = 75
FACE_DIM = 210
HAND_DIM = 63
TOTAL_DIM = 411

POSE_WEIGHT = 0.005
FACE_WEIGHT = 0.005
HAND_WEIGHT = 0.99

_MODEL_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "learning_model"
    / "model_fingerspell.pt"
)


class RecognitionService:
    _instance: "RecognitionService | None" = None
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
        print(f"[RecognitionService] device={self.device}")
        print(f"[RecognitionService] loading model: {_MODEL_PATH}")

        checkpoint = torch.load(
            str(_MODEL_PATH), map_location=self.device, weights_only=False
        )

        self.num_classes = checkpoint["num_classes"]
        self.idx_to_label = checkpoint["idx_to_label"]
        self.norm_mean = checkpoint["norm_params"]["mean"].to(self.device)
        self.norm_std = checkpoint["norm_params"]["std"].to(self.device)

        self.model = self._build_model(
            input_size=TOTAL_DIM, num_classes=self.num_classes
        )
        self.model.load_state_dict(checkpoint["model_kp_state"])
        self.model = self.model.to(self.device)
        self.model.eval()
        # warmup BatchNorm with eval-mode forward on dummy input
        with torch.no_grad():
            dummy = torch.zeros(1, TOTAL_DIM, device=self.device)
            self.model(dummy)

        self.mp_pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            min_detection_confidence=0.5,
        )
        self.mp_hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=0,
            min_detection_confidence=0.5,
        )
        self.mp_face = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
        )
        self._infer_lock = threading.Lock()

        print(
            f"[RecognitionService] ready. num_classes={self.num_classes} "
            f"labels={list(self.idx_to_label.values())}"
        )

    def _build_model(self, input_size: int, num_classes: int):
        nn = self.nn

        class KeypointClassifier(nn.Module):
            def __init__(self):
                super().__init__()
                self.model = nn.Sequential(
                    nn.Linear(input_size, 512),
                    nn.BatchNorm1d(512),
                    nn.ReLU(),
                    nn.Dropout(0.0),
                    nn.Linear(512, 256),
                    nn.BatchNorm1d(256),
                    nn.ReLU(),
                    nn.Dropout(0.0),
                    nn.Linear(256, 128),
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    nn.Dropout(0.0),
                    nn.Linear(128, 64),
                    nn.BatchNorm1d(64),
                    nn.ReLU(),
                    nn.Dropout(0.0),
                    nn.Linear(64, num_classes),
                )

            def forward(self, x):
                return self.model(x)

        return KeypointClassifier()

    @classmethod
    def instance(cls) -> "RecognitionService":
        with cls._lock:
            if cls._instance is None:
                cls._instance = RecognitionService()
            return cls._instance

    def extract_keypoints(self, bgr_frame: np.ndarray) -> Tuple[np.ndarray, bool]:
        import cv2

        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)

        pose_res = self.mp_pose.process(rgb)
        hand_res = self.mp_hands.process(rgb)
        face_res = self.mp_face.process(rgb)

        pose_kps: List[float] = []
        if pose_res.pose_landmarks:
            for i in range(25):
                lm = pose_res.pose_landmarks.landmark[i]
                pose_kps.extend([lm.x, lm.y, lm.visibility])
        else:
            pose_kps = [0.0] * POSE_DIM

        face_kps: List[float] = []
        if face_res.multi_face_landmarks:
            fl = face_res.multi_face_landmarks[0]
            for i in range(70):
                if i < len(fl.landmark):
                    lm = fl.landmark[i]
                    face_kps.extend([lm.x, lm.y, lm.z])
                else:
                    face_kps.extend([0.0, 0.0, 0.0])
        else:
            face_kps = [0.0] * FACE_DIM

        left_hand = [0.0] * HAND_DIM
        right_hand = [0.0] * HAND_DIM
        hand_detected = False

        if hand_res.multi_hand_landmarks:
            for idx, lms in enumerate(hand_res.multi_hand_landmarks):
                side = hand_res.multi_handedness[idx].classification[0].label
                kps = []
                for lm in lms.landmark:
                    kps.extend([lm.x, lm.y, lm.z])
                if side == "Left":
                    left_hand = kps
                    hand_detected = True
                elif side == "Right":
                    right_hand = kps
                    hand_detected = True

        combined = np.concatenate(
            [
                np.array(pose_kps, dtype=np.float32),
                np.array(face_kps, dtype=np.float32),
                np.array(left_hand, dtype=np.float32),
                np.array(right_hand, dtype=np.float32),
            ]
        ).astype(np.float32)

        return combined, hand_detected

    def _apply_weights(self, kp: np.ndarray) -> np.ndarray:
        out = kp.copy()
        out[0:POSE_DIM] *= POSE_WEIGHT
        out[POSE_DIM : POSE_DIM + FACE_DIM] *= FACE_WEIGHT
        out[POSE_DIM + FACE_DIM : POSE_DIM + FACE_DIM + HAND_DIM] *= HAND_WEIGHT
        out[POSE_DIM + FACE_DIM + HAND_DIM : TOTAL_DIM] *= HAND_WEIGHT
        return out

    def predict_top3(self, keypoints: np.ndarray) -> List[Tuple[str, float]]:
        torch = self.torch
        weighted = self._apply_weights(keypoints)
        x = torch.tensor(weighted, dtype=torch.float32).unsqueeze(0).to(self.device)
        x = (x - self.norm_mean) / self.norm_std

        with self._infer_lock, torch.no_grad():
            logits = self.model(x)
            probs = torch.softmax(logits, dim=1)
            top3_probs, top3_idx = torch.topk(probs, 3)

        results: List[Tuple[str, float]] = []
        for i in range(3):
            idx = top3_idx[0][i].item()
            prob = top3_probs[0][i].item() * 100.0
            results.append((self.idx_to_label[idx], prob))
        return results

    def predict_from_frame(self, bgr_frame: np.ndarray):
        import cv2

        kp, hand_detected = self.extract_keypoints(bgr_frame)
        kp_flip, hand_detected_flip = self.extract_keypoints(cv2.flip(bgr_frame, 1))

        if not hand_detected and not hand_detected_flip:
            return {"hand_detected": False, "top3": []}

        candidates: List[List[Tuple[str, float]]] = []
        if hand_detected:
            candidates.append(self.predict_top3(kp))
        if hand_detected_flip:
            candidates.append(self.predict_top3(kp_flip))

        top3 = max(candidates, key=lambda c: c[0][1])
        return {
            "hand_detected": True,
            "top3": [{"label": lbl, "prob": round(p, 2)} for lbl, p in top3],
        }
