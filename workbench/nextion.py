#!/usr/bin/env python3
"""Host CLI; Docker SSH contexts work without remote host bind paths."""
import argparse
import fcntl
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'sztupy/nextion-scripts@sha256:246a69a268419e333b3654984f9640a43f9db256f2356e09030d695ac5ef9a5e'
EDITOR_URL = 'https://nextion.tech/download/nextion-setup-v1-68-2.zip'
EDITOR_SHA = '1a00e05e86bc66f977ffaec7da3b9c8387233828021a07560b14e2efe2b8ff2d'
LABEL = 'com.kaga.nextion-workbench=1'

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)

class Docker:
    def __init__(self, host=None):
        self.command = ['docker'] + (['--host', host] if host else [])
    def run(self, *args, timeout=60, check=True, **kwargs):
        return subprocess.run(self.command + list(args), check=check, capture_output=True,
                              text=True, timeout=timeout, **kwargs)
    def json(self, *args):
        return json.loads(self.run(*args).stdout)

def doctor(docker, output=None):
    info = docker.json('info', '--format', '{{json .}}')
    result = {'clientOS': platform.system(), 'clientArch': platform.machine(),
              'dockerArchitecture': info['Architecture'], 'dockerCPUs': info['NCPU'],
              'dockerMemoryBytes': info['MemTotal'], 'dockerVersion': info['ServerVersion'],
              'dockerName': info['Name'], 'targetPlatform': 'linux/amd64',
              'clientDiskFreeBytes': shutil.disk_usage(ROOT).free}
    if platform.system() == 'Darwin' and info['Name'] == 'colima' and shutil.which('colima'):
        cp = subprocess.run(['colima', 'status', '--json'], capture_output=True, text=True)
        if cp.returncode == 0:
            result['colima'] = json.loads(cp.stdout)
    if output:
        write_json(output, result)
    return result

def build_image(docker, variant):
    archive = ROOT / 'workbench/downloads/nextion-1.68.2.zip'
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        temp = archive.with_suffix('.partial')
        request = urllib.request.Request(EDITOR_URL, headers={'User-Agent': 'Nextion-Workbench'})
        with urllib.request.urlopen(request, timeout=60) as source, temp.open('wb') as target:
            shutil.copyfileobj(source, target)
        temp.replace(archive)
    if sha(archive) != EDITOR_SHA:
        raise ValueError('Downloaded Editor SHA-256 did not match the pinned release')
    command = docker.command + ['build', '--platform', 'linux/amd64', '--target', variant,
              '-t', 'nextion-workbench:1.68.2-' + variant, str(ROOT / 'workbench')]
    return subprocess.call(command)

def compile_hmi(docker, image, source, output, timeout=180):
    source = Path(source).resolve(strict=True)
    if not source.is_file() or source.suffix.lower() != '.hmi':
        raise ValueError('A .hmi file is required')
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    lock = (output / '.compile.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        lock.close()
        raise RuntimeError('Another build owns this output directory') from exc
    run_id = time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8]
    destination = output / 'runs' / run_id
    destination.mkdir(parents=True)
    name = 'nextion-build-' + uuid.uuid4().hex[:12]
    created = False
    result = {'status': 'failed', 'runId': run_id, 'source': str(source)}
    try:
        original = sha(source)
        image_info = docker.json('image', 'inspect', image)[0]
        docker.run('create', '--platform', 'linux/amd64', '--name', name, '--label', LABEL,
                   '--network', 'none', '--no-healthcheck', '--cpus', '1.5', '--memory', '3g', '--shm-size', '128m',
                   image_info['Id'], 'compile', '--input', '/input/project.hmi', '--timeout', str(timeout))
        created = True
        docker.run('cp', str(source), name + ':/input/project.hmi')
        try:
            execution = docker.run('start', '-a', name, timeout=timeout + 90, check=False)
            (destination / 'container.log').write_text(execution.stdout + execution.stderr)
        except subprocess.TimeoutExpired:
            docker.run('kill', name, check=False)
            result['error'] = 'Host deadline exceeded'
        docker.run('cp', name + ':/workspace/.', str(destination), check=False)
        if (destination / 'result.json').exists():
            result.update(json.loads((destination / 'result.json').read_text()))
        else:
            result.setdefault('error', 'Container returned no result record')
        result.update(runId=run_id, source=str(source), imageId=image_info['Id'],
                      imageArchitecture=image_info['Architecture'], originalSha256=original)
        if sha(source) != original:
            result.update(status='failed', error='Original input changed during build')
        if result.get('inputSha256') != original:
            result.update(status='failed', error='Build input hash did not match original')
        if result['status'] == 'success':
            target = destination / 'exports/project.tft'
            if not target.is_file() or sha(target) != result.get('outputSha256'):
                result.update(status='failed', error='TFT export failed host verification')
        write_json(destination / 'result.json', result)
        # latest.json always points to this run, including failures.
        write_json(output / 'latest.json', {'run': str(destination.relative_to(output)), **result})
        return result
    finally:
        if created:
            docker.run('rm', '-f', name, check=False)
        lock.close()

