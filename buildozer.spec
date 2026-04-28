[app]

# 앱 기본 정보
title = VideoVault
package.name = videovault
package.domain = org.videovault
version = 1.0.0

# 소스 파일
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.include_patterns = assets/*,images/*
source.exclude_dirs = tests, bin, build

# 메인 파일
main.py = main.py

# ── 의존 패키지 ──────────────────────────────
requirements =
    python3==3.11.6,
    kivy==2.2.1,
    kivymd==1.1.1,
    android,
    pillow,
    charset-normalizer

# ── Android 설정 ─────────────────────────────
# 타겟 Android API
android.api = 33
android.minapi = 24
android.ndk = 25b
android.sdk = 33

# 아키텍처 (arm64-v8a 단독 권장 — 용량 작음)
android.archs = arm64-v8a, armeabi-v7a

# 권한
android.permissions =
    android.permission.READ_EXTERNAL_STORAGE,
    android.permission.WRITE_EXTERNAL_STORAGE,
    android.permission.READ_MEDIA_VIDEO,
    android.permission.INTERNET

# 화면 방향 (세로/가로 모두 허용)
orientation = all

# 풀스크린 (상태바 제거)
fullscreen = 0

# 아이콘 및 스플래시
#android.icon = assets/icon.png
#android.presplash = assets/presplash.png
android.presplash_color = #0d1117

# Gradle 버전
android.gradle_dependencies =

# Java SDK
android.accept_sdk_license = True

# ── Buildozer 설정 ───────────────────────────
[buildozer]

# 빌드 디렉토리
build_dir = .buildozer

# 로그 레벨: 0=오류만, 1=정보, 2=디버그
log_level = 2

# 경고를 오류로 처리 안 함
warn_on_root = 1
