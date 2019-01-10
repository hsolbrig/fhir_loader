# FHIR Loader
Simple python tools for managing data in a FHIR repository

[![Pyversions](https://img.shields.io/pypi/pyversions/fhir_loader.svg)](https://pypi.python.org/pypi/fhir_loader)

[![PyPi](https://img.shields.io/pypi/v/fhir_loader.svg)](https://pypi.python.org/pypi/fhir_loader)

## Revision history
* 0.0.1 - Initial commit -- handles PUT and not much else

## Usage

### Command line
```text
usage: fhir_loader [-h] [-f {json,xml,ttl}] [-r] server files [files ...]

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
```
** Example **

Transfer the glucose observation from the HL7 FHIR Server to a local HAPI server
```bash
fhir_loader http://35.174.101.217:88 http://hl7.org/fhir/observation-example-f001-glucose.xml
```

Upload the contents of a local directory of resources: