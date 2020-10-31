# -*- coding: utf-8 -*-

import pytest
from ftp_loader import loader


@pytest.mark.parametrize("filename, ans_url, ans_path, ans_files", [
    (
        'tests/ftp-config.toml', 'server.ftp.ru', '/projects/test-data', 
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


@pytest.mark.parametrize("path, options, files, answer", [
    (
        '/projects/test-data', {},
        [
            {
                'dst': 'work', 'src': 'storage', 'arch': 'bz2',
                'names': ['data1.txt', 'data2.txt']
            },
            {
                'dst': 'experiment', 'src': 'experiment', 'arch': 'gz',
                'names': ['data1.csv', 'data2.csv']
            }

        ], 
        [
            ('/projects/test-data/storage/data1.txt.bz2', r'work\data1.txt.bz2'),
            ('/projects/test-data/storage/data2.txt.bz2', r'work\data2.txt.bz2'),
            ('/projects/test-data/experiment/data1.csv.gz', r'experiment\data1.csv.gz'),
            ('/projects/test-data/experiment/data2.csv.gz', r'experiment\data2.csv.gz')
        ]
    )
])
def test_select_paths(path, options, files, answer):
    path_pairs = loader.select_paths_for_download(path, files, **options)
    assert path_pairs == answer
