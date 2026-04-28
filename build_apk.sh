#!/bin/bash
# ============================================================
#  VideoVault Android APK 빌드 스크립트
#  방법 1: Docker (권장 — 환경 문제 없음)
#  방법 2: Ubuntu 직접 설치
# ============================================================

set -e

echo "============================================================"
echo "  VideoVault — Android APK Build"
echo "============================================================"
echo ""

# ── 방법 선택 ─────────────────────────────────────────────────
BUILD_METHOD="${1:-docker}"

if [ "$BUILD_METHOD" = "docker" ]; then
    echo ">> Docker 방법으로 빌드합니다."
    echo ""

    # Docker 설치 확인
    if ! command -v docker &>/dev/null; then
        echo "[오류] Docker가 설치되어 있지 않습니다."
        echo "  https://docs.docker.com/get-docker/ 에서 설치하세요."
        exit 1
    fi

    # Docker로 빌드
    docker run --rm \
        -v "$(pwd)":/home/user/hostcwd \
        --workdir /home/user/hostcwd \
        kivy/buildozer:latest \
        android debug

    echo ""
    echo "============================================================"
    if ls bin/*.apk 2>/dev/null | head -1; then
        echo "  APK 빌드 성공!"
        ls -lh bin/*.apk
    fi
    echo "============================================================"

elif [ "$BUILD_METHOD" = "local" ]; then
    echo ">> 로컬 Ubuntu 환경에서 빌드합니다."
    echo ""

    # OS 확인
    if [[ "$(uname)" != "Linux" ]]; then
        echo "[오류] 로컬 빌드는 Ubuntu/Linux에서만 가능합니다."
        echo "  Docker 방법을 사용하세요: ./build_apk.sh docker"
        exit 1
    fi

    # 의존성 설치
    echo "[1/4] 시스템 패키지 설치..."
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends \
        python3-pip \
        python3-venv \
        git \
        zip \
        unzip \
        openjdk-17-jdk \
        autoconf \
        libtool \
        pkg-config \
        zlib1g-dev \
        libncurses5-dev \
        libncursesw5-dev \
        libtinfo5 \
        cmake \
        libffi-dev \
        libssl-dev \
        build-essential \
        ccache \
        ffmpeg \
        libsdl2-dev \
        libsdl2-image-dev \
        libsdl2-mixer-dev \
        libsdl2-ttf-dev \
        2>/dev/null

    echo ""
    echo "[2/4] Python 가상환경 및 buildozer 설치..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip wheel
    pip install buildozer cython kivymd

    echo ""
    echo "[3/4] Android SDK/NDK 자동 설치 및 APK 빌드..."
    echo "  (첫 빌드는 SDK/NDK 다운로드로 20-40분 소요됩니다)"
    echo ""
    buildozer android debug

    echo ""
    echo "============================================================"
    if ls bin/*.apk 2>/dev/null | head -1; then
        echo "  APK 빌드 성공!"
        ls -lh bin/*.apk
        echo ""
        echo "  설치 명령:"
        echo "  adb install bin/videovault-1.0.0-arm64-v8a-debug.apk"
    fi
    echo "============================================================"

else
    echo "사용법: ./build_apk.sh [docker|local]"
    echo ""
    echo "  docker : Docker 컨테이너로 빌드 (권장)"
    echo "  local  : Ubuntu 로컬 환경에서 빌드"
    exit 1
fi