def start_editor(docker, image, source, name, port, web=True, workspace_volume=None):
    source = Path(source).resolve(strict=True)
    info = docker.json('image', 'inspect', image)[0]
    version = next((x.split('=', 1)[1] for x in info['Config']['Env'] if x.startswith('NEXTION_EDITOR_VERSION=')), None)
    if not version or not all(c.isdigit() or c == '.' for c in version):
        raise ValueError('The image must declare a numeric NEXTION_EDITOR_VERSION')
    volume = workspace_volume or ('nextion-' + version.replace('.', '-') + '-' + sha(source)[:12])
    args = ['create', '--platform', 'linux/amd64', '--name', name, '--label', LABEL,
            '--cpus', '1.5', '--memory', '3g', '--shm-size', '128m',
            '--mount', f'type=volume,src={volume},dst=/workspace', '-e', 'NEXTION_WEB=' + ('1' if web else '0')]
    if web:
        args += ['-p', f'127.0.0.1:{port}:6080']
    else:
        args += ['--no-healthcheck']
    docker.run(*args, info['Id'], 'editor', '--input', '/input/project.hmi')
    try:
        docker.run('cp', str(source), name + ':/input/project.hmi')
        docker.run('start', name)
    except Exception:
        docker.run('rm', '-f', name, check=False)
        raise
    return {'container': name, 'volume': volume, 'urlOnDockerHost': f'http://127.0.0.1:{port}', 'state': 'starting'}

def stop_editor(docker, name):
    info = docker.json('inspect', name)[0]
    if info['Config'].get('Labels', {}).get('com.kaga.nextion-workbench') != '1':
        raise ValueError('Refusing to stop a container not owned by this workbench')
    docker.run('stop', '--time', '15', name)
    docker.run('rm', name)
    return {'container': name, 'state': 'stopped', 'workspaceVolumeRetained': True}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='Docker endpoint, including ssh://home-server')
    parser.add_argument('--image', default='nextion-workbench:1.68.2-slim')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('doctor'); p.add_argument('--output')
    p = sub.add_parser('build-image'); p.add_argument('--variant', choices=['full', 'slim'], default='slim')
    p = sub.add_parser('compile'); p.add_argument('input'); p.add_argument('--output', default='artifacts'); p.add_argument('--timeout', type=float, default=180)
    p = sub.add_parser('editor'); p.add_argument('input'); p.add_argument('--name', default='nextion-workbench'); p.add_argument('--port', type=int, default=6080); p.add_argument('--no-web', action='store_true')
    p = sub.add_parser('stop'); p.add_argument('--name', default='nextion-workbench')
    args = parser.parse_args()
    docker = Docker(args.host)
    try:
        if args.command == 'doctor': result = doctor(docker, args.output)
        elif args.command == 'build-image': return build_image(docker, args.variant)
        elif args.command == 'compile': result = compile_hmi(docker, args.image, args.input, args.output, args.timeout)
        elif args.command == 'editor': result = start_editor(docker, args.image, args.input, args.name, args.port, not args.no_web)
        else: result = stop_editor(docker, args.name)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('status') != 'failed' else 1
    except (ValueError, RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        if isinstance(exc, subprocess.CalledProcessError):
            print(exc.stderr.strip(), file=sys.stderr)
        else:
            print(str(exc), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
