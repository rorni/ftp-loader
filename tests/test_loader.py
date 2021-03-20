# -*- coding: utf-8 -*-

import pytest
from pathlib import Path, PurePosixPath
import bz2, gzip
from pysftp import Connection, CnOpts

from ftp_loader import loader


@pytest.mark.parametrize("filename, ans_url, ans_path, ans_files", [
    (
        'tests/ftp-config.toml', 'server.ftp.ru', 'projects/test-data', 
        [
            {
                'dst': 'work', 'src': 'storage', 'arch': 'bz2',
                'names': ['data1.txt', 'data2.txt']
            },
            {
                'dst': 'experiment', 'src': 'experiment', 'arch': 'gz',
                'names': ['data1.csv', 'data2.csv']
            }

        ]
    )
])
def test_config_loader(filename, ans_url, ans_path, ans_files):
    url, path, files = loader.load_config(filename)
    assert url == ans_url
    assert path == ans_path
    assert len(files) == len(ans_files)
    for case, ans in zip(files, ans_files):
        assert case['dst'] == ans['dst']
        assert case['src'] == ans['src']
        assert case['arch'] == ans['arch']
        assert case['names'] == ans['names']


@pytest.mark.parametrize("path, files, answer", [
    (
        'projects/test-data', 
        [
            {
                'dst': 'work', 'src': 'storage', 'arch': 'bz2',
                'names': ['data1.txt', 'data2.txt']
            },
            {
                'dst': 'experiment', 'src': 'experiment', 'arch': 'gz',
                'names': ['data1.csv', 'data2.csv']
            },
            {
                'dst': 'work/data', 'src': 'storage', 
                'names': ['simp.txt']
            }

        ], 
        [
            ('projects/test-data/storage', r'work', 'data1.txt', 'bz2'),
            ('projects/test-data/storage', r'work', 'data2.txt', 'bz2'),
            ('projects/test-data/experiment', r'experiment', 'data1.csv', 'gz'),
            ('projects/test-data/experiment', r'experiment', 'data2.csv', 'gz'),
            ('projects/test-data/storage', r'work/data', 'simp.txt', None)
        ]
    )
])
def test_file_transfer_creation(path, files, answer):
    file_trans = loader.create_file_transfers(path, files)
    assert len(file_trans) == len(answer)
    for ft, ans in zip(file_trans, answer):
        assert ft._remote_path == PurePosixPath(ans[0])
        assert ft._local_path == Path(ans[1])
        assert ft._name == ans[2]
        assert ft._arch == ans[3]


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
def ftp_server2(sftpserver):
    with sftpserver.serve_content({'/': {}}):
        yield sftpserver


@pytest.fixture(scope='function')
def ftp_server3(sftpserver):
    data = {
        'project1': {
            'test_data1': {
                'file1.txt.bz2': bz2.compress(b'herr'),
                'file2.txt.bz2': bz2.compress(b'herr'),
            },
            'test_data2': {
                'container': {
                    'file21.csv.gz': gzip.compress(b'herr'),
                    'file22.csv.gz': gzip.compress(b'herr')
                },
                'container2.txt': 'herr'
            }
        },
        'project2': {
            'readme.txt': 'herr',
            'data3': {
                'file31.txt': 'herr',
                'file32.txt': 'herr'
            }
        }
    }
    with sftpserver.serve_content(data):
        yield sftpserver


def create_temp_file(path, filename, content, isbyte=False):
    path.mkdir(parents=True, exist_ok=True)
    f = path / filename
    if isbyte:
        f.write_bytes(content)
    else:
        f.write_text(content)


def clear_dir(path):
    for p in path.iterdir():
        if p.is_dir():
            clear_dir(p)
            p.rmdir()
        else:
            p.unlink()


@pytest.fixture(scope="function")
def file_tree1(tmp_path):
    create_temp_file(tmp_path / "loc_project1/loc_test_data1", 'file1.txt', 'Not File1 content', False)
    create_temp_file(tmp_path / "loc_project1/loc_test_data2/loc_container", 'file21.csv', 'Not File21 content', False)
    create_temp_file(tmp_path / "loc_project1/loc_test_data2", 'container2.txt', 'Not Container2 content', False)
    create_temp_file(tmp_path / "loc_project1/loc_test_data2/loc_container", 'file22.csv.gz', gzip.compress(b'Not file 22'), True)
    yield
    clear_dir(tmp_path)


