#!/usr/bin/env python3
"""Isolated Wine process supervisor. Never accesses Docker or a physical panel."""
import argparse
import fcntl
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import struct
import subprocess
import sys
import time
from pathlib import Path

PREFIX = Path('/home/wineuser/.wine')
WORK = PREFIX / 'drive_c/workbench'
DATA = PREFIX / 'drive_c/data'
SPACE = Path('/workspace')
PROCESSES = []
STOP = False

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    temp.replace(path)

def copy_atomic(source, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(destination.suffix + '.tmp')
    shutil.copyfile(source, temp)
    # Exports belong to the host workspace owner, including bind-mounted Macs.
    owner = SPACE.stat()
    os.chown(temp, owner.st_uid, owner.st_gid)
    temp.replace(destination)

def spawn(args, label, wine=False):
    log = (SPACE / 'logs' / (label + '.log')).open('ab', buffering=0)
    command = ['gosu', 'wineuser'] + args if wine else args
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    log.close()
    PROCESSES.append(process)
    return process

def run_wine(args, timeout=15):
    return subprocess.run(['gosu', 'wineuser'] + args, capture_output=True, timeout=timeout)

def initialize():
    for name in ('logs', 'work', 'exports'):
        (SPACE / name).mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    shutil.chown(WORK, 'wineuser', 'wineuser')
    shutil.copyfile('/opt/workbench/compile.ahk', WORK / 'compile.ahk')
    shutil.chown(WORK / 'compile.ahk', 'wineuser', 'wineuser')
    spawn(['Xvfb', ':95', '-screen', '0', '1024x768x24', '-nolisten', 'tcp'], 'xvfb')
    until = time.monotonic() + 15
    while time.monotonic() < until:
        if subprocess.run(['xdotool', 'getdisplaygeometry'], capture_output=True).returncode == 0:
            break
        time.sleep(.1)
    else:
        raise RuntimeError('X display did not become ready')
    spawn(['openbox', '--sm-disable'], 'window-manager', wine=True)

def prepare(source):
    WORK.mkdir(parents=True, exist_ok=True)
    shutil.chown(WORK, 'wineuser', 'wineuser')
    source = Path(source)
    if not source.is_file() or source.is_symlink():
        raise ValueError('A regular HMI input is required')
    before = digest(source)
    shutil.copyfile(source, WORK / 'project.hmi')
    shutil.chown(WORK / 'project.hmi', 'wineuser', 'wineuser')
    if before != digest(WORK / 'project.hmi') or before != digest(source):
        raise ValueError('Input changed while creating the build snapshot')
    return before

def start_editor(bootstrap=True):
    executable = next((DATA / 'nextion' / name for name in ('Nextion Editor.exe', 'NextionEditor.exe')
                       if (DATA / 'nextion' / name).is_file()), None)
    if executable is None:
        raise RuntimeError('Nextion Editor executable is missing from the image')
    editor = spawn(['wine', str(executable), r'C:\workbench\project.hmi'], 'editor', wine=True)
    if bootstrap:
        spawn(['wine', str(DATA / 'ahk/AutoHotkeyU32.exe'), '/opt/workbench/bootstrap.ahk'], 'bootstrap', wine=True)
    return editor

def compiler_summary(log):
    match = re.search(r'Compile Successful!\s*(\d+) Errors,\s*(\d+) Warnings,\s*File Size:([\d,]+)', log)
    if not match or 'Compile Failed' in log:
        raise ValueError('No successful compiler summary was observed')
    errors, warnings, size = (int(x.replace(',', '')) for x in match.groups())
    if errors:
        raise ValueError(f'Compiler reported {errors} errors')
    return {'errors': errors, 'warnings': warnings, 'bytes': size}

def validate_tft(path):
    """Verify both F-series header checksums without modifying the binary."""
    with Path(path).open('rb') as stream:
        raw = stream.read(400)
    if len(raw) < 400:
        raise ValueError('Truncated TFT header')
    for start, end in ((0, 0xc4), (0xc8, 0x18c)):
        crc = 0xffffffff
        for byte in raw[start:end]:
            crc ^= byte
            for _ in range(32):
                crc = ((crc << 1) ^ (0x04c11db7 if crc & 0x80000000 else 0)) & 0xffffffff
        if crc != struct.unpack_from('<I', raw, end)[0]:
            raise ValueError('Invalid or unsupported TFT header checksum')
    return {'headerChecksumsValid': True, 'modelCode': hex(struct.unpack_from('<I', raw, 0x2e)[0])}

def locate_output(summary, since):
    roaming = PREFIX / 'drive_c/users/wineuser/AppData/Roaming/Nextion Editor/work'
    files = [p for p in roaming.rglob('*.tft') if p.is_file() and p.stat().st_mtime >= since - 1]
    files += [p for p in WORK.rglob('*.tft') if p.stat().st_mtime >= since - 1]
    files = [p for p in files if p.stat().st_size == summary['bytes'] and p.stat().st_size > 512]
    if len(files) != 1:
        raise ValueError(f'Expected exactly one new TFT of compiler-reported size; found {len(files)}')
    return files[0]

def screenshot(path):
    try:
        subprocess.run(['import', '-window', 'root', str(path)], timeout=8, capture_output=True)
    except (OSError, subprocess.TimeoutExpired):
        pass

def compile_project(source, timeout):
    began = time.monotonic()
    deadline = began + timeout
    report = {'status': 'failed', 'editorVersion': os.environ.get('NEXTION_EDITOR_VERSION'),
              'architecture': platform.machine(), 'physicalPanelAccessed': False}
    code = 1
    try:
        report['inputSha256'] = prepare(source)
        # Only the ephemeral container's compiler cache is cleared.
        cache = PREFIX / 'drive_c/users/wineuser/AppData/Roaming/Nextion Editor/work'
        for old in [*cache.rglob('*.tft'), *WORK.glob('*.tft')]:
            old.unlink()
        (WORK / 'compile-result.txt').unlink(missing_ok=True)
        initialize()
        started = time.time()
        start_editor(bootstrap=False)
        remaining = max(.001, deadline - time.monotonic())
        automation = spawn(['wine', str(DATA / 'ahk/AutoHotkeyU32.exe'), r'C:\workbench\compile.ahk'], 'automation', wine=True)
        try:
            rc = automation.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f'Compiler exceeded {timeout} seconds') from exc
        log_path = WORK / 'compile-result.txt'
        if log_path.exists():
            copy_atomic(log_path, SPACE / 'logs/compiler.txt')
        if rc:
            raise RuntimeError(f'Editor automation failed with exit code {rc}')
        summary = compiler_summary(log_path.read_text(encoding='utf-8-sig'))
        output = locate_output(summary, started)
        report['tftHeader'] = validate_tft(output)
        copy_atomic(output, SPACE / 'exports/project.tft')
        copy_atomic(WORK / 'project.hmi', SPACE / 'exports/project.hmi')
        report.update(status='success', compiler=summary, outputSha256=digest(output),
                      savedHmiSha256=digest(WORK / 'project.hmi'))
        code = 0
    except Exception as exc:
        report['error'] = str(exc)
        code = 124 if isinstance(exc, TimeoutError) else 1
        # Failed runs never expose a previous success artifact.
        for name in ('project.tft', 'project.hmi'):
            (SPACE / 'exports' / name).unlink(missing_ok=True)
    finally:
        screenshot(SPACE / 'logs/screen.png')
        report['durationSeconds'] = round(time.monotonic() - began, 3)
        report['exitCode'] = code
        atomic_json(SPACE / 'result.json', report)
        print(json.dumps(report), flush=True)
    return code

def editor_session(source):
    began = time.monotonic()
    existing = SPACE / 'work/project.hmi'
    if not existing.exists():
        if not Path(source).is_file():
            raise ValueError('Put your HMI at /workspace/input/project.hmi or use the editor CLI')
        copy_atomic(source, existing)
    prepare(existing)
    initialize()
    editor = start_editor()
    web = os.environ.get('NEXTION_WEB', '1') == '1'
    if web:
        spawn(['x11vnc', '-display', ':95', '-localhost', '-rfbport', '5900', '-forever', '-shared',
               '-nopw', '-noxdamage', '-wait', '30', '-defer', '20'], 'vnc')
        for name, target in [('project.hmi', SPACE / 'work/project.hmi'), ('project.tft', SPACE / 'exports/project.tft')]:
            link = Path('/opt/web') / name
            link.unlink(missing_ok=True)
            link.symlink_to(target)
        spawn(['python3', '/opt/workbench/web_proxy.py'], 'web')
    last_stamp = None
    last_output = None
    ready = False
    while not STOP:
        if editor.poll() is not None:
            raise RuntimeError(f'Editor exited with {editor.returncode}')
        path = WORK / 'project.hmi'
        stat = path.stat()
        stamp = (stat.st_mtime_ns, stat.st_size)
        if stamp != last_stamp and time.time() - stat.st_mtime > .75:
            copy_atomic(path, existing)
            last_stamp = stamp
        cache = PREFIX / 'drive_c/users/wineuser/AppData/Roaming/Nextion Editor/work'
        candidates = list(cache.rglob('*.tft')) + list(WORK.glob('*.tft'))
        if candidates:
            output = max(candidates, key=lambda p: p.stat().st_mtime_ns)
            stamp_out = (str(output), output.stat().st_mtime_ns, output.stat().st_size)
            if stamp_out != last_output and time.time() - output.stat().st_mtime > 1:
                copy_atomic(output, SPACE / 'exports/project.tft')
                last_output = stamp_out
        windows = subprocess.run(['xdotool', 'search', '--name', re.escape(r'Nextion Editor(C:\workbench\project.hmi)')], capture_output=True) if not ready else None
        if windows is not None and windows.returncode == 0:
            ready = True
            atomic_json(SPACE / 'status.json', {'state': 'ready', 'editorVersion': os.environ['NEXTION_EDITOR_VERSION'],
                'readySeconds': round(time.monotonic() - began, 3), 'web': web})
            print('EDITOR_READY', flush=True)
        time.sleep(.5)
    if path.exists():
        copy_atomic(path, existing)
    return 0

