import glob
import os
import sys
from argparse import ArgumentParser
from io import StringIO
from typing import Union, List, Iterator, Callable, Optional, Tuple
from xml.etree.ElementTree import ElementTree

import requests
from jsonasobj import loads
from rdflib import Graph, Namespace, RDF

FHIR = Namespace("http://hl7.org/fhir/")
FHIR_XML_URI = str(FHIR)[:-1]


def filename_iter(path: str, *, suffix: str = '', recursive: bool = False) -> Iterator[str]:
    """
    Return a filename iterator

    :param path: file, directory, url or actual data
    :param suffix: suffix filter for directory iteration
    :param recursive: True means recurse in directory iteration
    :return: iterator of file names
    """

    if '\n' in path:
        # Just data
        yield path

    elif ':/' in path:
        # URL
        response = requests.head(path)
        if response.status_code == 200:
            yield path
        else:
            raise requests.exceptions.HTTPError(response.reason)
    elif os.path.exists(path):
        if os.path.isdir(path):
            # Directory
            if suffix and not suffix.startswith('.'):
                suffix = '.' + suffix
            if not path.endswith('/'):
                path = path + '/'
            for f in glob.iglob(path + '**', recursive=recursive):
                if os.path.isfile(f) and (not suffix or f.endswith(suffix)):
                    yield f
        else:
            # Simple file
            yield path
    else:
        raise FileNotFoundError(f"{path} does not exist")


def file_iter(path: str, *, suffix: str = '', recursive: bool = False,
              fname_iter: Optional[Callable[[str, str, bool], Iterator[str]]] = None) \
        -> Iterator[Tuple[str, str]]:
    """
    Return a file contents iterator

    :param path: file, directory, url or actual data
    :param suffix: suffix filter for directory iteration
    :param recursive: True means recurse in directory iteration
    :param fname_iter: iterator of file names (default: filename_iter)

    :return: Iterator for filename, file contents
    """
    if fname_iter is None:
        fname_iter = filename_iter

    for fname in fname_iter(path, suffix=suffix, recursive=recursive):
        if '\n' in fname:
            yield '', fname
        elif ':/' in fname:
            response = requests.get(path)
            if response.status_code == 200:
                yield fname, response.text
            else:
                raise requests.exceptions.HTTPError(response=response)
        else:
            with open(fname) as f:
                txt = f.read()
            yield fname, txt


def resource_url(server: str, text: str) -> str:
    def as_url(resource_name, resource_format) -> str:
        return f"{server}{'/' if not server.endswith('/') else ''}{resource_name}" \
               f"?_format={resource_format}&_pretty=true"

    """ Create a server URL for uploading text """
    if text.startswith('<'):
        # XML
        doc = ElementTree().parse(source=StringIO(text))
        '{http://hl7.org/fhir}ClinicalProfile'
        typ = doc.tag.replace(f'{{{FHIR_XML_URI}}}', '')
        return as_url(typ, 'xml')
    elif text.startswith('{'):
        # JSON
        json_text = loads(text)
        return as_url(json_text.resourceType, 'json')
    elif text.startswith('@'):
        g = Graph()
        g.parse(data=text, format='turtle')
        focus = g.value(predicate=FHIR.nodeRole, object=FHIR.treeRoot)
        typ_uri = g.value(subject=focus, predicate=RDF.type)
        typ = str(typ_uri).replace(str(FHIR), '')
        return as_url(typ, 'ttl')
    else:
        raise ValueError("Unrecognized file type")


def create(server: str, files: List[str], format: str, recursive: bool, verbose: bool = False) -> List[Tuple[str, bool]]:
    """
    Upload files to server

    :param server: Target FHIR server
    :param files: File specification(s)
    :param format: file format if specification(s) name directories
    :param recursive: recurse in directories if specification(s) name directories
    :param verbose: True means speak to me
    :return: List of filename/success indicators
    """
    rval = []
    for filepath in files:
        for filename, text in file_iter(filepath, suffix=format, recursive=recursive):
            server_url = resource_url(server, text)
            if verbose:
                print(f"POST {filename} to {server_url}... ", end='')
            response = requests.post(server_url, data=text)
            if verbose:
                print(f"{'OK' if response.status_code == 200 else response.reason}")
            rval.append((filename, response.status_code))
    return rval


def genargs() -> ArgumentParser:
    """
    Create a command line parser

    :return: parser
    """
    parser = ArgumentParser(prog="fhir_loader")
    parser.add_argument("server", help="URL of FHIR server")
    parser.add_argument("files", help="URL(s), file(s) and/or directory(s) to load", nargs='+')
    parser.add_argument("-f", '--format', help="File format. Used as directory suffix filter. If not specified, the "
                                               "format is determined from the suffix or file content",
                        choices=['json', 'xml', 'ttl'])
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="True means recursively descend directory.  Only applicable if file is a directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Talk while working")
    return parser


def fhir_loader(args: Union[str, List[str]]) -> int:
    """
    FHIR data loader

    :param args: parameter list as defined by genargs above
    :return: 0 if success 1 if one or more uploads failed
    """
    opts = genargs().parse_args(args)
    rslts = create(opts.server, opts.files, opts.format, opts.recursive, opts.verbose)
    for rslt in rslts:
        if rslt[1] != 200:
            print(f"{rslt[0]} failure: {rslt[1]}", file=sys.stderr)
    return int(bool(any(r[1] != 200 for r in rslts)))

