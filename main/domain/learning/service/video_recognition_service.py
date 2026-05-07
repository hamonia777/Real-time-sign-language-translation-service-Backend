from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import List

import numpy as np


MODEL_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "learning_model"
    / "model_video.pt"
)
POSE_DIM = 75
FACE_DIM = 210
HAND_DIM = 63
TOTAL_DIM = 411
SENTENCE_PASS_THRESHOLD = 60.0

# 26.05.07 : 가령 : 수정 내용 - DB 문장명과 문장 모델 라벨명이 다른 항목을 같은 정답으로 처리
LESSON_TO_MODEL_SENTENCE_ALIASES = {
    "저는 프로그래머를 꿈꿉니다": ["저는 프로그래머를 꿈꾸고 있습니다"],
    "웹 사이트 제작 경험이 있습니다": ["웹사이트 제작 경험이 있습니다"],
    "결과는 언제 알 수 있을까요?": ["결과는 언제 알 수 있나요"],
    "오늘 제 역량을 보여드릴 기회를 주셔서 정말 감사합니다": [
        "오늘 제 역량을 보여드릴 기회를 주셔서 정말 감사합니다. 꼭 다시 뵙고 싶습니다"
    ],
}


def _normalize_sentence(label: str) -> str:
    return re.sub(r"[\s.?!。！？]+", "", label.strip())


def _target_variants(target: str | None) -> set[str]:
    if not isinstance(target, str) or not target.strip():
        return set()

    target = target.strip()
    variants = {target}
    variants.update(LESSON_TO_MODEL_SENTENCE_ALIASES.get(target, []))

    for lesson_label, model_labels in LESSON_TO_MODEL_SENTENCE_ALIASES.items():
        if target in model_labels:
            variants.add(lesson_label)
            variants.update(model_labels)

    return {v for v in variants if v}


def _is_target_label(label: str, target: str | None) -> bool:
    variants = _target_variants(target)
    if not variants:
        return False

    normalized_label = _normalize_sentence(label)
    return label in variants or normalized_label in {
        _normalize_sentence(variant) for variant in variants
    }


