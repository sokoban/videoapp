# VideoVault Android — APK 빌드 가이드

## ⚠️ 중요: 왜 별도 버전인가?

**PyQt6는 Android를 지원하지 않습니다.**
Android APK를 만들려면 Python Android 프레임워크인
**Kivy + KivyMD**로 UI를 다시 작성해야 합니다.

---

## 파일 구조

```
VideoVault_Android/
├── main.py                          ← Kivy 앱 소스
├── buildozer.spec                   ← APK 빌드 설정
├── build_apk.sh                     ← 빌드 스크립트
└── .github/workflows/build.yml     ← GitHub Actions 자동 빌드
```

---

## APK 빌드 방법 (3가지)

### 방법 1: GitHub Actions (가장 쉬움 — PC 사양 무관)

1. GitHub에 이 폴더를 repository로 push
2. Actions 탭 → "Build Android APK" → "Run workflow"
3. 완료 후 Artifacts에서 APK 다운로드

```bash
git init
git add .
git commit -m "VideoVault Android"
git remote add origin https://github.com/YOUR_NAME/videovault-android.git
git push -u origin main
```

### 방법 2: Docker (로컬 빌드, 권장)

```bash
# Docker 설치 후:
chmod +x build_apk.sh
./build_apk.sh docker
```

완료 후 `bin/` 폴더에 APK 생성

### 방법 3: Ubuntu 직접 빌드

```bash
chmod +x build_apk.sh
./build_apk.sh local
```

---

## Android 기기에 설치

```bash
# USB 디버깅 켜고 연결 후:
adb install bin/videovault-1.0.0-arm64-v8a-debug.apk
```

또는 APK 파일을 기기로 복사 후 직접 설치
(설정 → 보안 → 출처를 알 수 없는 앱 허용)

---

## Android 버전 구현 기능

| 기능 | 상태 |
|---|---|
| 폴더 선택 & 재귀 스캔 | ✅ |
| 동영상 목록 (파일명 정렬) | ✅ |
| 파일 크기 · 수정일 표시 | ✅ |
| 실시간 검색 | ✅ |
| 동영상 재생 | ✅ |
| 재생 컨트롤 (재생/정지/탐색) | ✅ |
| 볼륨 조절 | ✅ |
| 스캔 결과 저장 (앱 재시작 후 복원) | ✅ |
| Android 권한 요청 | ✅ |

---

## 빌드 시간 및 요구사항

| 항목 | 내용 |
|---|---|
| 첫 빌드 시간 | 20~40분 (SDK/NDK 다운로드 포함) |
| 이후 빌드 | 3~8분 |
| 디스크 공간 | ~10GB |
| 메모리 | 최소 8GB RAM |
| APK 크기 | 약 30~50MB |

---

## 자주 묻는 문제

### "SDK license not accepted"
```bash
# buildozer.spec에 이미 포함됨:
android.accept_sdk_license = True
```

### "Build failed: NDK not found"
```bash
# buildozer 캐시 초기화 후 재시도:
buildozer android clean
buildozer android debug
```

### Android 12+ 에서 외부 저장소 접근 안 됨
Android 13부터 `READ_MEDIA_VIDEO` 권한이 필요합니다.
`buildozer.spec`에 이미 포함되어 있습니다.
