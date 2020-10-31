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
    pass

