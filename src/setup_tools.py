"""Install official release assets locally, verifying GitHub SHA256 digests."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import urllib.request
import zipfile
from runtime_paths import TOOLS_DIR

TOOLS = TOOLS_DIR
SPECS = [
    ('yt-dlp/yt-dlp-nightly-builds', 'yt-dlp.exe', ['yt-dlp.exe']),
    ('yt-dlp/FFmpeg-Builds', 'ffmpeg-master-latest-win64-gpl-shared.zip', ['ffmpeg.exe', 'ffprobe.exe']),
    ('denoland/deno', 'deno-x86_64-pc-windows-msvc.zip', ['deno.exe']),
]

def request(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Goyo-MP3'}), timeout=30)

def install(log=print, cancel=None, update=False):
    TOOLS.mkdir(exist_ok=True)
    for repo, name, required in SPECS:
        if cancel and cancel.is_set():
            raise InterruptedError('준비를 중지했습니다.')
        if not update and all((TOOLS / p).is_file() for p in required):
            continue
        log(f'{repo} 공식 배포 확인 중…')
        with request(f'https://api.github.com/repos/{repo}/releases/latest') as response:
            release = json.load(response)
        asset = next(a for a in release['assets'] if a['name'] == name)
        digest = asset.get('digest', '')
        if not digest or not digest.startswith('sha256:'):
            raise RuntimeError(f'{name}: 공식 SHA256 정보가 없어 설치를 중단했습니다.')
        with tempfile.TemporaryDirectory(dir=TOOLS) as temporary:
            archive = Path(temporary) / name
            hasher = hashlib.sha256()
            received, last = 0, -1
            with request(asset['browser_download_url']) as response, archive.open('wb') as output:
                while chunk := response.read(1024 * 1024):
                    if cancel and cancel.is_set():
                        raise InterruptedError('준비를 중지했습니다.')
                    output.write(chunk)
                    hasher.update(chunk)
                    received += len(chunk)
                    percent = int(received * 100 / asset['size'])
                    if percent // 10 != last:
                        last = percent // 10
                        log(f'{name} 받는 중 · {percent}%')
            if hasher.hexdigest() != digest.split(':', 1)[1]:
                raise RuntimeError(f'{name}: 무결성 검사 실패')
            if name.endswith('.zip'):
                with zipfile.ZipFile(archive) as package:
                    for member in package.infolist():
                        base = Path(member.filename).name
                        if base in required or base.lower().endswith('.dll') or 'license' in base.lower():
                            target = TOOLS / base
                            with package.open(member) as source, target.open('wb') as output:
                                shutil.copyfileobj(source, output)
            else:
                os.replace(archive, TOOLS / name)
        if not all((TOOLS / p).is_file() for p in required):
            raise RuntimeError(f'{repo}: 필요한 실행 파일이 누락됐습니다.')
        log(f'{repo} 준비 완료 · {release["tag_name"]}')

if __name__ == '__main__':
    install()
