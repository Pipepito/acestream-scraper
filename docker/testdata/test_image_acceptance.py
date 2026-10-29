"""Fast tests for the production-image probe; no Docker or app dependencies."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('probe', Path(__file__).with_name('image_acceptance.py'))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

class ImageProbeTests(unittest.TestCase):
    def test_engine_version_must_match_manifest(self):
        with patch.object(probe, 'fetch', return_value=json.dumps({'result': {'version': '3.2.11'}}).encode()):
            probe.engine_version('127.0.0.1', '3.2.11')
            with self.assertRaises(AssertionError):
                probe.engine_version('127.0.0.1', '3.2.17')

    def test_engine_errors_never_pass(self):
        with patch.object(probe, 'fetch', return_value=b'{"error":"starting","result":{}}'):
            with self.assertRaises(AssertionError):
                probe.engine_version('127.0.0.1', '3.2.11')

    def test_wait_fails_when_deadline_expires(self):
        with patch.object(probe.time, 'monotonic', side_effect=[0, 0, 2]), patch.object(probe.time, 'sleep'):
            with self.assertRaisesRegex(AssertionError, 'did not become ready'):
                probe.wait_for(lambda: (_ for _ in ()).throw(OSError('unavailable')), seconds=1)

if __name__ == '__main__':
    unittest.main()
