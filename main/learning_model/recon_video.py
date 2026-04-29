# =============================================================================
# 실시간 웹캠 수어 인식 테스트
# =============================================================================

import os
import re
import cv2
import numpy as np
import torch
import torch.nn as nn
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    PoseLandmarker, PoseLandmarkerOptions,
    HandLandmarker, HandLandmarkerOptions,
    FaceLandmarker, FaceLandmarkerOptions,
    RunningMode
)
from PIL import ImageFont, ImageDraw, Image

# ============================================================
# 설정 (모델 경로 수정)
# ============================================================
MODEL_PATH = r"/Users/garyeong/Desktop/Real-time-sign-language-translation-service/models/video_model/sign_language_cnn_gru.pt"

MEDIAPIPE_MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mediapipe_models")
POSE_MODEL_PATH = os.path.join(MEDIAPIPE_MODEL_DIR, "pose_landmarker_lite.task")
HAND_MODEL_PATH = os.path.join(MEDIAPIPE_MODEL_DIR, "hand_landmarker.task")
FACE_MODEL_PATH = os.path.join(MEDIAPIPE_MODEL_DIR, "face_landmarker.task")
# ============================================================


# =============================================================================
# 랜드마크 연결 상수 및 그리기 헬퍼
# =============================================================================

HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17),
]

POSE_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,7),
    (0,4),(4,5),(5,6),(6,8),
    (9,10),
    (11,12),(11,13),(13,15),(15,17),(15,19),(15,21),(17,19),
    (12,14),(14,16),(16,18),(16,20),(16,22),(18,20),
    (11,23),(12,24),(23,24),(23,25),(24,26),(25,27),(26,28),
    (27,29),(28,30),(29,31),(30,32),(27,31),(28,32),
]


KOREAN_FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FONT_LARGE = ImageFont.truetype(KOREAN_FONT_PATH, 32)
FONT_MEDIUM = ImageFont.truetype(KOREAN_FONT_PATH, 28)
FONT_SMALL = ImageFont.truetype(KOREAN_FONT_PATH, 16)


def put_korean_text(frame, text, pos, font=FONT_LARGE, color=(0, 255, 0)):
    """PIL을 사용해 한국어 텍스트를 OpenCV 프레임에 그리기"""
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    draw.text(pos, text, font=font, fill=color)
    frame[:] = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def strip_label_suffix(label):
    """라벨에서 '_숫자' 접미사 제거 (예: '안녕하세요_1' -> '안녕하세요')"""
    return re.sub(r'_\d+$', '', label)


def draw_landmarks(frame, landmarks, connections, color=(0, 255, 0), radius=2, thickness=1):
    """OpenCV로 랜드마크와 연결선 그리기"""
    h, w = frame.shape[:2]
    points = []
    for lm in landmarks:
        px = int(lm.x * w)
        py = int(lm.y * h)
        points.append((px, py))
        cv2.circle(frame, (px, py), radius, color, -1)
    for (i, j) in connections:
        if i < len(points) and j < len(points):
            cv2.line(frame, points[i], points[j], color, thickness)


# =============================================================================
# 1. 모델 정의 (학습할 때와 동일한 구조)
# =============================================================================

class CnnGruModel(nn.Module):
    def __init__(self, input_dim=411, hidden_dim=128, num_layers=2,
                 num_classes=10, dropout=0.3):
        super(CnnGruModel, self).__init__()

        self.spatial = nn.Sequential(
            nn.Conv1d(input_dim, 256, 1),
            nn.BatchNorm1d(256),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Conv1d(256, hidden_dim, 1),
            nn.BatchNorm1d(hidden_dim),
            nn.ELU(),
        )

        self.temporal = nn.Sequential(
            nn.Conv1d(hidden_dim, hidden_dim, 3, padding=1),
            nn.BatchNorm1d(hidden_dim),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Conv1d(hidden_dim, hidden_dim, 3, padding=1),
            nn.BatchNorm1d(hidden_dim),
            nn.ELU(),
        )

        gru_dropout = dropout if num_layers > 1 else 0
        self.gru = nn.GRU(
            hidden_dim, hidden_dim, num_layers,
            batch_first=True, dropout=gru_dropout,
            bidirectional=True
        )

        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
            nn.Softmax(dim=1)
        )

        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes)
        )

    def forward(self, x):
        x = x.permute(0, 2, 1)
        x = self.spatial(x)
        x = self.temporal(x)
        x = x.permute(0, 2, 1)
        gru_output, _ = self.gru(x)
        attn = self.attention(gru_output)
        context = torch.sum(gru_output * attn, dim=1)
        output = self.classifier(context)
        return output


