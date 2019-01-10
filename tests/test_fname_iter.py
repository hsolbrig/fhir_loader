import os
import unittest

import requests

from fhir_loader import filename_iter
from tests import cwd, datadir


class FilenameIteratorTestCase(unittest.TestCase):
    iterdir = os.path.join(datadir, 'iterdir')

    def test_fname_iter(self):
        """ Test directory option of filename iterator """
        files = [os.path.relpath(fn, cwd) for fn in filename_iter(self.iterdir)]
        self.assertEqual([
            'data/iterdir/group101.json',
            'data/iterdir/group101.xml',
            'data/iterdir/group101.ttl'], files)

        files = [os.path.relpath(fn, cwd) for fn in filename_iter(self.iterdir, recursive=True)]
        self.assertEqual([
            'data/iterdir/group101.json',
            'data/iterdir/group101.xml',
            'data/iterdir/subdir1/subsubdir/group103.json',
            'data/iterdir/subdir1/group102.ttl',
            'data/iterdir/subdir1/group102.json',
            'data/iterdir/group101.ttl'], files)

        files = [os.path.relpath(fn, cwd) for fn in filename_iter(self.iterdir, recursive=True, suffix='json')]
        self.assertEqual([
            'data/iterdir/group101.json',
            'data/iterdir/subdir1/subsubdir/group103.json',
            'data/iterdir/subdir1/group102.json'], files)

        files = [os.path.relpath(fn, cwd) for fn in filename_iter(self.iterdir, recursive=True, suffix='.json')]
        self.assertEqual([
            'data/iterdir/group101.json',
            'data/iterdir/subdir1/subsubdir/group103.json',
            'data/iterdir/subdir1/group102.json'], files)
        with self.assertRaises(FileNotFoundError):
            [e for e in filename_iter(datadir + 'x')]

    def test_single_file_iter(self):
        """ Test text option option of filename iterator """
        fname = os.path.join(self.iterdir, 'group101.json')
        files = [os.path.relpath(e, cwd) for e in filename_iter(fname)]
        self.assertEqual([os.path.relpath(fname, cwd)], files)

    def test_raw_data_iter(self):
        """ Test text option option of filename iterator """
        files = [e for e in filename_iter("""{
    "test": 1
}""")]
        self.assertEqual(['{\n    "test": 1\n}'], list(filename_iter("""{
    "test": 1
}""")))

    def test_url_iter(self):
        """ Test the URL iterator"""
        files = [e for e in filename_iter("http://hl7.org/fhir/observation-example-f001-glucose.xml")]
        self.assertEqual(1, len(files))
        with self.assertRaises(requests.exceptions.HTTPError):
            [e for e in filename_iter("http://hl7.org/fhir/observation-example-f001-glucosez.xml")]


if __name__ == '__main__':
    unittest.main()
