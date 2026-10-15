#!/usr/bin/env python3
"""Sample cgroup v2 usage; retain raw values and the exact observation window."""
import argparse
import json
import signal
import time
from collections import deque
from pathlib import Path

STOP = False

def sample():
    root = Path('/sys/fs/cgroup')
    memory = int((root / 'memory.current').read_text())
    stat = dict(line.split() for line in (root / 'memory.stat').read_text().splitlines())
    cpu = dict(line.split() for line in (root / 'cpu.stat').read_text().splitlines())
    return {'monotonic': time.monotonic(), 'memoryBytes': memory,
            'workingSetBytes': max(0, memory - int(stat.get('inactive_file', 0))),
            'cpuUsageUsec': int(cpu['usage_usec'])}

class Summary:
    """Keep whole-run totals even after old raw samples leave the ring buffer."""
    def __init__(self, capacity=1200):
        if capacity < 2:
            raise ValueError('At least two samples must be retained')
        self.rows = deque(maxlen=capacity)
        self.count = 0
        self.working_sum = self.working_peak = self.memory_peak = 0
        self.first = None

    def add(self, row):
        if self.rows:
            previous = self.rows[-1]
            row['cpuPercentOneCore'] = (row['cpuUsageUsec'] - previous['cpuUsageUsec']) / ((row['monotonic'] - previous['monotonic']) * 10000)
        else:
            self.first = row
        self.rows.append(row)
        self.count += 1
        self.working_sum += row['workingSetBytes']
        self.working_peak = max(self.working_peak, row['workingSetBytes'])
        self.memory_peak = max(self.memory_peak, row['memoryBytes'])

    def result(self):
        result = {'sampleCount': self.count, 'retainedSampleCount': len(self.rows),
                  'rawSamplesTruncated': self.count > len(self.rows), 'samples': list(self.rows)}
        if self.count:
            last = self.rows[-1]
            elapsed = last['monotonic'] - self.first['monotonic']
            result['summary'] = {
                'meanCpuPercentOneCore': (last['cpuUsageUsec'] - self.first['cpuUsageUsec']) / (elapsed * 10000) if elapsed else 0,
                'meanWorkingSetBytes': self.working_sum / self.count,
                'peakWorkingSetBytes': self.working_peak, 'peakMemoryBytes': self.memory_peak,
            }
        return result

def collect(seconds, output, max_samples=1200):
    summary = Summary(max_samples)
    began = time.monotonic()
    while not STOP and (not seconds or time.monotonic() - began < seconds):
        summary.add(sample())
        time.sleep(.5)
    result = {'schemaVersion': 2, 'durationSeconds': round(time.monotonic() - began, 3),
              'cpuPercentMeaning': '100% equals one CPU core; time-weighted mean over the complete observation',
              **summary.result()}
    path = Path(output)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(result, indent=2) + '\n')
    temp.replace(path)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=float, default=0)
    parser.add_argument('--output', default='/workspace/resources.json')
    parser.add_argument('--max-samples', type=int, default=1200, help='Retain the last N raw samples; summaries cover the complete run')
    args = parser.parse_args()
    def stop(_signal, _frame):
        global STOP
        STOP = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    collect(args.seconds, args.output, args.max_samples)

if __name__ == '__main__':
    main()
