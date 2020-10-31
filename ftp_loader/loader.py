# -*- coding: utf-8 -*-

from tomlkit import parse


def load_config(filename="ftp-config.toml"):
    """Loads ftp configuration.

    Parameters
    ----------
    filename : str
        FTP configuration filename. Default: ftp-config.toml.

    Returns
    -------
    server_url : str
        URL of FTP server.
    transfer_cases : list
        List of files to be transfered.
    """
    with open(filename) as f:
        text = f.read()
    result = parse(text)
    path = result['path']
    if len(path) > 0 and not path.endswith('/'):
        path += '/'
    server_url = result['url'] + '/' + path
    return server_url, result['files']

