import pytest
from pathlib import Path, PurePosixPath
import bz2, gzip
from pysftp import Connection, CnOpts

from ftp_loader import loader
from ftp_loader.main import read_config, download_data
from tests.test_loader import create_temp_file


def clear_dir(path):
    for p in path.iterdir():
        if p.is_dir():
            clear_dir(p)
            print('Delete dir ' + str(p))
            p.rmdir()
        else:
            print('Delete file ' + str(p))
            p.unlink()
            

@pytest.fixture(scope='function')
def ftp_server1(sftpserver):
    data = {
        'project1': {
            'test_data1': {
                'file1.txt.bz2': bz2.compress(b'File1 content'),
                'file2.txt.bz2': bz2.compress(b'File2 content'),
            },
            'test_data2': {
                'container': {
                    'file21.csv.gz': gzip.compress(b'File21 content'),
                    'file22.csv.gz': gzip.compress(b'FIle22 content')
                },
                'container2.txt': 'Container2 content'
            }
        },
        'project2': {
            'readme.txt': 'Readme file',
            'data3': {
                'file31.txt': 'File31 content',
                'file32.txt': 'File32 content'
            }
        }
    }
    with sftpserver.serve_content(data):
        yield sftpserver


@pytest.fixture(scope='function')
def config1(tmp_path):
    f = tmp_path / 'ftp-config.toml'
    f.write_text('\n'.join([
        'url = "localhost"',
        'path = "project1"',
        '[[files]]',
        'dst = ' + '"{0}"'.format(str(tmp_path / "work1")).replace('\\', '\\\\'),
        'src = "test_data1"', 
        'arch = "bz2"', 
        'names = ["file1.txt", "file2.txt"]',
        '[[files]]',
        'dst = ' + '"{0}"'.format(str(tmp_path / "work2/cont2")).replace('\\', '\\\\'), 
        'src = "test_data2/container"', 
        'arch = "gz"',
        'names = ["file21.csv", "file22.csv"]',
        '[[files]]', 
        'dst = ' + '"{0}"'.format(str(tmp_path / "work2")).replace('\\', '\\\\'), 
        'src = "test_data2"', 
        'names = ["container2.txt"]'
    ]))
    yield
    clear_dir(tmp_path)


@pytest.mark.parametrize('download_cnt', [5])
def test_download(ftp_server1, config1, tmp_path, download_cnt):
    url, file_trans = read_config(tmp_path / 'ftp-config.toml')
    port = ftp_server1.port
    cnopts = CnOpts()
    cnopts.hostkeys = None
    downloads = download_data(url, 'user1', '1234', file_trans, False, port=port, cnopts=cnopts)
    assert len(downloads) == download_cnt


@pytest.fixture(scope='function')
def file_tree1(tmp_path):
    create_temp_file(tmp_path / "work1", 'file1.txt', 'Not File1 content', False)
    create_temp_file(tmp_path / "work2/cont2", 'file21.csv', 'Not File21 content', False)
    #create_temp_file(tmp_path / "work2", 'container2.txt', 'Not Container2 content', False)
    create_temp_file(tmp_path / "work2/cont2", 'file22.csv.gz', gzip.compress(b'Not file 22'), True)
    yield
    clear_dir(tmp_path)


@pytest.mark.parametrize('download_cnt, skip', [(5, False), (2, True)])
def test_download2(ftp_server1, config1, file_tree1, tmp_path, download_cnt, skip):
    url, file_trans = read_config(tmp_path / 'ftp-config.toml')
    port = ftp_server1.port
    cnopts = CnOpts()
    cnopts.hostkeys = None
    downloads = download_data(url, 'user1', '1234', file_trans, skip, port=port, cnopts=cnopts)
    assert len(downloads) == download_cnt

