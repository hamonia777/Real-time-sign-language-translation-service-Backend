"""
실시간 수어 문장 인식 스크립트 (Encoder-Decoder + Attention)

============================================================
파일 연결 구조:
============================================================
  sentance_model.ipynb  ──(학습)──▶  model_video.pt
                                           │
  sentance_recong.py (이 파일)  ◀──(로드)──┘
    │
    ├── 웹캠 열기
    ├── 's' 또는 SPACE → 15초 타이머 시작
    ├── 15초간 MediaPipe로 키포인트 추출 (411차원)
    ├── 시퀀스 전처리 + 정규화
    ├── 모델 추론 (Encoder-Decoder + Attention)
    └── 화면에 결과 표시

============================================================
가상환경 설정 및 실행 방법:
============================================================
  # 1. 프로젝트 루트로 이동
  cd /Users/garyeong/Desktop/Real-time-sign-language-translation-service

  # 2. 가상환경 활성화
  source .venv/bin/activate

  # 3. (최초 1회) 필요 패키지 설치
  pip install torch numpy opencv-python mediapipe pillow scikit-learn

  # 4. 실행
  python main/learning_model/recon_video.py

  # 5. 가상환경 비활성화 (사용 후)
  deactivate

============================================================
웹캠 조작:
============================================================
  SPACE 또는 's' : 15초 인식 시작
  'q'            : 종료

============================================================
주의: 아래 모델 클래스(Encoder, BahdanauAttention, Decoder,
      SentenceClassifier)는 sentance_model.ipynb과 반드시
      동일한 구조여야 합니다.
============================================================
"""

import cv2
import mediapipe as mp
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import time
import os
import re
import json
import glob
import unicodedata
import platform
import sys
from PIL import ImageFont, ImageDraw, Image


# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 26.05.07 : 가령 : 수정 내용 - 웹 문장 학습과 같은 교체 모델(model_video.pt)을 로드하도록 경로 변경
MODEL_PATH = os.path.join(SCRIPT_DIR, "model_video.pt")
KEYPOINTS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "..", "data", "문장_keypoints")

# 한글 폰트 (OS별)
if platform.system() == "Darwin":
    KOREAN_FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
elif platform.system() == "Windows":
    KOREAN_FONT_PATH = "C:/Windows/Fonts/malgun.ttf"
else:
    KOREAN_FONT_PATH = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

# 인식 시간 (초)
CAPTURE_DURATION = 15

# 프레임 샘플링 (학습 데이터와 동일하게 2프레임마다 1개)
FRAME_SAMPLE_RATE = 2


# ============================================================
# 1. 모델 아키텍처 (sentance_model.ipynb과 동일)
# ============================================================

class Encoder(nn.Module):
    """
    양방향 GRU 인코더
    - 시계열 키포인트 시퀀스를 입력받아 컨텍스트 표현으로 변환
    - 양방향이므로 출력 차원 = hidden_dim * 2
    """
    def __init__(self, input_dim=411, hidden_dim=256, num_layers=2, dropout=0.3):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ELU(),
            nn.Dropout(dropout),
        )

        self.gru = nn.GRU(
            hidden_dim, hidden_dim, num_layers,
            batch_first=True, bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )

        # 양방향 마지막 은닉 상태 → 디코더 초기 은닉 상태
        self.fc_hidden = nn.Linear(hidden_dim * 2, hidden_dim)

    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        x = self.input_proj(x)              # (batch, seq_len, hidden_dim)
        outputs, hidden = self.gru(x)       # outputs: (batch, seq_len, hidden_dim*2)
        # hidden: (num_layers*2, batch, hidden_dim)
        # 마지막 레이어의 forward/backward 결합
        forward_h = hidden[-2]              # (batch, hidden_dim)
        backward_h = hidden[-1]             # (batch, hidden_dim)
        decoder_init = torch.tanh(self.fc_hidden(
            torch.cat([forward_h, backward_h], dim=-1)
        ))  # (batch, hidden_dim)
        return outputs, decoder_init


