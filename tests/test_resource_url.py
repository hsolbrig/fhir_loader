import os
import unittest

from fhir_loader import resource_url
from tests import datadir

test_server = "http://localhost:88/baseR4"
urltestdir = os.path.join(datadir, 'urltestdir')


class ResourceURLTestCase(unittest.TestCase):
    @staticmethod
    def do_test(fname) -> str:
        with open(os.path.join(urltestdir, fname)) as f:
            text = f.read()
        return resource_url(test_server, text)

    def test_resource_url(self):
        self.assertEqual('http://localhost:88/baseR4/ClinicalProfile/jhu-asthma-profile-33-labs?_format=json&_pretty=true',
                         self.do_test('jhu-asthma-lab-33.json'))
        self.assertEqual('http://localhost:88/baseR4/ClinicalProfile/jhu-asthma-profile-33-labs?_format=xml&_pretty=true',
                         self.do_test('jhu-asthma-lab-33.xml'))
        self.assertEqual('http://localhost:88/baseR4/ClinicalProfile/None?_format=ttl&_pretty=true',
                         self.do_test('jhu-asthma-lab-33.ttl'))
        with self.assertRaises(ValueError):
            self.do_test('jhu-asthma-lab-33.csv')


if __name__ == '__main__':
    unittest.main()
