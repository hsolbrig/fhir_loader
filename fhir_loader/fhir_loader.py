import glob
import os
import sys
from argparse import ArgumentParser
from typing import Union, List, Iterator, Callable, Optional, Tuple

import requests


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


def create(server: str, files: List[str], format: str, recursive: bool) -> List[Tuple[str, bool]]:
    """
    Upload files to server

    :param server: Target FHIR server
    :param files: File specification(s)
    :param format: file format if specification(s) name directories
    :param recursive: recurse in directories if specification(s) name directories
    :return: List of filename/success indicators
    """
    rval = []
    for filename in files:
        for _, text in file_iter(filename, suffix=format, recursive=recursive):
            response = requests.post(server, data=text)
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
    return parser


def fhir_loader(args: Union[str, List[str]]) -> int:
    """
    FHIR data loader

    :param args: parameter list as defined by genargs above
    :return: 0 if success 1 if one or more uploads failed
    """
    opts = genargs().parse_args(args)
    rslts = create(opts.server, opts.files, opts.format, opts.recursive)
    for rslt in rslts:
        if rslt[1] != 200:
            print(f"{rslt[0]} failure: {rslt[1]}", file=sys.stderr)
    return int(bool(any(r[1] != 200 for r in rslts)))

