"""Fast tests for the production-image probe; no Docker or app dependencies."""
import importlib.util
import json
import struct
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

    def test_elf_dependencies_are_dynamic_entries_not_incidental_strings(self):
        for wide in (False, True):
            blob = bytearray(768)
            blob[:6] = b'\x7fELF' + bytes([2 if wide else 1, 1])
            struct.pack_into('<Q' if wide else '<I', blob, 32 if wide else 28, 64)
            struct.pack_into('<HH', blob, 54 if wide else 42, 56 if wide else 32, 2)
            if wide:
                struct.pack_into('<IIQQQQQQ', blob, 64, 1, 0, 0, 4096, 0, 768, 768, 0)
                struct.pack_into('<IIQQQQQQ', blob, 120, 2, 0, 256, 4352, 0, 48, 48, 0)
            else:
                struct.pack_into('<IIIIIIII', blob, 64, 1, 0, 4096, 0, 768, 768, 0, 0)
                struct.pack_into('<IIIIIIII', blob, 96, 2, 256, 4352, 0, 24, 24, 0, 0)
            fmt, step = ('<QQ', 16) if wide else ('<II', 8)
            struct.pack_into(fmt, blob, 256, 5, 4608)
            struct.pack_into(fmt, blob, 256 + step, 1, 0)
            blob[512:520] = b'libc.so\0'
            blob[600:610] = b'libc.so.6\0'
            self.assertEqual(probe.needed_libraries(blob), {'libc.so'})

    def test_wait_fails_when_deadline_expires(self):
        with patch.object(probe.time, 'monotonic', side_effect=[0, 0, 2]), patch.object(probe.time, 'sleep'):
            with self.assertRaisesRegex(AssertionError, 'did not become ready'):
                probe.wait_for(lambda: (_ for _ in ()).throw(OSError('unavailable')), seconds=1)

if __name__ == '__main__':
    unittest.main()