class VideoRecognitionService:
    _instance: "VideoRecognitionService | None" = None
    _lock = threading.Lock()

    def __init__(self):
        import mediapipe as mp
        import torch
        import torch.nn as nn
        import torch.nn.functional as F

        class _Encoder(nn.Module):
            def __init__(self, input_dim=411, hidden_dim=256, num_layers=2, dropout=0.3):
                super().__init__()
                self.input_proj = nn.Sequential(
                    nn.Linear(input_dim, hidden_dim),
                    nn.ELU(),
                    nn.Dropout(dropout),
                )
                self.gru = nn.GRU(
                    hidden_dim,
                    hidden_dim,
                    num_layers,
                    batch_first=True,
                    bidirectional=True,
                    dropout=dropout if num_layers > 1 else 0,
                )
                self.fc_hidden = nn.Linear(hidden_dim * 2, hidden_dim)

            def forward(self, x):
                x = self.input_proj(x)
                outputs, hidden = self.gru(x)
                forward_h = hidden[-2]
                backward_h = hidden[-1]
                decoder_init = torch.tanh(
                    self.fc_hidden(torch.cat([forward_h, backward_h], dim=-1))
                )
                return outputs, decoder_init

        class _BahdanauAttention(nn.Module):
            def __init__(self, enc_dim, dec_dim):
                super().__init__()
                self.W_enc = nn.Linear(enc_dim, dec_dim, bias=False)
                self.W_dec = nn.Linear(dec_dim, dec_dim, bias=False)
                self.V = nn.Linear(dec_dim, 1, bias=False)

            def forward(self, decoder_hidden, encoder_outputs):
                score = self.V(
                    torch.tanh(
                        self.W_enc(encoder_outputs)
                        + self.W_dec(decoder_hidden).unsqueeze(1)
                    )
                )
                attn_weights = F.softmax(score, dim=1)
                context = torch.sum(attn_weights * encoder_outputs, dim=1)
                return context, attn_weights.squeeze(-1)

        class _Decoder(nn.Module):
            def __init__(self, enc_dim, dec_dim, num_classes, decode_steps=5, dropout=0.3):
                super().__init__()
                self.decode_steps = decode_steps
                self.attention = _BahdanauAttention(enc_dim, dec_dim)
                self.gru_cell = nn.GRUCell(enc_dim, dec_dim)
                self.dropout = nn.Dropout(dropout)
                self.classifier = nn.Sequential(
                    nn.Linear(dec_dim + enc_dim, dec_dim),
                    nn.ELU(),
                    nn.Dropout(dropout),
                    nn.Linear(dec_dim, num_classes),
                )

            def forward(self, encoder_outputs, decoder_hidden):
                context = None
                attn_weights = None
                for _ in range(self.decode_steps):
                    context, attn_weights = self.attention(decoder_hidden, encoder_outputs)
                    decoder_hidden = self.gru_cell(context, decoder_hidden)
                    decoder_hidden = self.dropout(decoder_hidden)
                combined = torch.cat([decoder_hidden, context], dim=-1)
                return self.classifier(combined), attn_weights

        class _SentenceClassifier(nn.Module):
            def __init__(
                self,
                input_dim=411,
                hidden_dim=256,
                num_layers=2,
                num_classes=3,
                decode_steps=5,
                dropout=0.3,
            ):
                super().__init__()
                enc_dim = hidden_dim * 2
                self.encoder = _Encoder(input_dim, hidden_dim, num_layers, dropout)
                self.decoder = _Decoder(
                    enc_dim, hidden_dim, num_classes, decode_steps, dropout
                )

            def forward(self, x):
                encoder_outputs, decoder_init = self.encoder(x)
                return self.decoder(encoder_outputs, decoder_init)

        self.mp = mp
        self.torch = torch
        self.device = torch.device(
            "mps" if torch.backends.mps.is_available() else "cpu"
        )

        checkpoint = torch.load(str(MODEL_PATH), map_location=self.device, weights_only=False)
        config = checkpoint["config"]
        self.sequence_length = int(config.get("sequence_length", 100))
        self.model = _SentenceClassifier(
            input_dim=int(config.get("input_dim", TOTAL_DIM)),
            hidden_dim=int(config.get("hidden_dim", 256)),
            num_layers=int(config.get("num_layers", 2)),
            num_classes=int(checkpoint["num_classes"]),
            decode_steps=int(config.get("decode_steps", 5)),
            dropout=0,
        ).to(self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

        self.idx_to_label = {
            int(idx): label for idx, label in checkpoint["idx_to_label"].items()
        }
        self.supported_labels = set(self.idx_to_label.values())
        self.norm_mean = (
            np.array(checkpoint["norm_params"]["mean"]).squeeze().astype(np.float32)
        )
        self.norm_std = (
            np.array(checkpoint["norm_params"]["std"]).squeeze().astype(np.float32)
        )
        self.norm_std = np.where(self.norm_std < 1e-8, 1.0, self.norm_std)

        self.pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.face = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._infer_lock = threading.Lock()

    @classmethod
    def instance(cls) -> "VideoRecognitionService":
        with cls._lock:
            if cls._instance is None:
                cls._instance = VideoRecognitionService()
            return cls._instance

    def extract_keypoints(self, bgr_frame: np.ndarray) -> tuple[np.ndarray, bool]:
        import cv2

        # 26.05.07 : 가령 : 수정 내용 - 화면 미러링과 분리해 서버 추론은 원본 프레임 기준으로 처리
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        pose_res = self.pose.process(rgb)
        hand_res = self.hands.process(rgb)
        face_res = self.face.process(rgb)

        pose = np.zeros(POSE_DIM, dtype=np.float32)
        if pose_res.pose_landmarks:
            for i, lm in enumerate(pose_res.pose_landmarks.landmark[:25]):
                pose[i * 3] = lm.x
                pose[i * 3 + 1] = lm.y
                pose[i * 3 + 2] = lm.visibility

        face = np.zeros(FACE_DIM, dtype=np.float32)
        if face_res.multi_face_landmarks:
            for i, lm in enumerate(face_res.multi_face_landmarks[0].landmark[:70]):
                face[i * 3] = lm.x
                face[i * 3 + 1] = lm.y
                face[i * 3 + 2] = lm.z

        hand_left = np.zeros(HAND_DIM, dtype=np.float32)
        hand_right = np.zeros(HAND_DIM, dtype=np.float32)
        hand_detected = False
        if hand_res.multi_hand_landmarks:
            for idx, lms in enumerate(hand_res.multi_hand_landmarks):
                side = hand_res.multi_handedness[idx].classification[0].label
                hand = []
                for lm in lms.landmark:
                    hand.extend([lm.x, lm.y, lm.z])

                if side == "Left":
                    hand_left = np.array(hand, dtype=np.float32)
                else:
                    hand_right = np.array(hand, dtype=np.float32)
                hand_detected = True

        keypoints = np.concatenate([pose, face, hand_left, hand_right]).astype(np.float32)
        return keypoints, hand_detected

    def _fit_sequence(self, keypoints: List[np.ndarray]) -> np.ndarray:
        arr = np.array(keypoints, dtype=np.float32)
        if len(arr) >= self.sequence_length:
            start = (len(arr) - self.sequence_length) // 2
            sequence = arr[start : start + self.sequence_length]
        else:
            pad_len = self.sequence_length - len(arr)
            pad_before = pad_len // 2
            pad_after = pad_len - pad_before
            sequence = np.concatenate(
                [
                    np.tile(arr[0:1], (pad_before, 1)),
                    arr,
                    np.tile(arr[-1:], (pad_after, 1)),
                ]
            )

        return (sequence - self.norm_mean) / self.norm_std

    def predict_sequence(self, keypoints: List[np.ndarray]) -> tuple[list[dict], list[dict]]:
        torch = self.torch
        sequence = self._fit_sequence(keypoints)
        x = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0).to(self.device)

        with self._infer_lock, torch.no_grad():
            logits, _ = self.model(x)
            probs = torch.softmax(logits, dim=1).squeeze(0).detach().cpu().numpy()

        all_scores = [
            {"label": self.idx_to_label[idx], "prob": float(prob * 100.0)}
            for idx, prob in enumerate(probs)
        ]
        all_scores.sort(key=lambda item: -item["prob"])
        return all_scores[:3], all_scores


