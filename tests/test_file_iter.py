import os
import unittest
from pprint import pprint
from typing import Tuple, List

from fhir_loader import file_iter
from tests import cwd, datadir


class FileIteratorTestCase(unittest.TestCase):
    iterdir = os.path.join(datadir, 'iterdir')

    def eval_result(self, expected_names: List[str], rslt: List[Tuple[str, str]]) -> None:
        seen = set()
        for fn, actual in rslt:
            with open(fn) as f:
                expected = f.read()
            self.assertEqual(actual, expected)
            seen.add(os.path.relpath(fn, cwd))
        self.assertEqual(set(expected_names), seen)

    def test_fname_iter(self):
        """ Test directory option of filename iterator """
        files = [e for e in file_iter(self.iterdir)]
        self.eval_result([
            'data/iterdir/group101.json',
            'data/iterdir/group101.xml',
            'data/iterdir/group101.ttl'], files)

        files = [e for e in file_iter(self.iterdir, recursive=True)]
        self.eval_result([
            'data/iterdir/group101.json',
            'data/iterdir/group101.xml',
            'data/iterdir/subdir1/subsubdir/group103.json',
            'data/iterdir/subdir1/group102.ttl',
            'data/iterdir/subdir1/group102.json',
            'data/iterdir/group101.ttl'], files)

        files = [e for e in file_iter(self.iterdir, recursive=True, suffix='json')]
        self.eval_result([
            'data/iterdir/group101.json',
            'data/iterdir/subdir1/subsubdir/group103.json',
            'data/iterdir/subdir1/group102.json'], files)

        files = [e for e in file_iter(self.iterdir, recursive=True, suffix='.json')]
        self.eval_result([
            'data/iterdir/group101.json',
            'data/iterdir/subdir1/subsubdir/group103.json',
            'data/iterdir/subdir1/group102.json'], files)
        with self.assertRaises(FileNotFoundError):
            [e for e in file_iter(datadir + 'x')]

    def test_single_file_iter(self):
        """ Test text option option of filename iterator """
        fname = os.path.join(self.iterdir, 'group101.json')
        files = [e for e in file_iter(fname)]
        self.eval_result([os.path.relpath(fname, cwd)], files)

    def test_raw_data_iter(self):
        """ Test text option option of filename iterator """
        self.assertEqual([('', '{\n    "test": 1\n}')], list(file_iter("""{
    "test": 1
}""")))

    def test_url_iter(self):
        """ Test the URL iterator"""
        files = [e for e in file_iter("http://hl7.org/fhir/observation-example-f001-glucose.xml")]
        self.assertEqual(1, len(files))
        self.assertTrue('UCUM code mmol/L' in files[0][1])


if __name__ == '__main__':
    unittest.main()
