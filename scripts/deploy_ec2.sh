#!/usr/bin/env bash
# 로컬에서 이미지를 빌드해 EC2 로 옮기고 docker compose 로 실행한다.
#
# 사용법 (프로젝트 루트에서):
#   KEY=~/경로/garyeong64.pem ./scripts/deploy_ec2.sh
#
# 환경변수
#   KEY        SSH 개인키 경로 (필수)
#   HOST       서버 주소 (기본: 16.178.1.25, 탄력적 IP)
#   SSH_USER   SSH 사용자 (기본: ubuntu)
#   VIDEO_DIR  수어 학습 영상 폴더 (기본: ~/Downloads/data/data_set, 없으면 건너뜀)
set -euo pipefail

KEY=${KEY:?KEY 에 SSH 개인키 경로를 지정하세요}
HOST=${HOST:-16.178.1.25}
SSH_USER=${SSH_USER:-ubuntu}
REMOTE_DIR=/opt/sign-backend
TARGET="$SSH_USER@$HOST"
SSH_OPTS=(-i "$KEY" -o StrictHostKeyChecking=accept-new)

echo "[1/5] 이미지 빌드 (linux/amd64)"
docker build --platform linux/amd64 -t sign-backend:latest .

echo "[2/5] 서버에 Docker 설치 확인"
ssh "${SSH_OPTS[@]}" "$TARGET" \
  'command -v docker >/dev/null || (sudo apt-get update -y && sudo apt-get install -y docker.io docker-compose-v2 && sudo systemctl enable --now docker)'

echo "[3/5] 설정 파일 업로드"
ssh "${SSH_OPTS[@]}" "$TARGET" "sudo mkdir -p $REMOTE_DIR && sudo chown \$USER $REMOTE_DIR"
scp "${SSH_OPTS[@]}" docker-compose.yml Caddyfile .env "$TARGET:$REMOTE_DIR/"
ssh "${SSH_OPTS[@]}" "$TARGET" "chmod 600 $REMOTE_DIR/.env"

VIDEO_DIR=${VIDEO_DIR:-$HOME/Downloads/data/data_set}
if [ -d "$VIDEO_DIR" ]; then
  echo "      수어 영상 동기화 ($VIDEO_DIR)"
  rsync -az --delete -e "ssh ${SSH_OPTS[*]}" "$VIDEO_DIR/" "$TARGET:$REMOTE_DIR/videos/"
else
  echo "      영상 폴더 없음, 건너뜀 ($VIDEO_DIR)"
  ssh "${SSH_OPTS[@]}" "$TARGET" "mkdir -p $REMOTE_DIR/videos"
fi

echo "[4/5] 이미지 전송"
docker save sign-backend:latest | gzip | ssh "${SSH_OPTS[@]}" "$TARGET" 'gunzip | sudo docker load'

echo "[5/5] 컨테이너 실행"
ssh "${SSH_OPTS[@]}" "$TARGET" "cd $REMOTE_DIR && sudo docker compose up -d && sudo docker image prune -f"

echo "완료: https://signlanguagelab.scarlett-project.cloud/sign/ (DNS 가 $HOST 를 가리켜야 인증서가 발급됩니다)"