# =============================================================================
# 2. 모델 로드
# =============================================================================

def load_model(model_path):
    """학습된 모델 로드"""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    config = checkpoint['config']

    model = CnnGruModel(
        input_dim=config['input_dim'],
        hidden_dim=config['hidden_dim'],
        num_layers=config['num_layers'],
        num_classes=checkpoint['num_classes'],
        dropout=0
    ).to(device)

    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    # 정규화 파라미터 (차원 맞추기 - squeeze 적용)
    norm_params = {
        'mean': np.array(checkpoint['norm_params']['mean']).squeeze(),
        'std': np.array(checkpoint['norm_params']['std']).squeeze()
    }

    idx_to_label = checkpoint['idx_to_label']
    sequence_length = config['sequence_length']

    print("모델 로드 완료!")
    print("클래스 수:", checkpoint['num_classes'])
    print("시퀀스 길이:", sequence_length)

    return model, idx_to_label, norm_params, sequence_length, device


# =============================================================================
# 3. MediaPipe로 키포인트 추출 (411차원)
# =============================================================================

def extract_keypoints(pose_result, hand_result, face_result):
    """MediaPipe 결과에서 411차원 키포인트 추출"""

    # Pose (25 * 3 = 75)
    pose = np.zeros(75, dtype=np.float32)
    if pose_result.pose_landmarks and len(pose_result.pose_landmarks) > 0:
        for i, lm in enumerate(pose_result.pose_landmarks[0][:25]):
            pose[i*3] = lm.x
            pose[i*3 + 1] = lm.y
            pose[i*3 + 2] = lm.visibility

    # Face (70 * 3 = 210)
    face = np.zeros(210, dtype=np.float32)
    if face_result.face_landmarks and len(face_result.face_landmarks) > 0:
        for i, lm in enumerate(face_result.face_landmarks[0][:70]):
            face[i*3] = lm.x
            face[i*3 + 1] = lm.y
            face[i*3 + 2] = lm.z

    # Hands (21 * 3 = 63 each)
    hand_left = np.zeros(63, dtype=np.float32)
    hand_right = np.zeros(63, dtype=np.float32)

    if hand_result.hand_landmarks and len(hand_result.hand_landmarks) > 0:
        for idx, hand_landmarks in enumerate(hand_result.hand_landmarks):
            handedness = hand_result.handedness[idx][0].category_name
            hand_kp = np.zeros(63, dtype=np.float32)

            for i, lm in enumerate(hand_landmarks):
                hand_kp[i*3] = lm.x
                hand_kp[i*3 + 1] = lm.y
                hand_kp[i*3 + 2] = lm.z

            # 거울 모드라서 좌우 반전
            if handedness == 'Left':
                hand_right = hand_kp
            else:
                hand_left = hand_kp

    return np.concatenate([pose, face, hand_left, hand_right])


# =============================================================================
# 4. 실시간 웹캠 인식
# =============================================================================

