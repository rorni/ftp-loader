# -*- coding: utf-8 -*-

import argparse
import getpass

from . import loader


def download_data(conf_file, **options):
    url, path, files = loader.load_config(conf_file)
    file_pairs = loader.select_paths_for_download(path, files, **options)

    print('Start downloading project data from {0}'.format(url))
    print('Please, enter your login and password to access FTP server. \n')
    user = input('Username: ')
    passwd = getpass.getpass('Password: ')
    
    downloaded = loader.load_data(user, passwd, url, file_pairs)
    loader.decompress(downloaded)


def arg_parser():
    parser = argparse.ArgumentParser(prog='FTP Loader')

    parser.add_argument(
        '-c', '--config', type=str, nargs='?', default='ftp-config.toml',
        help='configuration file name.'
    )

    args = parser.parse_args()
    return dict(vars(args))


def main():
    args = arg_parser()
    download_data(args['config'])
