#!/usr/bin/env python3
"""Read-only per-process and per-thread CPU profile inside a Linux container."""
import json
import os
import time
from pathlib import Path


def snapshot():
    result = {}
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace').strip()
            for task in (proc / 'task').iterdir():
                raw = (task / 'stat').read_text()
                fields = raw[raw.rfind(')') + 2:].split()
                result[(int(proc.name), int(task.name))] = {
                    'ticks': int(fields[11]) + int(fields[12]),
                    'name': raw[raw.find('(') + 1:raw.rfind(')')],
                    'command': command, 'wait': (task / 'wchan').read_text().strip(),
                }
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return result


before = snapshot()
began = time.monotonic()
time.sleep(30)
after = snapshot()
elapsed = time.monotonic() - began
threads = []
processes = {}
for key, row in after.items():
    if key not in before:
        continue
    cpu = (row['ticks'] - before[key]['ticks']) / os.sysconf('SC_CLK_TCK') / elapsed * 100
    pid, tid = key
    threads.append({'pid': pid, 'tid': tid, 'cpuPercentOneCore': cpu, 'name': row['name'], 'wait': row['wait']})
    process = processes.setdefault(pid, {'pid': pid, 'command': row['command'], 'cpuPercentOneCore': 0})
    process['cpuPercentOneCore'] += cpu
print(json.dumps({'durationSeconds': elapsed,
                  'processes': sorted(processes.values(), key=lambda p: -p['cpuPercentOneCore']),
                  'threads': sorted(threads, key=lambda p: -p['cpuPercentOneCore'])[:30]}, indent=2))