class BahdanauAttention(nn.Module):
    """
    Bahdanau (Additive) 어텐션 메커니즘
    - 디코더 은닉 상태와 인코더 전체 출력 사이의 정렬 점수 계산
    - 긴 시퀀스에서 중요한 프레임에 집중
    """
    def __init__(self, enc_dim, dec_dim):
        super().__init__()
        self.W_enc = nn.Linear(enc_dim, dec_dim, bias=False)
        self.W_dec = nn.Linear(dec_dim, dec_dim, bias=False)
        self.V = nn.Linear(dec_dim, 1, bias=False)

    def forward(self, decoder_hidden, encoder_outputs):
        # decoder_hidden: (batch, dec_dim)
        # encoder_outputs: (batch, seq_len, enc_dim)
        score = self.V(torch.tanh(
            self.W_enc(encoder_outputs) +
            self.W_dec(decoder_hidden).unsqueeze(1)
        ))  # (batch, seq_len, 1)

        attn_weights = F.softmax(score, dim=1)                  # (batch, seq_len, 1)
        context = torch.sum(attn_weights * encoder_outputs, dim=1)  # (batch, enc_dim)
        return context, attn_weights.squeeze(-1)                # context, (batch, seq_len)


class Decoder(nn.Module):
    """
    GRU 디코더 + 어텐션 → 분류
    - decode_steps 만큼 반복하며 어텐션으로 인코더 출력 참조
    - 최종 은닉 상태 + 컨텍스트 벡터로 문장 분류
    """
    def __init__(self, enc_dim, dec_dim, num_classes, decode_steps=5, dropout=0.3):
        super().__init__()
        self.decode_steps = decode_steps

        self.attention = BahdanauAttention(enc_dim, dec_dim)
        self.gru_cell = nn.GRUCell(enc_dim, dec_dim)
        self.dropout = nn.Dropout(dropout)

        self.classifier = nn.Sequential(
            nn.Linear(dec_dim + enc_dim, dec_dim),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Linear(dec_dim, num_classes)
        )

    def forward(self, encoder_outputs, decoder_hidden):
        context = None
        attn_weights = None

        for step in range(self.decode_steps):
            context, attn_weights = self.attention(decoder_hidden, encoder_outputs)
            decoder_hidden = self.gru_cell(context, decoder_hidden)
            decoder_hidden = self.dropout(decoder_hidden)

        combined = torch.cat([decoder_hidden, context], dim=-1)
        logits = self.classifier(combined)
        return logits, attn_weights


class SentenceClassifier(nn.Module):
    """
    Encoder-Decoder + Attention 기반 수어 문장 분류 모델

    구조:
      입력 (batch, seq_len, 411)
        ↓
      [Encoder] 양방향 GRU → 인코더 출력 + 초기 은닉
        ↓
      [Attention + Decoder] GRU 디코더가 어텐션으로 인코더 참조
        ↓
      [Classifier] Softmax → 문장 클래스
    """
    def __init__(self, input_dim=411, hidden_dim=256, num_layers=2,
                 num_classes=3, decode_steps=5, dropout=0.3):
        super().__init__()
        enc_dim = hidden_dim * 2  # 양방향

        self.encoder = Encoder(input_dim, hidden_dim, num_layers, dropout)
        self.decoder = Decoder(enc_dim, hidden_dim, num_classes, decode_steps, dropout)

    def forward(self, x):
        encoder_outputs, decoder_init = self.encoder(x)
        logits, attn_weights = self.decoder(encoder_outputs, decoder_init)
        return logits, attn_weights


# ============================================================
# 2. KNN 실험용 유틸리티 (현재 웹/실시간 추론에는 사용하지 않음)
# ============================================================

SEQUENCE_LENGTH = 100

def extract_label(folder_name):
    """폴더명에서 문장 라벨 추출"""
    name = unicodedata.normalize('NFC', folder_name)
    name = re.sub(r'\(\d+\)$', '', name)
    name = re.sub(r'_\d+$', '', name)
    return name.rstrip('.?!')


