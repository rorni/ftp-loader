# -*- coding: utf-8 -*-

from pathlib import Path
from pysftp import Connection
import bz2, gzip

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
    path : str
        Project's path
    transfer_cases : list
        List of files to be transfered.
    """
    with open(filename) as f:
        text = f.read()
    result = parse(text)
    path = result['path']
    server_url = result['url']
    return server_url, path, result['files']


def select_paths_for_download(path, files, **kwargs):
    """Selects files to be downloaded.

    Parameters
    ----------
    path : str
        Common path to the project at FTP.
    files : list of dict
        List of files.
    
    Returns
    -------
    file_pairs : list
        A list of tuples - (dst_file, src_file).
    """
    file_pairs = []
    for case in files:
        dst_path = Path(case['dst'])
        src_path = Path(path, case['src'])
        arch = case.get('arch', None)
        if arch:
            ext = '.' + arch
        else: 
            ext = ''
        for name in case['names']:
            filename = name + ext
            dst_file = dst_path / filename
            src_file = src_path / filename
            if check_to_download(dst_file, **kwargs):
                file_pairs.append((src_file.as_posix(), str(dst_file)))
    return file_pairs


def check_to_download(dst_file, exists=True):
    if exists:
        return not dst_file.exists()
    else:
        return True


def load_data(user, passwd, url, files):
    """Loads data.

    Parameters
    ----------
    user : str
        User name to get access to FTP.
    passwd : str
        Password.
    url : str
        Base url.
    files : list of dict
        Files to be downloaded.
    """
    downloaded = []
    with Connection(url, user, password=passwd) as conn:
        print(conn.pwd)
        for remote_path, local_path in files:
            Path(local_path).parent.mkdir(exist_ok=True, parents=True)
            print('   * Downloading: {0} ...'.format(remote_path))
            conn.get(remote_path, local_path)
            downloaded.append(local_path)
    return downloaded


def decompress(files):
    """Decompresses downloaded files."""
    for filepath in files:
        path = Path(filepath)
        ext = path.suffix
        if ext == '.bz2':
            base = bz2
        elif ext == '.gz':
            base = gzip
        else:
            continue
        with open(path.stem, 'wb') as fdst:
            with base.open(path, 'rb') as fsrc:
                print('   * Extracting: {0} ...'.format(path))
                fdst.write(fsrc.read())


def get_decompressor(arch):
    if arch == 'bz2':
        return bz2.decompress
    elif arch == 'gz':
        return gzip.decompress
    else:
        raise ValueError('Unsupported archive type: {0}'.format(arch))