class VideoSession:
    def __init__(self, service: VideoRecognitionService):
        self.service = service
        self.keypoint_buffer: List[np.ndarray] = []
        self.hand_frame_count = 0

    def reset(self) -> None:
        self.keypoint_buffer = []
        self.hand_frame_count = 0

    def process_frame(self, bgr_frame: np.ndarray) -> dict:
        keypoints, hand_detected = self.service.extract_keypoints(bgr_frame)
        self.keypoint_buffer.append(keypoints)
        if hand_detected:
            self.hand_frame_count += 1

        return {
            "hand_detected": hand_detected,
            "buffer_count": len(self.keypoint_buffer),
            "sequence_length": self.service.sequence_length,
        }

    def finish(self, target_sentence: str | None = None) -> dict:
        if not self.keypoint_buffer:
            return {
                "hand_detected": False,
                "buffer_count": 0,
                "sequence_length": self.service.sequence_length,
                "target": target_sentence,
                "top3": [],
                "score": 0.0,
                "is_passed": False,
                "target_in_model": False,
                "matched_label": None,
            }

        top3, all_scores = self.service.predict_sequence(self.keypoint_buffer)
        matched_score = 0.0
        matched_label = None

        if target_sentence:
            for item in all_scores:
                if _is_target_label(item["label"], target_sentence):
                    matched_score = item["prob"]
                    matched_label = item["label"]
                    break
        elif top3:
            matched_score = top3[0]["prob"]
            matched_label = top3[0]["label"]

        score = round(matched_score, 2)
        target_in_model = bool(matched_label) if target_sentence else True

        return {
            "hand_detected": self.hand_frame_count > 0,
            "buffer_count": len(self.keypoint_buffer),
            "sequence_length": self.service.sequence_length,
            "target": target_sentence,
            "top3": [
                {"label": item["label"], "prob": round(item["prob"], 2)}
                for item in top3
            ],
            "score": score,
            "is_passed": score >= SENTENCE_PASS_THRESHOLD,
            "target_in_model": target_in_model,
            "matched_label": matched_label,
        }
