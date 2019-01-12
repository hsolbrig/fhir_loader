import os
import unittest
from contextlib import redirect_stdout
from io import StringIO

from fhir_loader import fhir_loader
from tests import cwd, server


class FHIRLoaderTestCase(unittest.TestCase):
    def setUpClass(cls):
        """ Make sure that the target files are present """

    def test_help(self):
        outf = StringIO()
        with redirect_stdout(outf):
            try:
                fhir_loader(['x', 'y', "-h"])
            except SystemExit:
                pass
        self.assertEqual("""usage: fhir_loader [-h] [-f {json,xml,ttl}] [-r] [-v] server files [files ...]

positional arguments:
  server                URL of FHIR server
  files                 URL(s), file(s) and/or directory(s) to load

optional arguments:
  -h, --help            show this help message and exit
  -f {json,xml,ttl}, --format {json,xml,ttl}
                        File format. Used as directory suffix filter. If not
                        specified, the format is determined from the suffix or
                        file content
  -r, --recursive       True means recursively descend directory. Only
                        applicable if file is a directory
  -v, --verbose         Talk while working""", outf.getvalue().strip())

    @unittest.skipIf(server is None, "tests/__init__.py/server must be set")
    def test_load_file(self):
        """ Make sure a file can be loaded to the server """
        fpath = os.path.join(cwd, 'data', 'jhu-asthma-lab-1.json')
        self.assertEqual(0, fhir_loader([server, fpath]))

    @unittest.skipIf(server is None, "tests/__init__.py/server must be set")
    def test_large_upload(self):
        """ Upload a large file to the server """
        fpath = os.path.join(cwd, 'data', 'jhu-asthma-lab-33.json')
        self.assertEqual(0, fhir_loader([server, fpath]))

    @unittest.skipIf(server is None, "tests/__init__.py/server must be set")
    def test_verbose(self):
        """ Test the server verbose option """
        fpath = os.path.join(cwd, 'data')
        outf = StringIO()
        with redirect_stdout(outf):
            fhir_loader(["-v", server, fpath])
        self.assertEqual("""Posting /Users/solbrig/git/hsolbrig/fhir_loader/tests/data/jhu-asthma-lab-1.json...OK
Posting /Users/solbrig/git/hsolbrig/fhir_loader/tests/data/jhu-asthma-lab-2.json...OK""", outf.getvalue().strip())



if __name__ == '__main__':
    unittest.main()
