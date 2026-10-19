import json
import os
from pathlib import Path
import subprocess
import threading
import uuid
from urllib.parse import parse_qs, urlencode, urlparse
from setup_tools import TOOLS, install

HIDDEN = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

def normalize_url(value, playlist=False):
    url = urlparse(value.strip())
    if url.scheme not in ('http', 'https') or url.hostname not in (
        'youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com', 'youtu.be', 'www.youtu.be'
    ) or url.username or url.password:
        raise ValueError('올바른 유튜브 주소를 입력해주세요.')
    query = parse_qs(url.query)
    if playlist:
        identifier = query.get('list', [''])[0]
        if not identifier:
            raise ValueError('재생목록 주소에 list 정보가 없습니다. 한 곡 모드를 선택하거나 재생목록 주소를 입력해주세요.')
        return 'https://www.youtube.com/playlist?' + urlencode({'list': identifier})
    video = query.get('v', [''])[0]
    parts = url.path.strip('/').split('/')
    if url.hostname in ('youtu.be', 'www.youtu.be'):
        video = parts[0]
    elif len(parts) > 1 and parts[0] in ('shorts', 'live', 'embed'):
        video = parts[1]
    if not video:
        raise ValueError('한 곡 모드에서는 동영상 주소를 입력해주세요.')
    return 'https://www.youtube.com/watch?' + urlencode({'v': video})

def command(url, folder, playlist=False):
    folder = Path(folder).resolve()
    template = ('%(playlist_title).70s/%(playlist_index)03d - ' if playlist else '') + '%(title).100s [%(id)s].%(ext)s'
    return [str(TOOLS / 'yt-dlp.exe'), '--ignore-config', '--no-plugin-dirs',
            '--ffmpeg-location', str(TOOLS), '--js-runtimes', f'deno:{TOOLS / "deno.exe"}',
            '--yes-playlist' if playlist else '--no-playlist', '--no-abort-on-error',
            '--windows-filenames', '--no-overwrites', '--newline', '--no-colors', '--no-quiet', '--progress',
            '--encoding', 'utf-8', '--socket-timeout', '25', '--retries', '3',
            '-f', 'bestaudio/best', '-x', '--audio-format', 'mp3', '--audio-quality', '320K',
            '--embed-metadata', '--embed-thumbnail', '--convert-thumbnails', 'jpg',
            '--progress-template', 'download:PROGRESS:%(progress._percent_str)s',
            '--print', 'after_move:FILE:%(filepath)j', '--no-simulate',
            '-P', str(folder), '-P', 'temp:' + str(Path(folder) / '.goyo-partials' / uuid.uuid4().hex),
            '-o', template, '--', normalize_url(url, playlist)]

class Downloader:
    def __init__(self, emit):
        self.emit = emit
        self.cancelled = threading.Event()
        self.process = None
        self.lock = threading.Lock()

    def stop(self):
        self.cancelled.set()
        with self.lock:
            if self.process and self.process.poll() is None:
                subprocess.run(['taskkill', '/PID', str(self.process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=HIDDEN)

    def run(self, url, folder, playlist=False, update=False):
        completed, errors = 0, 0
        try:
            install(lambda s: self.emit('log', s), self.cancelled, update=update)
            if update:
                self.emit('done', '도구 업데이트 완료')
                return
            if self.cancelled.is_set():
                raise InterruptedError()
            args = command(url, folder, playlist)
            Path(folder).mkdir(parents=True, exist_ok=True)
            with self.lock:
                if self.cancelled.is_set():
                    raise InterruptedError()
                self.process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding='utf-8', errors='replace', creationflags=HIDDEN)
            for line in self.process.stdout:
                line = line.strip()
                if line.startswith('PROGRESS:'):
                    try:
                        self.emit('progress', float(line.split(':', 1)[1].strip().rstrip('%')))
                    except ValueError:
                        pass
                elif line.startswith('FILE:'):
                    path = json.loads(line[5:])
                    if Path(path).is_file() and Path(path).suffix.lower() == '.mp3':
                        completed += 1
                        self.emit('log', f'저장 확인 · {path}')
                        self.emit('count', completed)
                else:
                    if line.startswith('ERROR:'):
                        errors += 1
                    if line:
                        self.emit('log', line)
            code = self.process.wait()
            if self.cancelled.is_set():
                self.emit('done', f'중지됨 · 저장 확인 {completed}곡')
            elif code or errors:
                self.emit('done', f'일부 또는 전체 실패 · 저장 확인 {completed}곡 · 아래 기록을 확인해주세요.')
            elif completed:
                self.emit('done', f'완료 · 저장 확인 {completed}곡')
            else:
                self.emit('done', '저장된 MP3가 없습니다. 아래 기록을 확인해주세요.')
        except InterruptedError:
            self.emit('done', f'중지됨 · 저장 확인 {completed}곡')
        except Exception as error:
            self.emit('log', str(error))
            self.emit('done', '작업 실패 · 아래 기록을 확인해주세요.')
        finally:
            self.emit('idle', None)
