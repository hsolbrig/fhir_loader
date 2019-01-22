import glob
import os
import re
import sys
from argparse import ArgumentParser
from io import StringIO
from typing import Union, List, Iterator, Callable, Optional, Tuple
from xml.etree.ElementTree import ElementTree

import requests
from jsonasobj import loads
from rdflib import Graph, Namespace, RDF
from requests import Response

FHIR = Namespace("http://hl7.org/fhir/")
FHIR_XML_URI = str(FHIR)[:-1]


def filename_iter(path: str, *, suffix: str = '', recursive: bool = False, pattern: Optional[str] = None) \
        -> Iterator[str]:
    """
    Return a filename iterator

    :param path: file, directory, url or actual data
    :param suffix: suffix filter for directory iteration
    :param recursive: True means recurse in directory iteration
    :param pattern: Match pattern
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
                fn = os.path.basename(f)
                if os.path.isfile(f) and (not pattern or re.match(pattern, fn)) and (not suffix or f.endswith(suffix)):
                    yield f
        else:
            # Simple file
            yield path
    else:
        raise FileNotFoundError(f"{path} does not exist")


def file_iter(path: str, *, suffix: str = '', recursive: bool = False, pattern: Optional[str] = None,
              fname_iter: Optional[Callable[[str, str, bool], Iterator[str]]] = None) \
        -> Iterator[Tuple[str, str]]:
    """
    Return a file contents iterator

    :param path: file, directory, url or actual data
    :param suffix: suffix filter for directory iteration
    :param recursive: True means recurse in directory iteration
    :param pattern: Match pattern for file name (RE)
    :param fname_iter: iterator of file names (default: filename_iter)

    :return: Iterator for filename, file contents
    """
    if fname_iter is None:
        fname_iter = filename_iter

    for fname in fname_iter(path, suffix=suffix, recursive=recursive, pattern = pattern):
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
    """ Create a URL out of the resource text """
    def as_url(resource_name:str, resource_format:str, resource_id:str) -> str:
        # Note that the 'json' below defines the response format.  The server is clever enough to figure out
        # what you are shipping...
        return f"{server}{'/' if not server.endswith('/') else ''}{resource_name}" \
               f"/{resource_id}?_format=json&_pretty=true"

    """ Create a server URL for uploading text """
    if text.startswith('<'):
        # XML
        doc = ElementTree().parse(source=StringIO(text))
        '{http://hl7.org/fhir}ClinicalProfile'
        typ = doc.tag.replace(f'{{{FHIR_XML_URI}}}', '')
        res_id = doc.findall('{http://hl7.org/fhir}id')[0].attrib['value']
        return as_url(typ, 'xml', res_id)
    elif text.startswith('{'):
        # JSON
        json_text = loads(text)
        return as_url(json_text.resourceType, 'json', json_text.id)
    elif text.startswith('@'):
        g = Graph()
        g.parse(data=text, format='turtle')
        focus = g.value(predicate=FHIR.nodeRole, object=FHIR.treeRoot)
        typ_uri = g.value(subject=focus, predicate=RDF.type)
        res_id = g.value(subject=focus, predicate=FHIR.id)
        typ = str(typ_uri).replace(str(FHIR), '')
        return as_url(typ, 'ttl', res_id)
    else:
        raise ValueError("Unrecognized file type")


def proc_response(response: Response) -> Optional[str]:
    if response.status_code != 200:
        return response.reason
    elif response.status_code == 400:
        outcome = loads(response.text)
        rval = []
        for issue in outcome.issue:
            rval.append(f"Severity: {issue.severity} - {issue.diagnostics}")
        return '\n'.join(rval)
    return None


def create(server: str, files: List[str], fmt: str, recursive: bool, verbose: bool = False,
           pattern: Optional[str] = None) -> List[Tuple[str, bool, Optional[str]]]:
    """
    Upload files to server

    :param server: Target FHIR server
    :param files: File specification(s)
    :param fmt: file format if specification(s) name directories
    :param recursive: recurse in directories if specification(s) name directories
    :param verbose: True means speak to me
    :param pattern: regular expression to match
    :return: Filename / success / Error message
    """
    rval = []
    for filepath in files:
        for filename, text in file_iter(filepath, suffix=fmt, recursive=recursive, pattern=pattern):
            server_url = resource_url(server, text)
            if verbose:
                print(f"PUT {filename} to {server_url}... ", end='')
            response = requests.put(server_url, data=text)
            fail_reason = proc_response(response)
            if verbose:
                print(f"{'OK' if response.status_code == 200 else response.reason}")
            rval.append((filename, response.status_code, fail_reason))
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
    parser.add_argument("-p", "--pattern", help="File match pattern (RE) for directories")
    return parser


def fhir_loader(args: Union[str, List[str]]) -> int:
    """
    FHIR data loader

    :param args: parameter list as defined by genargs above
    :return: 0 if success 1 if one or more uploads failed
    """
    opts = genargs().parse_args(args)
    rslts = create(opts.server, opts.files, opts.format, opts.recursive, opts.verbose, opts.pattern)
    for rslt in rslts:
        if rslt[1] not in (200, 201):
            print(f"{rslt[0]} failure: ({rslt[1]}) {rslt[2]}", file=sys.stderr)
    return int(bool(any(r[1] not in  (200, 201) for r in rslts)))

