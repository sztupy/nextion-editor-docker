import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('metrics', Path(__file__).parents[1] / 'metrics.py')
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


class LongRunningMetrics(unittest.TestCase):
    def test_bounded_history_keeps_whole_run_mean_and_early_peak(self):
        summary = metrics.Summary(1200)
        for i in range(10000):
            summary.add({'monotonic': i / 2, 'memoryBytes': 1000 if i == 0 else 100,
                         'workingSetBytes': 500 if i == 0 else 50, 'cpuUsageUsec': i * 50000})
        result = summary.result()
        self.assertEqual(result['sampleCount'], 10000)
        self.assertEqual(result['retainedSampleCount'], 1200)
        self.assertTrue(result['rawSamplesTruncated'])
        self.assertEqual(result['samples'][0]['monotonic'], 4400)
        self.assertEqual(result['summary']['peakMemoryBytes'], 1000)
        self.assertEqual(result['summary']['peakWorkingSetBytes'], 500)
        self.assertAlmostEqual(result['summary']['meanWorkingSetBytes'], 50.045)
        self.assertAlmostEqual(result['summary']['meanCpuPercentOneCore'], 10)

    def test_single_sample_has_no_cpu_interval(self):
        summary = metrics.Summary()
        summary.add({'monotonic': 1, 'memoryBytes': 100, 'workingSetBytes': 50, 'cpuUsageUsec': 10})
        self.assertEqual(summary.result()['summary']['meanCpuPercentOneCore'], 0)


if __name__ == '__main__':
    unittest.main()
