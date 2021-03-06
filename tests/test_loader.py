import os
import unittest
from contextlib import redirect_stdout
from io import StringIO

from fhir_loader import fhir_loader
from tests import cwd, server, datadir


@unittest.skipIf(server is None, "tests/__init__.py/server must be set")
class FHIRLoaderTestCase(unittest.TestCase):

    def test_help(self):
        outf = StringIO()
        with redirect_stdout(outf):
            try:
                fhir_loader(['x', 'y', "-h"])
            except SystemExit:
                pass
        self.assertEqual("""usage: fhir_loader [-h] [-f {json,xml,ttl}] [-r] [-v] [-p PATTERN]
                   server files [files ...]

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
  -v, --verbose         Talk while working
  -p PATTERN, --pattern PATTERN
                        File match pattern (RE) for directories""", outf.getvalue().strip())

    def test_load_file(self):
        """ Make sure a file can be loaded to the server """
        fpath = os.path.join(cwd, 'data', 'jhu-asthma-lab-1.json')
        self.assertEqual(0, fhir_loader([server, fpath]))

    def test_load_formats(self):
        """ Make sure all possible formats work """
        asthma_elements = os.path.join(datadir, 'urltestdir', 'jhu-asthma-lab-33')
        self.assertEqual(0, fhir_loader(["-v", server, asthma_elements + ".xml"]))
        self.assertEqual(0, fhir_loader([server, asthma_elements + ".json"]))

    def test_large_upload(self):
        """ Upload a large file to the server """
        fpath = os.path.join(cwd, 'data', 'jhu-asthma-lab-33.json')
        self.assertEqual(0, fhir_loader([server, fpath]))

    def test_verbose(self):
        """ Test the server verbose option """
        fpath = os.path.join(cwd, 'data')
        outf = StringIO()
        with redirect_stdout(outf):
            fhir_loader(["-v", server, fpath])
        shortened_response = outf.getvalue().replace(cwd, '').strip()
        self.assertEqual("""PUT /data/jhu-asthma-lab-33.json to http://localhost:88/baseR4/ClinicalProfile/jhu-asthma-profile-33-labs?_format=json&_pretty=true... OK
PUT /data/jhu-asthma-lab-1.json to http://localhost:88/baseR4/ClinicalProfile/jhu-asthma-profile-1-labs?_format=json&_pretty=true... OK
PUT /data/jhu-asthma-lab-2.json to http://localhost:88/baseR4/ClinicalProfile/jhu-asthma-profile-2-labs?_format=json&_pretty=true... OK""", shortened_response)



if __name__ == '__main__':
    unittest.main()
