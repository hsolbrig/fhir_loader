import os

cwd = os.path.abspath(os.path.dirname(__file__))
datadir = os.path.join(cwd, 'data')

# ***** server must be pointed at a working FHIR server for test_loader tests to work
server = "http://localhost:88/baseR4/"
# server=None