@pytest.fixture(scope='function')
def file_tree2(tmp_path):
    create_temp_file(tmp_path / 'loc_project1/loc_test_data1', 'file1.txt.bz2', bz2.compress(b'File1 content'), True)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data1', 'file2.txt.bz2', bz2.compress(b'File2 content'), True)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data2/loc_container', 'file21.csv.gz', gzip.compress(b'File21 content'), True)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data2/loc_container', 'file22.csv.gz', gzip.compress(b'FIle22 content'), True)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data2', 'container2.txt', 'Container2 content', False)
    create_temp_file(tmp_path / 'loc_project2/loc_data3', 'file31.txt', 'File31 content', False)
    create_temp_file(tmp_path / 'loc_project2/loc_data3', 'file32.txt', 'File32 content', False)
    create_temp_file(tmp_path / 'loc_project2', 'readme.txt', 'Readme file', False)
    yield
    clear_dir(tmp_path)


@pytest.fixture(scope='function')
def file_tree3(tmp_path):
    create_temp_file(tmp_path / 'loc_project1/loc_test_data1', 'file1.txt.bz2', bz2.compress(b'File1 content'), True)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data1', 'file1.txt', 'hren', False)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data1', 'file2.txt.bz2', bz2.compress(b'File2 content'), True)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data1', 'file2.txt', 'hren', False)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data2/loc_container', 'file21.csv.gz', gzip.compress(b'File21 content'), True)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data2/loc_container', 'file21.csv', 'hren', False)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data2/loc_container', 'file22.csv.gz', gzip.compress(b'FIle22 content'), True)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data2/loc_container', 'file22.csv', 'hren', False)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data2', 'container2.txt', 'Container2 content', False)
    create_temp_file(tmp_path / 'loc_project2/loc_data3', 'file31.txt', 'File31 content', False)
    create_temp_file(tmp_path / 'loc_project2/loc_data3', 'file32.txt', 'File32 content', False)
    create_temp_file(tmp_path / 'loc_project2', 'readme.txt', 'Readme file', False)
    yield
    clear_dir(tmp_path)


@pytest.fixture(scope='function')
def file_tree4(tmp_path):
    create_temp_file(tmp_path / 'loc_project1/loc_test_data1', 'file1.txt', 'File1 content', False)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data1', 'file2.txt', 'File2 content', False)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data2/loc_container', 'file21.csv', 'File21 content', False)
    create_temp_file(tmp_path / 'loc_project1/loc_test_data2/loc_container', 'file22.csv', 'FIle22 content', False)
    yield
    clear_dir(tmp_path)


@pytest.mark.parametrize('local, remote, name, arch', [
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2'),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz'),
    ('loc_project1/loc_test_data2', 'project1/test_data2', 'container2.txt', None),
    ('loc_project2/loc_data3', 'project2/data3', 'file31.txt', None),
    ('loc_project2/loc_data3', 'project2/data3', 'file32.txt', None),
    ('loc_project2', 'project2', 'readme.txt', None),
])
def test_clear(file_tree2, tmp_path, local, remote, name, arch):
    ft = loader.FileTransfer(name, tmp_path / local, remote, arch)
    ft.clear()
    if arch:
        assert False == (tmp_path / local / ft._arch_name).exists()
    assert False == (tmp_path / local / ft._name).exists()    


@pytest.mark.parametrize('local, remote, name, arch, skip, content', [
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2', True, 'File1 content'),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2', True, 'File2 content'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz', True, 'File21 content'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz', True, 'FIle22 content'),
    ('loc_project1/loc_test_data2', 'project1/test_data2', 'container2.txt', None, True, 'Container2 content'),
    ('loc_project2/loc_data3', 'project2/data3', 'file31.txt', None, True, 'File31 content'),
    ('loc_project2/loc_data3', 'project2/data3', 'file32.txt', None, True, 'File32 content'),
    ('loc_project2', 'project2', 'readme.txt', None, True, 'Readme file'),
])
def test_upload(ftp_server2, file_tree2, tmp_path, local, remote, name, arch, skip, content):
    host = '127.0.0.1'
    port = ftp_server2.port
    cnopts = CnOpts()
    cnopts.hostkeys = None
    ft = loader.FileTransfer(name, tmp_path / local, remote, arch)
    with Connection(host, port=port, username='user1', password='1234', cnopts=cnopts) as conn:
        ft.upload(conn, skip_existing=skip)
        filename = ft._arch_name
        data = ftp_server2.content_provider.get(remote + '/' + filename)
        if arch:
            data = loader.get_archivator(arch).decompress(data)
        assert data.decode() == content