def run_realtime_recognition():
    """실시간 웹캠 수어 인식"""

    # 모델 로드
    print("=" * 50)
    print("모델 로드 중...")
    print("=" * 50)
    model, idx_to_label, norm_params, sequence_length, device = load_model(MODEL_PATH)

    # MediaPipe 디텍터 초기화 (RunningMode.VIDEO)
    pose_detector = PoseLandmarker.create_from_options(
        PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=POSE_MODEL_PATH),
            running_mode=RunningMode.VIDEO,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    )

    hand_detector = HandLandmarker.create_from_options(
        HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=HAND_MODEL_PATH),
            running_mode=RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    )

    face_detector = FaceLandmarker.create_from_options(
        FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=FACE_MODEL_PATH),
            running_mode=RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    )

    # 키포인트 버퍼 (시퀀스 저장용)
    keypoint_buffer = []

    # 현재 예측 결과
    current_prediction = "Waiting..."
    current_confidence = 0.0

    # 프레임 타임스탬프 (ms 단위, 단조 증가 필요)
    frame_count = 0

    # 웹캠 열기
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("웹캠을 열 수 없습니다!")
        pose_detector.close()
        hand_detector.close()
        face_detector.close()
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_interval_ms = int(1000 / fps)

    print("\n" + "=" * 50)
    print("실시간 인식 시작!")
    print("'q' 키를 누르면 종료")
    print("=" * 50 + "\n")

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 좌우 반전 (거울 모드)
            frame = cv2.flip(frame, 1)

            # BGR -> RGB, mp.Image로 변환
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # 타임스탬프 계산 (단조 증가)
            timestamp_ms = frame_count * frame_interval_ms
            frame_count += 1

            # MediaPipe 처리
            pose_result = pose_detector.detect_for_video(mp_image, timestamp_ms)
            hand_result = hand_detector.detect_for_video(mp_image, timestamp_ms)
            face_result = face_detector.detect_for_video(mp_image, timestamp_ms)

            # 키포인트 추출 (411차원)
            keypoints = extract_keypoints(pose_result, hand_result, face_result)
            keypoint_buffer.append(keypoints)

            # 버퍼가 시퀀스 길이에 도달하면 예측
            if len(keypoint_buffer) >= sequence_length:
                # 최근 sequence_length개만 사용
                sequence = np.array(keypoint_buffer[-sequence_length:], dtype=np.float32)

                # 정규화 (이미 squeeze 적용됨)
                sequence = (sequence - norm_params['mean']) / norm_params['std']

                # 텐서 변환 및 예측
                input_tensor = torch.tensor(sequence, dtype=torch.float32)
                input_tensor = input_tensor.unsqueeze(0).to(device)

                with torch.no_grad():
                    output = model(input_tensor)
                    probs = torch.softmax(output, dim=1)
                    confidence, predicted_idx = torch.max(probs, dim=1)

                current_prediction = strip_label_suffix(idx_to_label[predicted_idx.item()])
                current_confidence = confidence.item()

                # 버퍼 절반 유지 (슬라이딩 윈도우)
                keypoint_buffer = keypoint_buffer[-sequence_length//2:]

            # =========== 화면에 표시 ===========

            # 손 랜드마크 그리기
            if hand_result.hand_landmarks:
                for hand_landmarks in hand_result.hand_landmarks:
                    draw_landmarks(frame, hand_landmarks, HAND_CONNECTIONS, color=(0, 255, 0))

            # 포즈 랜드마크 그리기
            if pose_result.pose_landmarks and len(pose_result.pose_landmarks) > 0:
                draw_landmarks(frame, pose_result.pose_landmarks[0], POSE_CONNECTIONS, color=(0, 128, 255))

            # 상단 배경 박스
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 120), (0, 0, 0), -1)

            # 버퍼 상태 프로그레스 바 (PIL 전에 OpenCV로 그리기)
            buffer_ratio = min(len(keypoint_buffer) / sequence_length, 1.0)
            bar_width = int(200 * buffer_ratio)
            cv2.rectangle(frame, (10, 100), (210, 115), (100, 100, 100), -1)
            cv2.rectangle(frame, (10, 100), (10 + bar_width, 115), (0, 255, 0), -1)

            # PIL로 한국어 텍스트 렌더링
            put_korean_text(frame, "예측: {}".format(current_prediction),
                           (10, 5), font=FONT_LARGE, color=(0, 255, 0))
            put_korean_text(frame, "신뢰도: {:.1f}%".format(current_confidence * 100),
                           (10, 45), font=FONT_MEDIUM, color=(0, 255, 255))
            put_korean_text(frame, "{}/{}".format(min(len(keypoint_buffer), sequence_length), sequence_length),
                           (220, 97), font=FONT_SMALL, color=(255, 255, 255))
            put_korean_text(frame, "'q' 종료",
                           (frame.shape[1] - 100, 5), font=FONT_SMALL, color=(200, 200, 200))

            # 화면 출력
            cv2.imshow('Sign Language Recognition', frame)

            # 'q' 누르면 종료
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        pose_detector.close()
        hand_detector.close()
        face_detector.close()
        cap.release()
        cv2.destroyAllWindows()

    print("\n인식 종료!")


# =============================================================================
# 실행
# =============================================================================

if __name__ == "__main__":
    run_realtime_recognition()
