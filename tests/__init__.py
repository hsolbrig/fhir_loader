import os

from fhir_loader import fhir_loader

cwd = os.path.abspath(os.path.dirname(__file__))
datadir = os.path.join(cwd, 'data')

# ***** server must be pointed at a working FHIR server for test_loader tests to work
# server = "http://localhost:88/baseR4/"
server = "http://35.174.101.217:88/baseR4"
# server=None

# Preload the groups so the rest of the tests work
fhir_loader([server, os.path.join(datadir, 'preload'), '-v', '-r'])