@pytest.mark.parametrize('local, remote, name, arch, skip, content', [
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2', False, 'File1 content'),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2', False, 'File2 content'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz', False, 'File21 content'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz', False, 'FIle22 content'),
    ('loc_project1/loc_test_data2', 'project1/test_data2', 'container2.txt', None, False, 'Container2 content'),
    ('loc_project2/loc_data3', 'project2/data3', 'file31.txt', None, False, 'File31 content'),
    ('loc_project2/loc_data3', 'project2/data3', 'file32.txt', None, False, 'File32 content'),
    ('loc_project2', 'project2', 'readme.txt', None, False, 'Readme file'),
])
def test_upload2(ftp_server3, file_tree2, tmp_path, local, remote, name, arch, skip, content):
    host = '127.0.0.1'
    port = ftp_server3.port
    cnopts = CnOpts()
    cnopts.hostkeys = None
    ft = loader.FileTransfer(name, tmp_path / local, remote, arch)
    with Connection(host, port=port, username='user1', password='1234', cnopts=cnopts) as conn:
        ft.upload(conn, skip_existing=skip)
        filename = ft._arch_name
        data = ftp_server3.content_provider.get(remote + '/' + filename)
        if arch:
            data = loader.get_archivator(arch).decompress(data)
        assert data.decode() == content


@pytest.mark.parametrize('local, remote, name, arch, skip', [
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2', True),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2', True),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz', True),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz', True),
    ('loc_project1/loc_test_data2', 'project1/test_data2', 'container2.txt', None, True),
    ('loc_project2/loc_data3', 'project2/data3', 'file31.txt', None, True),
    ('loc_project2/loc_data3', 'project2/data3', 'file32.txt', None, True),
    ('loc_project2', 'project2', 'readme.txt', None, True),
])
def test_upload_raise(ftp_server3, file_tree2, tmp_path, local, remote, name, arch, skip):
    host = '127.0.0.1'
    port = ftp_server3.port
    cnopts = CnOpts()
    cnopts.hostkeys = None
    ft = loader.FileTransfer(name, tmp_path / local, remote, arch)
    with Connection(host, port=port, username='user1', password='1234', cnopts=cnopts) as conn:
        with pytest.raises(loader.LoaderException):
            ft.upload(conn, skip_existing=skip)


@pytest.mark.parametrize('local, remote, name, arch, skip', [
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2', False),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2', False),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz', False),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz', False),
    ('loc_project1/loc_test_data2', 'project1/test_data2', 'container2.txt', None, False),
    ('loc_project2/loc_data3', 'project2/data3', 'file31.txt', None, False),
    ('loc_project2/loc_data3', 'project2/data3', 'file32.txt', None, False),
    ('loc_project2', 'project2', 'readme.txt', None, False),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2', True),
    ('loc_project2/loc_data3', 'project2/data3', 'file31.txt', None, True),
    ('loc_project2/loc_data3', 'project2/data3', 'file32.txt', None, True),
    ('loc_project2', 'project2', 'readme.txt', None, True),

])
def test_download(ftp_server1, file_tree1, tmp_path, local, remote, name, arch, skip):
    host = '127.0.0.1'
    port = ftp_server1.port
    cnopts = CnOpts()
    cnopts.hostkeys = None
    ft = loader.FileTransfer(name, tmp_path / local, remote, arch)
    with Connection(host, port=port, username='user1', password='1234', cnopts=cnopts) as conn:
        ft.download(conn, skip_existing=skip)
        filename = ft._arch_name
        mode = 'rb' if arch else 'r'
        with open(tmp_path / local / filename, mode) as f:
            data = f.read()
            assert data == ftp_server1.content_provider.get(remote + '/' + filename)


@pytest.mark.parametrize('local, remote, name, arch, skip', [
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2', True),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz', True),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz', True),
    ('loc_project1/loc_test_data2', 'project1/test_data2', 'container2.txt', None, True),
])
def test_download_raises(ftp_server1, file_tree1, tmp_path, local, remote, name, arch, skip):
    host = '127.0.0.1'
    port = ftp_server1.port
    cnopts = CnOpts()
    cnopts.hostkeys = None
    print(tmp_path)
    ft = loader.FileTransfer(name, tmp_path / local, remote, arch)
    with Connection(host, port=port, username='user1', password='1234', cnopts=cnopts) as conn:
        with pytest.raises(loader.LoaderException):
            ft.download(conn, skip_existing=skip)
        

