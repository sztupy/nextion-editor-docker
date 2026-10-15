#!/usr/bin/env python3
"""Repeatable measurements on one Docker host; no physical device access."""
import argparse
import json
import statistics
import time
import uuid
from pathlib import Path
from nextion import Docker, compile_hmi, start_editor, stop_editor, write_json

def wait_ready(docker, name, timeout=120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = docker.run('exec', name, 'cat', '/workspace/status.json', check=False)
        if value.returncode == 0:
            data = json.loads(value.stdout)
            if data.get('state') == 'ready':
                return data
            if data.get('state') == 'failed':
                raise RuntimeError(data.get('error'))
        elif docker.json('inspect', name)[0]['State']['Running'] is False:
            raise RuntimeError('Editor container exited')
        time.sleep(.5)
    raise TimeoutError('Editor readiness deadline exceeded')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host')
    p.add_argument('--image', required=True)
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--runs', type=int, default=5)
    p.add_argument('--mode', choices=['compile', 'startup', 'idle'], required=True)
    p.add_argument('--seconds', type=int, default=60)
    p.add_argument('--no-web', action='store_true')
    p.add_argument('--timeout', type=int, default=240)
    args = p.parse_args()
    docker = Docker(args.host)
    output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    image = docker.json('image', 'inspect', args.image)[0]
    report = {'mode': args.mode, 'image': args.image, 'imageId': image['Id'], 'imageBytes': image['Size'],
              'web': not args.no_web, 'cpusLimit': 1.5, 'memoryLimit': '3g', 'runs': []}
    for i in range(args.runs if args.mode != 'idle' else 1):
        if args.mode == 'compile':
            result = compile_hmi(docker, args.image, args.input, output / f'run-{i+1}', args.timeout)
            if result['status'] != 'success':
                report['runs'].append(result); write_json(output / 'summary.json', report)
                raise RuntimeError(result.get('error'))
        else:
            name = 'nextion-benchmark-' + uuid.uuid4().hex[:8]
            # Each sample starts with an untouched project and an independent volume.
            volume = name + '-workspace'
            start_editor(docker, args.image, args.input, name, 0, not args.no_web, volume)
            try:
                result = wait_ready(docker, name, args.timeout)
                if args.mode == 'idle':
                    # Let startup background work settle before recording idle.
                    time.sleep(5)
                    docker.run('exec', name, 'python3', '/opt/workbench/metrics.py', '--seconds', str(args.seconds),
                               '--output', '/workspace/idle.json', timeout=args.seconds + 30)
                    docker.run('cp', name + ':/workspace/idle.json', str(output / 'idle.json'))
                    result['resources'] = json.loads((output / 'idle.json').read_text())
            finally:
                stop_editor(docker, name)
                docker.run('volume', 'rm', volume)
        report['runs'].append(result)
        times = [r.get('durationSeconds', r.get('readySeconds')) for r in report['runs']]
        report['medianSeconds'] = statistics.median(times)
        if args.mode == 'compile':
            report['identicalTftHashes'] = len({r['outputSha256'] for r in report['runs']}) == 1
        write_json(output / 'summary.json', report)
        print(json.dumps({'mode': args.mode, 'image': args.image, 'run': i+1, 'seconds': times[-1]}), flush=True)

if __name__ == '__main__':
    main()
