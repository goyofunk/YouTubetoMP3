"""Build the Windows x64 application and its self-contained NSIS installer."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile

PACKAGING = Path(__file__).resolve().parent
ROOT = PACKAGING.parent
SOURCE = ROOT / 'src'
sys.path.insert(0, str(SOURCE))
BUILD = ROOT / 'build'
DIST = ROOT / 'dist'
NSIS_URL = 'https://downloads.sourceforge.net/project/nsis/NSIS%203/3.13/nsis-3.13.zip'
NSIS_SHA256 = 'ba63dffc4410ee89193e1cb5a41989991bd77c61068da17e3156d136b7b0b3d8'


def forbidden(path):
    for part in Path(path).parts:
        name = part.lower()
        if (name.startswith(('.git', '.claude', '.codex', '.agent', '.cursor', '.gemini', '.aider', '.vscode'))
            or name in ('agents.md', 'agent.md', 'claude.md', 'gemini.md', 'skill.md')
            or name == '.env' or name.startswith('.env.') or name.endswith(('.env', '.code-workspace'))):
            return True
    return False


def compiler():
    executable = BUILD / 'compiler' / 'nsis-3.13' / 'makensis.exe'
    if executable.is_file():
        return executable
    archive = BUILD / 'compiler' / 'nsis-3.13.zip'
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        with urllib.request.urlopen(NSIS_URL, timeout=60) as response, archive.open('xb') as output:
            shutil.copyfileobj(response, output)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != NSIS_SHA256:
        raise RuntimeError('NSIS SHA256 mismatch')
    with zipfile.ZipFile(archive) as package:
        for member in package.infolist():
            (archive.parent / member.filename).resolve().relative_to(archive.parent)
        package.extractall(archive.parent)
    return executable


def nsis_escape(value):
    return str(value).replace('$', '$$').replace('"', '$\\"')


def build(version):
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Use a numeric version such as 1.0.0')
    BUNDLE = DIST / 'YouTube to MP3'
    installer = ROOT / f'YouTube-to-MP3-{version}-Setup.exe'
    if BUNDLE.exists() or installer.exists():
        raise RuntimeError('Existing build output found; preserve or remove it explicitly before rebuilding.')
    BUILD.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    from setup_tools import install, TOOLS
    install()
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--windowed', '--onedir', '--noupx',
                    '--name', 'YouTube to MP3', '--icon', str(SOURCE / 'icon.ico'),
                    '--add-data', f'{SOURCE / "icon.png"}:.',
                    '--add-data', f'{SOURCE / "assets"}:assets',
                    '--distpath', str(DIST), '--workpath', str(BUILD / 'pyinstaller'),
                    '--specpath', str(BUILD), str(SOURCE / 'app.py')], cwd=ROOT, check=True)
    shutil.copy2(SOURCE / 'icon.ico', BUNDLE / 'icon.ico')
    tool_dir = BUNDLE / 'tools'
    tool_dir.mkdir()
    for file in TOOLS.iterdir():
        if file.is_file() and (file.suffix.lower() in ('.exe', '.dll') or file.name.lower() == 'license.txt'):
            shutil.copy2(file, tool_dir / file.name)
    required = ['yt-dlp.exe', 'ffmpeg.exe', 'ffprobe.exe', 'deno.exe']
    for name in required:
        if not (tool_dir / name).is_file():
            raise RuntimeError(f'Missing bundled tool: {name}')
    versions = {}
    for name, flag in [('yt-dlp.exe', '--version'), ('ffmpeg.exe', '-version'), ('deno.exe', '--version')]:
        versions[name] = subprocess.check_output([str(tool_dir / name), flag], text=True, encoding='utf-8').splitlines()[0]
    license_dir = BUNDLE / 'licenses'
    license_dir.mkdir()
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    shutil.copy2(python_license, license_dir / 'Python-LICENSE.txt')
    shutil.copy2(TOOLS / 'LICENSE.txt', license_dir / 'GPL-3.0.txt')
    notices = [
        'YouTube to MP3 - bundled third-party software', '',
        'Python: PSF License. Full license: licenses/Python-LICENSE.txt',
        'Python source: https://www.python.org/downloads/source/',
        'Tcl/Tk: BSD-style license. License files accompany the bundled Tcl/Tk libraries.',
        'Tcl/Tk source: https://www.tcl.tk/software/tcltk/download.html',
        'PyInstaller: GPL-2.0-or-later with bootloader exception.',
        'https://pyinstaller.org/en/stable/license.html',
        'yt-dlp Windows executable: GPL-3.0-or-later combined binary (upstream source is Unlicense).',
        'Source and dependency licenses: https://github.com/yt-dlp/yt-dlp',
        'Matching nightly release: https://github.com/yt-dlp/yt-dlp-nightly-builds/releases',
        'FFmpeg build: GPL-3.0-or-later. License: licenses/GPL-3.0.txt',
        'Source and build recipes: https://github.com/yt-dlp/FFmpeg-Builds',
        'FFmpeg source: https://git.ffmpeg.org/ffmpeg.git',
        'Deno: MIT. Source and third-party licenses: https://github.com/denoland/deno',
        '', 'Bundled versions:', json.dumps(versions, ensure_ascii=False, indent=2),
    ]
    (BUNDLE / 'THIRD_PARTY_NOTICES.txt').write_text('\n'.join(notices) + '\n', encoding='utf-8')
    files = sorted(p for p in BUNDLE.rglob('*') if p.is_file())
    for file in files:
        if forbidden(file.relative_to(BUNDLE)):
            raise RuntimeError(f'Forbidden distribution file: {file}')
    manifest = BUILD / 'uninstall_files.nsh'
    commands = [f'Delete "$INSTDIR\\{nsis_escape(str(p.relative_to(BUNDLE)))}"' for p in files]
    directories = sorted((p for p in BUNDLE.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True)
    commands += [f'RMDir "$INSTDIR\\{nsis_escape(str(p.relative_to(BUNDLE)))}"' for p in directories]
    manifest.write_text('\n'.join(commands) + '\n', encoding='utf-8-sig')
    (BUILD / 'payload-manifest.json').write_text(json.dumps([
        {'path': str(p.relative_to(BUNDLE)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
        for p in files], indent=2), encoding='utf-8')
    subprocess.run([str(compiler()), '/V2', '/WX', '/INPUTCHARSET', 'UTF8',
                    f'/DAPP_VERSION={version}', f'/DBUNDLE_DIR={BUNDLE}', f'/DOUTPUT_FILE={installer}',
                    f'/DAPP_ICON={SOURCE / "icon.ico"}',
                    f'/DUNINSTALL_MANIFEST={manifest}', str(PACKAGING / 'installer.nsi')], cwd=ROOT, check=True)
    checksum = hashlib.sha256(installer.read_bytes()).hexdigest()
    (DIST / 'SHA256SUMS.txt').write_text(f'{checksum}  ../{installer.name}\n', encoding='ascii')
    print(f'Installer: {installer}\nBytes: {installer.stat().st_size}\nSHA256: {checksum}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', default='1.0.1')
    build(parser.parse_args().version)
