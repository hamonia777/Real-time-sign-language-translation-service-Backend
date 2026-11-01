# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# OpenCV / MediaPipe 런타임에 필요한 시스템 라이브러리
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# torch 는 CPU 빌드로 먼저 설치해 CUDA 의존성(수 GB) 다운로드를 피한다.
# requirements.txt 의 torch==2.9.1 핀과 버전이 같으므로 이후 pip install 에서 재설치되지 않는다.
RUN pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main ./main
COPY alembic ./alembic
COPY alembic.ini ./
COPY frontend ./frontend

# SIGN_VIDEO_DIR 미설정 시 frontend/videos 로 폴백하므로 디렉터리가 반드시 존재해야 한다.
RUN mkdir -p /app/frontend/videos

# .env 는 이미지에 포함하지 않는다. 실행 시 --env-file 로 주입한다.
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "main.main:app", "--host", "0.0.0.0", "--port", "8000"]
