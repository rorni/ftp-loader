# -*- coding: utf-8 -*-

from pathlib import Path, PurePosixPath
import bz2, gzip
from enum import Enum

from tomlkit import parse


class ErrorCode(Enum):
    REMOTE_NOT_A_FOLDER = 1
    LOCAL_NOT_A_FOLDER = 2
    REMOTE_FILE_NOT_EXISTS = 3
    LOCAL_FILE_NOT_EXISTS = 4
    UNSUPPORTED_ARCHIVE = 5
    NOT_COMPRESSED = 6
    LOCAL_ALREADY_EXISTS = 7
    REMOTE_ALREADY_EXISTS = 8


class LoaderException(Exception):
    def __init__(self, code, message=''):
        self.code = code
        self.message = message


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


def create_file_transfers(path, files):
    """Creates a list of FileTransfer objects.

    Paramteters
    -----------
    path : str
        Project base path at FTP.
    files : list[dict]


    Returns
    -------
    file_transfers : list[FileTransfer]
        List of FileTransfer instances.
    """
    file_transfers = []
    for case in files:
        dst_path = Path(case['dst'])
        src_path = PurePosixPath(path, case['src'])
        arch = case.get('arch', None)
        for name in case['names']:
            file_transfers.append(FileTransfer(name, dst_path, src_path, arch))
    return file_transfers


class FileTransfer:
    """Represents file to be transferred.
    
    Parameters
    ----------
    name : str
        File name.
    local_path : str
        Path to the file in local folder.
    remote_path : str
        Path to the file in remote folder.
    arch : str
        Archive specifier. Default - None.
    """
    def __init__(self, name, local_path, remote_path, arch=None):
        self._name = name
        self._local_path = Path(local_path)
        self._remote_path = PurePosixPath(remote_path)
        self._arch = arch

    def create_local_folder(self):
        """Creates local folder to store files."""
        path = self._local_path
        path.mkdir(parents=True, exist_ok=True)
        if not path.is_dir():
            message = "File {0} exsists but folder is expected".format(path)
            raise LoaderException(ErrorCode.LOCAL_NOT_A_FOLDER, message)

    @property
    def _arch_name(self):
        if self._arch is None:
            return self._name
        return '{0}.{1}'.format(self._name, self._arch)

    def create_remote_folder(self, connection):
        """Creates remote folder to store files.

        Paramters
        ---------
        connection : pysftp.Connection
            Connection object.
        """
        try:
            connection.makedirs(str(self._remote_path))
        except OSError:
            message = "Remote file {0} exists but folder is expected".format(self._remote_path)
            raise LoaderException(ErrorCode.REMOTE_NOT_A_FOLDER, message)

    @staticmethod
    def check_local_file_exists(local_file, opt_message=''):
        if not local_file.exists():
            message = "  ! File {0} does not exists. {1}".format(local_file, opt_message)
            raise LoaderException(ErrorCode.LOCAL_FILE_NOT_EXISTS, message)

    @staticmethod
    def check_remote_file_exists(connection, remote_file, opt_message=''):
        if not connection.exists(str(remote_file)):
            message = "  ! Remote file {0} does not exist. {1}".format(remote_file, opt_message)
            raise LoaderException(ErrorCode.REMOTE_FILE_NOT_EXISTS, message)

    @staticmethod
    def check_local_or_remove(local_file, skip, opt_message=''):
        if local_file.exists():
            if skip:
                message = "  * File {0} already exists. {1}".format(local_file, opt_message)
                raise LoaderException(ErrorCode.LOCAL_ALREADY_EXISTS, message)
            local_file.unlink()

    @staticmethod
    def check_remote_or_remove(connection, remote_file, skip, opt_message=''):
        if connection.exists(str(remote_file)):
            if skip:
                message = "  * Remote file {0} already exists. {1}".format(remote_file, opt_message)
                raise LoaderException(ErrorCode.REMOTE_ALREADY_EXISTS, message)
            connection.remove(remote_file)

    def decompress(self, skip_existing=True, remove_archive=True):
        """Decompress loaded archive.

        Paramters
        ---------
        skip_existing : bool
            To skip already existing files. Default: True.
        remove_archive : bool
            To remove archive file after extraction. Default: True
        """
        if not self._arch:
            return
        dst_file = self._local_path / self._name
        src_file = self._local_path / self._arch_name
        self.check_local_file_exists(src_file, 'Nothing to decompress...')
        self.check_local_or_remove(dst_file, skip_existing, "Skipping...")
        dcmp = get_archivator(self._arch)
        with open(dst_file, 'wb') as fdst:
            with dcmp.open(src_file, 'rb') as fsrc:
                message = '   * Extracting: {0} ...'.format(src_file)
                print(message)
                fdst.write(fsrc.read())
        if remove_archive:
            message = "  * Removing archive file: {0} ...".format(src_file)
            print(message)

    def compress(self, skip_existing=True):
        """Compress data file.

        Parameters
        ----------
        skip_existing : bool
            To skip already archived files. Default: True.
        """
        if not self._arch:
            return
        dst_file = self._local_path / self._arch_name
        src_file = self._local_path / self._name
        self.check_local_file_exists(src_file, 'Nothing to compress...')
        self.check_local_or_remove(dst_file, skip_existing, "Skipping...")
        dcmp = get_archivator(self._arch)
        with open(dst_file, 'wb') as fdst:
            with open(src_file, 'rb') as fsrc:
                message = '  * Compressing: {0} ...'.format(src_file)
                print(message)
                fdst.write(dcmp.compress(fsrc.read()))

    def clear(self):
        """Clears local data file."""
        orig_file = self._local_path / self._name
        arch_file = self._local_path / self._arch_name
        if orig_file.exists():
            message = "  * Removing {0}...".format(orig_file)
            print(message)
            orig_file.unlink()
        if arch_file.exists():
            message = "  * Removing {0}...".format(arch_file)
            print(message)
            arch_file.unlink()

    def download(self, connection, skip_existing=True):
        """Downloads file from the FTP.

        Parameters
        ----------
        connection : pysftp.Connection
            Connection object.
        skip_existing : bool
            To skip already existing files. Default: True.
        """
        dst_file = self._local_path / self._arch_name
        dst_file2 = self._local_path / self._name
        src_file = str(self._remote_path / self._arch_name)
        self.check_remote_file_exists(connection, src_file, 'Nothing to download...')
        self.check_local_or_remove(dst_file, skip_existing, "Skipping...")
        self.check_local_or_remove(dst_file2, skip_existing, "Skipping...")
        self.create_local_folder()
        print('  * Downloading: {0} ...'.format(src_file))
        connection.get(src_file, dst_file)

    def upload(self, connection, skip_existing=True):
        """Uploads file to FTP.

        Parameters
        ----------
        connection : pysftp.Connection
            Connection object.
        skip_existing : bool
            To skip already Uploaded files. Default: True.
        """
        dst_file = str(self._remote_path / self._arch_name)
        src_file = self._local_path / self._arch_name
        self.check_local_file_exists(src_file, 'Nothing to upload...')
        self.check_remote_or_remove(connection, dst_file, skip_existing, "Skipping...")
        self.create_remote_folder(connection)
        print('  * Uploading: {0} ...'.format(src_file))
        connection.put(src_file, dst_file)        
                

def get_archivator(arch):
    if arch == 'bz2':
        return bz2
    elif arch == 'gz':
        return gzip
    else:
        message = "  ! Unsupported archive format {0}. Skipping".format(arch)
        raise LoaderException(ErrorCode.UNSUPPORTED_ARCHIVE, message)