@pytest.mark.parametrize('local, remote, name, arch, skip, content', [
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2', False, 'File1 content'),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2', False, 'File2 content'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz', False, 'File21 content'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz', False, 'FIle22 content'),
    ('loc_project1/loc_test_data2', 'project1/test_data2', 'container2.txt', None, False, 'Container2 content'),
    ('loc_project2/loc_data3', 'project2/data3', 'file31.txt', None, False, 'File31 content'),
    ('loc_project2/loc_data3', 'project2/data3', 'file32.txt', None, False, 'File32 content'),
    ('loc_project2', 'project2', 'readme.txt', None, False, 'Readme file'),
])
def test_decompress(file_tree3, tmp_path, local, remote, name, arch, skip, content):
    ft = loader.FileTransfer(name, tmp_path / local, remote, arch)
    ft.decompress(skip)
    filename = ft._name
    with open(tmp_path / local / filename) as f:
        data = f.read()
        assert data == content


@pytest.mark.parametrize('local, remote, name, arch, skip, content', [
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2', True, 'File1 content'),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2', True, 'File2 content'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz', True, 'File21 content'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz', True, 'FIle22 content'),
    ('loc_project1/loc_test_data2', 'project1/test_data2', 'container2.txt', None, True, 'Container2 content'),
    ('loc_project2/loc_data3', 'project2/data3', 'file31.txt', None, True, 'File31 content'),
    ('loc_project2/loc_data3', 'project2/data3', 'file32.txt', None, True, 'File32 content'),
    ('loc_project2', 'project2', 'readme.txt', None, True, 'Readme file'),
])
def test_decompress2(file_tree2, tmp_path, local, remote, name, arch, skip, content):
    ft = loader.FileTransfer(name, tmp_path / local, remote, arch)
    ft.decompress(skip)
    filename = ft._name
    with open(tmp_path / local / filename) as f:
        data = f.read()
        assert data == content

@pytest.mark.parametrize('local, remote, name, arch, skip', [
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2', True),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2', True),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz', True),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz', True),
])
def test_decompress_raises(file_tree3, tmp_path, local, remote, name, arch, skip):
    ft = loader.FileTransfer(name, tmp_path / local, remote, arch)
    with pytest.raises(loader.LoaderException):
        ft.decompress(skip)


@pytest.mark.parametrize('local, remote, name, arch, skip, content', [
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2', False, 'File1 content'),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2', False, 'File2 content'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz', False, 'File21 content'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz', False, 'FIle22 content'),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2', True, 'File1 content'),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2', True, 'File2 content'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz', True, 'File21 content'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz', True, 'FIle22 content'),
])
def test_compress(file_tree4, tmp_path, local, remote, name, arch, skip, content):
    ft = loader.FileTransfer(name, tmp_path / local, remote, arch)
    ft.compress(skip)
    filename = ft._arch_name
    with open(tmp_path / local / filename, 'rb') as f:
        data = f.read()
        archivator = loader.get_archivator(arch)
        assert archivator.decompress(data).decode() == content


@pytest.mark.parametrize('local, remote, name, arch, skip, content', [
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2', False, 'hren'),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2', False, 'hren'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz', False, 'hren'),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz', False, 'hren'),
])
def test_compress2(file_tree3, tmp_path, local, remote, name, arch, skip, content):
    ft = loader.FileTransfer(name, tmp_path / local, remote, arch)
    ft.compress(skip)
    filename = ft._arch_name
    with open(tmp_path / local / filename, 'rb') as f:
        data = f.read()
        archivator = loader.get_archivator(arch)
        assert archivator.decompress(data).decode() == content


@pytest.mark.parametrize('local, remote, name, arch, skip', [
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file1.txt', 'bz2', True),
    ('loc_project1/loc_test_data1', 'project1/test_data1', 'file2.txt', 'bz2', True),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file21.csv', 'gz', True),
    ('loc_project1/loc_test_data2/loc_container', 'project1/test_data2/container', 'file22.csv', 'gz', True),
])
def test_compress_raises(file_tree3, tmp_path, local, remote, name, arch, skip):
    ft = loader.FileTransfer(name, tmp_path / local, remote, arch)
    with pytest.raises(loader.LoaderException):
        ft.compress(skip)