def cleanup():
    for process in reversed(PROCESSES):
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    for process in PROCESSES:
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    try:
        run_wine(['wineserver', '-k'], timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        pass

def main():
    global STOP
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['compile', 'editor'])
    parser.add_argument('--input', default='/workspace/input/project.hmi')
    parser.add_argument('--timeout', type=float, default=180)
    args = parser.parse_args()
    # Browser input uses X11. Keep default Wine device services for batch
    # automation, where the tested keyboard/menu behavior depends on them.
    if args.mode == 'editor' and os.environ.get('NEXTION_OPTIMIZE_DEVICES', '1') == '1':
        os.environ['WINEDLLOVERRIDES'] = 'winebus.sys,wineusb.sys='
    SPACE.mkdir(parents=True, exist_ok=True)
    (SPACE / 'logs').mkdir(exist_ok=True)
    (SPACE / 'exports').mkdir(exist_ok=True)
    def stop(_signum, _frame):
        global STOP
        STOP = True
        if args.mode == 'compile':
            raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    lock = (SPACE / '.session.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('Another session owns this workspace', file=sys.stderr)
        return 73
    try:
        atomic_json(SPACE / 'status.json', {'state': 'starting', 'editorVersion': os.environ.get('NEXTION_EDITOR_VERSION')})
        # Interactive sessions may stay open for days. Measurement is opt-in
        # there, while bounded raw samples are kept for every batch build.
        if os.environ.get('NEXTION_METRICS', '1' if args.mode == 'compile' else '0') == '1':
            spawn(['python3', '/opt/workbench/metrics.py'], 'resources')
        return compile_project(args.input, args.timeout) if args.mode == 'compile' else editor_session(args.input)
    except Exception as exc:
        atomic_json(SPACE / 'status.json', {'state': 'failed', 'error': str(exc)})
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        cleanup()
        lock.close()

if __name__ == '__main__':
    sys.exit(main())