def load_keypoints_from_json(json_path):
    """JSON에서 411차원 키포인트 로드"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'people' not in data or len(data['people']) == 0:
            return np.zeros(411, dtype=np.float32)
        p = data['people'][0]
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
        return np.zeros(411, dtype=np.float32)

    pose = np.zeros(75, dtype=np.float32)
    face = np.zeros(210, dtype=np.float32)
    hand_l = np.zeros(63, dtype=np.float32)
    hand_r = np.zeros(63, dtype=np.float32)

    raw = p.get('pose_keypoints_2d', [])
    if raw: pose[:min(len(raw), 75)] = np.array(raw[:75], dtype=np.float32)
    raw = p.get('face_keypoints_2d', [])
    if raw: face[:min(len(raw), 210)] = np.array(raw[:210], dtype=np.float32)
    raw = p.get('hand_left_keypoints_2d', [])
    if raw: hand_l[:min(len(raw), 63)] = np.array(raw[:63], dtype=np.float32)
    raw = p.get('hand_right_keypoints_2d', [])
    if raw: hand_r[:min(len(raw), 63)] = np.array(raw[:63], dtype=np.float32)

    return np.concatenate([pose, face, hand_l, hand_r])


def load_knn_database(data_dir, sequence_length):
    """학습 데이터를 KNN 비교용으로 로드"""
    data_dir = os.path.abspath(data_dir)
    if not os.path.exists(data_dir):
        print(f"데이터 폴더를 찾을 수 없습니다: {data_dir}")
        sys.exit(1)

    folders = sorted([d for d in os.listdir(data_dir)
                      if os.path.isdir(os.path.join(data_dir, d))])

    sequences = []
    labels = []

    for folder in folders:
        folder_path = os.path.join(data_dir, folder)
        json_files = sorted(glob.glob(os.path.join(folder_path, '*_keypoints.json')))
        if not json_files:
            continue

        kps_list = [load_keypoints_from_json(jf) for jf in json_files]
        arr = np.array(kps_list, dtype=np.float32)

        # 중앙 크롭 또는 패딩
        if len(arr) >= sequence_length:
            start = (len(arr) - sequence_length) // 2
            seq = arr[start:start + sequence_length]
        else:
            pad = sequence_length - len(arr)
            pad_b = pad // 2
            seq = np.concatenate([
                np.tile(arr[0:1], (pad_b, 1)), arr,
                np.tile(arr[-1:], (pad - pad_b, 1))
            ])

        sequences.append(seq)
        labels.append(extract_label(folder))

    # 전체 정규화 파라미터 계산
    all_data = np.array(sequences, dtype=np.float32)
    norm_mean = all_data.mean(axis=(0, 1))
    norm_std = all_data.std(axis=(0, 1)) + 1e-8

    # 정규화 적용
    normed = [(s - norm_mean) / norm_std for s in sequences]

    unique_labels = sorted(set(labels))
    print(f"KNN 데이터 로드 완료!")
    print(f"  총 시퀀스: {len(sequences)}개")
    print(f"  고유 문장: {len(unique_labels)}개")
    for i, ul in enumerate(unique_labels):
        cnt = labels.count(ul)
        print(f"    {i+1}. {ul} ({cnt}개)")

    return normed, labels, unique_labels, norm_mean, norm_std


def knn_predict(query_seq, db_sequences, db_labels, unique_labels, k=5):
    """
    KNN 추론: 웹캠 시퀀스와 학습 데이터 간 거리 비교

    Returns:
        (predicted_label, confidence, top3_list)
    """
    # 쿼리와 모든 DB 시퀀스 간 유클리드 거리
    distances = []
    for i, db_seq in enumerate(db_sequences):
        dist = np.linalg.norm(query_seq - db_seq)
        distances.append((dist, db_labels[i]))

    distances.sort(key=lambda x: x[0])

    # 상위 K개 투표
    top_k = distances[:k]
    votes = {}
    for dist, label in top_k:
        if label not in votes:
            votes[label] = 0
        votes[label] += 1

    # 결과 정리
    sorted_votes = sorted(votes.items(), key=lambda x: -x[1])
    best_label = sorted_votes[0][0]
    confidence = sorted_votes[0][1] / k

    # Top-3
    top3 = []
    for label, count in sorted_votes[:3]:
        top3.append((label, count / k))

    return best_label, confidence, top3


# ============================================================
# 3. MediaPipe 키포인트 추출 (411차원)
#    - Pose: 25 랜드마크 × 3 (x, y, visibility) = 75
#    - Face: 70 랜드마크 × 3 (x, y, z) = 210
#    - Left Hand: 21 랜드마크 × 3 (x, y, z) = 63
#    - Right Hand: 21 랜드마크 × 3 (x, y, z) = 63
#    → 총 411차원
# ============================================================

def extract_keypoints_from_frame(frame, pose, hands, face_mesh, mirror=True):
    """
    한 프레임에서 411차원 키포인트 추출

    Args:
        frame: BGR 이미지
        pose, hands, face_mesh: MediaPipe 인스턴스
        mirror: 웹캠 좌우반전 모드일 때 True (좌우 손 교환)

    Returns:
        np.ndarray: (411,) 키포인트 벡터
    """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    pose_results = pose.process(rgb_frame)
    hands_results = hands.process(rgb_frame)
    face_results = face_mesh.process(rgb_frame)

    # Pose (25 * 3 = 75)
    pose_kps = np.zeros(75, dtype=np.float32)
    if pose_results.pose_landmarks:
        for i in range(25):
            if i < len(pose_results.pose_landmarks.landmark):
                lm = pose_results.pose_landmarks.landmark[i]
                pose_kps[i*3] = lm.x
                pose_kps[i*3 + 1] = lm.y
                pose_kps[i*3 + 2] = lm.visibility

    # Face (70 * 3 = 210)
    face_kps = np.zeros(210, dtype=np.float32)
    if face_results.multi_face_landmarks:
        face_landmarks = face_results.multi_face_landmarks[0]
        for i in range(70):
            if i < len(face_landmarks.landmark):
                lm = face_landmarks.landmark[i]
                face_kps[i*3] = lm.x
                face_kps[i*3 + 1] = lm.y
                face_kps[i*3 + 2] = lm.z

    # Hands (21 * 3 = 63 × 2)
    left_kps = np.zeros(63, dtype=np.float32)
    right_kps = np.zeros(63, dtype=np.float32)

    if hands_results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(hands_results.multi_hand_landmarks):
            handedness = hands_results.multi_handedness[idx].classification[0].label
            kps = np.zeros(63, dtype=np.float32)
            for i, lm in enumerate(hand_landmarks.landmark):
                kps[i*3] = lm.x
                kps[i*3 + 1] = lm.y
                kps[i*3 + 2] = lm.z

            if mirror:
                # 거울 모드: MediaPipe의 Left → 실제 오른손 → right_kps
                if handedness == "Left":
                    right_kps = kps
                else:
                    left_kps = kps
            else:
                if handedness == "Left":
                    left_kps = kps
                else:
                    right_kps = kps

    return np.concatenate([pose_kps, face_kps, left_kps, right_kps])


# ============================================================
# 4. 시퀀스 전처리
# ============================================================

def preprocess_sequence(keypoints_list, sequence_length, norm_params):
    """
    수집된 키포인트 리스트를 모델 입력 텐서로 변환

    1. 균등 샘플링으로 sequence_length에 맞춤
    2. 정규화 (학습 시 사용된 mean/std 적용)
    3. PyTorch 텐서로 변환

    Args:
        keypoints_list: list of (411,) arrays
        sequence_length: 모델 시퀀스 길이
        norm_params: {'mean': ..., 'std': ...}

    Returns:
        torch.Tensor: (1, sequence_length, 411)
    """
    arr = np.array(keypoints_list, dtype=np.float32)  # (N, 411)

    if len(arr) == 0:
        return None

    # 중앙 크롭 또는 패딩 (학습 데이터와 동일한 방식)
    if len(arr) >= sequence_length:
        start = (len(arr) - sequence_length) // 2
        sequence = arr[start:start + sequence_length]
    else:
        pad_len = sequence_length - len(arr)
        pad_before = pad_len // 2
        pad_after = pad_len - pad_before
        sequence = np.concatenate([
            np.tile(arr[0:1], (pad_before, 1)),
            arr,
            np.tile(arr[-1:], (pad_after, 1))
        ])

    # 정규화
    sequence = (sequence - norm_params['mean']) / norm_params['std']

    # 텐서 변환 (배치 차원 추가)
    tensor = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0)
    return tensor


def load_sentence_model(model_path):
    """교체된 Encoder-Decoder 문장 모델과 정규화 파라미터를 로드"""
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    config = checkpoint["config"]

    model = SentenceClassifier(
        input_dim=config.get("input_dim", 411),
        hidden_dim=config.get("hidden_dim", 256),
        num_layers=config.get("num_layers", 2),
        num_classes=checkpoint["num_classes"],
        decode_steps=config.get("decode_steps", 5),
        dropout=0,
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    norm_mean = np.array(checkpoint["norm_params"]["mean"]).squeeze().astype(np.float32)
    norm_std = np.array(checkpoint["norm_params"]["std"]).squeeze().astype(np.float32)
    norm_std = np.where(norm_std < 1e-8, 1.0, norm_std)
    norm_params = {"mean": norm_mean, "std": norm_std}
    idx_to_label = {int(idx): label for idx, label in checkpoint["idx_to_label"].items()}

    return model, config, norm_params, idx_to_label, device


def predict_sentence_model(tensor, model, idx_to_label, device, top_k=3):
    """문장 모델 추론 후 Top-K 문장 결과를 반환"""
    if tensor is None:
        return "(키포인트 없음)", 0.0, []

    tensor = tensor.to(device)
    with torch.no_grad():
        logits, _ = model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0)
        values, indices = torch.topk(probs, k=min(top_k, probs.numel()))

    top_results = [
        (idx_to_label[int(idx.item())], float(value.item()))
        for value, idx in zip(values, indices)
    ]
    best_label, best_confidence = top_results[0]
    return best_label, best_confidence, top_results


# ============================================================
# 5. 한글 텍스트 표시
# ============================================================

def put_korean_text(frame, text, pos, font, color=(0, 255, 0)):
    """PIL을 사용하여 OpenCV 프레임에 한국어 텍스트 표시"""
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    draw.text(pos, text, font=font, fill=color)
    frame[:] = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# ============================================================
# 5-1. 키포인트 저장 (학습 데이터 수집)
# ============================================================

def save_keypoints_to_dataset(keypoint_buffer, sentence_label):
    """
    웹캠에서 수집한 키포인트를 문장_keypoints 폴더에 저장

    Args:
        keypoint_buffer: list of (411,) np arrays
        sentence_label: 문장 라벨 (예: '저는 프로그래머를 꿈꾸고 있습니다')

    Returns:
        str: 저장된 폴더 경로
    """
    base_dir = os.path.abspath(KEYPOINTS_DIR)
    os.makedirs(base_dir, exist_ok=True)

    # 기존 폴더 번호 확인하여 다음 번호 결정
    existing = [d for d in os.listdir(base_dir)
                if os.path.isdir(os.path.join(base_dir, d)) and d.startswith(sentence_label)]
    next_num = len(existing) + 1
    folder_name = f"{sentence_label}_{next_num:02d}"
    folder_path = os.path.join(base_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # 각 프레임을 JSON으로 저장
    for i, kps in enumerate(keypoint_buffer):
        keypoint_data = {
            "people": [{
                "pose_keypoints_2d": kps[:75].tolist(),
                "face_keypoints_2d": kps[75:285].tolist(),
                "hand_left_keypoints_2d": kps[285:348].tolist(),
                "hand_right_keypoints_2d": kps[348:411].tolist()
            }]
        }
        json_path = os.path.join(folder_path, f"{folder_name}_{i:06d}_keypoints.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(keypoint_data, f, ensure_ascii=False)

    print(f"저장 완료: {folder_path} ({len(keypoint_buffer)}프레임)")
    return folder_path


# ============================================================
# 6. 메인 실시간 인식 루프
# ============================================================

def run_realtime_recognition():
    """웹캠으로 15초간 수어 문장 인식 (Encoder-Decoder 기반)"""

    # --- 문장 모델 로드 ---
    print("=" * 60)
    print("수어 문장 인식 시스템 (Encoder-Decoder 기반)")
    print("=" * 60)
    model, config, norm_params, idx_to_label, device = load_sentence_model(MODEL_PATH)
    sequence_length = int(config.get("sequence_length", SEQUENCE_LENGTH))
    label_list = [idx_to_label[idx] for idx in sorted(idx_to_label)]
    print(f"모델 로드 완료: {MODEL_PATH}")
    print(f"  device: {device}")
    print(f"  sequence_length: {sequence_length}")
    print(f"  문장 클래스: {len(label_list)}개")
    for i, label in enumerate(label_list):
        print(f"    {i+1}. {label}")

    # --- 폰트 로드 ---
    try:
        font_large = ImageFont.truetype(KOREAN_FONT_PATH, 32)
        font_medium = ImageFont.truetype(KOREAN_FONT_PATH, 24)
        font_small = ImageFont.truetype(KOREAN_FONT_PATH, 18)
    except:
        print(f"폰트를 찾을 수 없습니다: {KOREAN_FONT_PATH}")
        print("시스템 기본 폰트를 사용합니다.")
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large

    # --- MediaPipe 초기화 ---
    mp_pose = mp.solutions.pose
    mp_hands = mp.solutions.hands
    mp_face_mesh = mp.solutions.face_mesh

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    # --- 웹캠 열기 ---
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("웹캠을 열 수 없습니다!")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    print(f"\n웹캠 FPS: {fps:.0f}")
    print(f"인식 시간: {CAPTURE_DURATION}초")
    print(f"프레임 샘플링: {FRAME_SAMPLE_RATE}프레임마다 1개")
    print(f"\n'SPACE' 또는 's'로 인식 시작, 'q'로 종료\n")

    print("\n[학습 데이터 수집 모드]")
    print("인식 결과 화면에서 숫자키(1~7)를 누르면 해당 문장으로 키포인트를 저장합니다:")
    for i, label in enumerate(label_list):
        print(f"  {i+1}. {label}")

    # --- 상태 변수 ---
    STATE_IDLE = 0          # 대기 중
    STATE_CAPTURING = 1     # 15초 캡처 중
    STATE_RESULT = 2        # 결과 표시 중

    state = STATE_IDLE
    keypoint_buffer = []
    capture_start_time = 0
    frame_count_in_capture = 0

    # 현재 결과
    result_label = ""
    result_confidence = 0.0
    result_top3 = []

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 좌우 반전 (거울 모드) — 화면 표시용만
            original_frame = frame.copy()       # 키포인트 추출용 (원본)
            frame = cv2.flip(frame, 1)          # 화면 표시용 (거울)
            display_frame = frame.copy()
            h, w = frame.shape[:2]

            # ===== 상태별 처리 =====

            if state == STATE_CAPTURING:
                elapsed = time.time() - capture_start_time
                remaining = max(0, CAPTURE_DURATION - elapsed)

                # 프레임 샘플링: FRAME_SAMPLE_RATE마다 1개
                if frame_count_in_capture % FRAME_SAMPLE_RATE == 0:
                    kps = extract_keypoints_from_frame(original_frame, pose, hands, face_mesh, mirror=False)
                    keypoint_buffer.append(kps)

                frame_count_in_capture += 1

                # 타이머 종료 → 문장 모델 추론
                if elapsed >= CAPTURE_DURATION:
                    print(f"\n수집 완료: {len(keypoint_buffer)}개 키포인트 프레임")

                    if len(keypoint_buffer) > 0:
                        tensor = preprocess_sequence(keypoint_buffer, sequence_length, norm_params)
                        result_label, result_confidence, result_top3 = predict_sentence_model(
                            tensor, model, idx_to_label, device, top_k=3
                        )

                        print(f"인식 결과: {result_label} ({result_confidence*100:.0f}%)")
                        print("Top-3:")
                        for i, (label, conf) in enumerate(result_top3):
                            print(f"  {i+1}. {label}: {conf*100:.0f}%")
                    else:
                        result_label = "(키포인트 없음)"
                        result_confidence = 0.0
                        result_top3 = []

                    state = STATE_RESULT

                # 캡처 중 화면 표시
                else:
                    # 빨간 테두리
                    cv2.rectangle(display_frame, (0, 0), (w-1, h-1), (0, 0, 255), 4)

                    # 타이머 바
                    progress = elapsed / CAPTURE_DURATION
                    bar_w = int(w * progress)
                    cv2.rectangle(display_frame, (0, h-20), (bar_w, h), (0, 0, 255), -1)

                    # 정보 표시
                    cv2.rectangle(display_frame, (0, 0), (w, 80), (0, 0, 0), -1)
                    put_korean_text(display_frame,
                                    f"인식 중... {remaining:.1f}초 남음",
                                    (10, 5), font_large, color=(0, 0, 255))
                    put_korean_text(display_frame,
                                    f"수집 프레임: {len(keypoint_buffer)}개",
                                    (10, 45), font_medium, color=(255, 255, 255))

            elif state == STATE_RESULT:
                # 결과 화면
                cv2.rectangle(display_frame, (0, 0), (w, 190), (0, 0, 0), -1)
                put_korean_text(display_frame,
                                f"결과: {result_label}",
                                (10, 5), font_large, color=(0, 255, 0))
                put_korean_text(display_frame,
                                f"신뢰도: {result_confidence*100:.1f}%",
                                (10, 45), font_medium, color=(0, 255, 255))
                for i, (label, conf) in enumerate(result_top3[:3]):
                    put_korean_text(display_frame,
                                    f"{i+1}위: {label} ({conf*100:.1f}%)",
                                    (10, 78 + i * 25), font_small, color=(255, 255, 255))
                put_korean_text(display_frame,
                                "SPACE: 다시 인식 | q: 종료",
                                (10, 155), font_small, color=(200, 200, 200))
                put_korean_text(display_frame,
                                "1~7: 정답 문장 번호로 키포인트 저장",
                                (10, 175), font_small, color=(255, 200, 0))

            else:
                # 대기 화면
                cv2.rectangle(display_frame, (0, 0), (w, 50), (0, 0, 0), -1)
                put_korean_text(display_frame,
                                "SPACE 또는 's': 15초 인식 시작 | 'q': 종료",
                                (10, 10), font_medium, color=(200, 200, 200))

            # 화면 출력
            cv2.imshow("Sign Language Sentence Recognition", display_frame)

            # 키 입력 처리
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break

            elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6'), ord('7')]:
                if state == STATE_RESULT and keypoint_buffer:
                    label_idx = key - ord('1')
                    if label_idx < len(label_list):
                        save_label = label_list[label_idx]
                        save_keypoints_to_dataset(keypoint_buffer, save_label)
                        print("키포인트 저장 완료: 모델 반영은 재학습 후 교체가 필요합니다.")

                        put_korean_text(display_frame,
                                        f"저장됨: {save_label}",
                                        (10, 140), font_medium, color=(0, 255, 255))
                        cv2.imshow("Sign Language Sentence Recognition", display_frame)
                        cv2.waitKey(1000)

            elif key == ord('s') or key == ord(' '):
                if state != STATE_CAPTURING:
                    # 15초 캡처 시작
                    state = STATE_CAPTURING
                    keypoint_buffer = []
                    capture_start_time = time.time()
                    frame_count_in_capture = 0
                    print(f"\n{'='*40}")
                    print(f"15초 인식 시작!")
                    print(f"{'='*40}")

    finally:
        pose.close()
        hands.close()
        face_mesh.close()
        cap.release()
        cv2.destroyAllWindows()

    print("\n인식 종료!")


# ============================================================
# 실행
# ============================================================
if __name__ == "__main__":
    run_realtime_recognition()
