import os
import unittest
from contextlib import redirect_stdout
from io import StringIO

from fhir_loader import fhir_loader
from tests import cwd, server


class FHIRLoaderTestCase(unittest.TestCase):
    def test_help(self):
        outf = StringIO()
        with redirect_stdout(outf):
            try:
                fhir_loader(['x', 'y', "-h"])
            except SystemExit:
                pass
        self.assertEqual("""usage: fhir_loader [-h] [-f {json,xml,ttl}] [-r] server files [files ...]

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
                        applicable if file is a directory""", outf.getvalue().strip())

    def test_load_file(self):
        fpath = os.path.join(cwd, 'data', 'jhu-asthma-lab-1.json')
        self.assertEqual(0, fhir_loader([server, fpath]))


if __name__ == '__main__':
    unittest.main()
