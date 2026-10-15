import importlib.util
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('runtime', Path(__file__).parents[1] / 'runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

class CompilerResults(unittest.TestCase):
    def test_warnings_are_retained(self):
        result = runtime.compiler_summary('Compile Successful! 0 Errors, 32 Warnings,File Size:13,534,076')
        self.assertEqual(result, {'errors': 0, 'warnings': 32, 'bytes': 13534076})

    def test_failure_overrides_old_success_line(self):
        with self.assertRaises(ValueError):
            runtime.compiler_summary('Compile Successful! 0 Errors, 0 Warnings,File Size:600\nCompile Failed')

    def test_error_count_is_not_success(self):
        with self.assertRaises(ValueError):
            runtime.compiler_summary('Compile Successful! 1 Errors, 0 Warnings,File Size:600')

    def test_partial_log_is_not_success(self):
        with self.assertRaises(ValueError):
            runtime.compiler_summary('File Check Finish')

    def test_output_must_be_new_unique_and_match_size(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work = root / 'work'; work.mkdir()
            now = time.time()
            path = work / 'old.tft'; path.write_bytes(b'x' * 600)
            os.utime(path, (now - 60, now - 60))
            with patch.object(runtime, 'WORK', work), patch.object(runtime, 'PREFIX', root):
                with self.assertRaises(ValueError):
                    runtime.locate_output({'bytes': 600}, now)
                current = work / 'new.tft'; current.write_bytes(b'x' * 700)
                with self.assertRaises(ValueError):
                    runtime.locate_output({'bytes': 600}, now)
                current.write_bytes(b'x' * 600)
                self.assertEqual(runtime.locate_output({'bytes': 600}, now), current)
                (work / 'ambiguous.tft').write_bytes(b'x' * 600)
                with self.assertRaises(ValueError):
                    runtime.locate_output({'bytes': 600}, now)

    def test_truncated_and_corrupt_tft_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'test.tft'
            for data in (b'', b'0' * 600):
                p.write_bytes(data)
                with self.assertRaises(ValueError):
                    runtime.validate_tft(p)

if __name__ == '__main__':
    unittest.main()
