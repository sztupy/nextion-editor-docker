#!/usr/bin/env python3
"""Exercise real build failure, timeout, stale output, locking and recovery paths."""
import argparse
import fcntl
import json
import time
from pathlib import Path
from nextion import Docker, compile_hmi, sha, write_json

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host')
    p.add_argument('--image', default='nextion-workbench:1.68.2-slim')
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    docker = Docker(args.host)
    root = Path(args.output).resolve(); root.mkdir(parents=True, exist_ok=True)
    build = root / 'sequence'; build.mkdir(exist_ok=True)
    source = Path(args.input).resolve()
    before = sha(source)
    report = {'startedAt': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'image': args.image, 'cases': []}
    def record(name, passed, **details):
        report['cases'].append({'name': name, 'passed': passed, **details})
        write_json(root / 'summary.json', report)
        if not passed:
            raise AssertionError(name)
        print(name + ': passed', flush=True)
    # This deliberately leaves a previous-looking TFT in the chosen output folder.
    stale = build / 'project.tft'; stale.write_bytes(b'not a new build result')
    lock = (build / '.compile.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        try:
            compile_hmi(docker, args.image, source, build, 1)
        except RuntimeError as exc:
            record('duplicate-output-lock', 'Another build owns' in str(exc), error=str(exc))
        else:
            record('duplicate-output-lock', False)
    finally:
        lock.close()
    bad = root / 'broken.hmi'
    bad.write_bytes(b'corrupt Nextion HMI\x00' * 1000)
    for name, input_path, deadline in [('invalid-hmi', bad, 45), ('forced-timeout', source, .1)]:
        result = compile_hmi(docker, args.image, input_path, build, deadline)
        latest = json.loads((build / 'latest.json').read_text())
        run = build / latest['run']
        record(name, result['status'] == 'failed' and result.get('exitCode', 1) != 0,
               result=result, resultPath=str(run / 'result.json'))
        record(name + '-no-stale-export', not (run / 'exports/project.tft').exists()
               and latest['status'] == 'failed' and stale.read_bytes() == b'not a new build result')
        record(name + '-diagnostics', (run / 'logs/screen.png').exists() and (run / 'container.log').exists())
    recovered = compile_hmi(docker, args.image, source, build, 240)
    record('recovery-after-failure-and-lock-release', recovered['status'] == 'success', result=recovered)
    record('original-unchanged', sha(source) == before, sha256=before)
    remaining = docker.run('ps', '-a', '--filter', 'label=com.kaga.nextion-workbench=1',
                           '--filter', 'name=nextion-build-', '--format', '{{.Names}}').stdout.strip()
    record('build-containers-cleaned', not remaining, remaining=remaining)
    report['passed'] = all(c['passed'] for c in report['cases'])
    write_json(root / 'summary.json', report)

if __name__ == '__main__':
    main()
