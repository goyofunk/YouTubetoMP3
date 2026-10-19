# Windows 설치 파일 제작

## 개발 PC에서 소스 실행

프로젝트 루트의 `YouTube to MP3.cmd`는 개발 PC 전용 실행 파일입니다. 현재 `C:\Python314\pythonw.exe`로 `src\app.py`를 실행하며, 다른 개발 PC에서는 Python 경로를 맞춰야 합니다. 이 CMD는 일반 사용자에게 전달할 필요가 없습니다. 설치 EXE는 자체 실행 환경을 사용합니다.

## 설치 EXE 빌드

배포 대상은 64비트 Windows입니다. 설치 파일에는 Python, Tk, 앱, 아이콘, yt-dlp, FFmpeg, Deno가 포함됩니다. 사용자의 PC에 Python이 없어도 실행되며, 인터넷은 유튜브 다운로드와 도구 업데이트에 사용합니다.

일반 사용자는 GitHub Releases에서 `YouTube-to-MP3-1.0.1-Setup.exe`를 받아 실행합니다. 기본 설치 위치는 사용자 폴더의 `AppData\Local\Programs\YouTubeToMP3`입니다. 시작 메뉴에 실행·제거 바로가기를 만들고 Windows 설치된 앱 목록에 등록합니다. 다운로드한 음악은 설치 폴더 밖의 다운로드 폴더에 저장합니다.

개발 PC의 PowerShell에서 다음 순서로 빌드합니다.

```powershell
python -m venv .build-env
.\.build-env\Scripts\python.exe -m pip install pyinstaller==6.22.3
.\.build-env\Scripts\python.exe -B packaging\build_windows.py --version 1.0.1
```

설치 EXE는 프로젝트 루트에 생성되고, 체크섬은 `dist\SHA256SUMS.txt`에 기록됩니다. `dist\YouTube to MP3`는 설치 파일에 들어가는 앱 묶음입니다. 배포할 설치 EXE와 사용 설명서 `README.md`는 루트에 있습니다. 빌드에 필요한 도구가 없으면 공식 배포처에서 내려받습니다. 기존 빌드 출력은 자동 덮어쓰지 않습니다.

설치 파일 검증에서는 `/S /NOINTEGRATION /D=절대경로`로 프로젝트의 시험 폴더에 설치할 수 있습니다. `/NOINTEGRATION`은 시험 중 시작 메뉴와 제거 레지스트리를 변경하지 않는 내부 검증 옵션입니다. 일반 사용자는 이 옵션을 사용할 필요가 없습니다.

제거는 설치된 파일 목록만 대상으로 하며 다운로드한 음악은 삭제하지 않습니다. 빌드 시 환경변수·AI·에디터·Git 관련 파일이 배포 묶음에 포함되지 않았는지 검사합니다. 오픈소스 고지와 라이선스는 설치 폴더의 `THIRD_PARTY_NOTICES.txt`, `licenses`에 포함합니다.
